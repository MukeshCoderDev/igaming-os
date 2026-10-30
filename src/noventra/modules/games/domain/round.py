"""Games domain — game round model, FSM, bet→ledger, round voiding.

Per ADR-0092..0094 / DEC-0093..0095. Phase 15.
Builds on: Phase 11 (ledger), Phase 13 (bonus wagering), Phase 14 (RG/kill switch).
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from noventra.apps.reliability.domain.state_machine import (
    StateMachineMixin, TransitionError, transition,
)


class RoundState(str, enum.Enum):
    """Game round lifecycle states. Per ADR-0092."""
    OPEN = "open"           # Accepting bets
    CLOSED = "closed"       # No more bets; awaiting outcome
    SETTLED = "settled"     # Outcome determined; winnings paid
    VOIDED = "voided"       # Round voided (kill switch / SE / reality check fail)
    CANCELLED = "cancelled"  # Cancelled (operator action)


class BetType(str, enum.Enum):
    """Bet types."""
    WAGER = "wager"         # Real money bet
    BONUS = "bonus"         # Bonus balance bet (Phase 13 wagering)
    FREE_PLAY = "free_play" # Free play (no money)


@dataclass
class GameRound(StateMachineMixin):
    """Game round entity with FSM. Per ADR-0092.

    Round lifecycle: OPEN → CLOSED → SETTLED (or VOIDED/CANCELLED).
    Bets accepted during OPEN; no bets after CLOSED.
    Settlement posts to Phase 11 ledger (ADR-0092).
    Voiding returns bets via RealRoundVoidingAdapter (ADR-0093).
    """

    round_uuid: uuid.UUID
    tenant_uuid: uuid.UUID
    game_id: str  # Game identifier (e.g., "slots_starburst", "roulette_european")
    state: str = RoundState.OPEN.value
    total_bet_minor: int = 0  # Total bets in minor units
    total_payout_minor: int = 0  # Total payouts in minor units
    currency_code: str = "USD"
    exponent_at_time: int = 2
    opened_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    closed_at: Optional[datetime] = None
    settled_at: Optional[datetime] = None
    voided_at: Optional[datetime] = None
    void_reason: str = ""
    correlation_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # ── FSM transitions ───────────────────────────────────────────

    @transition(source=RoundState.OPEN.value, target=RoundState.CLOSED.value)
    def close(self):
        """OPEN → CLOSED. No more bets accepted."""
        self.closed_at = datetime.now(timezone.utc)

    @transition(source=RoundState.CLOSED.value, target=RoundState.SETTLED.value)
    def settle(self, *, payout_minor: int):
        """CLOSED → SETTLED. Outcome determined; winnings paid via Phase 11 ledger.

        Per ADR-0092: settlement posts to Phase 11 ledger.
        - If payout > bet: debit house, credit player (winnings).
        - If payout < bet: debit player (loss already posted at bet time).
        - If payout = bet: no additional entry (push).
        """
        self.total_payout_minor = payout_minor
        self.settled_at = datetime.now(timezone.utc)

    @transition(source=RoundState.OPEN.value, target=RoundState.VOIDED.value)
    @transition(source=RoundState.CLOSED.value, target=RoundState.VOIDED.value)
    def void(self, *, reason: str):
        """OPEN/CLOSED → VOIDED. Round voided; bets returned.

        Per ADR-0093: called by kill switch, SE activation, reality check failure.
        Bets returned via RealRoundVoidingAdapter (Phase 11 ledger reversal).
        """
        self.voided_at = datetime.now(timezone.utc)
        self.void_reason = reason

    @transition(source=RoundState.OPEN.value, target=RoundState.CANCELLED.value)
    def cancel(self, *, reason: str):
        """OPEN → CANCELLED. Operator cancellation."""
        self.voided_at = datetime.now(timezone.utc)
        self.void_reason = reason

    @property
    def is_accepting_bets(self) -> bool:
        """True if round is accepting bets (OPEN state only)."""
        return self.state == RoundState.OPEN.value

    @property
    def is_terminal(self) -> bool:
        """True if round is in a terminal state (no further transitions)."""
        return self.state in (RoundState.SETTLED.value, RoundState.VOIDED.value,
                              RoundState.CANCELLED.value)

    @property
    def house_result_minor(self) -> int:
        """House result = total bet - total payout. Positive = house wins."""
        return self.total_bet_minor - self.total_payout_minor


@dataclass(frozen=True)
class Bet:
    """A single bet on a game round. Per ADR-0092.

    Bets consume player balance (real or bonus) via Phase 11 ledger.
    Bonus bets contribute to wagering requirements (Phase 13).
    """

    bet_uuid: uuid.UUID
    round_uuid: uuid.UUID
    tenant_uuid: uuid.UUID
    player_uuid: uuid.UUID
    bet_type: BetType
    amount_minor: int  # Integer minor units (no floats)
    currency_code: str
    exponent_at_time: int
    contribution_rate: float = 1.0  # Game-class contribution (slots=1.0, table=0.1)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
