"""Payments migration — Phase 12.

Per ADR-0073..0077. Creates: payments_order, payments_dispute, payments_webhook_log.
All tenant-scoped (RLS per Phase 5). No card fields (PCI SAQ-A).
"""

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.RunSQL(sql=[
            # PaymentOrder table
            """
            CREATE TABLE payments_order (
                order_uuid UUID PRIMARY KEY,
                tenant_uuid UUID NOT NULL,
                player_uuid UUID NOT NULL,
                amount_minor BIGINT NOT NULL,
                currency_code CHAR(3) NOT NULL,
                exponent_at_time SMALLINT NOT NULL,
                direction VARCHAR(12) NOT NULL,
                payment_method VARCHAR(32),
                psp_token VARCHAR(255),
                psp_charge_id VARCHAR(255),
                status VARCHAR(20) DEFAULT 'PENDING',
                idempotency_key UUID NOT NULL,
                correlation_id UUID NOT NULL,
                fx_pair_id UUID,
                failure_reason TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(tenant_uuid, idempotency_key)
            );
            """,
            # DisputeCase table
            """
            CREATE TABLE payments_dispute (
                dispute_uuid UUID PRIMARY KEY,
                tenant_uuid UUID NOT NULL,
                order_uuid UUID NOT NULL REFERENCES payments_order(order_uuid),
                psp_dispute_id VARCHAR(255) NOT NULL,
                reason VARCHAR(32) NOT NULL,
                status VARCHAR(20) DEFAULT 'open',
                amount_minor BIGINT NOT NULL,
                currency_code CHAR(3) NOT NULL,
                evidence_pack_uuid UUID,
                deadline_at TIMESTAMPTZ NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            """,
            # WebhookLog table
            """
            CREATE TABLE payments_webhook_log (
                webhook_uuid UUID PRIMARY KEY,
                tenant_uuid UUID NOT NULL,
                psp_name VARCHAR(32) NOT NULL,
                psp_event_id VARCHAR(255) NOT NULL,
                event_type VARCHAR(64) NOT NULL,
                payload JSONB DEFAULT '{}',
                signature_valid BOOLEAN DEFAULT FALSE,
                processed BOOLEAN DEFAULT FALSE,
                response_status INTEGER DEFAULT 200,
                received_at TIMESTAMPTZ DEFAULT NOW(),
                processed_at TIMESTAMPTZ,
                UNIQUE(tenant_uuid, psp_name, psp_event_id)
            );
            """,
            # RLS on all tables
            "ALTER TABLE payments_order ENABLE ROW LEVEL SECURITY;",
            "ALTER TABLE payments_order FORCE ROW LEVEL SECURITY;",
            "ALTER TABLE payments_dispute ENABLE ROW LEVEL SECURITY;",
            "ALTER TABLE payments_dispute FORCE ROW LEVEL SECURITY;",
            "ALTER TABLE payments_webhook_log ENABLE ROW LEVEL SECURITY;",
            "ALTER TABLE payments_webhook_log FORCE ROW LEVEL SECURITY;",
            # RLS policies
            """
            CREATE POLICY payments_order_rls ON payments_order
                FOR ALL TO noventra_app, noventra_worker
                USING (tenant_uuid = app.tenant_uuid())
                WITH CHECK (tenant_uuid = app.tenant_uuid());
            """,
            """
            CREATE POLICY payments_dispute_rls ON payments_dispute
                FOR ALL TO noventra_app, noventra_worker
                USING (tenant_uuid = app.tenant_uuid())
                WITH CHECK (tenant_uuid = app.tenant_uuid());
            """,
            """
            CREATE POLICY payments_webhook_log_rls ON payments_webhook_log
                FOR ALL TO noventra_app, noventra_worker
                USING (tenant_uuid = app.tenant_uuid())
                WITH CHECK (tenant_uuid = app.tenant_uuid());
            """,
            # Grants
            "GRANT SELECT, INSERT, UPDATE, DELETE ON payments_order, payments_dispute, payments_webhook_log TO noventra_app, noventra_worker, noventra_admin;",
        ], reverse_sql=[
            "DROP TABLE IF EXISTS payments_webhook_log CASCADE;",
            "DROP TABLE IF EXISTS payments_dispute CASCADE;",
            "DROP TABLE IF EXISTS payments_order CASCADE;",
        ]),
    ]
