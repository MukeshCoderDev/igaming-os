"""Ledger migration — Phase 11 Stage B.

Per ADR-0059..0065 / DEC-0065..0071.
Creates: ledger_account, ledger_journal_entry, ledger_journal_line,
ledger_account_balance, ledger_financial_audit_event, ledger_reconciliation_log.
All tenant-scoped (RLS). All financial tables insert-only (trigger).
"""
from django.db import migrations, models
import uuid

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.RunSQL(sql=[
            "CREATE TABLE ledger_account (account_uuid UUID PRIMARY KEY, tenant_uuid UUID NOT NULL, account_class VARCHAR(16) NOT NULL, currency_code CHAR(3) NOT NULL, status VARCHAR(16) DEFAULT 'active', metadata JSONB DEFAULT '{}', created_at TIMESTAMPTZ DEFAULT NOW(), updated_at TIMESTAMPTZ DEFAULT NOW());",
            "CREATE TABLE ledger_journal_entry (entry_uuid UUID PRIMARY KEY, tenant_uuid UUID NOT NULL, posted_at TIMESTAMPTZ DEFAULT NOW(), journal_type VARCHAR(16) NOT NULL, source_ref UUID, correlation_id UUID NOT NULL, idempotency_key UUID NOT NULL, fx_pair_id UUID, status VARCHAR(8) DEFAULT 'POSTED', prev_hash CHAR(64), hash CHAR(64), created_at TIMESTAMPTZ DEFAULT NOW(), UNIQUE(tenant_uuid, idempotency_key));",
            "CREATE TABLE ledger_journal_line (line_uuid UUID PRIMARY KEY, entry_uuid UUID NOT NULL REFERENCES ledger_journal_entry(entry_uuid), account_uuid UUID NOT NULL REFERENCES ledger_account(account_uuid), tenant_uuid UUID NOT NULL, currency_code CHAR(3) NOT NULL, exponent_at_time SMALLINT NOT NULL, debit_minor BIGINT DEFAULT 0, credit_minor BIGINT DEFAULT 0, created_at TIMESTAMPTZ DEFAULT NOW());",
            "CREATE TABLE ledger_account_balance (account_uuid UUID PRIMARY KEY REFERENCES ledger_account(account_uuid), tenant_uuid UUID NOT NULL, balance_minor BIGINT DEFAULT 0, as_of_entry_uuid UUID REFERENCES ledger_journal_entry(entry_uuid), last_reconciled_at TIMESTAMPTZ, last_reconciled_status VARCHAR(16), updated_at TIMESTAMPTZ DEFAULT NOW());",
            "CREATE TABLE ledger_financial_audit_event (event_uuid UUID NOT NULL, tenant_uuid UUID, actor_id UUID NOT NULL, actor_type VARCHAR(16) NOT NULL, event_type VARCHAR(64) NOT NULL, target_type VARCHAR(64), target_id VARCHAR(128), payload JSONB DEFAULT '{}', prev_hash CHAR(64), hash CHAR(64), correlation_id VARCHAR(64), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (event_uuid, created_at)) PARTITION BY RANGE (created_at);",
            "CREATE TABLE ledger_financial_audit_event_default PARTITION OF ledger_financial_audit_event DEFAULT;",
            "CREATE TABLE ledger_reconciliation_log (log_uuid UUID PRIMARY KEY, tenant_uuid UUID NOT NULL, account_uuid UUID, started_at TIMESTAMPTZ DEFAULT NOW(), completed_at TIMESTAMPTZ, status VARCHAR(16) DEFAULT 'running', mismatched_accounts JSONB, correlation_id UUID NOT NULL);",
            # RLS
            "ALTER TABLE ledger_account ENABLE ROW LEVEL SECURITY; ALTER TABLE ledger_account FORCE ROW LEVEL SECURITY;",
            "ALTER TABLE ledger_journal_entry ENABLE ROW LEVEL SECURITY; ALTER TABLE ledger_journal_entry FORCE ROW LEVEL SECURITY;",
            "ALTER TABLE ledger_journal_line ENABLE ROW LEVEL SECURITY; ALTER TABLE ledger_journal_line FORCE ROW LEVEL SECURITY;",
            "ALTER TABLE ledger_account_balance ENABLE ROW LEVEL SECURITY; ALTER TABLE ledger_account_balance FORCE ROW LEVEL SECURITY;",
            "ALTER TABLE ledger_financial_audit_event ENABLE ROW LEVEL SECURITY; ALTER TABLE ledger_financial_audit_event FORCE ROW LEVEL SECURITY;",
            "ALTER TABLE ledger_reconciliation_log ENABLE ROW LEVEL SECURITY; ALTER TABLE ledger_reconciliation_log FORCE ROW LEVEL SECURITY;",
            # RLS policies
            "CREATE POLICY ledger_account_rls ON ledger_account FOR ALL TO noventra_app, noventra_worker USING (tenant_uuid = app.tenant_uuid()) WITH CHECK (tenant_uuid = app.tenant_uuid());",
            "CREATE POLICY ledger_journal_entry_rls ON ledger_journal_entry FOR ALL TO noventra_app, noventra_worker USING (tenant_uuid = app.tenant_uuid()) WITH CHECK (tenant_uuid = app.tenant_uuid());",
            "CREATE POLICY ledger_journal_line_rls ON ledger_journal_line FOR ALL TO noventra_app, noventra_worker USING (tenant_uuid = app.tenant_uuid()) WITH CHECK (tenant_uuid = app.tenant_uuid());",
            "CREATE POLICY ledger_account_balance_rls ON ledger_account_balance FOR ALL TO noventra_app, noventra_worker USING (tenant_uuid = app.tenant_uuid()) WITH CHECK (tenant_uuid = app.tenant_uuid());",
            "CREATE POLICY ledger_financial_audit_event_rls ON ledger_financial_audit_event FOR ALL TO noventra_app, noventra_worker USING (tenant_uuid IS NULL OR tenant_uuid = app.tenant_uuid()) WITH CHECK (tenant_uuid IS NULL OR tenant_uuid = app.tenant_uuid());",
            "CREATE POLICY ledger_reconciliation_log_rls ON ledger_reconciliation_log FOR ALL TO noventra_app, noventra_worker USING (tenant_uuid = app.tenant_uuid()) WITH CHECK (tenant_uuid = app.tenant_uuid());",
            # Insert-only triggers
            "CREATE OR REPLACE FUNCTION ledger_enforce_insert_only() RETURNS TRIGGER AS $$ BEGIN RAISE EXCEPTION 'ledger table is insert-only'; END; $$ LANGUAGE plpgsql;",
            "CREATE OR REPLACE FUNCTION ledger_financial_audit_event_set_hash() RETURNS TRIGGER AS $$ DECLARE v_prev_hash CHAR(64); v_prev_created_at TIMESTAMPTZ; BEGIN PERFORM pg_advisory_xact_lock(hashtextextended(COALESCE(NEW.tenant_uuid::TEXT, 'global'), 0)); SELECT hash, created_at INTO v_prev_hash, v_prev_created_at FROM ledger_financial_audit_event WHERE tenant_uuid IS NOT DISTINCT FROM NEW.tenant_uuid ORDER BY created_at DESC, event_uuid DESC LIMIT 1; IF v_prev_created_at IS NOT NULL THEN NEW.created_at := GREATEST(COALESCE(NEW.created_at, NOW()), v_prev_created_at + INTERVAL '1 microsecond'); END IF; NEW.prev_hash := v_prev_hash; NEW.hash := encode(digest(COALESCE(NEW.prev_hash, '') || '|' || NEW.event_uuid::TEXT || '|' || COALESCE(NEW.tenant_uuid::TEXT, '') || '|' || NEW.actor_id::TEXT || '|' || NEW.actor_type || '|' || NEW.event_type || '|' || COALESCE(NEW.payload, '{}'::JSONB)::TEXT || '|' || NEW.created_at::TEXT, 'sha256'), 'hex'); RETURN NEW; END; $$ LANGUAGE plpgsql;",
            "CREATE TRIGGER ledger_financial_audit_event_hash BEFORE INSERT ON ledger_financial_audit_event FOR EACH ROW EXECUTE FUNCTION ledger_financial_audit_event_set_hash();",
            "CREATE TRIGGER ledger_je_no_update BEFORE UPDATE ON ledger_journal_entry FOR EACH ROW EXECUTE FUNCTION ledger_enforce_insert_only();",
            "CREATE TRIGGER ledger_je_no_delete BEFORE DELETE ON ledger_journal_entry FOR EACH ROW EXECUTE FUNCTION ledger_enforce_insert_only();",
            "CREATE TRIGGER ledger_jl_no_update BEFORE UPDATE ON ledger_journal_line FOR EACH ROW EXECUTE FUNCTION ledger_enforce_insert_only();",
            "CREATE TRIGGER ledger_jl_no_delete BEFORE DELETE ON ledger_journal_line FOR EACH ROW EXECUTE FUNCTION ledger_enforce_insert_only();",
            "CREATE TRIGGER ledger_fae_no_update BEFORE UPDATE ON ledger_financial_audit_event FOR EACH ROW EXECUTE FUNCTION ledger_enforce_insert_only();",
            "CREATE TRIGGER ledger_fae_no_delete BEFORE DELETE ON ledger_financial_audit_event FOR EACH ROW EXECUTE FUNCTION ledger_enforce_insert_only();",
            # Grants
            "GRANT SELECT, INSERT, UPDATE, DELETE ON ledger_account, ledger_account_balance, ledger_reconciliation_log TO noventra_app, noventra_worker, noventra_admin;",
            "GRANT INSERT, SELECT ON ledger_journal_entry, ledger_journal_line, ledger_financial_audit_event TO noventra_app, noventra_worker;",
            "GRANT SELECT, INSERT, UPDATE, DELETE ON ledger_journal_entry, ledger_journal_line, ledger_financial_audit_event TO noventra_admin;",
        ], reverse_sql=[])
    ]
