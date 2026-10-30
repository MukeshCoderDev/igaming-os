"""Players migration — Phase 9.

Per Phase 9 spec output #10: players, consents tables.
Both tenant-scoped (RLS per DEC-0003).
Consent insert-only (trigger per ADR-0049, reusing Phase 7 pattern).
"""

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("tenancy", "0001_initial"),
        ("identity", "0001_initial"),
    ]

    operations = [
        # ── Player table (tenant-scoped) ─────────────────────────────
        migrations.CreateModel(
            name="Player",
            fields=[
                ("player_uuid", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_uuid", models.UUIDField()),
                ("email", models.EmailField(db_index=True, max_length=254)),
                ("full_name", models.CharField(max_length=255)),
                ("date_of_birth", models.CharField(blank=True, max_length=32, null=True)),
                ("phone", models.CharField(blank=True, max_length=64, null=True)),
                ("address", models.TextField(blank=True, null=True)),
                ("jurisdiction", models.CharField(default="", max_length=64)),
                ("user_uuid", models.UUIDField(blank=True, null=True)),
                ("state", models.CharField(default="prospect", max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_active_at", models.DateTimeField(blank=True, null=True)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"db_table": "players_player"},
        ),
        # ── Consent table (tenant-scoped, insert-only) ───────────────
        migrations.CreateModel(
            name="Consent",
            fields=[
                ("consent_uuid", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("player_uuid", models.UUIDField()),
                ("tenant_uuid", models.UUIDField()),
                ("purpose", models.CharField(max_length=64)),
                ("channel", models.CharField(max_length=32)),
                ("status", models.CharField(default="pending", max_length=16)),
                ("granted_at", models.DateTimeField(blank=True, null=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("policy_version", models.IntegerField(default=1)),
                ("consent_text_hash", models.CharField(blank=True, max_length=64, null=True)),
                ("ip_address", models.CharField(blank=True, max_length=64, null=True)),
                ("user_agent", models.CharField(blank=True, max_length=255, null=True)),
                ("correlation_id", models.CharField(blank=True, max_length=64, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("prev_hash", models.CharField(blank=True, max_length=64, null=True)),
                ("hash", models.CharField(blank=True, max_length=64, null=True)),
            ],
            options={"db_table": "players_consent"},
        ),
        # ── RLS on both tables ───────────────────────────────────────
        migrations.RunSQL(
            sql=[
                "ALTER TABLE players_player ENABLE ROW LEVEL SECURITY;",
                "ALTER TABLE players_player FORCE ROW LEVEL SECURITY;",
                "ALTER TABLE players_consent ENABLE ROW LEVEL SECURITY;",
                "ALTER TABLE players_consent FORCE ROW LEVEL SECURITY;",
            ],
            reverse_sql=[],
        ),
        # ── RLS policies ─────────────────────────────────────────────
        migrations.RunSQL(
            sql=[
                """
                CREATE POLICY players_player_rls ON players_player
                    FOR ALL TO noventra_app, noventra_worker
                    USING (tenant_uuid = app.tenant_uuid())
                    WITH CHECK (tenant_uuid = app.tenant_uuid());
                """,
                """
                CREATE POLICY players_consent_rls ON players_consent
                    FOR ALL TO noventra_app, noventra_worker
                    USING (tenant_uuid = app.tenant_uuid())
                    WITH CHECK (tenant_uuid = app.tenant_uuid());
                """,
            ],
            reverse_sql=[
                "DROP POLICY IF EXISTS players_player_rls ON players_player;",
                "DROP POLICY IF EXISTS players_consent_rls ON players_consent;",
            ],
        ),
        # ── Consent insert-only enforcement (reusing Phase 7 pattern) ──
        # Per ADR-0049: consents are insert-only. Revocation = new record.
        migrations.RunSQL(
            sql=[
                """
                CREATE OR REPLACE FUNCTION consent_enforce_insert_only()
                RETURNS TRIGGER AS $$
                BEGIN
                    RAISE EXCEPTION 'players_consent is insert-only (ADR-0049). UPDATE and DELETE are forbidden.';
                END;
                $$ LANGUAGE plpgsql;
                """,
                "CREATE TRIGGER players_consent_no_update BEFORE UPDATE ON players_consent FOR EACH ROW EXECUTE FUNCTION consent_enforce_insert_only();",
                "CREATE TRIGGER players_consent_no_delete BEFORE DELETE ON players_consent FOR EACH ROW EXECUTE FUNCTION consent_enforce_insert_only();",
            ],
            reverse_sql=[
                "DROP TRIGGER IF EXISTS players_consent_no_delete ON players_consent;",
                "DROP TRIGGER IF EXISTS players_consent_no_update ON players_consent;",
                "DROP FUNCTION IF EXISTS consent_enforce_insert_only();",
            ],
        ),
        # ── Grants ───────────────────────────────────────────────────
        migrations.RunSQL(
            sql=[
                "GRANT SELECT, INSERT, UPDATE, DELETE ON players_player TO noventra_app, noventra_worker, noventra_admin;",
                "GRANT INSERT, SELECT ON players_consent TO noventra_app, noventra_worker;",
                "GRANT SELECT, INSERT, UPDATE, DELETE ON players_consent TO noventra_admin;",
            ],
            reverse_sql=[],
        ),
    ]
