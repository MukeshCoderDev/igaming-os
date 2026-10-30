"""Bonus award domain — wagering requirements + max bet + consumption order.

Per ADR-0079 / DEC-0079. Phase 13.
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


class AwardState(str, enum.Enum):
    """Bonus award lifecycle states per ADR-0079."""
    PENDING = "pending"
    ACTIVE = "active"
    WAGERING_IN_PROGRESS = "wagering_in_progress"
    WAGERING_COMPLETE = "wagering_complete"
    CONVERTED = "converted"  # Terminal — bonus → real money
    EXPIRED = "expired"  # Terminal
    FORFEITED = "forfeited"  # Terminal
    CANCELLED = "cancelled"  # Terminal
    REVOKED = "revoked"  # Terminal (abuse detection)


@dataclass
class BonusAward:
    """Bonus award entity. Per ADR-0079.

    Wagering requirements: multiplier (e.g., 30x), game-class contributions,
    time limit, max bet during wagering (UK GC mandate).
    Bonus-first consumption order.
    Conversion: bonus_balance → real_balance via Phase 11 ledger entry.
    """

    award_uuid: uuid.UUID
    tenant_uuid: uuid.UUID
    player_uuid: uuid.UUID
    offer_uuid: uuid.UUID
    state: str = AwardState.PENDING.value
    bonus_balance_minor: int = 0  # Integer minor units (no floats, rule 78)
    real_balance_at_award: int = 0
    wagering_requirement_multiplier: int = 30  # e.g., 30x
    wagering_requirement_amount: int = 0  # multiplier × bonus_balance
    wagered_amount: int = 0
    max_bet_during_wagering: int = 500  # e.g., $5.00 in minor units
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    @property
    def remaining_wagering(self) -> int:
        """Remaining wagering requirement amount."""
        return max(0, self.wagering_requirement_amount - self.wagered_amount)

    @property
    def is_wagering_complete(self) -> bool:
        """True if wagering requirement is met."""
        return self.wagered_amount >= self.wagering_requirement_amount

    @property
    def is_expired(self) -> bool:
        """True if the award has expired (time limit)."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def apply_bet(self, bet_amount: int, game_class_contribution: float = 1.0) -> int:
        """Apply a bet to the award. Returns amount consumed from bonus balance.

        Per ADR-0079: bonus-first consumption. Bets consume bonus balance
        before real balance. Each bet reduces remaining wagering by
        (bet_amount × game_class_contribution).

        Args:
            bet_amount: The bet amount in minor units.
            game_class_contribution: Contribution rate (slots=1.0, table=0.1, live=0.05).

        Returns:
            Amount consumed from bonus balance.
        """
        if self.state not in (AwardState.ACTIVE.value, AwardState.WAGERING_IN_PROGRESS.value):
            return 0

        if self.state == AwardState.ACTIVE.value:
            self.state = AwardState.WAGERING_IN_PROGRESS.value

        # Max bet enforcement (UK GC mandate).
        if bet_amount > self.max_bet_during_wagering:
            raise ValueError(
                f"Bet {bet_amount} exceeds max bet during wagering {self.max_bet_during_wagering}"
            )

        # Bonus-first consumption.
        consumed_from_bonus = min(bet_amount, self.bonus_balance_minor)
        self.bonus_balance_minor -= consumed_from_bonus

        # Wagering progress.
        self.wagered_amount += int(bet_amount * game_class_contribution)

        # Check if wagering complete.
        if self.is_wagering_complete:
            self.state = AwardState.WAGERING_COMPLETE.value

        return consumed_from_bonus

    def convert(self) -> bool:
        """Convert bonus balance to real balance. Per ADR-0079.

        Only allowed when wagering is complete.
        Returns True if conversion succeeded.
        Triggers Phase 11 ledger entry: debit player-bonus-balance, credit
        player-real-balance (per ADR-0083).
        """
        if self.state != AwardState.WAGERING_COMPLETE.value:
            return False

        # Conversion: bonus_balance → real_balance.
        # The actual ledger posting happens in the service layer (same DB
        # transaction per ADR-0083).
        self.state = AwardState.CONVERTED.value
        self.bonus_balance_minor = 0
        return True

    def forfeit(self) -> bool:
        """Forfeit the award. Per ADR-0079.

        Forfeiture: debit bonus-balance, credit house (per ADR-0083).
        """
        if self.state in (AwardState.CONVERTED.value, AwardState.EXPIRED.value,
                          AwardState.FORFEITED.value, AwardState.REVOKED.value):
            return False

        self.state = AwardState.FORFEITED.value
        self.bonus_balance_minor = 0
        return True
