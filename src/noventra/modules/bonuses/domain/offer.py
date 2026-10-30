"""Bonus offer domain — model + FSM + offer type catalog.

Per ADR-0078 / DEC-0078. Phase 13.
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


class OfferType(str, enum.Enum):
    """Closed catalog of 7 bonus offer types per ADR-0078."""
    DEPOSIT_MATCH = "deposit_match"
    FREE_SPINS = "free_spins"
    FREE_BET = "free_bet"
    CASHBACK = "cashback"
    RELOAD = "reload"
    REFER_FRIEND = "refer_friend"
    NO_DEPOSIT = "no_deposit"


class OfferState(str, enum.Enum):
    """Bonus offer lifecycle states per ADR-0078."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    PAUSED = "paused"
    EXPIRED = "expired"  # Terminal
    REVOKED = "revoked"  # Terminal (synchronous revocation per Law 10)


@dataclass
class BonusOffer(StateMachineMixin):
    """Bonus offer entity. Per ADR-0078.

    7 offer types (closed catalog). State FSM with synchronous revocation.
    Realtime invalidation via RealtimePort (stub log+no-op).
    """

    offer_uuid: uuid.UUID
    tenant_uuid: uuid.UUID
    offer_type: OfferType
    name: str
    description: str = ""
    eligibility_rules: dict = field(default_factory=dict)
    visibility: str = "opt_in"  # opt_in, auto_claimed, targeted
    state: str = OfferState.DRAFT.value
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    max_awards: int = 0  # 0 = unlimited
    current_awards: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    # ── FSM transitions ───────────────────────────────────────────

    @transition(source=OfferState.DRAFT.value, target=OfferState.SCHEDULED.value)
    def schedule(self):
        """Draft → Scheduled."""
        pass

    @transition(source=OfferState.SCHEDULED.value, target=OfferState.PUBLISHED.value)
    def publish(self):
        """Scheduled → Published."""
        pass

    @transition(source=OfferState.PUBLISHED.value, target=OfferState.PAUSED.value)
    def pause(self):
        """Published → Paused."""
        pass

    @transition(source=OfferState.PAUSED.value, target=OfferState.PUBLISHED.value)
    def resume(self):
        """Paused → Published (resume)."""
        pass

    @transition(source=OfferState.PUBLISHED.value, target=OfferState.EXPIRED.value)
    @transition(source=OfferState.PAUSED.value, target=OfferState.EXPIRED.value)
    def expire(self):
        """Published/Paused → Expired (terminal)."""
        pass

    @transition(source=OfferState.PUBLISHED.value, target=OfferState.REVOKED.value)
    @transition(source=OfferState.PAUSED.value, target=OfferState.REVOKED.value)
    @transition(source=OfferState.SCHEDULED.value, target=OfferState.REVOKED.value)
    def revoke(self):
        """Published/Paused/Scheduled → Revoked (terminal).

        Per Law 10: synchronous revocation. The offer is unretrievable
        in the same transaction. RealtimePort.invalidates connected clients
        (stub in Phase 13; Phase 22 implements actual WebSocket fan-out).
        """
        pass

    @property
    def is_retrievable(self) -> bool:
        """A revoked offer is NOT retrievable (Law 10)."""
        return self.state != OfferState.REVOKED.value

    @property
    def is_terminal(self) -> bool:
        return self.state in (OfferState.EXPIRED.value, OfferState.REVOKED.value)
