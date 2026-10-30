"""Math Version Model — Immutable, Hash-Verified. Per ADR-0099 / DEC-0100. Phase 16.

Game math config (RTP, volatility, hit frequency, paytable) is regulator-sensitive.
Every change requires recertification. This model enforces:

1. **Immutability after certification.** The math_version table is insert-only
   (UPDATE/DELETE forbidden at DB layer via migration trigger, per Phase 7 pattern).
   Supersession is recorded as a new row, never a mutation.

2. **Tamper detection at game launch.** Every math version carries a
   `math_config_hash` (SHA-256 over canonical JSON of `math_config`). Round
   initiation recomputes the hash and verifies it before accepting any bet.

This module is the most regulator-sensitive gaming artifact in the platform.
Law 19 mandates lab certification of math; mutable math defeats certification.
"""

from __future__ import annotations

import enum
import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


# ─────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────

class MathVersionStatus(str, enum.Enum):
    """Math version lifecycle states. Per ADR-0099.

    draft        — Created, not yet certified.
    certified    — Lab has certified this version (evidence attached).
    published    — Active in production (release FSM ADR-0103 reached 'published').
    superseded   — Replaced by a newer version; retained for audit.
    revoked      — Synchronously revoked (Law 10); no longer playable.
    """
    DRAFT = "draft"
    CERTIFIED = "certified"
    PUBLISHED = "published"
    SUPERSEDED = "superseded"
    REVOKED = "revoked"


class Volatility(str, enum.Enum):
    """Volatility classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ─────────────────────────────────────────────────────────────────────────
# Canonical JSON
# ─────────────────────────────────────────────────────────────────────────

def canonical_json(obj: Any) -> str:
    """Canonical JSON encoding for hash stability. Per ADR-0099.

    The hash is computed over canonical JSON to ensure that two structurally
    identical configs produce the same hash regardless of key order or
    whitespace. The encoding is pinned to:
    - sort_keys=True (deterministic key order)
    - separators=(',', ':') (no whitespace)
    - ensure_ascii=False (no Unicode escapes for ASCII chars)
    - allow_nan=False (reject NaN/Infinity — invalid in JSON spec)

    This function MUST be stable across Python versions. The pinning above
    is the Python json module's stable canonical form.
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def compute_math_config_hash(math_config: dict) -> str:
    """Compute SHA-256 hex over canonical JSON of math_config. Per ADR-0099.

    Args:
        math_config: The full math config dict (RNG seed handling, reel strips,
                     paytable, etc.). Must be JSON-serializable.

    Returns:
        64-character hex string (SHA-256).
    """
    canonical = canonical_json(math_config).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


# ─────────────────────────────────────────────────────────────────────────
# MathVersion entity
# ─────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MathVersion:
    """Immutable math version entity. Per ADR-0099 / DEC-0100.

    This is a frozen dataclass — instances cannot be mutated after creation.
    The DB trigger (migration 0001) enforces the same property at the data
    layer (UPDATE/DELETE forbidden).

    Lifecycle:
    1. Created in `draft` status (no cert evidence yet).
    2. Lab certifies → status = `certified`, cert_evidence_id set.
    3. Release FSM (ADR-0103) reaches `published` → status = `published`.
    4. New version supersedes → status = `superseded`, superseded_by set.
    5. Synchronous revocation (Law 10) → status = `revoked` (terminal).

    The `math_config_hash` is computed at construction time and verified at
    every downstream read (round initiation, audit, dispute evidence).
    """

    version_uuid: uuid.UUID
    tenant_uuid: uuid.UUID
    game_id: str
    version: str  # Semver-style (e.g., "1.0.0")
    rtp_percentage: float  # 4 decimal places (e.g., 96.1234)
    volatility: Volatility
    hit_frequency: float  # 0.0–1.0
    paytable: dict  # Full paytable structure
    math_config: dict  # Full math config (RNG seed handling, reel strips, etc.)
    math_config_hash: str  # SHA-256 hex over canonical JSON of math_config
    status: MathVersionStatus = MathVersionStatus.DRAFT
    certified_at: Optional[datetime] = None
    certified_by: Optional[str] = None  # Lab name (e.g., "GLI")
    cert_evidence_id: Optional[uuid.UUID] = None  # FK → CertificationEvidence
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    superseded_by: Optional[uuid.UUID] = None  # FK → newer MathVersion

    def __post_init__(self):
        """Verify math_config_hash matches recomputed hash. Per ADR-0099.

        This catches tampering at construction time. If a caller tries to
        construct a MathVersion with a math_config that doesn't match the
        declared hash, the construction fails.
        """
        recomputed = compute_math_config_hash(self.math_config)
        if recomputed != self.math_config_hash:
            raise ValueError(
                f"math_config_hash mismatch: declared={self.math_config_hash} "
                f"but recomputed={recomputed}. Math config may have been tampered."
            )

    @classmethod
    def create_draft(
        cls,
        *,
        tenant_uuid: uuid.UUID,
        game_id: str,
        version: str,
        rtp_percentage: float,
        volatility: Volatility,
        hit_frequency: float,
        paytable: dict,
        math_config: dict,
    ) -> "MathVersion":
        """Create a new draft math version. Per ADR-0099.

        Computes the math_config_hash from the math_config dict.
        Returns a MathVersion in DRAFT status (no cert evidence yet).
        """
        return cls(
            version_uuid=uuid.uuid4(),
            tenant_uuid=tenant_uuid,
            game_id=game_id,
            version=version,
            rtp_percentage=rtp_percentage,
            volatility=volatility,
            hit_frequency=hit_frequency,
            paytable=paytable,
            math_config=math_config,
            math_config_hash=compute_math_config_hash(math_config),
            status=MathVersionStatus.DRAFT,
        )

    def certify(
        self,
        *,
        lab_name: str,
        cert_evidence_id: uuid.UUID,
        certified_at: Optional[datetime] = None,
    ) -> "MathVersion":
        """Return a NEW MathVersion instance in CERTIFIED status. Per ADR-0099.

        Because MathVersion is frozen, this returns a new instance with the
        certified_at, certified_by, cert_evidence_id, and status fields updated.
        The original instance is unchanged (audit trail).

        This method does NOT mutate the DB row. The DB trigger forbids UPDATE.
        The service layer (math_version_service.py) handles the DB write,
        which is an INSERT of a new row + UPDATE of the old row's status to
        SUPERSEDED (the trigger allows status transitions; it forbids
        mutation of math_config / math_config_hash).
        """
        if self.status != MathVersionStatus.DRAFT:
            raise ValueError(
                f"Cannot certify math version in status {self.status.value}; "
                f"only DRAFT can be certified."
            )
        return MathVersion(
            version_uuid=self.version_uuid,
            tenant_uuid=self.tenant_uuid,
            game_id=self.game_id,
            version=self.version,
            rtp_percentage=self.rtp_percentage,
            volatility=self.volatility,
            hit_frequency=self.hit_frequency,
            paytable=self.paytable,
            math_config=self.math_config,
            math_config_hash=self.math_config_hash,
            status=MathVersionStatus.CERTIFIED,
            certified_at=certified_at or datetime.now(timezone.utc),
            certified_by=lab_name,
            cert_evidence_id=cert_evidence_id,
            created_at=self.created_at,
            superseded_by=None,
        )

    def revoke(self, *, reason: str = "") -> "MathVersion":
        """Return a NEW MathVersion instance in REVOKED status. Per ADR-0099, Law 10.

        Synchronous revocation: the revoked version is unretrievable in the
        same transaction. New round initiation using a revoked math version
        is refused.
        """
        if self.status == MathVersionStatus.REVOKED:
            raise ValueError("Math version is already revoked (terminal state).")
        if self.status == MathVersionStatus.SUPERSEDED:
            raise ValueError("Cannot revoke a superseded math version.")
        return MathVersion(
            version_uuid=self.version_uuid,
            tenant_uuid=self.tenant_uuid,
            game_id=self.game_id,
            version=self.version,
            rtp_percentage=self.rtp_percentage,
            volatility=self.volatility,
            hit_frequency=self.hit_frequency,
            paytable=self.paytable,
            math_config=self.math_config,
            math_config_hash=self.math_config_hash,
            status=MathVersionStatus.REVOKED,
            certified_at=self.certified_at,
            certified_by=self.certified_by,
            cert_evidence_id=self.cert_evidence_id,
            created_at=self.created_at,
            superseded_by=None,
        )

    @property
    def is_playable(self) -> bool:
        """True if this math version can be used for new rounds. Per ADR-0099.

        Only PUBLISHED versions are playable. DRAFT/CERTIFIED are pre-release;
        SUPERSEDED/REVOKED are not playable.
        """
        return self.status == MathVersionStatus.PUBLISHED

    @property
    def is_terminal(self) -> bool:
        """True if this math version is in a terminal state (no further transitions)."""
        return self.status in (MathVersionStatus.REVOKED,)

    def verify_hash(self) -> bool:
        """Verify that the stored math_config_hash matches a fresh computation.

        Called at:
        - Round initiation (ADR-0101): refuse bet if hash mismatch.
        - Audit reads (Phase 7): flag audit failure if hash mismatch.
        - Dispute evidence pack (ADR-0076): include hash for lab verification.
        - Regulator inquiry API: return hash for independent verification.
        """
        return compute_math_config_hash(self.math_config) == self.math_config_hash
