"""KYC case FSM — 16 states with regulatory constraints.

Per ADR-0052 / DEC-0057. Uses Phase 8 state machine base.
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


class KycCaseState(str, enum.Enum):
    """16-state KYC case FSM per ADR-0052."""
    PENDING_SUBMISSION = "pending_submission"
    SUBMITTED = "submitted"
    AUTO_VERIFIED = "auto_verified"
    AUTO_REJECTED = "auto_rejected"
    IN_REVIEW = "in_review"
    REVIEW_PASSED = "review_passed"
    REVIEW_FAILED = "review_failed"
    ED_TRIGGERED = "ed_triggered"  # Enhanced Due Diligence
    ED_IN_PROGRESS = "ed_in_progress"
    ED_PASSED = "ed_passed"
    ED_FAILED = "ed_failed"
    PEP_FLAGGED = "pep_flagged"
    SANCTIONS_FLAGGED = "sanctions_flagged"
    ESCALATED = "escalated"  # Escalated to MLRO
    SUSPENDED = "suspended"
    SUSPENDED_PENDING_SAR = "suspended_pending_sar"
    CLOSED_APPROVED = "closed_approved"
    CLOSED_REJECTED = "closed_rejected"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Default risk threshold for EDD trigger (Q1-blocked; default = HIGH).
EDD_RISK_THRESHOLD = RiskLevel.HIGH


@dataclass
class KycCase(StateMachineMixin):
    """KYC case entity. Per ADR-0052.

    16-state FSM with regulatory constraints:
    - PEP → EDD (ed_triggered)
    - Sanctions → escalate
    - Risk > threshold → EDD
    """

    case_uuid: uuid.UUID
    player_uuid: uuid.UUID
    tenant_uuid: uuid.UUID
    risk_level: RiskLevel = RiskLevel.LOW
    risk_score: int = 0
    state: str = KycCaseState.PENDING_SUBMISSION.value
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    submitted_at: Optional[datetime] = None
    decided_at: Optional[datetime] = None
    reviewer_uuid: Optional[uuid.UUID] = None
    mlro_uuid: Optional[uuid.UUID] = None

    # ── FSM transitions ───────────────────────────────────────────

    @transition(source=KycCaseState.PENDING_SUBMISSION.value, target=KycCaseState.SUBMITTED.value)
    def submit(self):
        """Pending → Submitted (documents uploaded)."""
        self.submitted_at = datetime.now(timezone.utc)

    @transition(source=KycCaseState.SUBMITTED.value, target=KycCaseState.AUTO_VERIFIED.value)
    def auto_verify(self):
        """Submitted → Auto-Verified (vendor verification passed)."""
        pass

    @transition(source=KycCaseState.SUBMITTED.value, target=KycCaseState.AUTO_REJECTED.value)
    def auto_reject(self):
        """Submitted → Auto-Rejected (vendor verification failed)."""
        pass

    @transition(source=KycCaseState.SUBMITTED.value, target=KycCaseState.IN_REVIEW.value)
    def enter_review(self):
        """Submitted → In-Review (manual review needed)."""
        pass

    @transition(source=KycCaseState.AUTO_REJECTED.value, target=KycCaseState.IN_REVIEW.value)
    def escalate_to_review(self):
        """Auto-Rejected → In-Review (reviewer overrides)."""
        pass

    @transition(source=KycCaseState.IN_REVIEW.value, target=KycCaseState.REVIEW_PASSED.value)
    def review_pass(self):
        """In-Review → Review-Passed."""
        self.decided_at = datetime.now(timezone.utc)

    @transition(source=KycCaseState.IN_REVIEW.value, target=KycCaseState.REVIEW_FAILED.value)
    def review_fail(self):
        """In-Review → Review-Failed."""
        self.decided_at = datetime.now(timezone.utc)

    @transition(source=KycCaseState.AUTO_VERIFIED.value, target=KycCaseState.ED_TRIGGERED.value)
    @transition(source=KycCaseState.REVIEW_PASSED.value, target=KycCaseState.ED_TRIGGERED.value)
    def trigger_edd(self, *, reason: str = ""):
        """Auto-Verified/Review-Passed → ED-Triggered.

        Regulatory constraint: PEP flag or risk > threshold triggers EDD.
        """
        pass

    @transition(source=KycCaseState.ED_TRIGGERED.value, target=KycCaseState.ED_IN_PROGRESS.value)
    def start_edd(self):
        """ED-Triggered → ED-In-Progress."""
        pass

    @transition(source=KycCaseState.ED_IN_PROGRESS.value, target=KycCaseState.ED_PASSED.value)
    def edd_pass(self):
        """ED-In-Progress → ED-Passed."""
        self.decided_at = datetime.now(timezone.utc)

    @transition(source=KycCaseState.ED_IN_PROGRESS.value, target=KycCaseState.ED_FAILED.value)
    def edd_fail(self):
        """ED-In-Progress → ED-Failed."""
        self.decided_at = datetime.now(timezone.utc)

    @transition(source=KycCaseState.AUTO_VERIFIED.value, target=KycCaseState.PEP_FLAGGED.value)
    @transition(source=KycCaseState.REVIEW_PASSED.value, target=KycCaseState.PEP_FLAGGED.value)
    def flag_pep(self):
        """Auto-Verified/Review-Passed → PEP-Flagged.

        Regulatory constraint: PEP → EDD.
        """
        pass

    @transition(source=KycCaseState.PEP_FLAGGED.value, target=KycCaseState.ED_TRIGGERED.value)
    def pep_to_edd(self):
        """PEP-Flagged → ED-Triggered (PEP → EDD regulatory constraint)."""
        pass

    @transition(source=KycCaseState.SUBMITTED.value, target=KycCaseState.SANCTIONS_FLAGGED.value)
    @transition(source=KycCaseState.AUTO_VERIFIED.value, target=KycCaseState.SANCTIONS_FLAGGED.value)
    def flag_sanctions(self):
        """Submitted/Auto-Verified → Sanctions-Flagged.

        Regulatory constraint: sanctions → escalate.
        """
        pass

    @transition(source=KycCaseState.SANCTIONS_FLAGGED.value, target=KycCaseState.ESCALATED.value)
    def escalate_to_mlro(self):
        """Sanctions-Flagged → Escalated (to MLRO).

        Regulatory constraint: sanctions → escalate.
        """
        pass

    @transition(source=KycCaseState.ED_FAILED.value, target=KycCaseState.ESCALATED.value)
    @transition(source=KycCaseState.REVIEW_FAILED.value, target=KycCaseState.ESCALATED.value)
    def escalate_from_failure(self):
        """ED-Failed/Review-Failed → Escalated (to MLRO)."""
        pass

    @transition(source=KycCaseState.ESCALATED.value, target=KycCaseState.CLOSED_APPROVED.value)
    def mlro_approve(self, *, mlro_uuid: uuid.UUID):
        """Escalated → Closed-Approved (MLRO decision).

        MLRO decisions are regulator-reportable.
        """
        self.mlro_uuid = mlro_uuid
        self.decided_at = datetime.now(timezone.utc)

    @transition(source=KycCaseState.ESCALATED.value, target=KycCaseState.CLOSED_REJECTED.value)
    def mlro_reject(self, *, mlro_uuid: uuid.UUID):
        """Escalated → Closed-Rejected (MLRO decision)."""
        self.mlro_uuid = mlro_uuid
        self.decided_at = datetime.now(timezone.utc)

    @transition(source=KycCaseState.ESCALATED.value, target=KycCaseState.SUSPENDED_PENDING_SAR.value)
    def mlro_suspend_for_sar(self, *, mlro_uuid: uuid.UUID):
        """Escalated → Suspended-Pending-SAR (SAR filing triggered).

        Tipping-off prohibition: the player is NOT notified.
        """
        self.mlro_uuid = mlro_uuid

    @transition(source=KycCaseState.ED_PASSED.value, target=KycCaseState.CLOSED_APPROVED.value)
    @transition(source=KycCaseState.AUTO_VERIFIED.value, target=KycCaseState.CLOSED_APPROVED.value)
    @transition(source=KycCaseState.REVIEW_PASSED.value, target=KycCaseState.CLOSED_APPROVED.value)
    def close_approved(self):
        """ED-Passed/Auto-Verified/Review-Passed → Closed-Approved."""
        self.decided_at = datetime.now(timezone.utc)

    @transition(source=KycCaseState.AUTO_REJECTED.value, target=KycCaseState.CLOSED_REJECTED.value)
    @transition(source=KycCaseState.REVIEW_FAILED.value, target=KycCaseState.CLOSED_REJECTED.value)
    @transition(source=KycCaseState.ED_FAILED.value, target=KycCaseState.CLOSED_REJECTED.value)
    def close_rejected(self):
        """Auto-Rejected/Review-Failed/ED-Failed → Closed-Rejected."""
        self.decided_at = datetime.now(timezone.utc)

    # ── Regulatory constraint helpers ─────────────────────────────

    def check_risk_for_edd(self) -> bool:
        """Check if risk level requires EDD. Returns True if EDD should trigger."""
        risk_order = {RiskLevel.LOW: 0, RiskLevel.MEDIUM: 1, RiskLevel.HIGH: 2}
        return risk_order.get(self.risk_level, 0) >= risk_order.get(EDD_RISK_THRESHOLD, 2)
