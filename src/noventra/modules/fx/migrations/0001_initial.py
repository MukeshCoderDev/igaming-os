"""FX migration — Phase 11 Stage B. Per ADR-0064 / DEC-0070."""
from django.db import migrations

class Migration(migrations.Migration):
    initial = True
    dependencies = [("ledger", "0001_initial")]
    operations = [
        migrations.RunSQL(sql=[
            "CREATE TABLE fx_rate_snapshot (snapshot_uuid UUID PRIMARY KEY, tenant_uuid UUID, source VARCHAR(20) NOT NULL, base_currency CHAR(3) NOT NULL, quote_currency CHAR(3) NOT NULL, rate_minor BIGINT NOT NULL, rate_exponent SMALLINT NOT NULL, bid_minor BIGINT, ask_minor BIGINT, captured_at TIMESTAMPTZ NOT NULL, created_at TIMESTAMPTZ DEFAULT NOW());",
            "ALTER TABLE fx_rate_snapshot ENABLE ROW LEVEL SECURITY; ALTER TABLE fx_rate_snapshot FORCE ROW LEVEL SECURITY;",
            "CREATE POLICY fx_rate_snapshot_rls ON fx_rate_snapshot FOR ALL TO noventra_app, noventra_worker USING (tenant_uuid IS NULL OR tenant_uuid = app.tenant_uuid()) WITH CHECK (tenant_uuid IS NULL OR tenant_uuid = app.tenant_uuid());",
            "CREATE TRIGGER fx_rs_no_update BEFORE UPDATE ON fx_rate_snapshot FOR EACH ROW EXECUTE FUNCTION ledger_enforce_insert_only();",
            "CREATE TRIGGER fx_rs_no_delete BEFORE DELETE ON fx_rate_snapshot FOR EACH ROW EXECUTE FUNCTION ledger_enforce_insert_only();",
            "GRANT INSERT, SELECT ON fx_rate_snapshot TO noventra_app, noventra_worker;",
            "GRANT SELECT, INSERT, UPDATE, DELETE ON fx_rate_snapshot TO noventra_admin;",
        ], reverse_sql=[])
    ]
