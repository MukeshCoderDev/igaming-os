"""Identity migration — Phase 6.

Per Phase 6 spec output #8: migrations for users, tenant_memberships,
roles, permissions, role_permissions, service_identities,
refresh_token_blacklist.

Per DEC-0003 / ADR-0003: every tenant-scoped table has RLS.
Per ADR-0032: baseline roles + permission catalog seeded.
Per ADR-0034: baseline service identities seeded.
"""

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("tenancy", "0001_initial"),
    ]

    operations = [
        # ── Role (global, not tenant-scoped) ─────────────────────────
        migrations.CreateModel(
            name="Role",
            fields=[
                ("role_uuid", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=64, unique=True)),
                ("description", models.CharField(max_length=255)),
                ("is_system", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "identity_role"},
        ),
        # ── Permission (global) ──────────────────────────────────────
        migrations.CreateModel(
            name="Permission",
            fields=[
                ("permission_uuid", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("code", models.CharField(max_length=128, unique=True)),
                ("description", models.CharField(max_length=255)),
                ("category", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "identity_permission"},
        ),
        # ── RolePermission (global) ─────────────────────────────────
        migrations.CreateModel(
            name="RolePermission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("role", models.ForeignKey(db_column="role_uuid", on_delete=django.db.models.deletion.CASCADE, to="identity.role", to_field="role_uuid")),
                ("permission", models.ForeignKey(db_column="permission_uuid", on_delete=django.db.models.deletion.CASCADE, to="identity.permission", to_field="permission_uuid")),
            ],
            options={
                "db_table": "identity_role_permission",
                "unique_together": {("role", "permission")},
            },
        ),
        # ── User (global, not tenant-scoped — multi-tenant via membership) ──
        migrations.CreateModel(
            name="User",
            fields=[
                ("user_uuid", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("email", models.EmailField(db_index=True, max_length=254, unique=True)),
                ("password_hash", models.CharField(max_length=255)),
                ("status", models.CharField(default="invited", max_length=32)),
                ("mfa_secret", models.CharField(blank=True, max_length=255, null=True)),
                ("mfa_enabled", models.BooleanField(default=False)),
                ("default_tenant_uuid", models.UUIDField(blank=True, null=True)),
                ("failed_login_count", models.IntegerField(default=0)),
                ("locked_until", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "identity_user"},
        ),
        # ── TenantMembership (tenant-scoped — RLS) ───────────────────
        migrations.CreateModel(
            name="TenantMembership",
            fields=[
                ("membership_uuid", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_uuid", models.UUIDField()),
                ("status", models.CharField(default="invited", max_length=32)),
                ("joined_at", models.DateTimeField(blank=True, null=True)),
                ("invited_by", models.UUIDField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("role", models.ForeignKey(db_column="role_uuid", on_delete=django.db.models.deletion.PROTECT, to="identity.role", to_field="role_uuid")),
                ("user", models.ForeignKey(db_column="user_uuid", on_delete=django.db.models.deletion.CASCADE, to="identity.user", to_field="user_uuid")),
            ],
            options={
                "db_table": "identity_tenant_membership",
                "unique_together": {("user", "tenant_uuid")},
            },
        ),
        # ── ServiceIdentity (tenant-scoped — RLS) ────────────────────
        migrations.CreateModel(
            name="ServiceIdentity",
            fields=[
                ("service_uuid", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=128)),
                ("tenant_uuid", models.UUIDField()),
                ("status", models.CharField(default="shadow", max_length=32)),
                ("promoted_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "identity_service_identity",
                "unique_together": {("tenant_uuid", "name")},
            },
        ),
        # ── RefreshTokenBlacklist (global) ───────────────────────────
        migrations.CreateModel(
            name="RefreshTokenBlacklist",
            fields=[
                ("jti", models.CharField(max_length=255, primary_key=True, serialize=False)),
                ("user_uuid", models.UUIDField()),
                ("revoked_at", models.DateTimeField(auto_now_add=True)),
                ("reason", models.CharField(default="rotation", max_length=64)),
            ],
            options={"db_table": "identity_refresh_token_blacklist"},
        ),
        # ── RLS: enable + force on tenant-scoped tables ───────────────
        # identity_tenant_membership and identity_service_identity are tenant-scoped.
        migrations.RunSQL(
            sql=[
                "ALTER TABLE identity_tenant_membership ENABLE ROW LEVEL SECURITY;",
                "ALTER TABLE identity_tenant_membership FORCE ROW LEVEL SECURITY;",
                "ALTER TABLE identity_service_identity ENABLE ROW LEVEL SECURITY;",
                "ALTER TABLE identity_service_identity FORCE ROW LEVEL SECURITY;",
            ],
            reverse_sql=[],
        ),
        # ── RLS policies ─────────────────────────────────────────────
        migrations.RunSQL(
            sql=[
                """
                CREATE POLICY identity_tenant_membership_rls ON identity_tenant_membership
                    FOR ALL TO noventra_app, noventra_worker
                    USING (tenant_uuid = app.tenant_uuid())
                    WITH CHECK (tenant_uuid = app.tenant_uuid());
                """,
                """
                CREATE POLICY identity_service_identity_rls ON identity_service_identity
                    FOR ALL TO noventra_app, noventra_worker
                    USING (tenant_uuid = app.tenant_uuid())
                    WITH CHECK (tenant_uuid = app.tenant_uuid());
                """,
            ],
            reverse_sql=[
                "DROP POLICY IF EXISTS identity_tenant_membership_rls ON identity_tenant_membership;",
                "DROP POLICY IF EXISTS identity_service_identity_rls ON identity_service_identity;",
            ],
        ),
        # ── Grant noventra_admin on identity tables ──────────────────
        migrations.RunSQL(
            sql=[
                "GRANT SELECT, INSERT, UPDATE, DELETE ON identity_user, identity_tenant_membership, identity_role, identity_permission, identity_role_permission, identity_service_identity, identity_refresh_token_blacklist TO noventra_admin;",
                "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO noventra_admin;",
            ],
            reverse_sql=[],
        ),
        # ── Baseline data: roles ─────────────────────────────────────
        # Fixed UUIDs for deterministic tests.
        migrations.RunSQL(
            sql=[
                """
                INSERT INTO identity_role (role_uuid, name, description, is_system, created_at) VALUES
                    ('00000000-0000-0000-0000-000000000101', 'admin', 'Full access (no service permissions)', true, NOW()),
                    ('00000000-0000-0000-0000-000000000102', 'manager', 'Read + write + invite (no delete)', true, NOW()),
                    ('00000000-0000-0000-0000-000000000103', 'viewer', 'Read-only', true, NOW()),
                    ('00000000-0000-0000-0000-000000000104', 'service', 'Service-account role (service-only permissions)', true, NOW())
                ON CONFLICT (name) DO NOTHING;
                """,
            ],
            reverse_sql=[],
        ),
        # ── Baseline data: permissions (from permissions.py catalog) ──
        migrations.RunSQL(
            sql=[
                """
                INSERT INTO identity_permission (permission_uuid, code, description, category, created_at) VALUES
                    ('00000000-0000-0000-0001-000000000001', 'tenancy.tenant.read', 'Read tenant metadata', 'tenancy', NOW()),
                    ('00000000-0000-0000-0001-000000000002', 'tenancy.tenant.write', 'Create/update tenant', 'tenancy', NOW()),
                    ('00000000-0000-0000-0001-000000000003', 'tenancy.tenant.delete', 'Delete/suspend tenant', 'tenancy', NOW()),
                    ('00000000-0000-0000-0001-000000000004', 'tenancy.brand.read', 'Read brand metadata', 'tenancy', NOW()),
                    ('00000000-0000-0000-0001-000000000005', 'tenancy.brand.write', 'Create/update brand', 'tenancy', NOW()),
                    ('00000000-0000-0000-0002-000000000001', 'identity.user.read', 'Read user metadata', 'identity', NOW()),
                    ('00000000-0000-0000-0002-000000000002', 'identity.user.write', 'Create/update user', 'identity', NOW()),
                    ('00000000-0000-0000-0002-000000000003', 'identity.user.delete', 'Delete/suspend user', 'identity', NOW()),
                    ('00000000-0000-0000-0002-000000000004', 'identity.user.invite', 'Invite user to tenant', 'identity', NOW()),
                    ('00000000-0000-0000-0002-000000000005', 'identity.role.read', 'Read role metadata', 'identity', NOW()),
                    ('00000000-0000-0000-0002-000000000006', 'identity.role.write', 'Create/update role (Phase 7+)', 'identity', NOW()),
                    ('00000000-0000-0000-0003-000000000001', 'audit.log.read', 'Read audit log entries', 'audit', NOW()),
                    ('00000000-0000-0000-0003-000000000002', 'audit.log.export', 'Export audit log bundles', 'audit', NOW()),
                    ('00000000-0000-0000-0004-000000000001', 'service.mutate', 'Mutate state (service-only; shadow denied)', 'service', NOW()),
                    ('00000000-0000-0000-0004-000000000002', 'service.promote', 'Promote shadow service to live', 'service', NOW())
                ON CONFLICT (code) DO NOTHING;
                """,
            ],
            reverse_sql=[],
        ),
        # ── Baseline data: role_permissions ──────────────────────────
        # admin: all non-service permissions.
        # manager: read+write+invite (no delete, no service).
        # viewer: read-only.
        # service: read + service-only.
        migrations.RunSQL(
            sql=[
                # admin: all non-service permissions
                """
                INSERT INTO identity_role_permission (role_uuid, permission_uuid, created_at)
                SELECT r.role_uuid, p.permission_uuid, NOW()
                FROM identity_role r CROSS JOIN identity_permission p
                WHERE r.name = 'admin' AND p.code NOT LIKE 'service.%'
                ON CONFLICT DO NOTHING;
                """,
                # manager
                """
                INSERT INTO identity_role_permission (role_uuid, permission_uuid, created_at)
                SELECT r.role_uuid, p.permission_uuid, NOW()
                FROM identity_role r CROSS JOIN identity_permission p
                WHERE r.name = 'manager' AND p.code IN (
                    'tenancy.tenant.read', 'tenancy.tenant.write',
                    'tenancy.brand.read', 'tenancy.brand.write',
                    'identity.user.read', 'identity.user.write', 'identity.user.invite',
                    'identity.role.read', 'audit.log.read'
                )
                ON CONFLICT DO NOTHING;
                """,
                # viewer
                """
                INSERT INTO identity_role_permission (role_uuid, permission_uuid, created_at)
                SELECT r.role_uuid, p.permission_uuid, NOW()
                FROM identity_role r CROSS JOIN identity_permission p
                WHERE r.name = 'viewer' AND p.code IN (
                    'tenancy.tenant.read', 'tenancy.brand.read',
                    'identity.user.read', 'identity.role.read', 'audit.log.read'
                )
                ON CONFLICT DO NOTHING;
                """,
                # service
                """
                INSERT INTO identity_role_permission (role_uuid, permission_uuid, created_at)
                SELECT r.role_uuid, p.permission_uuid, NOW()
                FROM identity_role r CROSS JOIN identity_permission p
                WHERE r.name = 'service' AND p.code IN (
                    'tenancy.tenant.read', 'tenancy.brand.read',
                    'identity.user.read', 'identity.role.read', 'audit.log.read',
                    'service.mutate', 'service.promote'
                )
                ON CONFLICT DO NOTHING;
                """,
            ],
            reverse_sql=[],
        ),
        # ── Baseline data: dev users + memberships ───────────────────
        # For testing: one user per tenant with admin role.
        migrations.RunSQL(
            sql=[
                """
                INSERT INTO identity_user (user_uuid, email, password_hash, status, mfa_enabled, default_tenant_uuid, failed_login_count, created_at) VALUES
                    ('00000000-0000-0000-0000-000000000a01', 'admin@acme.example', 'argon2id$placeholder', 'active', false, '00000000-0000-0000-0000-000000000001', 0, NOW()),
                    ('00000000-0000-0000-0000-000000000a02', 'admin@globex.example', 'argon2id$placeholder', 'active', false, '00000000-0000-0000-0000-000000000002', 0, NOW())
                ON CONFLICT (email) DO NOTHING;
                """,
                """
                INSERT INTO identity_tenant_membership (membership_uuid, user_uuid, tenant_uuid, role_uuid, status, joined_at, created_at) VALUES
                    ('00000000-0000-0000-0000-000000000b01', '00000000-0000-0000-0000-000000000a01', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000101', 'active', NOW(), NOW()),
                    ('00000000-0000-0000-0000-000000000b02', '00000000-0000-0000-0000-000000000a02', '00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000101', 'active', NOW(), NOW())
                ON CONFLICT DO NOTHING;
                """,
            ],
            reverse_sql=[],
        ),
        # ── Baseline data: service identities ────────────────────────
        # One shadow + one live service per tenant for testing.
        migrations.RunSQL(
            sql=[
                """
                INSERT INTO identity_service_identity (service_uuid, name, tenant_uuid, status, created_at) VALUES
                    ('00000000-0000-0000-0000-000000000c01', 'requirements-agent', '00000000-0000-0000-0000-000000000001', 'shadow', NOW()),
                    ('00000000-0000-0000-0000-000000000c02', 'audit-agent', '00000000-0000-0000-0000-000000000001', 'live', NOW()),
                    ('00000000-0000-0000-0000-000000000c03', 'compliance-agent', '00000000-0000-0000-0000-000000000002', 'shadow', NOW())
                ON CONFLICT DO NOTHING;
                """,
                # Mark the live service as promoted.
                """
                UPDATE identity_service_identity SET promoted_at = NOW() WHERE name = 'audit-agent' AND status = 'live';
                """,
            ],
            reverse_sql=[],
        ),
    ]
