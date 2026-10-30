"""Core app baseline migration — Phase 3.

Per Phase 3 spec output #6, this migration creates:
- Extensions (uuid-ossp, pgcrypto)
- DB roles (noventra_owner, noventra_app NOBYPASSRLS, noventra_worker, noventra_readonly)
- Grants
- Schema `app`
- Function `app.tenant_uuid()` (fail-closed)

This migration is idempotent: every statement uses IF NOT EXISTS or
DO-block guards. It is safe to run on an empty DB or on a DB that
already has the baseline (e.g., from deploy/docker/init/*.sql).

Per-table RLS policies land with the modules that own the tables
(Phase 5+). The check_rls_coverage management command (Phase 3 stub)
verifies coverage; it's a vacuous pass until Phase 5.
"""

from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        # ── Extensions ───────────────────────────────────────────────
        # uuid-ossp: uuid_generate_v4() for default UUIDs.
        # pgcrypto: crypt() for password hashing (if needed by auth).
        migrations.RunSQL(
            sql=[
                'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";',
                'CREATE EXTENSION IF NOT EXISTS pgcrypto;',
            ],
            reverse_sql=[],
        ),
        # ── DB roles ─────────────────────────────────────────────────
        # Per stage-02-handoff.md §3.3 (refined in Phase 3 spec output #6):
        #   noventra_owner    — owner of all objects; can CREATE, GRANT.
        #   noventra_app      — app role for normal requests; NOBYPASSRLS;
        #                       no write to audit log (enforced by grant).
        #   noventra_worker   — background worker role (Celery, etc.).
        #   noventra_readonly — read-only role for analytics.
        #
        # CREATE ROLE IF NOT EXISTS is not standard PG; use DO blocks.
        migrations.RunSQL(
            sql=[
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'noventra_owner') THEN
                        CREATE ROLE noventra_owner NOLOGIN;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'noventra_app') THEN
                        CREATE ROLE noventra_app NOLOGIN NOBYPASSRLS;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'noventra_worker') THEN
                        CREATE ROLE noventra_worker NOLOGIN NOBYPASSRLS;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'noventra_readonly') THEN
                        CREATE ROLE noventra_readonly NOLOGIN;
                    END IF;
                END
                $$;
                """,
            ],
            reverse_sql=[],
        ),
        # ── Schema `app` ─────────────────────────────────────────────
        # The `app` schema holds cross-cutting functions like tenant_uuid().
        migrations.RunSQL(
            sql=["CREATE SCHEMA IF NOT EXISTS app;"],
            reverse_sql=["DROP SCHEMA IF EXISTS app CASCADE;"],
        ),
        # ── Grants on schema `app` ──────────────────────────────────
        migrations.RunSQL(
            sql=[
                "GRANT USAGE ON SCHEMA app TO noventra_app, noventra_worker, noventra_readonly;",
            ],
            reverse_sql=[],
        ),
        # ── Function app.tenant_uuid() — fail-closed ────────────────
        # Returns the current tenant UUID from the session setting
        # `app.tenant_id`. Fail-closed: if the setting is not set, returns
        # NULL, which causes RLS policies using `tenant_id = app.tenant_uuid()`
        # to match no rows (deny-all).
        migrations.RunSQL(
            sql=[
                """
                CREATE OR REPLACE FUNCTION app.tenant_uuid() RETURNS uuid AS $$
                BEGIN
                    RETURN NULLIF(current_setting('app.tenant_id', true), '')::uuid;
                END;
                $$ LANGUAGE plpgsql STABLE;
                """,
            ],
            reverse_sql=["DROP FUNCTION IF EXISTS app.tenant_uuid();"],
        ),
        # ── Grants on function ──────────────────────────────────────
        migrations.RunSQL(
            sql=[
                "GRANT EXECUTE ON FUNCTION app.tenant_uuid() TO noventra_app, noventra_worker, noventra_readonly;",
            ],
            reverse_sql=[],
        ),
        # ── Default grants on public schema ─────────────────────────
        # noventra_owner: all privileges (it owns the objects).
        # noventra_app: SELECT, INSERT, UPDATE, DELETE on tables (RLS applies).
        # noventra_worker: same as app (RLS applies).
        # noventra_readonly: SELECT only.
        # Per-table grants are added as tables are created in later phases;
        # the default privileges here ensure new tables auto-grant correctly.
        migrations.RunSQL(
            sql=[
                """
                ALTER DEFAULT PRIVILEGES FOR ROLE noventra_owner IN SCHEMA public
                    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO noventra_app;
                ALTER DEFAULT PRIVILEGES FOR ROLE noventra_owner IN SCHEMA public
                    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO noventra_worker;
                ALTER DEFAULT PRIVILEGES FOR ROLE noventra_owner IN SCHEMA public
                    GRANT SELECT ON TABLES TO noventra_readonly;
                ALTER DEFAULT PRIVILEGES FOR ROLE noventra_owner IN SCHEMA public
                    GRANT USAGE, SELECT ON SEQUENCES TO noventra_app, noventra_worker;
                """,
            ],
            reverse_sql=[],
        ),
    ]
