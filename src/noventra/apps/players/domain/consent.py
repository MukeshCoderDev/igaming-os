"""Consent domain — schema + immutability.

Per ADR-0048 (schema) + ADR-0049 (immutability).
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


class ConsentStatus(str, enum.Enum):
    GRANTED = "granted"
    REVOKED = "revoked"
    EXPIRED = "expired"
    PENDING = "pending"


class ConsentPurpose(str, enum.Enum):
    """Closed catalog of consent purposes.

    Per ADR-0048: purpose is a closed catalog. New purposes require ADR amendment.
    """

    MARKETING_EMAIL = "marketing.email"
    MARKETING_SMS = "marketing.sms"
    ANALYTICS = "analytics"
    THIRD_PARTY_SHARING = "third_party_sharing"
    PROFILING = "profiling"


@dataclass(frozen=True)
class Consent:
    """A consent record.

    Per ADR-0048: id, player_id, tenant_id, purpose, channel, status,
    granted_at, revoked_at, policy_version, consent_text_hash,
    ip_address, user_agent, correlation_id, created_at.

    Per ADR-0049: immutable (hash-chained). Revocation creates a NEW
    record (status=revoked), not a mutation.
    """

    consent_uuid: uuid.UUID
    player_uuid: uuid.UUID
    tenant_uuid: uuid.UUID
    purpose: str  # ConsentPurpose
    channel: str  # NotificationChannel
    status: ConsentStatus = ConsentStatus.PENDING
    granted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    policy_version: int = 1
    consent_text_hash: Optional[str] = None  # SHA-256 of consent text
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    correlation_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    # Hash-chain fields (per ADR-0049, reusing Phase 7 pattern).
    prev_hash: Optional[str] = None
    hash: Optional[str] = None

    def is_active(self) -> bool:
        """A consent is active if granted and not revoked/expired."""
        return self.status == ConsentStatus.GRANTED
