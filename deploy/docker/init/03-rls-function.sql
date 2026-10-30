-- 03-rls-function.sql — idempotent.
-- Creates the fail-closed app.tenant_uuid() function.
--
-- Fail-closed semantics: if `app.tenant_uuid` is not set in the current
-- session, returns NULL. RLS policies using `tenant_id = app.tenant_uuid()`
-- will then match no rows (deny-all). This is the critical isolation
-- invariant per DEC-0003.
--
-- The middleware (Phase 4+) sets `app.tenant_id` per request via
-- `SET LOCAL app.tenant_uuid = '<uuid>'` after authenticating the user.

CREATE OR REPLACE FUNCTION app.tenant_uuid() RETURNS uuid AS $$
BEGIN
    RETURN NULLIF(current_setting('app.tenant_uuid', true), '')::uuid;
END;
$$ LANGUAGE plpgsql STABLE;

GRANT EXECUTE ON FUNCTION app.tenant_uuid() TO noventra_app, noventra_worker, noventra_readonly;
