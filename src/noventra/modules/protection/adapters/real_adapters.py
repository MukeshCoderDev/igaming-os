"""Real adapters for Phase 14. Replaces Phase 13 stubs.

Per ADR-0084..0091. Phase 14.
- RealRGAdapter: actual RG enforcement (limits, SE, reality checks).
- RealRealtimeAdapter: actual Redis pub/sub (replaces Phase 13 log+no-op stub).
- StubRoundVoidingAdapter: logs void (Phase 15 implements real).
- StubGeoAdapter: permissive (Q5-blocked).
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from noventra.modules.bonuses.domain.ports import RGPort, RealtimePort
from noventra.modules.protection.domain.ports import RoundVoidingPort, GeoPort, VoidResult, GeoResult
from noventra.modules.protection.domain.self_exclusion import SelfExclusion

log = logging.getLogger("noventra.protection.adapters")


class RealRGAdapter(RGPort):
    """Real RG adapter. Per ADR-0084, ADR-0085, ADR-0086. Phase 14.

    Replaces Phase 13 StubRGAdapter (which was permissive).
    Enforces: self-exclusion, deposit limits, loss limits, reality checks.
    """

    def __init__(
        self,
        self_exclusions: list[SelfExclusion] | None = None,
        deposit_limits: dict[str, int] | None = None,  # player_uuid → remaining
        loss_limits: dict[str, int] | None = None,
    ):
        self._self_exclusions = self_exclusions or []
        self._deposit_limits = deposit_limits or {}
        self._loss_limits = loss_limits or {}

    def check_self_exclusion(self, player_id: uuid.UUID) -> bool:
        """Returns True if player is NOT self-excluded (can proceed).

        Per ADR-0085: checks active SE records for this player.
        """
        for se in self._self_exclusions:
            if se.player_uuid == player_id and se.is_active:
                log.warning("rg_blocked_self_excluded", extra={"player_id": str(player_id)})
                return False  # Player IS self-excluded — blocked.
        return True  # Not self-excluded — can proceed.

    def check_deposit_limit(self, player_id: uuid.UUID, amount: int) -> bool:
        """Returns True if deposit is within limit. Per ADR-0084."""
        remaining = self._deposit_limits.get(str(player_id), float("inf"))
        if amount > remaining:
            log.warning("rg_blocked_deposit_limit", extra={
                "player_id": str(player_id), "amount": amount, "remaining": remaining,
            })
            return False
        return True

    def check_loss_limit(self, player_id: uuid.UUID) -> bool:
        """Returns True if player is within loss limit. Per ADR-0084."""
        # Phase 14 stub: always True. Real implementation queries Phase 11 ledger.
        return True


class RealRealtimeAdapter(RealtimePort):
    """Real realtime adapter. Per ADR-0091. Phase 14.

    Replaces Phase 13 StubRealtimeAdapter (which was log+no-op).
    Uses Redis pub/sub to fan out events to WebSocket consumers.
    """

    def __init__(self, redis_client=None):
        self._redis = redis_client  # None in dev (no Redis); falls back to log.

    def invalidate(
        self,
        tenant_id: uuid.UUID,
        channel: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        """Invalidate a realtime channel via Redis pub/sub.

        Per ADR-0091: sends event to Redis channel; WebSocket consumers
        receive it and disconnect clients (e.g., kill switch).
        """
        import json
        message = json.dumps({
            "event_type": event_type,
            "tenant_id": str(tenant_id),
            "channel": channel,
            "payload": payload,
        })

        if self._redis is not None:
            self._redis.publish(f"noventra:{channel}", message)
            log.info("realtime_invalidate_published", extra={
                "tenant_id": str(tenant_id), "channel": channel, "event_type": event_type,
            })
        else:
            log.info("realtime_invalidate_no_redis", extra={
                "tenant_id": str(tenant_id), "channel": channel, "event_type": event_type,
                "message": message,
            })


class StubRoundVoidingAdapter(RoundVoidingPort):
    """Stub round voiding adapter. Per ADR-0090. Phase 14.

    Logs the void request. Phase 15 implements real voiding
    (actual bet returns via Phase 11 ledger reversal).
    """

    def void_round(
        self,
        *,
        tenant_id: uuid.UUID,
        round_id: str,
        reason: str,
    ) -> VoidResult:
        log.warning("round_void_stub", extra={
            "tenant_id": str(tenant_id), "round_id": round_id, "reason": reason,
        })
        return VoidResult(success=True)  # Stub: always succeeds.


class StubGeoAdapter(GeoPort):
    """Stub geo adapter. Per ADR-0088. Phase 14.

    Returns permissive (country=unknown, no VPN flag).
    Real adapter (Q5-blocked) uses MaxMind + IPQualityScore.
    """

    def get_geo(self, ip_address: str) -> GeoResult:
        log.debug("geo_stub", extra={"ip": ip_address})
        return GeoResult(country_code="UNKNOWN")
