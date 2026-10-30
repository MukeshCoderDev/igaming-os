"""Identity domain — pure domain logic (no infra imports).

Per ADR-0002 (hexagonal), ADR-0031 (AuthN), ADR-0032 (RBAC),
ADR-0033 (tenant resolution order), ADR-0034 (service identity).
"""

from .aggregates import (  # noqa: F401
    Permission,
    Role,
    ServiceIdentity,
    ServiceIdentityStatus,
    TenantMembership,
    User,
    UserStatus,
)
from .permissions import PERMISSION_CATALOG, PermissionCode  # noqa: F401
from .ports import (  # noqa: F401
    RoleRepository,
    ServiceIdentityRepository,
    TenantMembershipRepository,
    UserRepository,
)
