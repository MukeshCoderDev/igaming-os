"""Identity ORM adapter — Django models.

Per ADR-0031 (AuthN), ADR-0032 (RBAC), ADR-0033 (tenant resolution),
ADR-0034 (service identity). Per DEC-0003 (RLS): every tenant-scoped
table has tenant_uuid + RLS policy.
"""

from __future__ import annotations

import uuid

from django.db import models


class User(models.Model):
    """Human user. NOT tenant-scoped (a user can belong to multiple tenants).

    Per ADR-0031: UUID PK, email (unique), Argon2id password hash.
    Per ADR-0033: multi-tenant via TenantMembership.
    """

    user_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    password_hash = models.CharField(max_length=255)  # Argon2id
    status = models.CharField(max_length=32, default="invited")
    mfa_secret = models.CharField(max_length=255, null=True, blank=True)  # Encrypted TOTP secret
    mfa_enabled = models.BooleanField(default=False)
    default_tenant_uuid = models.UUIDField(null=True, blank=True)
    failed_login_count = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "identity_user"
        app_label = "identity"

    def __str__(self) -> str:
        return f"User({self.email})"


class TenantMembership(models.Model):
    """A user's membership in a tenant.

    Per ADR-0032: per-membership role + status.
    Per ADR-0033: determines effective tenant context.
    Tenant-scoped (RLS): a user's memberships are visible only within
    the tenant context.
    """

    membership_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_uuid", to_field="user_uuid")
    tenant_uuid = models.UUIDField()  # FK to tenancy_tenant (not a Django FK to avoid cross-app coupling)
    role = models.ForeignKey("Role", on_delete=models.PROTECT, db_column="role_uuid", to_field="role_uuid")
    status = models.CharField(max_length=32, default="invited")
    joined_at = models.DateTimeField(null=True, blank=True)
    invited_by = models.UUIDField(null=True, blank=True)  # user_uuid of inviter
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "identity_tenant_membership"
        app_label = "identity"
        unique_together = (("user", "tenant_uuid"),)


class Role(models.Model):
    """RBAC role. NOT tenant-scoped (system-wide catalog).

    Per ADR-0032: baseline roles (admin, manager, viewer, service) seeded.
    """

    role_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=255)
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "identity_role"
        app_label = "identity"

    def __str__(self) -> str:
        return f"Role({self.name})"


class Permission(models.Model):
    """A permission in the closed catalog. NOT tenant-scoped.

    Per ADR-0032: closed enumeration seeded from permissions.py.
    """

    permission_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=128, unique=True)
    description = models.CharField(max_length=255)
    category = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "identity_permission"
        app_label = "identity"

    def __str__(self) -> str:
        return f"Permission({self.code})"


class RolePermission(models.Model):
    """Many-to-many: role ↔ permission. NOT tenant-scoped."""

    role = models.ForeignKey(Role, on_delete=models.CASCADE, db_column="role_uuid", to_field="role_uuid")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, db_column="permission_uuid", to_field="permission_uuid")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "identity_role_permission"
        app_label = "identity"
        unique_together = (("role", "permission"),)


class ServiceIdentity(models.Model):
    """Service/agent identity. Tenant-scoped (RLS).

    Per ADR-0034: shadow→live promotion gate. typ=service JWT.
    """

    service_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    tenant_uuid = models.UUIDField()
    status = models.CharField(max_length=32, default="shadow")  # shadow, live, deprecated
    promoted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "identity_service_identity"
        app_label = "identity"
        unique_together = (("tenant_uuid", "name"),)


class RefreshTokenBlacklist(models.Model):
    """Blacklisted refresh tokens (after rotation or revocation).

    Per ADR-0031: rotating refresh tokens; old tokens blacklisted.
    NOT tenant-scoped (token revocation is global).
    """

    jti = models.CharField(max_length=255, primary_key=True)  # JWT ID
    user_uuid = models.UUIDField()
    revoked_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=64, default="rotation")  # rotation, logout, revocation

    class Meta:
        db_table = "identity_refresh_token_blacklist"
        app_label = "identity"
