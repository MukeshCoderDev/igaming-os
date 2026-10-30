-- 00-extensions.sql — idempotent.
-- Runs as superuser when Postgres container first starts.
-- Mirrors the baseline migration in src/noventra/apps/core/migrations/0001_initial.py
-- so that the DB is ready for Django migrations out of the box.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;
