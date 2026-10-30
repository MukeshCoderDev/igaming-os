"""Permission catalog — closed enumeration.

Per ADR-0032 / DEC-0037: the permission catalog is a closed enumeration.
No ad-hoc permissions. Every permission has a code, description, and
category. The catalog is the single authority for what permissions exist.

Linter rule 35 verifies the catalog is closed (every permission code in
the codebase must appear here).

To add a new permission:
1. Add it to PERMISSION_CATALOG below.
2. Add it to the appropriate role in the baseline migration.
3. Add a (role, permission) test case to the permission matrix.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


@dataclass(frozen=True)
class PermissionDef:
    code: str
    description: str
    category: str


class PermissionCode(str, enum.Enum):
    """Closed enumeration of permission codes.

    Adding a new code here requires:
    - A migration to insert it into the permissions table.
    - A role_permissions entry for every role that should have it.
    - A test case in the permission matrix.
    """

    # Tenancy
    TENANCY_TENANT_READ = "tenancy.tenant.read"
    TENANCY_TENANT_WRITE = "tenancy.tenant.write"
    TENANCY_TENANT_DELETE = "tenancy.tenant.delete"
    TENANCY_BRAND_READ = "tenancy.brand.read"
    TENANCY_BRAND_WRITE = "tenancy.brand.write"

    # Identity
    IDENTITY_USER_READ = "identity.user.read"
    IDENTITY_USER_WRITE = "identity.user.write"
    IDENTITY_USER_DELETE = "identity.user.delete"
    IDENTITY_USER_INVITE = "identity.user.invite"
    IDENTITY_ROLE_READ = "identity.role.read"
    IDENTITY_ROLE_WRITE = "identity.role.write"

    # Audit
    AUDIT_LOG_READ = "audit.log.read"
    AUDIT_LOG_EXPORT = "audit.log.export"

    # Service-only (no human should have these)
    SERVICE_MUTATE = "service.mutate"
    SERVICE_PROMOTE = "service.promote"


PERMISSION_CATALOG: tuple[PermissionDef, ...] = (
    # Tenancy
    PermissionDef("tenancy.tenant.read", "Read tenant metadata", "tenancy"),
    PermissionDef("tenancy.tenant.write", "Create/update tenant", "tenancy"),
    PermissionDef("tenancy.tenant.delete", "Delete/suspend tenant", "tenancy"),
    PermissionDef("tenancy.brand.read", "Read brand metadata", "tenancy"),
    PermissionDef("tenancy.brand.write", "Create/update brand", "tenancy"),

    # Identity
    PermissionDef("identity.user.read", "Read user metadata", "identity"),
    PermissionDef("identity.user.write", "Create/update user", "identity"),
    PermissionDef("identity.user.delete", "Delete/suspend user", "identity"),
    PermissionDef("identity.user.invite", "Invite user to tenant", "identity"),
    PermissionDef("identity.role.read", "Read role metadata", "identity"),
    PermissionDef("identity.role.write", "Create/update role (Phase 7+)", "identity"),

    # Audit
    PermissionDef("audit.log.read", "Read audit log entries", "audit"),
    PermissionDef("audit.log.export", "Export audit log bundles", "audit"),

    # Service-only
    PermissionDef("service.mutate", "Mutate state (service-only; shadow services denied)", "service"),
    PermissionDef("service.promote", "Promote a shadow service to live", "service"),
)


# Baseline role → permission mapping (used by migration to seed role_permissions).
# Per ADR-0032: admin (all), manager (read+write+invite, no delete), viewer (read-only),
# service (service-only).
BASELINE_ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "admin": tuple(pc.value for pc in PermissionCode if not pc.value.startswith("service.")),
    "manager": (
        "tenancy.tenant.read", "tenancy.tenant.write",
        "tenancy.brand.read", "tenancy.brand.write",
        "identity.user.read", "identity.user.write", "identity.user.invite",
        "identity.role.read",
        "audit.log.read",
    ),
    "viewer": (
        "tenancy.tenant.read", "tenancy.brand.read",
        "identity.user.read", "identity.role.read",
        "audit.log.read",
    ),
    "service": (
        "tenancy.tenant.read", "tenancy.brand.read",
        "identity.user.read", "identity.role.read",
        "audit.log.read",
        "service.mutate",  # Only LIVE services can exercise this.
        "service.promote",
    ),
}


def all_permission_codes() -> tuple[str, ...]:
    """Return all permission codes (for linter rule 35 + migration)."""
    return tuple(pc.value for pc in PermissionCode)
