"""Audit domain aggregates.

Per ADR-0035 (hash-chain), ADR-0036 (schema), ADR-0039 (clearance).
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class ActorType(str, enum.Enum):
    HUMAN = "human"
    SERVICE = "service"


@dataclass(frozen=True)
class AuditEvent:
    """A single audit event.

    Per ADR-0036: UUID PK, tenant_id (NULL for global), actor_id,
    actor_type, event_type (closed catalog), target_type, target_id,
    payload (JSONB), prev_hash, hash, correlation_id, created_at.
    """

    event_uuid: uuid.UUID
    tenant_id: Optional[uuid.UUID]  # None for global events
    actor_id: uuid.UUID
    actor_type: ActorType
    event_type: str  # from EventTypeCatalog
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    payload: dict = field(default_factory=dict)
    prev_hash: Optional[str] = None  # hex digest
    hash: Optional[str] = None  # hex digest (computed by trigger)
    correlation_id: Optional[str] = None
    created_at: Optional[datetime] = None  # DB now() on insert


@dataclass(frozen=True)
class AuditChainHead:
    """The head of a hash chain (singleton per scope).

    Per ADR-0035: chain scope = hybrid (per-tenant + global).
    """

    scope: str  # "global" or str(tenant_uuid)
    last_event_uuid: Optional[uuid.UUID] = None
    last_hash: Optional[str] = None  # hex digest
    updated_at: Optional[datetime] = None
