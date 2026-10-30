"""Tenancy domain aggregates.

Per DEC-0014 (Tenant as first-class aggregate root) and DEC-0001
(event-sourced). The Tenant (Operator) is the root; Brand is a child
aggregate within the tenant's boundary.

Phase 5 stub: minimal aggregates for the schema. Event-sourced
rebuild lands in Phase 8 (DEC-0018). Phase 5 uses Django ORM
persistence with RLS.
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


class TenantStatus(str, enum.Enum):
    """Lifecycle states of a tenant."""

    PROVISIONING = "provisioning"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEPROVISIONED = "deprovisioned"


@dataclass(frozen=True)
class Tenant:
    """Tenant (Operator) aggregate root.

    A Tenant is a customer institution (bank, EMI, fintech). It owns
    Brands and is the unit of RLS isolation. Per DEC-0014, every other
    aggregate carries a tenant_uuid reference.
    """

    tenant_uuid: uuid.UUID
    legal_name: str
    contract_id: str
    status: TenantStatus = TenantStatus.PROVISIONING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    suspended_at: Optional[datetime] = None

    def is_active(self) -> bool:
        return self.status == TenantStatus.ACTIVE

    def can_provision_brand(self) -> bool:
        """A brand can be provisioned only if the tenant is active."""
        return self.is_active()


@dataclass(frozen=True)
class Brand:
    """Brand — a child aggregate within a tenant.

    A Brand is a customer-facing brand under a tenant (e.g., a tenant
    bank may operate multiple consumer brands). Brand inherits the
    tenant's RLS isolation via tenant_uuid.
    """

    brand_uuid: uuid.UUID
    tenant_uuid: uuid.UUID
    name: str
    display_name: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
