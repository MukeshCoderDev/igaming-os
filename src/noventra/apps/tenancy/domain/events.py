"""Tenancy domain events.

Per DEC-0001 (event-sourced). Events are immutable records of state
changes. Phase 5 stub: events are emitted to the audit log; full
event sourcing lands in Phase 8 (DEC-0018).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class TenantCreatedEvent:
    tenant_uuid: uuid.UUID
    legal_name: str
    contract_id: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class TenantSuspendedEvent:
    tenant_uuid: uuid.UUID
    reason: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class BrandCreatedEvent:
    brand_uuid: uuid.UUID
    tenant_uuid: uuid.UUID
    name: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
