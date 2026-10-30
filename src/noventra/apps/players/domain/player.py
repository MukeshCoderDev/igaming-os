"""Player domain — entity + lifecycle FSM.

Per ADR-0047 (Player entity) + ADR-0050 (lifecycle FSM).
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from noventra.apps.reliability.domain.state_machine import (
    StateMachineMixin,
    TransitionError,
    transition,
)


class PlayerState(str, enum.Enum):
    """Player lifecycle states per ADR-0050.

    8 states: prospect, registered, active, suspended, self_excluded,
    dormant, closed, deleted.
    """

    PROSPECT = "prospect"
    REGISTERED = "registered"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    SELF_EXCLUDED = "self_excluded"
    DORMANT = "dormant"
    CLOSED = "closed"
    DELETED = "deleted"


# Default regulatory constraints (Phase 9 uses defaults per DEC-0157).
SELF_EXCLUSION_COOLING_OFF_HOURS = 24  # Default.
DORMANCY_INACTIVITY_DAYS = 365  # Default.


@dataclass
class Player(StateMachineMixin):
    """Player entity — the end-user of a tenant's platform.

    Per ADR-0047: separate entity, optionally linked to User (Phase 6).
    Tenant-scoped. PII fields per extended PII register.
    Per ADR-0050: lifecycle FSM with 8 states.
    """

    player_uuid: uuid.UUID
    tenant_uuid: uuid.UUID
    email: str
    full_name: str
    date_of_birth: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    user_uuid: Optional[uuid.UUID] = None  # Link to Phase 6 User (nullable for prospects)
    state: str = PlayerState.PROSPECT.value
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_active_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    # ── FSM transitions per ADR-0050 ──────────────────────────────

    @transition(source=PlayerState.PROSPECT.value, target=PlayerState.REGISTERED.value)
    def register(self):
        """Prospect → Registered."""
        pass

    @transition(source=PlayerState.REGISTERED.value, target=PlayerState.ACTIVE.value)
    def activate(self):
        """Registered → Active."""
        pass

    @transition(source=PlayerState.ACTIVE.value, target=PlayerState.SUSPENDED.value)
    def suspend(self):
        """Active → Suspended."""
        pass

    @transition(source=PlayerState.SUSPENDED.value, target=PlayerState.ACTIVE.value)
    def reactivate(self):
        """Suspended → Active."""
        pass

    @transition(source=PlayerState.ACTIVE.value, target=PlayerState.SELF_EXCLUDED.value)
    def self_exclude(self):
        """Active → Self-Excluded.

        Regulatory constraint: cooling-off period (Q1-blocked; default 24h).
        During cooling-off, the player cannot reactivate.
        """
        pass

    @transition(source=PlayerState.SELF_EXCLUDED.value, target=PlayerState.ACTIVE.value)
    def reactivate_from_exclusion(self, *, cooling_off_elapsed: bool = False):
        """Self-Excluded → Active.

        Guard: cooling_off_elapsed must be True (regulatory constraint).
        """
        if not cooling_off_elapsed:
            raise TransitionError(
                "Self-exclusion cooling-off period not elapsed "
                f"(default {SELF_EXCLUSION_COOLING_OFF_HOURS}h)"
            )

    @transition(source=PlayerState.ACTIVE.value, target=PlayerState.DORMANT.value)
    def trigger_dormancy(self):
        """Active → Dormant.

        Triggered by inactivity > DORMANCY_INACTIVITY_DAYS (Q1-blocked default).
        """
        pass

    @transition(source=PlayerState.DORMANT.value, target=PlayerState.ACTIVE.value)
    def reactivate_from_dormancy(self):
        """Dormant → Active (player logged in)."""
        pass

    @transition(
        source=PlayerState.ACTIVE.value,
        target=PlayerState.CLOSED.value,
    )
    def close(self):
        """Active → Closed."""
        pass

    @transition(source=PlayerState.CLOSED.value, target=PlayerState.DELETED.value)
    def delete(self):
        """Closed → Deleted (right-to-erasure; cascade per ADR-0051)."""
        pass

    # ── Side-effect hooks ─────────────────────────────────────────

    def _after_transition(self, name: str, source: str, target: str) -> None:
        """After every transition: emit outbox event + audit event.

        Per Phase 8 (outbox) + Phase 7 (audit). The actual emission
        is handled by the service layer; this hook is the extension point.
        """
        pass  # Service layer calls append_to_outbox + append_audit_event.
