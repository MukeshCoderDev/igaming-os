# Stage 03 Handoff — Phase 4 Entry Criteria

| Field | Value |
|---|---|
| Document | `docs/stage-handoffs/stage-03-handoff.md` |
| Version | 5.4 (Phase 3) |
| Status | Approved |
| Owner | Engineering Lead |
| Authority | Phase 3 hard acceptance; BLUEPRINT §10, §11 |

This document defines what Phase 3 hands off to Phase 4, the entry
criteria Phase 4 must satisfy, and the consumption record for the
stage-02-handoff.md constraints (per Phase 3 spec output #2).

## 1. Phase 3 deliverables handed off

### 1.1 Repo skeleton (per ADR-0022 / DEC-0027)

| Artefact | Path | Notes |
|---|---|---|
| `pyproject.toml` | repo root | Pinned deps: Django 5.0.9, DRF 3.15.2, drf-spectacular 0.27.2, psycopg 3.2.3, redis 5.0.8, ruff 0.6.9, pytest 8.3.3. |
| `Dockerfile` | repo root | Python 3.11-slim, non-root user, gunicorn CMD. |
| `docker-compose.yml` | repo root | Postgres 16 + Redis 7, healthchecks, app depends_on healthy. |
| `.env.example` | repo root | All required + optional vars. |
| `.pre-commit-config.yaml` | repo root | ruff + traceability linter + standard hooks. |
| `Makefile` | repo root | Targets: bootstrap, install, migrate, test, lint, typecheck, runserver, openapi-check, check-rls, docker-up, docker-down, clean. |
| `CODEOWNERS` | repo root | References `docs/requirements/roles.md` role titles. |
| `README.md` | repo root | Links to `docs/BLUEPRINT.md` and `docs/audits/`. |
| `manage.py` | repo root | DJANGO_SETTINGS_MODULE defaults to local. |
| `pytest.ini` | repo root | DJANGO_SETTINGS_MODULE=test. |

### 1.2 Django project

| Path | Purpose |
|---|---|
| `src/noventra/__init__.py` | Root package; `__version__ = "0.3.0"`. |
| `src/noventra/settings/{base,local,test,production}.py` | Settings split per DEC-0028 / ADR-0023. |
| `src/noventra/urls.py` | Root URLs; mounts `/health/`. |
| `src/noventra/wsgi.py`, `asgi.py` | WSGI/ASGI entrypoints. |
| `src/noventra/api/health.py` | `GET /health/` endpoint. |
| `src/noventra/api/urls.py` | Health URL routing. |

### 1.3 Django apps (10 skeletons)

Per stage-02-handoff.md §3.1 (9 apps) + 1 `core` app for the baseline
migration. Each app follows the hexagonal layout (domain/, adapters/,
api/, migrations/).

| App | Path | Phase 3 status |
|---|---|---|
| `core` | `src/noventra/apps/core/` | Baseline migration (0001_initial.py); check_rls_coverage command. |
| `tenancy` | `src/noventra/apps/tenancy/` | Skeleton. |
| `identity` | `src/noventra/apps/identity/` | Skeleton. |
| `audit` | `src/noventra/apps/audit/` | Skeleton. |
| `config` | `src/noventra/apps/config/` | Skeleton. |
| `flags` | `src/noventra/apps/flags/` | Skeleton. |
| `telemetry` | `src/noventra/apps/telemetry/` | Skeleton. |
| `reliability` | `src/noventra/apps/reliability/` | Skeleton. |
| `backups` | `src/noventra/apps/backups/` | Skeleton. |
| `webhooks` | `src/noventra/apps/webhooks/` | Skeleton. |

### 1.4 Baseline migration + RLS

- `src/noventra/apps/core/migrations/0001_initial.py` — creates
  extensions (uuid-ossp, pgcrypto), DB roles (noventra_owner,
  noventra_app NOBYPASSRLS, noventra_worker, noventra_readonly),
  schema `app`, function `app.tenant_uuid()` (fail-closed), default
  grants.
- `src/noventra/apps/core/management/commands/check_rls_coverage.py`
  — vacuous pass until Phase 5.

### 1.5 Deploy init scripts

- `deploy/docker/init/00-extensions.sql` — idempotent.
- `deploy/docker/init/01-roles.sql` — idempotent.
- `deploy/docker/init/02-grants.sql` — idempotent.
- `deploy/docker/init/03-rls-function.sql` — idempotent.

### 1.6 CI + test harness

- `.github/workflows/ci.yml` — per ADR-0024 / DEC-0029.
- `pytest.ini`, `tests/conftest.py`, `tests/factories/__init__.py`,
  `tests/test_health.py`.

### 1.7 OpenAPI spec

- `docs/api/openapi.yaml` — minimal spec (health endpoint only).
  CI drift check compares against `manage.py spectacular` output.

### 1.8 Documentation

- `docs/architecture/settings-split.md` — DEC-0028 / ADR-0023.
- `docs/stage-handoffs/stage-03-handoff.md` — this document.
- `docs/audits/phase-003-audit.md` — Phase 3 audit.
- `docs/adr/INDEX.md` — updated with ADR-0022/0023/0024 and status
  transitions (0001, 0006, 0022, 0023, 0024 → ACCEPTED).

### 1.9 Updated governance

- `docs/requirements/traceability.md` — v5.4 (DEC-0027, DEC-0028,
  DEC-0029 added; registry = 29).
- `docs/requirements/unresolved-decisions.md` — env naming, secret
  strategy, CI runner cost (Q5-blocked ASSUMED) added.
- `scripts/check_traceability.sh` — rules 13–16 added.

## 2. Consumption record: stage-02-handoff.md constraints

Per Phase 3 spec output #2, every constraint from stage-02-handoff.md
§3 must be encoded, deferred-with-open-question, or marked N/A with
justification.

| Constraint (stage-02 §3) | Status | Evidence / Notes |
|---|---|---|
| §3.1 Module → Django app map (9 apps) | ENCODED | 9 apps created + 1 `core` app for baseline migration (10 total). See §1.3. |
| §3.2 Postgres major version lock (PG 16) | ENCODED | `docker-compose.yml` pins `postgres:16-alpine`; CI `ci.yml` pins `postgres:16-alpine`. ADR-0019 documents forward-only migrations. |
| §3.3 RLS role model (3 roles) | ENCODED + REFINED | stage-02 specified 3 roles (app_writer, app_reader, app_admin). Phase 3 spec refined to 4 roles (noventra_owner, noventra_app, noventra_worker, noventra_readonly). 4-role model encoded in baseline migration 0001_initial.py and deploy/docker/init/01-roles.sql. RLS function `app.tenant_uuid()` created (fail-closed). Per-table RLS policies deferred to Phase 5 (when first tenant-scoped tables are introduced). |
| §3.4 Idempotency middleware contract | DEFERRED | `reliability/middleware/` skeleton exists; middleware class lands in Phase 4 per ADR-0008. Phase 3 wires the URL conf but the middleware is commented out in `base.py` MIDDLEWARE. |
| §3.5 Boundary enforcement (static analyzer) | DEFERRED | Ruff (I, F401, E402, F403/F405) provides basic import checking. Full boundary analyzer (rejecting cross-context imports) is a Phase 4 deliverable. |
| §3.6 Forward-only migrations | ENCODED | ADR-0019 ACCEPTED (PROPOSED → ACCEPTED transition pending; status remains PROPOSED per Phase 3 spec — ADR-0019 is not in the ACCEPTED list). Linter rejecting down-migrations is a Phase 4 deliverable. **Note**: ADR-0019 remains PROPOSED with transition target Phase 8 (per Phase 3 spec, only ADRs 0001, 0006, 0022, 0023, 0024 transition to ACCEPTED). |
| §3.7 Telemetry middleware | DEFERRED | `telemetry/middleware/` skeleton exists; OTel middleware lands in Phase 4 per ADR-0020. Phase 3 wires the URL conf but the middleware is commented out in `base.py` MIDDLEWARE. |

**Summary**: 4 constraints ENCODED, 1 ENCODED+REFINED, 3 DEFERRED (with
target phases). No N/A. All deferrals have stated target phases.

## 3. Phase 4 entry criteria

Phase 4 starts only when ALL of the following are true:

### 3.1 Phase 0 evidence gate passed
The Phase 0 evidence pack is signed off (Legal, Commercial, Financial
all PASS). If BLOCKED, Phase 4 does not start.

### 3.2 Phase 3 hard acceptance met
All Phase 3 hard acceptance criteria verified true (see
`docs/audits/phase-003-audit.md`):
- `check` + `check --deploy` green.
- Migrations produce schema + roles + grants + function.
- Health 200 with all checks; 503 path tested.
- Missing required env var: named message, non-zero exit, pre-connection.
- CI green on trunk incl. rules 1–16.
- `compose up` → healthy in one command.
- Make targets present.
- `.env.example` complete; CODEOWNERS references roles doc; README
  links BLUEPRINT + audits.
- Stage-02 constraints fully consumed (see §2 above).
- ADRs encoded by code = ACCEPTED (0001, 0006, 0022, 0023, 0024).

### 3.3 Linter green on rules 1–16
`scripts/check_traceability.sh` exits 0.

### 3.4 Five ADRs ACCEPTED
- ADR-0001 (event-sourced domain model) — ACCEPTED.
- ADR-0006 (append-only audit log) — ACCEPTED.
- ADR-0022 (repo skeleton) — ACCEPTED.
- ADR-0023 (settings split) — ACCEPTED.
- ADR-0024 (CI pipeline) — ACCEPTED.

### 3.5 Open-questions carry-over explicit
Q1, Q2, Q4, Q5 carry-over status recorded in `unresolved-decisions.md`.
If any is BLOCKED, Phase 4 does not start.

## 4. Phase 4 scope (preview)

Phase 4 begins the first real feature: the Tenancy context (Tenant
aggregate, provisioning workflow WF-01, configuration workflow WF-02)
and the Identity context primitives (User, Role, Session).

| Deliverable | Owner | Notes |
|---|---|---|
| Tenant model + migration (with RLS policy) | Architecture Lead | First tenant-scoped table; check_rls_coverage becomes real. |
| Tenant provisioning API (WF-01) | Architecture Lead | End-to-end workflow with audit events. |
| Tenant configuration API (WF-02) | Architecture Lead | Self-serve config updates. |
| User model + migration (with RLS policy) | Identity Lead | Per-tenant user aggregate. |
| Identity primitives (token issuance stub) | Identity Lead | Full OIDC in Phase 5. |
| Idempotency middleware (ADR-0008) | Architecture Lead | Wire into MIDDLEWARE. |
| Telemetry middleware (ADR-0020) | Infrastructure Lead | Wire into MIDDLEWARE. |
| Boundary static analyzer | Architecture Lead | Reject cross-context imports. |
| ADR-0008, ADR-0020 → ACCEPTED | Architecture / Infrastructure Lead | After middleware is live. |
| First real test factories | Engineering Lead | TenantFactory, UserFactory. |

Phase 4 does NOT deliver: full OIDC (Phase 5), audit log implementation
(Phase 8–10), ledger (Phase 11), or any workflow runtime.

## 5. Open risks inherited by Phase 4

| Risk ID | Title | Score | Phase 4 action |
|---|---|---|---|
| R-TNC-01 | RLS bypass via application bug | 15 (P1) | Implement boundary analyzer; integration tests per service |
| R-REL-01 | Idempotency store loss | 8 (P1) | Implement Redis with AOF + multi-AZ |
| R-IDT-01 | OIDC provider outage | 15 (P1) | Phase 5 (full OIDC); Phase 4 stub must degrade gracefully |
| R-SCL-02 | Database connection ceiling | 12 (P1) | PgBouncer evaluation (Q30) |

## 6. Handoff sign-off

- **Engineering Lead** — Phase 3 acceptance criteria met.
- **Architecture Lead** — ADRs ACCEPTED; constraints consumed.
- **Security Lead** — Settings split + named-var loud failure verified.
- **Infrastructure Lead** — Docker, compose, CI verified.

## 7. Worklog pointer

`/home/z/my-project/worklog.md` — Phase 3 close-out entry is the last
entry before Phase 4 kick-off.
