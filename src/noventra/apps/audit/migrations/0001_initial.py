"""Audit migration — Phase 7.

Per Phase 7 spec output #9: audit_event, audit_chain_head tables +
BEFORE INSERT trigger (hash) + BEFORE UPDATE/DELETE trigger (insert-
only) + baseline partition.

Per ADR-0035: hash-chain (SHA-256, Merkle-style payload).
Per ADR-0036: partitioning by month + tenant.
Per ADR-0038: insert-only enforcement (trigger + GRANT).
"""

from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("tenancy", "0001_initial"),
        ("identity", "0001_initial"),
    ]

    operations = [
        # ── audit_chain_head table (singleton per scope) ─────────────
        migrations.RunSQL(
            sql=[
                """
                CREATE TABLE audit_chain_head (
                    scope VARCHAR(64) PRIMARY KEY,
                    last_event_uuid UUID,
                    last_hash CHAR(64),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """,
                # Global chain head singleton.
                """
                INSERT INTO audit_chain_head (scope, last_event_uuid, last_hash)
                VALUES ('global', NULL, NULL)
                ON CONFLICT (scope) DO NOTHING;
                """,
            ],
            reverse_sql=["DROP TABLE IF EXISTS audit_chain_head;"],
        ),
        # ── audit_event table (partitioned by month) ─────────────────
        # Phase 7: partition by RANGE (created_at). Sub-partitioning by
        # tenant_id LIST is Phase 8 (when tenant count grows).
        migrations.RunSQL(
            sql=[
                """
                CREATE TABLE audit_event (
                    event_uuid UUID NOT NULL,
                    tenant_id UUID,
                    actor_id UUID NOT NULL,
                    actor_type VARCHAR(16) NOT NULL,
                    event_type VARCHAR(64) NOT NULL,
                    target_type VARCHAR(64),
                    target_id VARCHAR(128),
                    payload JSONB NOT NULL DEFAULT '{}',
                    prev_hash CHAR(64),
                    hash CHAR(64),
                    correlation_id VARCHAR(64),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (event_uuid, created_at)
                ) PARTITION BY RANGE (created_at);
                """,
                # Baseline partition for current month (2025-10).
                """
                CREATE TABLE audit_event_2025_10
                    PARTITION OF audit_event
                    FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');
                """,
                # Default partition (catch-all; Phase 8 adds monthly automation).
                """
                CREATE TABLE audit_event_default
                    PARTITION OF audit_event
                    DEFAULT;
                """,
            ],
            reverse_sql=[
                "DROP TABLE IF EXISTS audit_event CASCADE;",
            ],
        ),
        # ── Hash-chain computation function (BEFORE INSERT) ──────────
        # Per ADR-0035: Merkle-style payload hashing + SHA-256 chain.
        migrations.RunSQL(
            sql=[
                """
                CREATE OR REPLACE FUNCTION audit_compute_hash()
                RETURNS TRIGGER AS $$
                DECLARE
                    v_scope TEXT;
                    v_prev_hash CHAR(64);
                    v_chain_head RECORD;
                    v_merkle_root CHAR(64);
                    v_field_key TEXT;
                    v_field_hash CHAR(64);
                    v_field_hashes TEXT := '';
                BEGIN
                    -- Determine chain scope: per-tenant for tenant-scoped events, global otherwise.
                    IF NEW.tenant_id IS NOT NULL THEN
                        v_scope := NEW.tenant_id::TEXT;
                    ELSE
                        v_scope := 'global';
                    END IF;

                    -- Lock the chain head row for this scope (pgbouncer-compatible: short transaction).
                    SELECT * INTO v_chain_head
                        FROM audit_chain_head
                        WHERE scope = v_scope
                        FOR UPDATE;

                    -- If no chain head exists for this scope, create one.
                    IF v_chain_head.scope IS NULL THEN
                        INSERT INTO audit_chain_head (scope, last_event_uuid, last_hash)
                        VALUES (v_scope, NULL, NULL)
                        ON CONFLICT (scope) DO NOTHING;
                        v_prev_hash := NULL;
                    ELSE
                        v_prev_hash := v_chain_head.last_hash;
                    END IF;

                    NEW.prev_hash := v_prev_hash;

                    -- Merkle-style payload hashing: hash each field individually.
                    -- v_field_hashes is the concatenation of all field hashes in canonical order.
                    FOR v_field_key IN SELECT jsonb_object_keys(NEW.payload) ORDER BY v_field_key LOOP
                        v_field_hash := encode(
                            digest(
                                v_field_key || '=' || COALESCE(NEW.payload->>v_field_key, ''),
                                'sha256'
                            ),
                            'hex'
                        );
                        v_field_hashes := v_field_hashes || v_field_hash;
                    END LOOP;

                    -- Merkle root = SHA256(concatenation of all field hashes).
                    v_merkle_root := encode(digest(v_field_hashes, 'sha256'), 'hex');

                    -- Chain hash = SHA256(prev_hash || merkle_root || event_meta).
                    NEW.hash := encode(
                        digest(
                            COALESCE(v_prev_hash, '') || '|' ||
                            v_merkle_root || '|' ||
                            NEW.event_type || '|' ||
                            NEW.actor_id::TEXT || '|' ||
                            COALESCE(NEW.tenant_id::TEXT, '') || '|' ||
                            EXTRACT(EPOCH FROM NEW.created_at)::TEXT,
                            'sha256'
                        ),
                        'hex'
                    );

                    -- Update chain head.
                    UPDATE audit_chain_head
                    SET last_event_uuid = NEW.event_uuid,
                        last_hash = NEW.hash,
                        updated_at = NOW()
                    WHERE scope = v_scope;

                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                """,
            ],
            reverse_sql=["DROP FUNCTION IF EXISTS audit_compute_hash();"],
        ),
        # ── BEFORE INSERT trigger ────────────────────────────────────
        migrations.RunSQL(
            sql=[
                """
                CREATE TRIGGER audit_event_before_insert
                    BEFORE INSERT ON audit_event
                    FOR EACH ROW
                    EXECUTE FUNCTION audit_compute_hash();
                """,
            ],
            reverse_sql=["DROP TRIGGER IF EXISTS audit_event_before_insert ON audit_event;"],
        ),
        # ── Insert-only enforcement (BEFORE UPDATE OR DELETE) ────────
        # Per ADR-0038: raises exception for ALL roles including owner.
        migrations.RunSQL(
            sql=[
                """
                CREATE OR REPLACE FUNCTION audit_enforce_insert_only()
                RETURNS TRIGGER AS $$
                BEGIN
                    RAISE EXCEPTION 'audit_event is insert-only (DEC-0006 / ADR-0038). UPDATE and DELETE are forbidden for all roles.';
                END;
                $$ LANGUAGE plpgsql;
                """,
                """
                CREATE TRIGGER audit_event_no_update
                    BEFORE UPDATE ON audit_event
                    FOR EACH ROW
                    EXECUTE FUNCTION audit_enforce_insert_only();
                """,
                """
                CREATE TRIGGER audit_event_no_delete
                    BEFORE DELETE ON audit_event
                    FOR EACH ROW
                    EXECUTE FUNCTION audit_enforce_insert_only();
                """,
            ],
            reverse_sql=[
                "DROP TRIGGER IF EXISTS audit_event_no_delete ON audit_event;",
                "DROP TRIGGER IF EXISTS audit_event_no_update ON audit_event;",
                "DROP FUNCTION IF EXISTS audit_enforce_insert_only();",
            ],
        ),
        # ── Grants: INSERT + SELECT only to noventra_app ─────────────
        # Per ADR-0038: no UPDATE/DELETE privilege.
        migrations.RunSQL(
            sql=[
                "GRANT INSERT, SELECT ON audit_event TO noventra_app, noventra_worker;",
                "GRANT SELECT ON audit_event TO noventra_readonly;",
                "GRANT INSERT, SELECT, UPDATE ON audit_chain_head TO noventra_app, noventra_worker;",
                "GRANT SELECT ON audit_chain_head TO noventra_readonly;",
                "GRANT INSERT, SELECT, UPDATE, DELETE ON audit_event, audit_chain_head TO noventra_admin;",
            ],
            reverse_sql=[],
        ),
        # ── Enable RLS on audit_event (tenant-scoped reads) ──────────
        # Per DEC-0003: tenant-scoped tables have RLS. audit_event has
        # tenant_id (NULL for global). Policy: visible if tenant_id IS
        # NULL (global) OR tenant_id = app.tenant_uuid().
        migrations.RunSQL(
            sql=[
                "ALTER TABLE audit_event ENABLE ROW LEVEL SECURITY;",
                "ALTER TABLE audit_event FORCE ROW LEVEL SECURITY;",
                """
                CREATE POLICY audit_event_rls ON audit_event
                    FOR ALL TO noventra_app, noventra_worker
                    USING (tenant_id IS NULL OR tenant_id = app.tenant_uuid())
                    WITH CHECK (tenant_id IS NULL OR tenant_id = app.tenant_uuid());
                """,
            ],
            reverse_sql=[
                "DROP POLICY IF EXISTS audit_event_rls ON audit_event;",
                "ALTER TABLE audit_event NO FORCE ROW LEVEL SECURITY;",
                "ALTER TABLE audit_event DISABLE ROW LEVEL SECURITY;",
            ],
        ),
    ]
