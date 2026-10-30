"""Review queue domain.

Per ADR-0058 / DEC-0063.
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional


class ReviewDecision(str, enum.Enum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_MORE_INFO = "request_more_info"
    ESCALATE = "escalate"


# Default SLA: 48 hours from queue entry to decision (Q1-blocked).
DEFAULT_SLA_HOURS = 48


@dataclass
class ReviewQueueEntry:
    """A review queue entry. Per ADR-0058.

    Per-tenant queue (Phase 10). Round-robin assignment (Phase 10).
    SLA tracking with alerting. Escalation: reviewer → senior → MLRO.
    Concurrency: row-level lock (SELECT FOR UPDATE) or claim-based.
    """

    entry_uuid: uuid.UUID
    case_uuid: uuid.UUID
    player_uuid: uuid.UUID
    tenant_uuid: uuid.UUID
    assigned_to: Optional[uuid.UUID] = None  # reviewer_uuid
    claimed_at: Optional[datetime] = None
    decision: Optional[ReviewDecision] = None
    decision_at: Optional[datetime] = None
    reviewer_notes: str = ""
    sla_deadline: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(hours=DEFAULT_SLA_HOURS)
    )
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    escalated: bool = False
    escalated_to: Optional[str] = None  # "senior" or "mlro"

    @property
    def is_sla_breached(self) -> bool:
        """Check if SLA is breached (past deadline without decision)."""
        if self.decision is not None:
            return False  # Decided; no breach.
        return datetime.now(timezone.utc) > self.sla_deadline

    @property
    def is_claimed(self) -> bool:
        return self.assigned_to is not None and self.decision is None
