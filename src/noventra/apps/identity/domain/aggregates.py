"""Identity domain aggregates.

Per ADR-0031 (AuthN), ADR-0032 (RBAC), ADR-0033 (tenant resolution),
ADR-0034 (service identity).
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INVITED = "invited"
    SUSPENDED = "suspended"
    DEPROVISIONED = "deprovisioned"


class MembershipStatus(str, enum.Enum):
    ACTIVE = "active"
    INVITED = "invited"
    REVOKED = "revoked"


class ServiceIdentityStatus(str, enum.Enum):
    SHADOW = "shadow"
    LIVE = "live"
    DEPRECATED = "deprecated"


@dataclass(frozen=True)
class User:
    """Human user aggregate root.

    Per ADR-0031: UUID PK, email (unique), Argon2id password hash,
    status, MFA secret (TOTP), recovery codes (hashed). Multi-tenant
    via TenantMembership (not a direct tenant FK).
    """

    user_uuid: uuid.UUID
    email: str
    password_hash: str  # Argon2id
    status: UserStatus = UserStatus.INVITED
    mfa_secret: Optional[str] = None  # TOTP secret (encrypted at rest)
    mfa_enabled: bool = False
    default_tenant_uuid: Optional[uuid.UUID] = None
    failed_login_count: int = 0
    locked_until: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE

    def is_locked(self) -> bool:
        if self.locked_until is None:
            return False
        return self.locked_until > datetime.now(timezone.utc)


@dataclass(frozen=True)
class TenantMembership:
    """A user's membership in a tenant.

    Per ADR-0032: per-membership role + status. Per ADR-0033: the
    membership determines the user's effective tenant context.
    """

    membership_uuid: uuid.UUID
    user_uuid: uuid.UUID
    tenant_uuid: uuid.UUID
    role_uuid: uuid.UUID
    status: MembershipStatus = MembershipStatus.INVITED
    joined_at: Optional[datetime] = None
    invited_by: Optional[uuid.UUID] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_active(self) -> bool:
        return self.status == MembershipStatus.ACTIVE


@dataclass(frozen=True)
class Role:
    """RBAC role — a named collection of permissions.

    Per ADR-0032: baseline roles (admin, manager, viewer, service)
    seeded by migration. Custom roles are Phase 7+.
    """

    role_uuid: uuid.UUID
    name: str  # e.g., "admin", "manager", "viewer", "service"
    description: str
    is_system: bool = False  # System roles cannot be deleted.
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class Permission:
    """A single permission in the closed catalog.

    Per ADR-0032: closed enumeration. See permissions.py for the catalog.
    """

    permission_uuid: uuid.UUID
    code: str  # e.g., "tenancy.tenant.read"
    description: str
    category: str  # e.g., "tenancy", "identity", "audit"


@dataclass(frozen=True)
class ServiceIdentity:
    """Service/agent identity (non-human caller).

    Per ADR-0034: shadow→live promotion gate. typ=service JWT.
    Human-only and service-only endpoint separation.
    """

    service_uuid: uuid.UUID
    name: str  # e.g., "requirements-agent"
    tenant_uuid: uuid.UUID
    status: ServiceIdentityStatus = ServiceIdentityStatus.SHADOW
    promoted_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def can_mutate(self) -> bool:
        """Shadow services cannot mutate state (read-only)."""
        return self.status == ServiceIdentityStatus.LIVE

    def is_live(self) -> bool:
        return self.status == ServiceIdentityStatus.LIVE
