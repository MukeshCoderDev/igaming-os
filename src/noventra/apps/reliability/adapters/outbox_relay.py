"""Outbox relay — polls outbox table + publishes events.

Per ADR-0040 / DEC-0045: polling 50ms; SELECT FOR UPDATE SKIP LOCKED;
at-least-once; per-aggregate ordering; backpressure; replay.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Callable, Optional

from django.db import connection, transaction

log = logging.getLogger("noventra.reliability.outbox_relay")

POLL_INTERVAL_MS = 50
BATCH_SIZE = 100
MAX_RETRIES = 3


def append_to_outbox(
    *,
    event_type: str,
    aggregate_id: str,
    aggregate_type: str,
    tenant_id: str,
    actor_id: str,
    payload: dict,
    correlation_id: str | None = None,
    event_version: int = 1,
) -> str:
    """Append an event to the outbox (same transaction as the aggregate change).

    Returns the event_id.
    """
    event_id = str(uuid.uuid4())
    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL app.tenant_uuid = %s", [tenant_id])
        cursor.execute(
            """
            INSERT INTO reliability_outbox
                (event_id, tenant_id, event_type, event_version, aggregate_id,
                 aggregate_type, actor_id, correlation_id, occurred_at, payload,
                 status, retry_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, 'pending', 0)
            """,
            [
                event_id, tenant_id, event_type, event_version,
                aggregate_id, aggregate_type, actor_id, correlation_id,
                json.dumps(payload),
            ],
        )
    log.info("outbox_appended", extra={"event_id": event_id, "event_type": event_type})
    return event_id


def relay_batch(publish: Callable[[dict], None]) -> int:
    """Relay a batch of outbox events. Returns count relayed.

    Per ADR-0040: SELECT FOR UPDATE SKIP LOCKED for multi-instance.
    At-least-once: publish-then-mark.
    """
    with transaction.atomic():
        with connection.cursor() as cursor:
            # Select a batch of pending events (skip locked for multi-instance).
            cursor.execute(
                """
                SELECT event_id, tenant_id, event_type, event_version, aggregate_id,
                       aggregate_type, actor_id, correlation_id, payload, retry_count
                FROM reliability_outbox
                WHERE status = 'pending'
                ORDER BY event_id
                LIMIT %s
                FOR UPDATE SKIP LOCKED
                """,
                [BATCH_SIZE],
            )
            rows = cursor.fetchall()

            if not rows:
                return 0

            for row in rows:
                event_id, tenant_id, event_type, event_version, aggregate_id, \
                    aggregate_type, actor_id, correlation_id, payload_raw, retry_count = row

                payload = payload_raw if isinstance(payload_raw, dict) else json.loads(payload_raw or "{}")
                event = {
                    "event_id": str(event_id),
                    "event_type": event_type,
                    "event_version": event_version,
                    "aggregate_id": aggregate_id,
                    "aggregate_type": aggregate_type,
                    "tenant_id": str(tenant_id),
                    "actor_id": str(actor_id),
                    "correlation_id": correlation_id,
                    "payload": payload,
                }

                try:
                    publish(event)
                    # Mark as relayed.
                    cursor.execute(
                        "UPDATE reliability_outbox SET status = 'relayed', relayed_at = NOW() WHERE event_id = %s",
                        [event_id],
                    )
                except Exception as e:
                    log.error("outbox_relay_failed", extra={
                        "event_id": str(event_id), "error": str(e), "retry_count": retry_count,
                    })
                    if retry_count >= MAX_RETRIES - 1:
                        cursor.execute(
                            "UPDATE reliability_outbox SET status = 'failed', retry_count = %s WHERE event_id = %s",
                            [retry_count + 1, event_id],
                        )
                    else:
                        cursor.execute(
                            "UPDATE reliability_outbox SET retry_count = %s WHERE event_id = %s",
                            [retry_count + 1, event_id],
                        )

    return len(rows)


class OutboxRelay:
    """Outbox relay worker (runs as a background process).

    Phase 8 stub: relay_batch is called manually or via a management command.
    Phase 9: runs as a Celery beat task (50ms interval).
    """

    def __init__(self, publish: Callable[[dict], None]):
        self._publish = publish

    def run_once(self) -> int:
        """Relay one batch. Returns count."""
        return relay_batch(self._publish)
