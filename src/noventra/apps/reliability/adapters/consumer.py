"""Consumer base class + inbox dedup.

Per ADR-0041 / DEC-0046: inbox table with (message_id, consumer_id) PK;
ON CONFLICT DO NOTHING; insert after processing in same transaction.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from typing import Any, Callable

from django.db import connection, transaction

log = logging.getLogger("noventra.reliability.consumer")


class ConsumerBase:
    """Base class for inbox-dedup consumers.

    Per ADR-0041: process(message) wraps the handler in a transaction +
    inbox insert. Duplicates are detected by ON CONFLICT DO NOTHING.
    """

    def __init__(self, consumer_id: str):
        self.consumer_id = consumer_id

    def process(self, message: dict[str, Any]) -> bool:
        """Process a message with inbox dedup. Returns True if processed, False if duplicate.

        Per ADR-0041: insert into inbox in the SAME transaction as the side effect.
        """
        message_id = message.get("event_id") or message.get("message_id")
        if not message_id:
            log.error("consumer_missing_message_id", extra={"consumer": self.consumer_id})
            return False

        tenant_id = message.get("tenant_id")
        if not tenant_id:
            log.error("consumer_missing_tenant_id", extra={"consumer": self.consumer_id})
            return False

        payload_hash = hashlib.sha256(
            json.dumps(message, sort_keys=True).encode()
        ).hexdigest()

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL app.tenant_uuid = %s", [tenant_id])

                # Check if already processed (inbox dedup).
                cursor.execute(
                    "SELECT 1 FROM reliability_inbox WHERE message_id = %s AND consumer_id = %s",
                    [message_id, self.consumer_id],
                )
                if cursor.fetchone():
                    log.info("consumer_duplicate_skipped", extra={
                        "message_id": message_id, "consumer": self.consumer_id,
                    })
                    return False

                # Process the message (handler runs in this transaction).
                try:
                    self.handle(message)
                except Exception as e:
                    log.error("consumer_handler_failed", extra={
                        "message_id": message_id, "error": str(e),
                    })
                    raise  # Transaction rolls back; no inbox insert.

                # Insert into inbox (same transaction as the side effect).
                cursor.execute(
                    """
                    INSERT INTO reliability_inbox (message_id, consumer_id, processed_at, tenant_id, payload_hash)
                    VALUES (%s, %s, NOW(), %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    [message_id, self.consumer_id, tenant_id, payload_hash],
                )

        log.info("consumer_processed", extra={
            "message_id": message_id, "consumer": self.consumer_id,
        })
        return True

    def handle(self, message: dict[str, Any]) -> None:
        """Override: process the message. Called within a transaction."""
        raise NotImplementedError


class DLQConsumer(ConsumerBase):
    """Consumer that moves poison messages to a DLQ.

    Per ADR-0042 / DEC-0047: poison criteria (N=3 retries, deserialization
    failure, terminal error, TTL exceeded). DLQ in Redis Stream (Phase 8).
    """

    def __init__(self, consumer_id: str, dlq_publisher: Callable[[dict, str], None] | None = None):
        super().__init__(consumer_id)
        self._dlq_publisher = dlq_publisher

    def handle(self, message: dict[str, Any]) -> None:
        """Default: no-op. Override for real processing."""
        pass

    def send_to_dlq(self, message: dict[str, Any], reason: str) -> None:
        """Send a poison message to the DLQ."""
        if self._dlq_publisher:
            enriched = {
                **message,
                "dlq_reason": reason,
                "dlq_consumer": self.consumer_id,
                "dlq_timestamp": str(uuid.uuid4()),  # Phase 8 stub; real timestamp in prod.
            }
            self._dlq_publisher(enriched, reason)
            log.warning("dlq_message_sent", extra={
                "message_id": message.get("event_id"),
                "reason": reason,
            })
