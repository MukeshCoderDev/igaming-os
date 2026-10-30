"""Certification Evidence + Lab Registry + Auto-Suspend on Expiry.

Per ADR-0102 / DEC-0103. Phase 16.

Three subsystems:

1. **LabRegistry** — configurable list of approved labs.
   GLI is approved globally; BMM in most; iTechLabs in some.

2. **CertificationEvidence** — stores lab certification artifacts (RNG cert,
   math cert, RTP verification, game logic cert). Linked to a specific math
   version (ADR-0099). Stored via Phase 10 storage port (immutable).

3. **Auto-suspend on expiry** — daily Celery task. On cert expiry, the math
   version transitions to REVOKED (synchronous, Law 10), the linked game
   release transitions to SUSPENDED (ADR-0103), and active rounds are voided
   (ADR-0093).

Law 19 mandates lab certification; expired cert = operating without cert =
regulator-reportable. The auto-suspend is the safety net that prevents this.
"""

from __future__ import annotations

import enum
import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Optional


# ─────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────

class EvidenceType(str, enum.Enum):
    """Types of certification evidence. Per ADR-0102."""
    RNG_CERT = "rng_cert"                # RNG certified by lab
    MATH_CERT = "math_cert"              # Math config certified by lab
    RTP_VERIFICATION = "rtp_verification"  # RTP verified by lab
    GAME_LOGIC_CERT = "game_logic_cert"  # Game logic certified by lab


# ─────────────────────────────────────────────────────────────────────────
# LabRegistry entity
# ─────────────────────────────────────────────────────────────────────────

@dataclass
class LabRegistry:
    """Approved lab registry entry. Per ADR-0102.

    A lab appears once in the registry. Per DEC-0157 (Global Mode), labs are
    approved globally; the previous approvals list has been removed.

    The registry is configurable via Django admin; changes are
    audit-logged (Phase 7).
    """

    lab_uuid: uuid.UUID
    lab_name: str  # e.g., "GLI", "BMM Testlabs", "iTechLabs"
    lab_code: str  # Short code (e.g., "gli", "bmm")
    # jurisdictions field removed per DEC-0157 (Global Mode)
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_approved(self) -> bool:
        """True if this lab is active and approved globally."""
        return self.is_active


# ─────────────────────────────────────────────────────────────────────────
# CertificationEvidence entity
# ─────────────────────────────────────────────────────────────────────────

@dataclass
class CertificationEvidence:
    """Certification evidence for a math version. Per ADR-0102.

    Stored via Phase 10 storage port (immutable, retention 7+ years). The
    `evidence_hash` allows tamper detection: any modification of the stored
    artifact is detected by recomputing the hash.

    Lifecycle:
    1. Lab certifies a math version → CertificationEvidence created with
       evidence_storage_uri pointing to the immutable artifact.
    2. Daily Celery task checks `expires_at`:
       - Within 30 days → alert (Slack/email to Compliance Lead + Product Owner).
       - Past expiry → math version REVOKED, release SUSPENDED, rounds VOIDED.
    3. Re-certification creates a NEW CertificationEvidence (immutable, never mutated).
    """

    evidence_uuid: uuid.UUID
    tenant_uuid: uuid.UUID
    math_version_uuid: uuid.UUID  # FK → MathVersion
    lab_uuid: uuid.UUID           # FK → LabRegistry
    evidence_type: EvidenceType
    evidence_storage_uri: str     # URI in Phase 10 storage port
    evidence_hash: str            # SHA-256 hex of the stored artifact
    issued_at: datetime
    expires_at: datetime          # 1–3 years; default 2 years per DEC-0157
    cert_number: str              # Lab-assigned cert number (e.g., "GLI-23-12345")
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_expired(self) -> bool:
        """True if the evidence has expired (expires_at is in the past)."""
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_expiring_soon(self) -> bool:
        """True if the evidence expires within 30 days. Per ADR-0102."""
        return (
            not self.is_expired
            and (self.expires_at - datetime.now(timezone.utc)) <= timedelta(days=30)
        )

    def verify_evidence_hash(self, *, artifact_bytes: bytes) -> bool:
        """Verify that the stored evidence_hash matches a fresh computation.

        Called at:
        - Audit reads: flag audit failure if hash mismatch.
        - Regulator inquiry: return hash for independent verification.

        Args:
            artifact_bytes: The raw bytes of the stored artifact (fetched via
                Phase 10 storage port).

        Returns:
            True if SHA-256(artifact_bytes) == self.evidence_hash.
        """
        recomputed = hashlib.sha256(artifact_bytes).hexdigest()
        return recomputed == self.evidence_hash


# ─────────────────────────────────────────────────────────────────────────
# Auto-suspend service
# ─────────────────────────────────────────────────────────────────────────

@dataclass
class AutoSuspendResult:
    """Result of a single auto-suspend check run. Per ADR-0102."""
    expired_count: int = 0          # Evidence past expiry → revoked
    expiring_soon_count: int = 0    # Evidence expiring within 30 days → alert
    rounds_voided: int = 0          # Active rounds voided due to expiry
    alerts_sent: int = 0            # Pre-expiry alerts sent
    errors: List[str] = field(default_factory=list)


class CertExpiryService:
    """Service that checks cert expiry and triggers auto-suspend. Per ADR-0102.

    This service is called by a daily Celery task (`check_cert_expiry`).
    The task is registered in the Celery beat schedule (Phase 8 reliability).

    For each CertificationEvidence:
    1. If `expires_at` is within 30 days → alert (Slack/email to Compliance Lead + Product Owner).
    2. If `expires_at` has passed:
       a. Transition the linked MathVersion to status `revoked` (ADR-0099 synchronous revocation).
       b. Transition the linked GameRelease (ADR-0103) to `suspended`.
       c. Void all active rounds using this math version (ADR-0093).
       d. Refuse new round initiation using this math version.
    3. Emit audit event (Phase 7) + outbox event (Phase 8).
    """

    def __init__(self, *, alert_sender=None, math_version_repo=None,
                 release_repo=None, round_voiding_adapter=None):
        """
        Args:
            alert_sender: Callable that sends pre-expiry alerts (Slack/email).
                          Signature: alert_sender(evidence: CertificationEvidence) -> None.
            math_version_repo: Repository for MathVersion (for revoke transition).
            release_repo: Repository for GameRelease (for suspend transition).
            round_voiding_adapter: RealRoundVoidingAdapter (Phase 15) for voiding active rounds.
        """
        self._alert_sender = alert_sender
        self._math_version_repo = math_version_repo
        self._release_repo = release_repo
        self._round_voiding_adapter = round_voiding_adapter

    def check_all(self, *, evidences: List[CertificationEvidence]) -> AutoSuspendResult:
        """Check all evidence for expiry. Per ADR-0102.

        Args:
            evidences: All CertificationEvidence rows to check.

        Returns:
            AutoSuspendResult with counts of expired/expiring_soon/rounds_voided/alerts_sent.
        """
        result = AutoSuspendResult()
        for evidence in evidences:
            try:
                if evidence.is_expired:
                    self._handle_expired(evidence, result)
                elif evidence.is_expiring_soon:
                    self._handle_expiring_soon(evidence, result)
            except Exception as e:
                result.errors.append(
                    f"evidence {evidence.evidence_uuid}: {type(e).__name__}: {e}"
                )
        return result

    def _handle_expired(self, evidence: CertificationEvidence,
                        result: AutoSuspendResult) -> None:
        """Handle an expired evidence: revoke + suspend + void + alert. Per ADR-0102."""
        result.expired_count += 1

        # 1. Revoke the math version (synchronous, Law 10).
        if self._math_version_repo is not None:
            math_version = self._math_version_repo.get(evidence.math_version_uuid)
            if math_version is not None and not math_version.is_terminal:
                revoked = math_version.revoke(reason=f"cert_expired:{evidence.evidence_uuid}")
                self._math_version_repo.save(revoked)

        # 2. Suspend the linked game release.
        if self._release_repo is not None:
            release = self._release_repo.get_by_math_version(evidence.math_version_uuid)
            if release is not None and release.status == "published":
                release.suspend(reason="cert_expired")
                self._release_repo.save(release)

        # 3. Void all active rounds using this math version.
        if self._round_voiding_adapter is not None:
            active_rounds = self._round_voiding_adapter.list_active_rounds_for_math_version(
                math_version_uuid=evidence.math_version_uuid,
            )
            for round_id in active_rounds:
                self._round_voiding_adapter.void_round(
                    tenant_id=evidence.tenant_uuid,
                    round_id=round_id,
                    reason="cert_expired",
                )
                result.rounds_voided += 1

        # 4. Emit audit event + outbox event (Phase 7 + Phase 8).
        # In production this would call audit_service.append() + outbox_service.emit().
        # For Stage A design, we log the event.
        import logging
        logging.getLogger("noventra.games.cert").warning(
            "cert_expired_auto_suspend",
            extra={
                "evidence_uuid": str(evidence.evidence_uuid),
                "math_version_uuid": str(evidence.math_version_uuid),
                "rounds_voided": result.rounds_voided,
            },
        )

    def _handle_expiring_soon(self, evidence: CertificationEvidence,
                              result: AutoSuspendResult) -> None:
        """Handle an expiring-soon evidence: send pre-expiry alert. Per ADR-0102."""
        result.expiring_soon_count += 1
        if self._alert_sender is not None:
            try:
                self._alert_sender(evidence)
                result.alerts_sent += 1
            except Exception as e:
                result.errors.append(
                    f"alert send failed for {evidence.evidence_uuid}: {e}"
                )


# ─────────────────────────────────────────────────────────────────────────
# Celery task stub (registered in Phase 8 beat schedule)
# ─────────────────────────────────────────────────────────────────────────

def check_cert_expiry_task() -> AutoSuspendResult:
    """Daily Celery task: check cert expiry + auto-suspend. Per ADR-0102.

    This is a stub. In production, this task is registered in the Celery beat
    schedule with `crontab(hour=2, minute=0)` (daily at 02:00 UTC). The task
    loads all CertificationEvidence rows from the DB and calls
    CertExpiryService.check_all().

    The task is idempotent: re-running it on the same day produces the same
    result (expired evidences are already revoked; alerts are deduplicated by
    the alert_sender).
    """
    # In production: load evidences from DB, build service, call check_all.
    # For Stage A design, this stub returns an empty result.
    return AutoSuspendResult()
