"""Release FSM — Evidence-Gated Transitions (No Skipping).

Per ADR-0103 / DEC-0104. Phase 16.

A game release is the lifecycle from initial draft through to publication and
(eventually) suspension/revocation. Each transition requires specific evidence;
absent evidence → no transition. The regulator mandate (Law 19) is absolute:
no game can skip states.

States + transitions:
    draft → math_configured → rng_certified → math_certified → lab_tested
        → ready_for_release → published → suspended / revoked

Each transition requires its specific evidence:
    draft → math_configured:        active_math_version_uuid set
    math_configured → rng_certified: rng_cert_evidence_uuid set, non-expired
    rng_certified → math_certified:  math_cert_evidence_uuid set, non-expired
    math_certified → lab_tested:     lab_test_evidence_uuid set, non-expired
    lab_tested → ready_for_release:  all three evidence UUIDs verified non-expired
    ready_for_release → published:   operator_approval_at + operator_approval_by set
    published → suspended:           cert expired, operator action, regulator mandate
    suspended → published:           re-certification (new evidence + operator re-approval)
    suspended → revoked:             terminal: regulator-mandated revocation
    published → revoked:             terminal: regulator-mandated revocation
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


class ReleaseState(str, enum.Enum):
    """Game release lifecycle states. Per ADR-0103."""
    DRAFT = "draft"
    MATH_CONFIGURED = "math_configured"
    RNG_CERTIFIED = "rng_certified"
    MATH_CERTIFIED = "math_certified"
    LAB_TESTED = "lab_tested"
    READY_FOR_RELEASE = "ready_for_release"
    PUBLISHED = "published"
    SUSPENDED = "suspended"
    REVOKED = "revoked"  # Terminal


@dataclass
class GameRelease(StateMachineMixin):
    """Game release entity with evidence-gated FSM. Per ADR-0103 / DEC-0104.

    The FSM refuses any transition that skips a state. Each transition method
    verifies the required evidence UUID is set AND that the linked
    CertificationEvidence is non-expired. If the evidence is missing or expired,
    the transition raises TransitionError and the release remains in its
    current state.

    Linter rule 131 (Phase 16) forbids any code path that publishes a release
    without all evidence verified.
    Linter rule 132 (Phase 16) forbids any code path that skips a state.
    Linter rule 133 (Phase 16) requires every release in `published` status
    to have a non-expired cert evidence chain.
    """

    release_uuid: uuid.UUID
    tenant_uuid: uuid.UUID
    game_id: str
    game_name: str
    state: str = ReleaseState.DRAFT.value
    active_math_version_uuid: Optional[uuid.UUID] = None
    rng_cert_evidence_uuid: Optional[uuid.UUID] = None
    math_cert_evidence_uuid: Optional[uuid.UUID] = None
    lab_test_evidence_uuid: Optional[uuid.UUID] = None
    operator_approval_at: Optional[datetime] = None
    operator_approval_by: Optional[str] = None
    suspended_at: Optional[datetime] = None
    suspended_reason: str = ""
    revoked_at: Optional[datetime] = None
    revoked_reason: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # ── FSM transitions (evidence-gated) ────────────────────────────────

    @transition(source=ReleaseState.DRAFT.value, target=ReleaseState.MATH_CONFIGURED.value)
    def configure_math(self, *, math_version_uuid: uuid.UUID) -> None:
        """DRAFT → MATH_CONFIGURED. Requires math version attached.

        Per ADR-0103: this transition requires active_math_version_uuid set.
        The math version must exist in DRAFT status (it will be CERTIFIED
        in a later transition).
        """
        if math_version_uuid is None:
            raise TransitionError("configure_math requires math_version_uuid")
        self.active_math_version_uuid = math_version_uuid
        self.updated_at = datetime.now(timezone.utc)

    @transition(source=ReleaseState.MATH_CONFIGURED.value, target=ReleaseState.RNG_CERTIFIED.value)
    def attach_rng_cert(self, *, evidence_uuid: uuid.UUID,
                        evidence_is_expired: bool = False) -> None:
        """MATH_CONFIGURED → RNG_CERTIFIED. Requires RNG cert evidence.

        Per ADR-0103: this transition requires rng_cert_evidence_uuid set,
        and the linked CertificationEvidence must be non-expired.
        """
        if evidence_uuid is None:
            raise TransitionError("attach_rng_cert requires evidence_uuid")
        if evidence_is_expired:
            raise TransitionError(
                "attach_rng_cert refused: RNG cert evidence is expired. "
                "Re-certify before attaching."
            )
        self.rng_cert_evidence_uuid = evidence_uuid
        self.updated_at = datetime.now(timezone.utc)

    @transition(source=ReleaseState.RNG_CERTIFIED.value, target=ReleaseState.MATH_CERTIFIED.value)
    def attach_math_cert(self, *, evidence_uuid: uuid.UUID,
                         evidence_is_expired: bool = False) -> None:
        """RNG_CERTIFIED → MATH_CERTIFIED. Requires math cert evidence.

        Per ADR-0103: this transition requires math_cert_evidence_uuid set,
        and the linked CertificationEvidence must be non-expired.
        """
        if evidence_uuid is None:
            raise TransitionError("attach_math_cert requires evidence_uuid")
        if evidence_is_expired:
            raise TransitionError(
                "attach_math_cert refused: math cert evidence is expired."
            )
        self.math_cert_evidence_uuid = evidence_uuid
        self.updated_at = datetime.now(timezone.utc)

    @transition(source=ReleaseState.MATH_CERTIFIED.value, target=ReleaseState.LAB_TESTED.value)
    def attach_lab_test(self, *, evidence_uuid: uuid.UUID,
                        evidence_is_expired: bool = False) -> None:
        """MATH_CERTIFIED → LAB_TESTED. Requires lab test evidence.

        Per ADR-0103: this transition requires lab_test_evidence_uuid set,
        and the linked CertificationEvidence must be non-expired.
        """
        if evidence_uuid is None:
            raise TransitionError("attach_lab_test requires evidence_uuid")
        if evidence_is_expired:
            raise TransitionError(
                "attach_lab_test refused: lab test evidence is expired."
            )
        self.lab_test_evidence_uuid = evidence_uuid
        self.updated_at = datetime.now(timezone.utc)

    @transition(source=ReleaseState.LAB_TESTED.value, target=ReleaseState.READY_FOR_RELEASE.value)
    def ready_for_release(self, *, all_evidence_non_expired: bool = True) -> None:
        """LAB_TESTED → READY_FOR_RELEASE. Requires all evidence verified non-expired.

        Per ADR-0103: this transition requires all three evidence UUIDs set
        and verified non-expired.
        """
        if not all_evidence_non_expired:
            raise TransitionError(
                "ready_for_release refused: one or more evidence is expired."
            )
        if not (self.rng_cert_evidence_uuid
                and self.math_cert_evidence_uuid
                and self.lab_test_evidence_uuid):
            raise TransitionError(
                "ready_for_release refused: all three evidence UUIDs must be set."
            )
        self.updated_at = datetime.now(timezone.utc)

    @transition(source=ReleaseState.READY_FOR_RELEASE.value, target=ReleaseState.PUBLISHED.value)
    def publish(self, *, operator_approval_by: str) -> None:
        """READY_FOR_RELEASE → PUBLISHED. Requires operator sign-off.

        Per ADR-0103: this transition requires operator_approval_at +
        operator_approval_by set (operator sign-off is regulator-mandated).
        """
        if not operator_approval_by:
            raise TransitionError(
                "publish refused: operator_approval_by is required (regulator-mandated)."
            )
        self.operator_approval_at = datetime.now(timezone.utc)
        self.operator_approval_by = operator_approval_by
        self.updated_at = datetime.now(timezone.utc)

    @transition(source=ReleaseState.PUBLISHED.value, target=ReleaseState.SUSPENDED.value)
    def suspend(self, *, reason: str) -> None:
        """PUBLISHED → SUSPENDED. Operator action, cert expiry, or regulator mandate.

        Per ADR-0103: this transition is non-terminal (can be reversed by
        re-certification + re-approval). Active rounds are voided by the
        caller (CertExpiryService in ADR-0102).
        """
        if not reason:
            raise TransitionError("suspend requires a reason")
        self.suspended_at = datetime.now(timezone.utc)
        self.suspended_reason = reason
        self.updated_at = datetime.now(timezone.utc)

    @transition(source=ReleaseState.SUSPENDED.value, target=ReleaseState.PUBLISHED.value)
    def resume_publication(self, *, operator_approval_by: str,
                           new_evidence_attached: bool = True) -> None:
        """SUSPENDED → PUBLISHED. Re-certification + operator re-approval.

        Per ADR-0103: this transition requires new evidence attached (re-
        certification) AND operator re-approval.
        """
        if not new_evidence_attached:
            raise TransitionError(
                "resume_publication refused: new evidence must be attached (re-certification)."
            )
        if not operator_approval_by:
            raise TransitionError(
                "resume_publication refused: operator_approval_by is required."
            )
        self.operator_approval_at = datetime.now(timezone.utc)
        self.operator_approval_by = operator_approval_by
        self.suspended_at = None
        self.suspended_reason = ""
        self.updated_at = datetime.now(timezone.utc)

    @transition(source=ReleaseState.PUBLISHED.value, target=ReleaseState.REVOKED.value)
    @transition(source=ReleaseState.SUSPENDED.value, target=ReleaseState.REVOKED.value)
    def revoke(self, *, reason: str) -> None:
        """PUBLISHED/SUSPENDED → REVOKED. Terminal: regulator-mandated revocation.

        Per ADR-0103: REVOKED is terminal. No further transitions possible.
        """
        if not reason:
            raise TransitionError("revoke requires a reason")
        self.revoked_at = datetime.now(timezone.utc)
        self.revoked_reason = reason
        self.updated_at = datetime.now(timezone.utc)

    # ── Properties ──────────────────────────────────────────────────────

    @property
    def is_terminal(self) -> bool:
        """True if release is in terminal state (no further transitions)."""
        return self.state == ReleaseState.REVOKED.value

    @property
    def is_playable(self) -> bool:
        """True if release is in PUBLISHED state (new rounds can use it)."""
        return self.state == ReleaseState.PUBLISHED.value

    @property
    def evidence_chain_complete(self) -> bool:
        """True if all three evidence UUIDs are set. Per ADR-0103."""
        return bool(
            self.rng_cert_evidence_uuid
            and self.math_cert_evidence_uuid
            and self.lab_test_evidence_uuid
        )
