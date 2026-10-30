# Stage 05 Handoff — Phase 6 Entry Criteria

| Field | Value |
|---|---|
| Document | `docs/stage-handoffs/stage-05-handoff.md` |
| Version | 5.6 (Phase 5) |
| Status | Approved |
| Owner | Engineering Lead |
| Authority | Phase 5 hard acceptance; BLUEPRINT §10, §11 |

This document defines what Phase 5 hands off to Phase 6, the entry
criteria Phase 6 must satisfy, and the contracts Phase 6 must honor.

## 1. Phase 5 deliverables handed off

### 1.1 ADRs (3 ACCEPTED in Phase 5)

| ADR | Title | Status | Approver |
|---|---|---|---|
| ADR-0002 | Adopt hexagonal architecture (ports and adapters) | ACCEPTED | Architecture Lead + Engineering Lead |
| ADR-0029 | Tenant resolution (JWT claim primary + X-Tenant-ID fallback) | ACCEPTED | Architecture Lead + Security Lead + API Lead |
| ADR-0030 | pgbouncer compatibility (transaction-mode; SET LOCAL only) | ACCEPTED | Infrastructure Lead + Architecture Lead + Reliability Lead |

### 1.2 Tenancy data model

| Path | Purpose |
|---|---|
| `src/noventra/apps/tenancy/domain/aggregates.py` | Tenant (Operator) + Brand aggregates; TenantStatus enum. |
| `src/noventra/apps/tenancy/domain/commands.py` | CreateTenantCommand, SuspendTenantCommand, CreateBrandCommand. |
| `src/noventra/apps/tenancy/domain/events.py` | TenantCreatedEvent, TenantSuspendedEvent, BrandCreatedEvent. |
| `src/noventra/apps/tenancy/domain/ports.py` | TenantRepository port (interface). |
| `src/noventra/apps/tenancy/adapters/orm.py` | Django ORM models: Tenant, Brand. |
| `src/noventra/apps/tenancy/migrations/0001_initial.py` | Tables + RLS policies + FORCE RLS + noventra_admin role + baseline dev data. |

### 1.3 Middleware

| Path | Purpose |
|---|---|
| `src/noventra/middleware/tenant.py` | TenantResolutionMiddleware: JWT claim primary, X-Tenant-ID fallback, 400 on missing/malformed, SET LOCAL app.tenant_uuid, contextvar. |

Wired into `settings/base.py` MIDDLEWARE after CorrelationIdMiddleware.

### 1.4 pgbouncer

| Path | Purpose |
|---|---|
| `docker-compose.yml` (updated) | pgbouncer service (transaction-mode, port 6432). |
| `docs/architecture/pgbouncer-compatibility.md` | Constraints: SET LOCAL only, no session cursors, ATOMIC_REQUESTS, prepare_threshold=None. |
| `settings/base.py` (updated) | ATOMIC_REQUESTS=True, prepare_threshold=None. |

### 1.5 RLS + break-glass

| Path | Purpose |
|---|---|
| `src/noventra/apps/core/management/commands/check_rls_coverage.py` | Non-vacuous: scans all tenant-scoped tables, verifies RLS enabled + forced + policy with USING + WITH CHECK. |
| `docs/architecture/break-glass-admin.md` | noventra_admin (BYPASSRLS) workflow: dual-control, time-bound, heavy audit. |

### 1.6 Tests

| Path | Tests |
|---|---|
| `tests/test_tenancy_rls.py` | Cross-tenant read (zero rows), cross-tenant write (403/RLS violation), middleware 400 on missing/malformed, exempt paths, lifecycle (create/suspend), break-glass role. |
| `tests/test_pgbouncer.py` | Read, write, rollback, SET LOCAL no-leak between transactions. |

### 1.7 Linter extended

`scripts/check_traceability.sh` now enforces rules 1–28 (Phase 5
added rules 24–28). All green.

## 2. Contracts Phase 6 must honor

### 2.1 RLS contract

- Every new tenant-scoped table MUST have:
  - `tenant_uuid` column (UUID, NOT NULL).
  - `ALTER TABLE ... ENABLE ROW LEVEL SECURITY;`
  - `ALTER TABLE ... FORCE ROW LEVEL SECURITY;`
  - `CREATE POLICY ... USING (tenant_uuid = app.tenant_uuid()) WITH CHECK (tenant_uuid = app.tenant_uuid());`
- `check_rls_coverage` runs in CI (rule 24) and fails the build if any table is missing RLS.
- Global tables (no tenant_uuid) must be added to `GLOBAL_ALLOWLIST` in the command.

### 2.2 Tenant resolution contract

- Every new API endpoint MUST work with `TenantResolutionMiddleware`.
- Endpoints that don't need tenant context must be added to `EXEMPT_PATHS` in `tenant.py`.
- The tenant_uuid is available via `get_tenant_uuid()` from `noventra.middleware.tenant`.
- Never read tenant identity from request.GET or request.POST; always use the middleware.

### 2.3 pgbouncer contract

- Use `SET LOCAL` only (never bare `SET`).
- Use `with transaction.atomic():` for multi-statement transactions.
- No session cursors; use Django ORM iterator() or Paginator.
- No LISTEN/NOTIFY; use Redis pub/sub or Celery.
- No session-level advisory locks; use `pg_advisory_xact_lock` within atomic blocks.

### 2.4 Phase 4 contracts (still in force)

- Error format: `problem_response()` for all error responses.
- Logging: `get_logger()` from observability; redaction at boundary.
- Correlation-ID: `CorrelationIdMiddleware` runs before tenant middleware.
- mypy strict: new modules added to `[[tool.mypy.overrides]]`.
- Coverage: diff ≥80%; baseline locked.

## 3. Phase 6 entry criteria

Phase 6 starts only when ALL of the following are true:

### 3.1 Phase 0 evidence gate passed
Q1, Q2, Q4, Q5 resolved or formally BLOCKED.

### 3.2 Phase 5 hard acceptance met
- Migrations produce schema + RLS + baseline.
- Middleware 400s before DB on missing/malformed tenant.
- Cross-tenant read = zero rows; write = 403/RLS violation.
- pgbouncer test passes against local compose instance.
- check_rls_coverage green (rule 24).
- ADR-0002/0029/0030 ACCEPTED.
- Phase 4 contracts honored; coverage ≥60%.
- Rules 1–28 green.

### 3.3 Linter green on rules 1–28

### 3.4 Open-questions carry-over explicit
Q1, Q2, Q4, Q5 carry-over recorded. Q41 (pgbouncer vs pgcat — resolved
pgbouncer), Q42 (break-glass approval tool) added.

## 4. Phase 6 scope (preview)

Phase 6 begins the Identity context: User model + migration with RLS,
OIDC token issuance/verification, role assignment, session management.

| Deliverable | Owner |
|---|---|
| User model + migration (with RLS policy) | Identity Lead |
| OIDC token issuance stub (full in Phase 7) | Identity Lead |
| Role assignment API (WF-05) | Identity Lead |
| User invitation API (WF-03) | Identity Lead |
| ADR-0004 (OIDC) → ACCEPTED | Identity Lead |
| ADR-0015 (RBAC) → ACCEPTED | Identity Lead |
| Real test factories (TenantFactory, UserFactory) | Engineering Lead |

## 5. Handoff sign-off

- **Engineering Lead** — Phase 5 acceptance criteria met.
- **Architecture Lead** — 3 ADRs ACCEPTED; RLS contracts documented.
- **Security Lead** — Break-glass workflow + RLS enforcement verified.
- **Infrastructure Lead** — pgbouncer compat verified.

## 6. Worklog pointer

`/home/z/my-project/worklog.md` — Phase 5 close-out entry.
