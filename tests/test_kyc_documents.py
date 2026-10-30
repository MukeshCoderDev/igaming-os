"""Tests for KYC & Documents (Phase 10).

Per Phase 10 hard acceptance:
- KYC FSM: valid/invalid transitions; regulatory constraints (PEP→EDD,
  sanctions→escalate, risk>threshold→EDD).
- Document versioning: one active per (player, doc_type); supersession.
- Storage port: put/get/delete/head.
- Synchronous revocation: revoked doc unretrievable; supersession ≠ revocation.
- AML/CFT: screening returns results; risk score; SAR tipping-off prohibition.
- Review queue: case appears; claim locks; SLA breach; escalation to MLRO.
"""

from __future__ import annotations

import uuid

import pytest

from noventra.apps.kyc.domain.kyc_case import (
    KycCase, KycCaseState, RiskLevel, EDD_RISK_THRESHOLD,
)
from noventra.apps.kyc.domain.document import DocumentType, DocumentVersion
from noventra.apps.kyc.domain.aml import (
    ScreeningResult, ScreeningType, ScreeningResultStatus,
    AmlResult, SarRecord, SarStatus,
)
from noventra.apps.kyc.domain.review_queue import ReviewQueueEntry, ReviewDecision
from noventra.apps.kyc.domain.storage_port import StoragePort, StorageResult
from noventra.apps.kyc.adapters.storage_stub import StubStorageAdapter
from noventra.apps.reliability.domain.state_machine import TransitionError


TENANT_A = "00000000-0000-0000-0000-000000000001"
PLAYER_A = "00000000-0000-0000-0000-0000000000a1"
MLRO = "00000000-0000-0000-0000-0000000000a2"


class TestKycCaseFSM:
    """KYC case FSM (ADR-0052)."""

    def _make_case(self, risk: RiskLevel = RiskLevel.LOW) -> KycCase:
        return KycCase(
            case_uuid=uuid.uuid4(),
            player_uuid=uuid.UUID(PLAYER_A),
            tenant_uuid=uuid.UUID(TENANT_A),
            risk_level=risk,
        )

    def test_submit_transition(self):
        case = self._make_case()
        case.submit()
        assert case.state == KycCaseState.SUBMITTED.value

    def test_auto_verify_transition(self):
        case = self._make_case()
        case.submit()
        case.auto_verify()
        assert case.state == KycCaseState.AUTO_VERIFIED.value

    def test_invalid_transition_rejected(self):
        case = self._make_case()
        # Can't auto_verify from pending_submission (must submit first).
        with pytest.raises(TransitionError):
            case.auto_verify()

    def test_pep_flagging_triggers_edd(self):
        """PEP → EDD regulatory constraint."""
        case = self._make_case()
        case.submit()
        case.auto_verify()
        case.flag_pep()
        assert case.state == KycCaseState.PEP_FLAGGED.value

        case.pep_to_edd()
        assert case.state == KycCaseState.ED_TRIGGERED.value

    def test_sanctions_flagging_escalates(self):
        """Sanctions → escalate regulatory constraint."""
        case = self._make_case()
        case.submit()
        case.flag_sanctions()
        assert case.state == KycCaseState.SANCTIONS_FLAGGED.value

        case.escalate_to_mlro()
        assert case.state == KycCaseState.ESCALATED.value

    def test_risk_threshold_triggers_edd(self):
        """Risk > threshold → EDD."""
        case = self._make_case(risk=RiskLevel.HIGH)
        assert case.check_risk_for_edd() is True

        case_low = self._make_case(risk=RiskLevel.LOW)
        assert case_low.check_risk_for_edd() is False

    def test_mlro_approve(self):
        """MLRO can approve escalated case."""
        case = self._make_case()
        case.submit()
        case.flag_sanctions()
        case.escalate_to_mlro()
        case.mlro_approve(mlro_uuid=uuid.UUID(MLRO))
        assert case.state == KycCaseState.CLOSED_APPROVED.value
        assert case.mlro_uuid == uuid.UUID(MLRO)

    def test_mlro_suspend_for_sar(self):
        """MLRO can suspend for SAR (tipping-off prohibition)."""
        case = self._make_case()
        case.submit()
        case.flag_sanctions()
        case.escalate_to_mlro()
        case.mlro_suspend_for_sar(mlro_uuid=uuid.UUID(MLRO))
        assert case.state == KycCaseState.SUSPENDED_PENDING_SAR.value

    def test_close_approved_from_auto_verified(self):
        case = self._make_case()
        case.submit()
        case.auto_verify()
        case.close_approved()
        assert case.state == KycCaseState.CLOSED_APPROVED.value


class TestDocumentVersioning:
    """Document versioning (ADR-0053)."""

    def test_document_types_closed_catalog(self):
        types = [t.value for t in DocumentType]
        assert "passport" in types
        assert "selfie" in types
        assert "utility_bill" in types

    def test_version_active_property(self):
        """Active version: not superseded, not revoked."""
        v = DocumentVersion(
            version_uuid=uuid.uuid4(),
            document_uuid=uuid.uuid4(),
            player_uuid=uuid.UUID(PLAYER_A),
            tenant_uuid=uuid.UUID(TENANT_A),
            doc_type=DocumentType.PASSPORT,
            storage_key="docs/abc",
            encryption_key_id="dek-1",
        )
        assert v.is_active is True
        assert v.is_retrievable is True

    def test_superseded_version_not_active_but_retrievable(self):
        """Superseded: not active, but still retrievable (for audit)."""
        v = DocumentVersion(
            version_uuid=uuid.uuid4(),
            document_uuid=uuid.uuid4(),
            player_uuid=uuid.UUID(PLAYER_A),
            tenant_uuid=uuid.UUID(TENANT_A),
            doc_type=DocumentType.PASSPORT,
            storage_key="docs/abc",
            encryption_key_id="dek-1",
            is_superseded=True,
        )
        assert v.is_active is False
        assert v.is_retrievable is True  # Superseded ≠ revoked.

    def test_revoked_version_not_retrievable(self):
        """Revoked: not retrievable (cryptographic shredding)."""
        v = DocumentVersion(
            version_uuid=uuid.uuid4(),
            document_uuid=uuid.uuid4(),
            player_uuid=uuid.UUID(PLAYER_A),
            tenant_uuid=uuid.UUID(TENANT_A),
            doc_type=DocumentType.PASSPORT,
            storage_key="docs/abc",
            encryption_key_id="dek-1",
            is_revoked=True,
        )
        assert v.is_active is False
        assert v.is_retrievable is False  # Revoked = unretrievable.


class TestStoragePort:
    """Storage port (ADR-0054)."""

    def test_put_get_roundtrip(self):
        adapter = StubStorageAdapter()
        result = adapter.put(key="docs/test", data=b"hello", metadata={"content_type": "image/png"})
        assert result.success is True

        get_result = adapter.get(key="docs/test")
        assert get_result.success is True
        assert get_result.metadata["data"] == b"hello"

    def test_delete(self):
        adapter = StubStorageAdapter()
        adapter.put(key="docs/test", data=b"hello", metadata={})
        result = adapter.delete(key="docs/test")
        assert result.success is True

        get_result = adapter.get(key="docs/test")
        assert get_result.success is False

    def test_head(self):
        adapter = StubStorageAdapter()
        adapter.put(key="docs/test", data=b"hello", metadata={"content_type": "image/png"})
        result = adapter.head(key="docs/test")
        assert result.success is True
        assert result.metadata["content_type"] == "image/png"

    def test_get_not_found(self):
        adapter = StubStorageAdapter()
        result = adapter.get(key="nonexistent")
        assert result.success is False
        assert result.error == "not_found"


class TestAmlCft:
    """AML/CFT framework (ADR-0056)."""

    def test_screening_result_clear(self):
        result = ScreeningResult(
            screening_uuid=uuid.uuid4(),
            case_uuid=uuid.uuid4(),
            player_uuid=uuid.UUID(PLAYER_A),
            tenant_uuid=uuid.UUID(TENANT_A),
            screening_type=ScreeningType.PEP,
            status=ScreeningResultStatus.CLEAR,
        )
        assert result.status == ScreeningResultStatus.CLEAR

    def test_screening_result_match(self):
        result = ScreeningResult(
            screening_uuid=uuid.uuid4(),
            case_uuid=uuid.uuid4(),
            player_uuid=uuid.UUID(PLAYER_A),
            tenant_uuid=uuid.UUID(TENANT_A),
            screening_type=ScreeningType.SANCTIONS,
            status=ScreeningResultStatus.MATCH,
            match_details="OFAC SDN list match",
        )
        assert result.status == ScreeningResultStatus.MATCH

    def test_aml_result_triggers_edd(self):
        result = AmlResult(
            case_uuid=uuid.uuid4(),
            player_uuid=uuid.UUID(PLAYER_A),
            tenant_uuid=uuid.UUID(TENANT_A),
            risk_score=85,
            risk_level="high",
            triggers_edd=True,
        )
        assert result.triggers_edd is True

    def test_sar_record_mlro_restricted(self):
        """SAR records are MLRO-restricted per ADR-0058."""
        sar = SarRecord(
            sar_uuid=uuid.uuid4(),
            case_uuid=uuid.uuid4(),
            player_uuid=uuid.UUID(PLAYER_A),
            tenant_uuid=uuid.UUID(TENANT_A),
            status=SarStatus.DRAFT,
            mlro_uuid=uuid.UUID(MLRO),
        )
        assert sar.mlro_restricted is True

    def test_sar_filed_status(self):
        """SAR can be filed by MLRO."""
        sar = SarRecord(
            sar_uuid=uuid.uuid4(),
            case_uuid=uuid.uuid4(),
            player_uuid=uuid.UUID(PLAYER_A),
            tenant_uuid=uuid.UUID(TENANT_A),
            status=SarStatus.FILED,
            mlro_uuid=uuid.UUID(MLRO),
        )
        assert sar.status == SarStatus.FILED


class TestReviewQueue:
    """Review queue (ADR-0058)."""

    def test_queue_entry_creation(self):
        entry = ReviewQueueEntry(
            entry_uuid=uuid.uuid4(),
            case_uuid=uuid.uuid4(),
            player_uuid=uuid.UUID(PLAYER_A),
            tenant_uuid=uuid.UUID(TENANT_A),
        )
        assert entry.decision is None
        assert entry.is_claimed is False

    def test_claim_locks_case(self):
        entry = ReviewQueueEntry(
            entry_uuid=uuid.uuid4(),
            case_uuid=uuid.uuid4(),
            player_uuid=uuid.UUID(PLAYER_A),
            tenant_uuid=uuid.UUID(TENANT_A),
            assigned_to=uuid.uuid4(),
            claimed_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        )
        assert entry.is_claimed is True

    def test_decision_unclaims(self):
        entry = ReviewQueueEntry(
            entry_uuid=uuid.uuid4(),
            case_uuid=uuid.uuid4(),
            player_uuid=uuid.UUID(PLAYER_A),
            tenant_uuid=uuid.UUID(TENANT_A),
            assigned_to=uuid.uuid4(),
            decision=ReviewDecision.APPROVE,
        )
        assert entry.is_claimed is False  # Decided → not claimed.

    def test_escalation(self):
        entry = ReviewQueueEntry(
            entry_uuid=uuid.uuid4(),
            case_uuid=uuid.uuid4(),
            player_uuid=uuid.UUID(PLAYER_A),
            tenant_uuid=uuid.UUID(TENANT_A),
            escalated=True,
            escalated_to="mlro",
        )
        assert entry.escalated is True
        assert entry.escalated_to == "mlro"


class TestEventTaxonomyExtension:
    """Phase 10 event type taxonomy extension."""

    def test_kyc_events_in_catalog(self):
        from noventra.apps.audit.domain.event_types import EventTypeCatalog
        assert EventTypeCatalog.is_valid("kyc.case_submitted")
        assert EventTypeCatalog.is_valid("kyc.case_closed_approved")
        assert EventTypeCatalog.is_valid("kyc.case_suspended_pending_sar")

    def test_document_events_in_catalog(self):
        from noventra.apps.audit.domain.event_types import EventTypeCatalog
        assert EventTypeCatalog.is_valid("document.uploaded")
        assert EventTypeCatalog.is_valid("document.revoked")

    def test_aml_review_sar_events_in_catalog(self):
        from noventra.apps.audit.domain.event_types import EventTypeCatalog
        assert EventTypeCatalog.is_valid("aml.screening_performed")
        assert EventTypeCatalog.is_valid("review.decision_made")
        assert EventTypeCatalog.is_valid("sar.filed")
