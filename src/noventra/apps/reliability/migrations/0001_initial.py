"""Reliability migration — Phase 8.

Per Phase 8 spec output #11: outbox, inbox, idempotency_key tables.
All tenant-scoped (RLS per DEC-0003).
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
        # ── OutboxEvent (tenant-scoped) ──────────────────────────────
        migrations.CreateModel(
            name="OutboxEvent",
            fields=[
                ("event_id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField()),
                ("event_type", models.CharField(max_length=64)),
                ("event_version", models.IntegerField(default=1)),
                ("aggregate_id", models.CharField(max_length=128)),
                ("aggregate_type", models.CharField(max_length=64)),
                ("actor_id", models.UUIDField()),
                ("correlation_id", models.CharField(blank=True, max_length=64, null=True)),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
                ("payload", models.JSONField(default=dict)),
                ("status", models.CharField(default="pending", max_length=16)),
                ("relayed_at", models.DateTimeField(blank=True, null=True)),
                ("retry_count", models.IntegerField(default=0)),
            ],
            options={"db_table": "reliability_outbox"},
        ),
        # ── InboxEntry (tenant-scoped) ───────────────────────────────
        migrations.CreateModel(
            name="InboxEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("message_id", models.UUIDField()),
                ("consumer_id", models.CharField(max_length=64)),
                ("processed_at", models.DateTimeField(auto_now_add=True)),
                ("payload_hash", models.CharField(blank=True, max_length=64, null=True)),
                ("tenant_id", models.UUIDField()),
            ],
            options={
                "db_table": "reliability_inbox",
                "unique_together": {("message_id", "consumer_id")},
            },
        ),
        # ── IdempotencyKey (tenant-scoped) ───────────────────────────
        migrations.CreateModel(
            name="IdempotencyKey",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=64)),
                ("tenant_id", models.UUIDField()),
                ("endpoint", models.CharField(max_length=128)),
                ("request_hash", models.CharField(max_length=64)),
                ("response_status", models.IntegerField()),
                ("response_body", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
            ],
            options={
                "db_table": "reliability_idempotency_key",
                "unique_together": {("key", "tenant_id", "endpoint")},
            },
        ),
        # ── RLS on all three tables ──────────────────────────────────
        migrations.RunSQL(
            sql=[
                "ALTER TABLE reliability_outbox ENABLE ROW LEVEL SECURITY;",
                "ALTER TABLE reliability_outbox FORCE ROW LEVEL SECURITY;",
                "ALTER TABLE reliability_inbox ENABLE ROW LEVEL SECURITY;",
                "ALTER TABLE reliability_inbox FORCE ROW LEVEL SECURITY;",
                "ALTER TABLE reliability_idempotency_key ENABLE ROW LEVEL SECURITY;",
                "ALTER TABLE reliability_idempotency_key FORCE ROW LEVEL SECURITY;",
            ],
            reverse_sql=[],
        ),
        # ── RLS policies ─────────────────────────────────────────────
        migrations.RunSQL(
            sql=[
                """
                CREATE POLICY reliability_outbox_rls ON reliability_outbox
                    FOR ALL TO noventra_app, noventra_worker
                    USING (tenant_id = app.tenant_uuid())
                    WITH CHECK (tenant_id = app.tenant_uuid());
                """,
                """
                CREATE POLICY reliability_inbox_rls ON reliability_inbox
                    FOR ALL TO noventra_app, noventra_worker
                    USING (tenant_id = app.tenant_uuid())
                    WITH CHECK (tenant_id = app.tenant_uuid());
                """,
                """
                CREATE POLICY reliability_idempotency_key_rls ON reliability_idempotency_key
                    FOR ALL TO noventra_app, noventra_worker
                    USING (tenant_id = app.tenant_uuid())
                    WITH CHECK (tenant_id = app.tenant_uuid());
                """,
            ],
            reverse_sql=[
                "DROP POLICY IF EXISTS reliability_outbox_rls ON reliability_outbox;",
                "DROP POLICY IF EXISTS reliability_inbox_rls ON reliability_inbox;",
                "DROP POLICY IF EXISTS reliability_idempotency_key_rls ON reliability_idempotency_key;",
            ],
        ),
        # ── Grants ───────────────────────────────────────────────────
        migrations.RunSQL(
            sql=[
                "GRANT SELECT, INSERT, UPDATE, DELETE ON reliability_outbox, reliability_inbox, reliability_idempotency_key TO noventra_app, noventra_worker, noventra_admin;",
                "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO noventra_admin;",
            ],
            reverse_sql=[],
        ),
    ]
