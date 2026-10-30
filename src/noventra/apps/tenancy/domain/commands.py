"""Tenancy domain commands.

Per DEC-0001 (event-sourced) and DEC-0014 (tenant aggregate root).
Commands are pure data; command handlers (in adapters/) execute them.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class CreateTenantCommand:
    """Command: create a new tenant (Operator)."""

    legal_name: str
    contract_id: str
    tenant_uuid: uuid.UUID  # Caller-provided for idempotency


@dataclass(frozen=True)
class SuspendTenantCommand:
    """Command: suspend an active tenant."""

    tenant_uuid: uuid.UUID
    reason: str


@dataclass(frozen=True)
class CreateBrandCommand:
    """Command: create a brand under a tenant."""

    tenant_uuid: uuid.UUID
    name: str
    display_name: str
    brand_uuid: uuid.UUID  # Caller-provided for idempotency
