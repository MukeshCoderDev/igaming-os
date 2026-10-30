"""Port interfaces for Phase 14 forward-dependencies.

Per ADR-0090 (RoundVoidingPort — Phase 15 implements).
Per ADR-0088 (GeoPort — Q5-blocked stub).
"""

from __future__ import annotations

import abc
import uuid
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class VoidResult:
    """Result of a round voiding operation."""
    success: bool
    error: Optional[str] = None


class RoundVoidingPort(abc.ABC):
    """Port: round voiding. Per ADR-0090.

    Phase 14: StubRoundVoidingAdapter (logs void request).
    Phase 15: RealRoundVoidingAdapter (actual bet returns via Phase 11 ledger reversal).

    Called by: kill switch trigger, SE activation, reality check failure.
    """

    @abc.abstractmethod
    def void_round(
        self,
        *,
        tenant_id: uuid.UUID,
        round_id: str,
        reason: str,
    ) -> VoidResult:
        """Void a game round. Bets are returned to players.

        Args:
            tenant_id: The tenant the round belongs to.
            round_id: The round to void.
            reason: The reason for voiding (e.g., "kill_switch", "self_exclusion").

        Returns:
            VoidResult indicating success or failure.
        """


@dataclass(frozen=True)
class GeoResult:
    """Result of a geo lookup. Per ADR-0088."""
    country_code: str  # ISO 3166-1 alpha-2
    is_vpn: bool = False
    is_proxy: bool = False
    is_datacenter: bool = False
    isp: Optional[str] = None


class GeoPort(abc.ABC):
    """Port: geo lookup + VPN/proxy detection. Per ADR-0088.

    Phase 14: StubGeoAdapter (returns country=unknown, no VPN flag).
    Phase 22: Real adapter (MaxMind GeoIP2 + IPQualityScore; Q5-blocked).
    """

    @abc.abstractmethod
    def get_geo(self, ip_address: str) -> GeoResult:
        """Look up geographic information for an IP address.

        Args:
            ip_address: The IP address to look up.

        Returns:
            GeoResult with country code, VPN/proxy/datacenter flags.
        """
