"""Player protection limits. Per ADR-0084 / DEC-0084. Phase 14.

UK GC mandate: player-configurable limits (deposit, loss, wagering, session).
Tightening = instant; loosening = cooling-off (24h-7d configurable).
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional


class LimitType(str, enum.Enum):
    DEPOSIT = "deposit"
    LOSS = "loss"
    WAGERING = "wagering"
    SESSION_TIME = "session_time"


class LimitPeriod(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


# Default cooling-off for limit loosening (Phase 14 default per DEC-0157).
DEFAULT_LOOSEN_COOLING_OFF_HOURS = 24


@dataclass
class PlayerLimit:
    """Player protection limit. Per ADR-0084.

    Enforcement:
    - Deposit: Phase 12 payment service checks before processing.
    - Wagering: Phase 15 game platform checks before accepting bet.
    - Loss: calculated from Phase 11 ledger (cumulative net loss per period).
    - Session: client timer + server enforcement on every API call.
    """

    limit_uuid: uuid.UUID
    tenant_uuid: uuid.UUID
    player_uuid: uuid.UUID
    limit_type: LimitType
    period: LimitPeriod
    amount_minor: int  # Integer minor units (or minutes for session_time)
    current_cumulative: int = 0
    reset_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    # Cooling-off for loosening
    pending_new_amount: Optional[int] = None
    pending_effective_at: Optional[datetime] = None

    @property
    def is_exceeded(self) -> bool:
        """True if current cumulative >= amount_minor."""
        return self.current_cumulative >= self.amount_minor

    @property
    def remaining(self) -> int:
        """Remaining amount before limit is exceeded."""
        return max(0, self.amount_minor - self.current_cumulative)

    def tighten(self, new_amount: int) -> None:
        """Tighten (lower) the limit. Instant — no cooling-off.

        Per ADR-0084: tightening is instant (player can always reduce limits).
        """
        if new_amount >= self.amount_minor:
            raise ValueError("Tighten requires new_amount < current amount")
        self.amount_minor = new_amount
        self.updated_at = datetime.now(timezone.utc)

    def loosen(self, new_amount: int, cooling_off_hours: int = DEFAULT_LOOSEN_COOLING_OFF_HOURS) -> None:
        """Loosen (raise) the limit. Cooling-off period enforced.

        Per ADR-0084: loosening has 24h-7d cooling-off (configurable).
        The new amount is pending until cooling-off expires.
        """
        if new_amount <= self.amount_minor:
            raise ValueError("Loosen requires new_amount > current amount")
        self.pending_new_amount = new_amount
        self.pending_effective_at = datetime.now(timezone.utc) + timedelta(hours=cooling_off_hours)
        self.updated_at = datetime.now(timezone.utc)

    def apply_pending_loosen(self) -> bool:
        """Apply pending loosening if cooling-off has expired.

        Returns True if applied, False if still in cooling-off.
        """
        if self.pending_new_amount is None or self.pending_effective_at is None:
            return False
        if datetime.now(timezone.utc) < self.pending_effective_at:
            return False  # Still in cooling-off.
        self.amount_minor = self.pending_new_amount
        self.pending_new_amount = None
        self.pending_effective_at = None
        self.updated_at = datetime.now(timezone.utc)
        return True

    def consume(self, amount: int) -> bool:
        """Consume from the limit. Returns True if within limit, False if exceeded.

        Per ADR-0084: every deposit/bet checks limits.
        """
        if self.current_cumulative + amount > self.amount_minor:
            return False  # Limit exceeded.
        self.current_cumulative += amount
        return True
