"""Tenancy domain ports (interfaces).

Per ADR-0002 (hexagonal): ports are interfaces defined in the domain
layer. Adapters (in adapters/) implement them. Domain logic depends
only on these ports, never on Django ORM or other infrastructure.
"""

from __future__ import annotations

import abc
import uuid
from typing import Optional

from .aggregates import Brand, Tenant


class TenantRepository(abc.ABC):
    """Port: repository for Tenant and Brand aggregates."""

    @abc.abstractmethod
    def get_tenant(self, tenant_uuid: uuid.UUID) -> Optional[Tenant]:
        """Return the tenant with the given UUID, or None if not found."""

    @abc.abstractmethod
    def save_tenant(self, tenant: Tenant) -> None:
        """Persist a tenant (create or update)."""

    @abc.abstractmethod
    def get_brand(self, brand_uuid: uuid.UUID) -> Optional[Brand]:
        """Return the brand with the given UUID, or None if not found."""

    @abc.abstractmethod
    def save_brand(self, brand: Brand) -> None:
        """Persist a brand (create or update)."""

    @abc.abstractmethod
    def tenant_exists(self, tenant_uuid: uuid.UUID) -> bool:
        """Return True if a tenant with the given UUID exists.

        Used by the tenant middleware for fast existence checks.
        """
