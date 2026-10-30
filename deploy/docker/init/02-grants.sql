-- 02-grants.sql — idempotent.
-- Grants base privileges to the four roles. Per-table grants are added
-- by Django migrations as tables are created; the default privileges
-- here ensure new tables auto-grant correctly.

-- Schema `app` holds cross-cutting functions (e.g., tenant_uuid()).
CREATE SCHEMA IF NOT EXISTS app;
GRANT USAGE ON SCHEMA app TO noventra_app, noventra_worker, noventra_readonly;

-- Default privileges: new tables in `public` auto-grant to the roles.
ALTER DEFAULT PRIVILEGES FOR ROLE noventra_owner IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO noventra_app;
ALTER DEFAULT PRIVILEGES FOR ROLE noventra_owner IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO noventra_worker;
ALTER DEFAULT PRIVILEGES FOR ROLE noventra_owner IN SCHEMA public
    GRANT SELECT ON TABLES TO noventra_readonly;
ALTER DEFAULT PRIVILEGES FOR ROLE noventra_owner IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO noventra_app, noventra_worker;

-- The django_migrations table (created by Django) needs to be readable
-- by all roles so the health check can count applied migrations.
-- This is handled by the default privileges above once Django creates
-- the table; no explicit grant needed here.
