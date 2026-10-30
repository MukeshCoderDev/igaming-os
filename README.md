# Noventra — B2B OS Provider Platform

**Phase 3 — Repository & Bootstrap** (Increment 1 — Governed Foundation)

This is the Phase 3 skeleton of the Noventra platform. It is the first
phase to contain application code. See `docs/BLUEPRINT.md` for the full
architecture and `docs/audits/` for phase-by-phase audit reports.

## Quick start

```bash
# 1. Copy .env.example to .env and fill in required vars.
cp .env.example .env
# Edit .env: set SECRET_KEY, DATABASE_URL, REDIS_URL.

# 2. Bootstrap: install deps + migrate DB.
make bootstrap

# 3. (Optional) Start docker-compose for Postgres + Redis.
docker compose up -d postgres redis

# 4. Run the dev server.
make runserver

# 5. Health check.
curl http://localhost:8000/health/
# → {"status":"healthy","version":"0.3.0","checks":{"db":true,"redis":true,"migrations_applied":true}}
```

## Make targets

| Target | Description |
|---|---|
| `make bootstrap` | Install deps + migrate DB (full setup). |
| `make install` | Install Python deps (editable, with dev extras). |
| `make migrate` | Apply database migrations. |
| `make test` | Run pytest suite. |
| `make lint` | Run ruff linter. |
| `make typecheck` | Run type checker (Phase 4+). |
| `make runserver` | Run Django dev server. |
| `make openapi-check` | Check OpenAPI spec drift. |
| `make check-rls` | Check RLS coverage (Phase 3: vacuous pass). |
| `make docker-up` | Start docker-compose stack. |
| `make docker-down` | Stop docker-compose stack. |

## Required environment variables

Per DEC-0028 / ADR-0023, the following env vars are **required** and
validated at settings import time. Missing any → named message + `sys.exit(1)`
before any DB/network call.

- `SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`

See `.env.example` for the full list (including optional vars) and
`docs/architecture/settings-split.md` for the complete settings-split
documentation.

## Architecture overview

- **Blueprint**: [`docs/BLUEPRINT.md`](docs/BLUEPRINT.md) — master authority.
- **ADRs**: [`docs/adr/INDEX.md`](docs/adr/INDEX.md) — 24 ADRs (5 ACCEPTED,
  19 PROPOSED).
- **Requirements**: [`docs/requirements/traceability.md`](docs/requirements/traceability.md)
  — 62 REQs + 29 DECs.
- **Architecture**: [`docs/architecture/`](docs/architecture/) — security,
  NFR allocation, capacity, data classification, risk register.
- **Audits**: [`docs/audits/`](docs/audits/) — phase-by-phase audit reports.

## Phase 3 status

- ✅ Repo skeleton (src-layout, pinned deps, Docker, compose).
- ✅ Settings split (base/local/test/production; named-var loud failure).
- ✅ Health endpoint (`GET /health/`).
- ✅ Baseline migrations (extensions, DB roles, RLS function).
- ✅ CI workflow (linter 1–16, ruff, check, migrate, pytest, OpenAPI drift).
- ✅ Test harness (pytest, conftest, factories stub).
- ✅ 5 ADRs ACCEPTED (0001, 0006, 0022, 0023, 0024); 19 PROPOSED.

See `docs/audits/phase-003-audit.md` for the full Phase 3 audit.

## License

Proprietary. See `pyproject.toml`.
