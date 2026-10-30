-- 01-roles.sql — idempotent.
-- Creates the four DB roles per stage-02-handoff.md §3.3 (refined in
-- Phase 3 spec output #6). NOLOGIN roles; the Django app connects via
-- a LOGIN role that is a member of noventra_app (created by docker-compose
-- env vars POSTGRES_USER).

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'noventra_owner') THEN
        CREATE ROLE noventra_owner NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'noventra_app') THEN
        -- NOBYPASSRLS: this role cannot bypass RLS policies. Critical for
        -- tenant isolation (DEC-0003).
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

-- Grant noventra_app to the POSTGRES_USER login role (created by docker-compose).
-- This lets the Django app inherit noventra_app's RLS-scoped privileges.
-- In dev, POSTGRES_USER=noventra_dev; in prod, a separate provisioned login.
DO $$
DECLARE
    login_role text := current_setting('POSTGRES_USER', true);
BEGIN
    IF login_role IS NOT NULL AND login_role <> '' THEN
        EXECUTE format('GRANT noventra_app TO %I', login_role);
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        -- POSTGRES_USER may not be set; skip silently.
        NULL;
END
$$;
