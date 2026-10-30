"""Self-exclusion + cooling-off + SE-survives-erasure.

Per ADR-0085 / DEC-0085. Phase 14.
HMAC pseudonymization: SE record survives player erasure (Phase 9).
Cross-module enforcement via RGPort (Law 18).
"""

from __future__ import annotations

import enum
import hashlib
import hmac
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional


class ExclusionPeriod(str, enum.Enum):
    SIX_MONTHS = "6m"
    ONE_YEAR = "1y"
    TWO_YEARS = "2y"
    FIVE_YEARS = "5y"
    LIFETIME = "lifetime"


# Period duration mapping (for non-lifetime).
PERIOD_DURATIONS = {
    ExclusionPeriod.SIX_MONTHS: timedelta(days=182),
    ExclusionPeriod.ONE_YEAR: timedelta(days=365),
    ExclusionPeriod.TWO_YEARS: timedelta(days=730),
    ExclusionPeriod.FIVE_YEARS: timedelta(days=1825),
}

# Default reactivation cooling-off (Phase 14 default per DEC-0157).
DEFAULT_REACTIVATION_COOLING_OFF_HOURS = 24


def compute_pseudonymized_identity(identity_document: str, secret_key: str) -> str:
    """Compute HMAC of identity document for SE-survives-erasure.

    Per ADR-0085: the HMAC survives player erasure. On new registration,
    the same identity document produces the same HMAC, allowing detection
    of excluded players who try to re-register after erasure.

    Args:
        identity_document: The player's identity document (e.g., passport number).
        secret_key: The HMAC key (from settings.SECRET_KEY or dedicated SE key).

    Returns:
        Hex-encoded HMAC-SHA256.
    """
    return hmac.new(
        secret_key.encode("utf-8"),
        identity_document.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


@dataclass
class SelfExclusion:
    """Self-exclusion record. Per ADR-0085.

    Persists across erasure via HMAC pseudonymization.
    Cross-module enforcement via RGPort: games/bonuses/payments/marketing blocked.
    """

    exclusion_uuid: uuid.UUID
    tenant_uuid: uuid.UUID
    player_uuid: Optional[uuid.UUID]  # NULL after erasure (retained with pseudonymized_identity)
    period: ExclusionPeriod
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ends_at: Optional[datetime] = None  # None for lifetime
    status: str = "active"  # active, expired, reactivated
    pseudonymized_identity: str = ""  # HMAC of identity document
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Compute ends_at based on period."""
        if self.period != ExclusionPeriod.LIFETIME and self.ends_at is None:
            duration = PERIOD_DURATIONS.get(self.period)
            if duration:
                self.ends_at = self.started_at + duration

    @property
    def is_active(self) -> bool:
        """True if SE is currently active (not expired, not reactivated)."""
        if self.status != "active":
            return False
        if self.ends_at is None:
            return True  # Lifetime exclusion.
        return datetime.now(timezone.utc) < self.ends_at

    @property
    def can_reactivate(self) -> bool:
        """True if reactivation is allowed (period has ended)."""
        if self.status != "active":
            return False
        if self.ends_at is None:
            return False  # Lifetime — cannot reactivate.
        return datetime.now(timezone.utc) >= self.ends_at

    def reactivate(self, cooling_off_hours: int = DEFAULT_REACTIVATION_COOLING_OFF_HOURS) -> bool:
        """Reactivate the self-exclusion after the period ends.

        Per ADR-0085: only after ends_at; explicit player request;
        24h cooling-off before reactivation; audit-logged.

        Returns True if reactivation initiated (cooling-off started).
        """
        if not self.can_reactivate:
            return False

        # Phase 14 stub: immediately set status to reactivated.
        # Real implementation: start 24h cooling-off, then reactivate.
        self.status = "reactivated"
        self.updated_at = datetime.now(timezone.utc)
        return True

    @staticmethod
    def check_pseudonymized_identity(
        pseudonymized_identity: str,
        existing_exclusions: list["SelfExclusion"],
    ) -> bool:
        """Check if a pseudonymized identity has an active SE.

        Per ADR-0085: on new registration, check pseudonymized_identity
        against SE registry. Reject if active SE.

        Returns True if the identity is clear (no active SE).
        Returns False if the identity has an active SE (registration should be rejected).
        """
        for exclusion in existing_exclusions:
            if exclusion.pseudonymized_identity == pseudonymized_identity:
                if exclusion.is_active:
                    return False  # Active SE — reject registration.
        return True  # No active SE — allow registration.
