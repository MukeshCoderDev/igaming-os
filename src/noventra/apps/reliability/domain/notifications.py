"""Notifications domain — port interface + send types.

Per ADR-0045 / DEC-0050: port interface documented; channels email + SMS;
adapters per channel; vendor per Q5; fallback strategy.
"""

from __future__ import annotations

import abc
import enum
from dataclasses import dataclass, field
from typing import Any, Optional


class NotificationChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    # PUSH = "push"  # Phase 9+
    # WEBHOOK = "webhook"  # Phase 9+


class SendType(str, enum.Enum):
    """Send-type taxonomy per ADR-0046.

    transactional: bypasses suppression, respects caps.
    marketing: respects both suppression + caps.
    """

    TRANSACTIONAL = "transactional"
    MARKETING = "marketing"


@dataclass(frozen=True)
class SendResult:
    """Result of a notification send."""

    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class NotificationPort(abc.ABC):
    """Port: notification sending interface.

    Per ADR-0045: send(channel, recipient, content, context) -> SendResult.
    Adapters implement this per channel (vendor per Q5; stub if blocked).
    """

    @abc.abstractmethod
    def send(
        self,
        *,
        channel: NotificationChannel,
        recipient: str,
        content: str,
        context: dict[str, Any],
    ) -> SendResult:
        """Send a notification. Returns SendResult."""
