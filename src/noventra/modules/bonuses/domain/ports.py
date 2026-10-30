"""Port interfaces for forward-dependencies. Per ADR-0081, ADR-0082. Phase 13.

RGPort (Phase 14 implements real adapter).
RealtimePort (Phase 22 implements real WebSocket fan-out).

Stubs are permissive (RG) or log+no-op (realtime) in Phase 13.
"""

from __future__ import annotations

import abc
import logging
import uuid
from typing import Any

log = logging.getLogger("noventra.bonuses.ports")


class RGPort(abc.ABC):
    """Port: Responsible Gambling checks. Per ADR-0081.

    Phase 13: StubRGAdapter (permissive — returns True).
    Phase 14: RealRGAdapter (actual RG enforcement).
    """

    @abc.abstractmethod
    def check_self_exclusion(self, player_id: uuid.UUID) -> bool:
        """Returns True if player is NOT self-excluded (can proceed)."""

    @abc.abstractmethod
    def check_deposit_limit(self, player_id: uuid.UUID, amount: int) -> bool:
        """Returns True if deposit is within limit."""

    @abc.abstractmethod
    def check_loss_limit(self, player_id: uuid.UUID) -> bool:
        """Returns True if player is within loss limit."""


# JurisdictionPort removed per DEC-0157 (Global Mode)


class RealtimePort(abc.ABC):
    """Port: Realtime invalidation. Per ADR-0082.

    Phase 13: StubRealtimeAdapter (logs + no-ops).
    Phase 22: RealRealtimeAdapter (WebSocket fan-out).
    """

    @abc.abstractmethod
    def invalidate(
        self,
        tenant_id: uuid.UUID,
        channel: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        """Invalidate a realtime channel. Connected clients receive the event."""
