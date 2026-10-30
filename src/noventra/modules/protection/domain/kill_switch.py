"""Kill switch. Per ADR-0089 / DEC-0089. Phase 14.

**Most safety-critical feature in the platform.**
Regulator-mandated <200ms SLO (commit → WebSocket disconnect).
Must HALT all play across all tenants instantly.
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


class KillSwitchScope(str, enum.Enum):
    """Kill switch scope: per-tenant or global."""
    TENANT = "tenant"  # One tenant
    GLOBAL = "global"  # All tenants


class KillSwitchStatus(str, enum.Enum):
    """Kill switch status."""
    INACTIVE = "inactive"
    ACTIVE = "active"  # Kill switch triggered; all play HALTED
    LIFTED = "lifted"  # Kill switch lifted; play resumed


@dataclass
class KillSwitch:
    """Kill switch state. Per ADR-0089.

    Architecture:
    1. Admin triggers kill switch (DB flag + outbox event).
    2. ASGI WebSocket consumer (Phase 22 pulled forward) receives event via Redis pub/sub.
    3. Consumer disconnects all WebSocket connections (<200ms from commit to disconnect).
    4. All API endpoints check kill switch flag (cached in Redis; <1ms check).
    5. Phase 15 game platform voids all in-progress rounds via RoundVoidingPort.

    Fan-out: per-tenant (one tenant) or global (all tenants).
    Audit: every kill switch trigger + lift is audited per Phase 7.
    """

    switch_uuid: uuid.UUID
    tenant_uuid: Optional[uuid.UUID]  # None for global
    scope: KillSwitchScope
    status: KillSwitchStatus = KillSwitchStatus.INACTIVE
    triggered_at: Optional[datetime] = None
    triggered_by: Optional[uuid.UUID] = None  # admin user_uuid
    trigger_reason: str = ""
    lifted_at: Optional[datetime] = None
    lifted_by: Optional[uuid.UUID] = None
    lift_reason: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def trigger(self, *, triggered_by: uuid.UUID, reason: str) -> None:
        """Trigger the kill switch. Per ADR-0089.

        This is the most consequential action in the platform:
        - All play HALTED immediately.
        - All WebSocket connections disconnected (<200ms).
        - All in-progress rounds voided (via RoundVoidingPort).
        - Audit event emitted per Phase 7.

        Args:
            triggered_by: The admin user who triggered the kill switch.
            reason: The reason for triggering (audited).
        """
        if self.status == KillSwitchStatus.ACTIVE:
            return  # Already active.
        self.status = KillSwitchStatus.ACTIVE
        self.triggered_at = datetime.now(timezone.utc)
        self.triggered_by = triggered_by
        self.trigger_reason = reason

    def lift(self, *, lifted_by: uuid.UUID, reason: str) -> None:
        """Lift the kill switch. Per ADR-0089.

        Play resumes. Audit event emitted.

        Args:
            lifted_by: The admin user who lifted the kill switch.
            reason: The reason for lifting (audited).
        """
        if self.status != KillSwitchStatus.ACTIVE:
            return  # Not active.
        self.status = KillSwitchStatus.LIFTED
        self.lifted_at = datetime.now(timezone.utc)
        self.lifted_by = lifted_by
        self.lift_reason = reason

    @property
    def is_active(self) -> bool:
        """True if kill switch is currently active (all play HALTED)."""
        return self.status == KillSwitchStatus.ACTIVE

    @property
    def should_halt(self) -> bool:
        """True if all play should be HALTED (kill switch is active).

        This is checked on every API call (cached in Redis; <1ms).
        Per ADR-0089: this is the <200ms SLO path.
        """
        return self.is_active
