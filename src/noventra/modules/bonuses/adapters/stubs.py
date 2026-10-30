"""Stub adapters for Phase 13 forward-dependency ports.

Per ADR-0081, ADR-0082. Phase 14 implements real RG adapter.
Phase 22 implements real Realtime adapter.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from noventra.modules.bonuses.domain.ports import RGPort, RealtimePort

log = logging.getLogger("noventra.bonuses.adapters.stubs")


class StubRGAdapter(RGPort):
    """Stub RG adapter. Permissive — returns True for all checks.

    Phase 14 replaces with RealRGAdapter (actual RG enforcement).
    """

    def check_self_exclusion(self, player_id: uuid.UUID) -> bool:
        log.debug("stub_rg: check_self_exclusion (permissive)", extra={"player_id": str(player_id)})
        return True  # Permissive: not self-excluded.

    def check_deposit_limit(self, player_id: uuid.UUID, amount: int) -> bool:
        log.debug("stub_rg: check_deposit_limit (permissive)", extra={"player_id": str(player_id), "amount": amount})
        return True  # Permissive: within limit.

    def check_loss_limit(self, player_id: uuid.UUID) -> bool:
        log.debug("stub_rg: check_loss_limit (permissive)", extra={"player_id": str(player_id)})
        return True  # Permissive: within limit.


class StubRealtimeAdapter(RealtimePort):
    """Stub Realtime adapter. Logs the event + no-ops.

    Phase 22 replaces with RealRealtimeAdapter (WebSocket fan-out).
    """

    def invalidate(
        self,
        tenant_id: uuid.UUID,
        channel: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        log.info("stub_realtime: invalidate (no-op)",
                 extra={
                     "tenant_id": str(tenant_id),
                     "channel": channel,
                     "event_type": event_type,
                 })
        # No-op: connected clients do NOT receive the event in Phase 13.
        # They'll see the change on next API call.
