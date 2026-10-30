"""Document model + versioning + types.

Per ADR-0053 / DEC-0058.
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


class DocumentType(str, enum.Enum):
    """Closed catalog of document types per Phase 10 spec output #10."""
    PASSPORT = "passport"
    NATIONAL_ID = "national_id"
    DRIVER_LICENSE = "driver_license"
    UTILITY_BILL = "utility_bill"
    BANK_STATEMENT = "bank_statement"
    TAX_DOCUMENT = "tax_document"
    SELFIE = "selfie"


@dataclass(frozen=True)
class Document:
    """A document (one per player + doc_type). Per ADR-0053.

    The document itself is a container; versions are immutable.
    One active version per (player, doc_type).
    """

    document_uuid: uuid.UUID
    player_uuid: uuid.UUID
    tenant_uuid: uuid.UUID
    doc_type: DocumentType
    active_version_uuid: Optional[uuid.UUID] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class DocumentVersion:
    """An immutable document version. Per ADR-0053.

    Each version is insert-only. Supersession creates a new version;
    the old version is marked superseded (not deleted). Revocation
    (ADR-0055) is separate from supersession.
    """

    version_uuid: uuid.UUID
    document_uuid: uuid.UUID
    player_uuid: uuid.UUID
    tenant_uuid: uuid.UUID
    doc_type: DocumentType
    storage_key: str  # Key in the storage backend (ADR-0054)
    encryption_key_id: str  # DEK ID for cryptographic shredding (ADR-0055)
    is_superseded: bool = False
    is_revoked: bool = False  # Synchronous revocation (ADR-0055)
    superseded_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_active(self) -> bool:
        """A version is active if not superseded and not revoked."""
        return not self.is_superseded and not self.is_revoked

    @property
    def is_retrievable(self) -> bool:
        """A version is retrievable if not revoked (superseded is still retrievable for audit)."""
        return not self.is_revoked
