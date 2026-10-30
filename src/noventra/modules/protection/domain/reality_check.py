"""Reality checks. Per ADR-0086 / DEC-0086. Phase 14.

UK GC mandate: periodic reminders of time spent and money lost/gained.
Player must acknowledge before continuing.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class RealityCheck:
    """Reality check state for a player session. Per ADR-0086.

    Client-side timer triggers display; server enforces on every API call
    (if overdue, block until acknowledged).
    """

    check_uuid: uuid.UUID
    tenant_uuid: uuid.UUID
    player_uuid: uuid.UUID
    session_started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    interval_minutes: int = 30  # Default; global default per DEC-0157
    last_shown_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    net_gain_loss_minor: int = 0  # From Phase 11 ledger

    @property
    def is_overdue(self) -> bool:
        """True if reality check is overdue (should be shown but not yet acknowledged)."""
        now = datetime.now(timezone.utc)
        if self.last_shown_at is None:
            # Never shown — check if interval has elapsed since session start.
            elapsed = (now - self.session_started_at).total_seconds() / 60
            return elapsed >= self.interval_minutes

        if self.acknowledged_at is not None:
            # Last check was acknowledged — check if interval has elapsed since.
            elapsed = (now - self.acknowledged_at).total_seconds() / 60
            return elapsed >= self.interval_minutes

        # Shown but not acknowledged — overdue.
        return True

    def show(self) -> None:
        """Mark reality check as shown (client displays it)."""
        self.last_shown_at = datetime.now(timezone.utc)
        self.acknowledged_at = None

    def acknowledge(self) -> None:
        """Player acknowledges the reality check. Unblocks API calls."""
        self.acknowledged_at = datetime.now(timezone.utc)

    def get_display_data(self) -> dict:
        """Get data to display to the player. Per ADR-0086.

        Display: session duration, net gain/loss, option to continue or exit.
        """
        now = datetime.now(timezone.utc)
        session_duration_minutes = int((now - self.session_started_at).total_seconds() / 60)
        return {
            "session_duration_minutes": session_duration_minutes,
            "net_gain_loss_minor": self.net_gain_loss_minor,
            "interval_minutes": self.interval_minutes,
            "message": "You have been playing for {0} minutes. Your net {1} is {2}.".format(
                session_duration_minutes,
                "gain" if self.net_gain_loss_minor >= 0 else "loss",
                abs(self.net_gain_loss_minor),
            ),
        }
