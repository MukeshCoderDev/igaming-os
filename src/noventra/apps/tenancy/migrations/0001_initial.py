"""Tenancy migration — Phase 5.

Per Phase 5 spec outputs #2, #3, #6:
- Operator (Tenant) + Brand tables.
- RLS policies on both: USING (tenant_uuid = app.tenant_uuid()) WITH CHECK.
- Global tables (none in Phase 5) would be allowlisted.
- Baseline dev data: 2 tenants + 2 brands for testing.

Per DEC-0003 / ADR-0003: RLS enforced strictly at tenant_uuid level.
Per DEC-0035 / ADR-0030: SET LOCAL only (no session-level features).
"""

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        # ── Tenant (Operator) table ──────────────────────────────────
        migrations.CreateModel(
            name="Tenant",
            fields=[
                (
                    "tenant_uuid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        help_text="Tenant UUID (PK). Used by RLS policy.",
                    ),
                ),
                ("legal_name", models.CharField(max_length=255, help_text="Legal name of the tenant institution.")),
                ("jurisdiction", models.CharField(max_length=64, help_text="Jurisdiction code (e.g., US-NY, EU-DE).")),
                ("contract_id", models.CharField(max_length=128, help_text="External contract identifier.")),
                ("status", models.CharField(default="provisioning", max_length=32, help_text="Lifecycle status: provisioning, active, suspended, deprovisioned.")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("suspended_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "tenancy_tenant",
            },
        ),
        # ── Brand table ──────────────────────────────────────────────
        migrations.CreateModel(
            name="Brand",
            fields=[
                (
                    "brand_uuid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        help_text="Brand UUID (PK).",
                    ),
                ),
                ("name", models.CharField(max_length=128, help_text="Brand name (machine-readable).")),
                ("display_name", models.CharField(max_length=255, help_text="Brand display name (human-readable).")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        db_column="tenant_uuid",
                        help_text="Owning tenant.",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="brands",
                        to="tenancy.tenant",
                        to_field="tenant_uuid",
                    ),
                ),
            ],
            options={
                "db_table": "tenancy_brand",
                "unique_together": {("tenant", "name")},
            },
        ),
        # ── RLS: enable on tenancy_tenant ────────────────────────────
        # Per DEC-0003: every tenant-scoped table gets RLS.
        migrations.RunSQL(
            sql=["ALTER TABLE tenancy_tenant ENABLE ROW LEVEL SECURITY;"],
            reverse_sql=["ALTER TABLE tenancy_tenant DISABLE ROW LEVEL SECURITY;"],
        ),
        # ── RLS: enable on tenancy_brand ─────────────────────────────
        migrations.RunSQL(
            sql=["ALTER TABLE tenancy_brand ENABLE ROW LEVEL SECURITY;"],
            reverse_sql=["ALTER TABLE tenancy_brand DISABLE ROW LEVEL SECURITY;"],
        ),
        # ── RLS policy: tenancy_tenant ───────────────────────────────
        # USING: visible rows must match current tenant.
        # WITH CHECK: new rows must match current tenant.
        # Fail-closed: if app.tenant_uuid() returns NULL, no rows match.
        migrations.RunSQL(
            sql=[
                """
                CREATE POLICY tenancy_tenant_rls ON tenancy_tenant
                    FOR ALL
                    TO noventra_app, noventra_worker
                    USING (tenant_uuid = app.tenant_uuid())
                    WITH CHECK (tenant_uuid = app.tenant_uuid());
                """,
            ],
            reverse_sql=["DROP POLICY IF EXISTS tenancy_tenant_rls ON tenancy_tenant;"],
        ),
        # ── RLS policy: tenancy_brand ────────────────────────────────
        # The brand table's tenant_uuid column is the FK to tenancy_tenant.
        migrations.RunSQL(
            sql=[
                """
                CREATE POLICY tenancy_brand_rls ON tenancy_brand
                    FOR ALL
                    TO noventra_app, noventra_worker
                    USING (tenant_uuid = app.tenant_uuid())
                    WITH CHECK (tenant_uuid = app.tenant_uuid());
                """,
            ],
            reverse_sql=["DROP POLICY IF EXISTS tenancy_brand_rls ON tenancy_brand;"],
        ),
        # ── Force RLS on table owner ─────────────────────────────────
        # Per DEC-0003: even the table owner must be subject to RLS.
        # The owner role (noventra_owner) is NOLOGIN; the app connects
        # as noventra_app. This ensures no bypass via ownership.
        migrations.RunSQL(
            sql=[
                "ALTER TABLE tenancy_tenant FORCE ROW LEVEL SECURITY;",
                "ALTER TABLE tenancy_brand FORCE ROW LEVEL SECURITY;",
            ],
            reverse_sql=[],
        ),
        # ── Break-glass admin role (DEC-0003 §3.3) ──────────────────
        # noventra_admin has BYPASSRLS. Used only via break-glass
        # workflow (dual-control, time-bound, heavy audit).
        migrations.RunSQL(
            sql=[
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'noventra_admin') THEN
                        CREATE ROLE noventra_admin NOLOGIN BYPASSRLS;
                    END IF;
                END
                $$;
                """,
                "GRANT SELECT, INSERT, UPDATE, DELETE ON tenancy_tenant, tenancy_brand TO noventra_admin;",
                "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO noventra_admin;",
            ],
            reverse_sql=[],
        ),
        migrations.RunSQL(
            sql=[
                "GRANT SELECT, INSERT, UPDATE, DELETE ON tenancy_tenant, tenancy_brand TO noventra_app, noventra_worker;",
            ],
            reverse_sql=[],
        ),
        # ── Baseline dev data (2 tenants + 2 brands) ─────────────────
        # Only loaded in dev/test. Production seeds via provisioning API.
        # UUIDs are fixed for deterministic tests.
        migrations.RunSQL(
            sql=[
                """
                INSERT INTO tenancy_tenant (tenant_uuid, legal_name, jurisdiction, contract_id, status, created_at)
                VALUES
                    ('00000000-0000-0000-0000-000000000001', 'Acme Bank', 'US-NY', 'CTR-001', 'active', NOW()),
                    ('00000000-0000-0000-0000-000000000002', 'Globex EMI', 'EU-DE', 'CTR-002', 'active', NOW())
                ON CONFLICT (tenant_uuid) DO NOTHING;
                """,
                """
                INSERT INTO tenancy_brand (brand_uuid, tenant_uuid, name, display_name, created_at)
                VALUES
                    ('00000000-0000-0000-0000-0000000000a1', '00000000-0000-0000-0000-000000000001', 'acme-retail', 'Acme Retail Banking', NOW()),
                    ('00000000-0000-0000-0000-0000000000b1', '00000000-0000-0000-0000-000000000002', 'globex-consumer', 'Globex Consumer', NOW())
                ON CONFLICT (brand_uuid) DO NOTHING;
                """,
            ],
            reverse_sql=[],
        ),
    ]
