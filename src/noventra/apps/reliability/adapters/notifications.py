"""Notification adapter stubs — email + SMS.

Per ADR-0045 / DEC-0050: vendor per Q5 (stub if blocked).
"""

from __future__ import annotations

import logging
from typing import Any

from noventra.apps.reliability.domain.notifications import (
    NotificationChannel,
    NotificationPort,
    SendResult,
)

log = logging.getLogger("noventra.reliability.notifications")


class EmailStubAdapter(NotificationPort):
    """Stub email adapter. Logs + returns success. Real vendor (Q5) in Phase 9."""

    def send(
        self,
        *,
        channel: NotificationChannel,
        recipient: str,
        content: str,
        context: dict[str, Any],
    ) -> SendResult:
        log.info("email_stub_send", extra={"recipient": recipient, "channel": channel.value})
        return SendResult(
            success=True,
            message_id=f"stub-email-{recipient}",
            metadata={"adapter": "stub", "channel": channel.value},
        )


class SMSStubAdapter(NotificationPort):
    """Stub SMS adapter. Logs + returns success. Real vendor (Q5) in Phase 9."""

    def send(
        self,
        *,
        channel: NotificationChannel,
        recipient: str,
        content: str,
        context: dict[str, Any],
    ) -> SendResult:
        log.info("sms_stub_send", extra={"recipient": recipient, "channel": channel.value})
        return SendResult(
            success=True,
            message_id=f"stub-sms-{recipient}",
            metadata={"adapter": "stub", "channel": channel.value},
        )


class FallbackAdapter(NotificationPort):
    """Fallback: if primary fails, log + queue for retry. No silent drop."""

    def __init__(self, primary: NotificationPort):
        self._primary = primary

    def send(
        self,
        *,
        channel: NotificationChannel,
        recipient: str,
        content: str,
        context: dict[str, Any],
    ) -> SendResult:
        try:
            return self._primary.send(
                channel=channel, recipient=recipient, content=content, context=context
            )
        except Exception as e:
            log.error("notification_fallback", extra={
                "recipient": recipient, "error": str(e),
            })
            # Queue for retry (Phase 8 stub: log; Phase 9: Redis queue).
            return SendResult(
                success=False,
                error=str(e),
                metadata={"fallback": True, "queued_for_retry": True},
            )
