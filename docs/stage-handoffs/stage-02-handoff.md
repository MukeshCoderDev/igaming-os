# Stage 02 Handoff — Phase 3 Entry Criteria

| Field | Value |
|---|---|
| Document | `docs/stage-handoffs/stage-02-handoff.md` |
| Version | 5.3 (Phase 2) |
| Status | Approved |
| Owner | Engineering Lead |
| Authority | BLUEPRINT §10, §11; Phase 2 hard acceptance |

This document defines what Phase 2 hands off to Phase 3, the entry
criteria Phase 3 must satisfy before it can start, and the
constraints Phase 3 must encode structurally (module → Django app
map, Postgres major version lock, RLS role model, etc.). Phase 3
does not start until (a) all entry criteria are met, (b) the Phase 0
evidence pack has been signed off per `phase-0-evidence.md`, and (c)
the linter (rules 1–12) is green.

## 1. Phase 2 deliverables handed off

Phase 2 produces architecture artefacts (no application code). The
handed-off set is:

### 1.1 Architecture documents (six new files per DEC-0025)

| Artefact | Path | Purpose |
|---|---|---|
| ADR INDEX | `docs/adr/INDEX.md` | ADR status table; ADR↔DEC consistency; component view (03-view) |
| Security architecture | `docs/architecture/security.md` | STRIDE threat model across 5 surfaces (30 stub findings) |
| NFR allocation | `docs/architecture/nfr-allocation.md` | Every NFR → ≥1 mechanism (24 NFRs mapped) |
| Capacity assumptions | `docs/architecture/capacity-assumptions.md` | Capacity table; 20 rows; ≥1 per pillar |
| Data classification | `docs/architecture/data-classification.md` | PII register; 15 elements; GDPR Art.30 |
| Risk register | `docs/architecture/risk-register.md` | Architectural risks; ≥1 per pillar + vendor + SPOF + scaling |

### 1.2 ADR stubs upgraded (21 files)

All 21 ADR stubs (`docs/adr/ADR-0001.md` through `ADR-0021.md`)
are upgraded to Nygard format (DEC-0026) with status `PROPOSED`.
Each stub now carries full front-matter (`ADR`, `Title`, `Status`,
`DEC`, `Owner`, `Created`, `Last-Reviewed`, `Supersedes`,
`Superseded-By`) and five body sections (`Context`, `Decision`,
`Alternatives`, `Consequences`, `Validation Plan`).

### 1.3 Errata verification

`docs/errata/v5.2.1-verification.md` records the verification of
errata E1–E7 with blueprint line references, commit hashes, and
reviewer sign-offs. `BLUEPRINT.md` remains byte-frozen.

### 1.4 Audits

`docs/audits/phase-001-audit.md` and
`docs/audits/phase-002-audit.md` record the Phase 1 and Phase 2
audit findings with dispositions.

### 1.5 Updated governance documents

| Document | Update |
|---|---|
| `docs/requirements/traceability.md` | v5.3 — DEC-0025, DEC-0026 added (registry = 26); DEC-0021 narrative reviewed |
| `docs/requirements/unresolved-decisions.md` | Q1/Q2/Q4/Q5 carry-over explicit; architectural Qs added |
| `scripts/check_traceability.sh` | Rules 8–12 added; same tool, no fork |

### 1.6 What is NOT handed off

- Application code (Django models, DRF serializers, services,
  migrations). Phase 3 begins repo scaffold.
- CI pipeline configuration. Phase 3 deliverable.
- Static analyzer implementation (Phase 2 defines the rules; Phase 3
  implements).
- Test suite. Phase 3 begins test scaffolding.
- Runbooks for production operation. Phase 3+ deliverable.

## 2. Phase 3 entry criteria

Phase 3 starts only when ALL of the following are true. The
Engineering Lead is Accountable for verifying each criterion.

### 2.1 Phase 0 evidence gate passed

The Phase 0 evidence pack (`phase-0-evidence.md`) is signed off,
with all three gates (Legal, Commercial, Financial) marked PASS.
If any gate is BLOCKED, Phase 3 does not start. There are no
exceptions. See BLUEPRINT §10 and `unresolved-decisions.md` §4.

### 2.2 Phase 2 hard acceptance met

All Phase 2 hard acceptance criteria are verified true:

- [ ] Rules 1–7 re-executed as regression (zero new Law-REQs); rules 8–12 green.
- [ ] Every NFR in `nfr.md` → ≥1 mechanism in `nfr-allocation.md` (rule 8).
- [ ] Every boundary in `domain-boundaries.md` → ≥1 component in 03-view (rule 9).
- [ ] Every ADR has owner, decision statement, status, DEC link, supersede history, last-reviewed, validation plan (rule 10).
- [ ] INDEX ↔ DEC seed consistent (rule 11).
- [ ] Capacity table complete per schema; threat model and PII register exist (rule 12).
- [ ] Errata E1–E7 verified with commit hashes + reviewers.

### 2.3 Linter green on rules 1–12

`scripts/check_traceability.sh` exits 0 against the committed
baseline. The linter's exit code is recorded in the worklog.

### 2.4 Open-questions carry-over explicit

Q1, Q2, Q4, Q5 carry-over status is explicitly recorded in
`unresolved-decisions.md`. If any of these is BLOCKED, Phase 3
does not start. If any is RESOLVED, the resolution is migrated to
a DEC row in `traceability.md` §C and the question is marked Closed.

### 2.5 ADR ownership complete

All 21 ADRs have a named owner (per `roles.md` §1) and a decision
statement. Status may remain PROPOSED; the gate criterion is
"owned + decided + DEC-linked", not "ACCEPTED".

### 2.6 Architecture inventory complete

All six Phase 2 architecture files exist and are non-empty. The
inventory map in `docs/adr/INDEX.md` §1 lists every file. The
linter (rule 12) verifies the inventory.

### 2.7 Capacity and risk registers reviewed

The capacity table (`capacity-assumptions.md`) and the risk
register (`risk-register.md`) have been reviewed by the
Architecture Lead and the Engineering Lead. ASSUMED rows (Q5-
dependent) are flagged; mitigation plans exist for all P0 and P1
risks.

## 3. Constraints Phase 3 must encode

Phase 3 begins repo skeleton and the first application code. The
following constraints must be encoded structurally in Phase 3;
they are not negotiable and not deferred.

### 3.1 Module → Django app map

The 12 bounded contexts in `domain-boundaries.md` map to Django
apps as follows. Phase 3 creates the apps that are in scope for
Increment 1 (Tenancy, Identity primitives, Audit, Configuration,
Feature Flags, Telemetry, Reliability, Webhooks). The remaining
apps are created in their respective phases.

| Bounded context | Django app | Phase created | Phase 3? |
|---|---|---|---|
| Tenancy | `tenancy/` | Phase 3 | Yes |
| Identity | `identity/` | Phase 3 (skeleton); Phase 4–7 (full) | Yes (skeleton) |
| Audit | `audit/` | Phase 3 | Yes |
| Workflow Engine | `workflow/` | Phase 8 | No |
| Ledger | `ledger/` | Phase 11 | No |
| Configuration | `config/` | Phase 3 | Yes |
| Feature Flags | `flags/` | Phase 3 | Yes |
| Telemetry | `telemetry/` | Phase 3 (middleware) | Yes |
| Reliability | `reliability/` | Phase 3 (middleware + lib) | Yes |
| Backups & DR | `backups/` | Phase 3 (management commands) | Yes |
| Sandbox | `sandbox/` | Phase 4 | No |
| Webhooks | `webhooks/` | Phase 3 | Yes |

Phase 3 creates 9 Django apps. Each app follows the hexagonal layout
(DEC-0002):

```
<app>/
  domain/          # pure domain logic; no infra imports
    aggregates.py
    commands.py
    events.py
    ports.py       # interfaces (ports)
  adapters/        # infrastructure adapters
    orm.py
    events.py
    http.py
  api/             # DRF views, serializers (boundary)
    views.py
    serializers.py
    urls.py
  apps.py
  migrations/
```

### 3.2 Postgres major version lock

The platform locks to **PostgreSQL 16** (major version) for the
duration of Increment 1. Major version upgrades require an ADR
and a migration plan. Minor version upgrades are applied via
the cloud provider's managed service.

- **Locked version:** PostgreSQL 16.x (latest minor at deployment time)
- **Rationale:** RLS (DEC-0003) and JSONB are stable in PG 16;
  PG 17 introduces breaking changes in `pg_stat_statements` that
  require validation.
- **Upgrade path:** Documented in `docs/adr/ADR-0019.md` (forward-only
  migrations). Major upgrade is a forward migration with a parallel
  run.
- **Owner:** Infrastructure Lead.

### 3.3 RLS role model

The RLS implementation uses three database roles:

| Role | Purpose | Permissions |
|---|---|---|
| `app_writer` | Service role for normal requests | `SELECT, INSERT, UPDATE, DELETE` with RLS policies enforcing `tenant_id = current_setting('app.tenant_id')` |
| `app_reader` | Service role for read-only endpoints (analytics, audit query) | `SELECT` with RLS policies |
| `app_admin` | Break-glass role for operations | `SELECT, INSERT, UPDATE, DELETE` without RLS; use logged and audited |

Phase 3 implements:

- The three roles as PostgreSQL `ROLE` objects.
- RLS policies on every tenant-scoped table.
- A connection-pooler (PgBouncer) configured to use `app_writer` by
  default; `app_reader` for read-only endpoints; `app_admin` only
  via break-glass procedure.
- A `SET LOCAL app.tenant_id = ...` middleware that sets the tenant
  context per request from the authenticated user's tenant.

The break-glass procedure (`app_admin` role use) requires:
two-person approval (per `roles.md` §5), audit log entry per
operation, and a post-use review by the Security Lead.

### 3.4 Idempotency middleware contract

Phase 3 implements `reliability.middleware.IdempotencyMiddleware`
per ADR-0008. The middleware:

- Reads the `Idempotency-Key` header on every mutating request.
- Looks up the key in the idempotency store (Redis).
- If found: returns the cached response.
- If not found: processes the request, caches the response with
  the key (TTL 24h), returns the response.
- If the header is missing on a mutating endpoint: rejects with
  400.

Every mutating endpoint (POST, PUT, PATCH, DELETE) is wired
through this middleware. The CI gate (Phase 3) rejects any
mutating endpoint without the middleware.

### 3.5 Boundary enforcement (static analyzer)

Phase 3 implements the static analyzer described in
`domain-boundaries.md` §9. The analyzer rejects:

- Any import of `django.db`, `rest_framework`, or `pika` from
  `domain/` packages.
- Any direct table access from a service that does not own the
  table.
- Any cross-tenant synchronous call (detected by import analysis).

The analyzer runs at pre-commit and in CI.

### 3.6 Forward-only migrations

Phase 3 implements the migration linter per ADR-0019. The linter
rejects any migration with a `reverse()` that does anything other
than `django.db.migrations.RunPython.noop` or equivalent. Down-
migrations are forbidden in production.

### 3.7 Telemetry middleware

Phase 3 implements `telemetry.middleware.SpanMiddleware` per
ADR-0020. The middleware emits an OpenTelemetry span for every
boundary operation (inbound request, outbound call, audit write).
The CI gate (Phase 3) rejects any boundary without a span.

## 4. Phase 3 scope (preview)

Phase 3 begins repo skeleton, CI, dev environment, and the first
application code. The Phase 3 deliverables are previewed here so
that the Phase 2 handoff is informed by what Phase 3 will need.

| Deliverable | Owner | Notes |
|---|---|---|
| Repo skeleton (Django project, DRF scaffold, 9 apps per §3.1) | Architecture Lead | First application code. |
| CI pipeline (build, test, lint, traceability check rules 1–12, boundary analyzer) | Engineering Lead | `check_traceability.sh` integrated as a CI step. |
| Dev environment (Docker Compose, local seed data, local KMS, local IdP stub, local audit log) | Infrastructure Lead | Per §3.2, §3.3. |
| Test scaffolding (pytest, integration test framework, property-based tests) | Engineering Lead | Per NFR §7.1, §7.2. |
| Static analyzer (boundary enforcement per §3.5) | Architecture Lead | Per `domain-boundaries.md` §9. |
| Migration linter (forward-only per §3.6) | Architecture Lead | Per ADR-0019. |
| RLS implementation (roles, policies, middleware per §3.3) | Architecture Lead | Per DEC-0003. |
| Idempotency middleware (per §3.4) | Architecture Lead | Per ADR-0008. |
| Telemetry middleware (per §3.7) | Infrastructure Lead | Per ADR-0020. |
| Agent runbooks (9 agents, draft) | Engineering Lead | Per DEC-0022. Shadow runs begin. |
| ADR full sections (21 ADRs) | Architecture Lead | Context / Decision / Alternatives / Consequences / Validation Plan expanded. |

Phase 3 does NOT deliver: identity primitives beyond skeleton
(Phase 4–7), audit log implementation beyond skeleton (Phase 8–10),
ledger (Phase 11), or any workflow runtime.

## 5. Open risks inherited by Phase 3

The risks in `risk-register.md` are open at the Phase 2 / Phase 3
boundary. The following are the highest-priority risks Phase 3
inherits:

| Risk ID | Title | Score | Phase 3 action |
|---|---|---|---|
| R-TNC-01 | RLS bypass via application bug | 15 (P1) | Implement static analyzer (§3.5); integration tests per service |
| R-REL-01 | Idempotency store loss | 8 (P1) | Implement Redis with AOF + multi-AZ (§3.4) |
| R-REL-03 | Backpressure ignored | 9 (P1) | CI gate rejecting callers without backpressure handling |
| R-SCL-02 | Database connection ceiling | 12 (P1) | Implement PgBouncer connection pooling |
| R-VND-06 | Event store vendor lock-in (Q11) | 12 (P1) | Evaluate EventStoreDB vs Postgres-based vs DynamoDB at Phase 3 start |
| R-SPOF-03 | Idempotency store SPOF | 8 (P1) | Multi-AZ Redis; fail-open to reject |

All risks are tracked in `risk-register.md`; Phase 3 reviews and
updates the register at its boundary.

## 6. Deferred work (Phase 4–24)

The following Phase 2 stubs are deferred to later phases per their
scope:

| Stub | Deferred to | Authority |
|---|---|---|
| STRIDE threat model full depth (30 findings) | Phase 24 | `security.md` §10 |
| Identity full implementation | Phase 4–7 | `scope.md` §1.2 |
| Audit log full implementation | Phase 8–10 | `scope.md` §1.3 |
| Workflow Engine implementation | Phase 8–10 | `scope.md` §2 |
| Ledger implementation | Phase 11 | `scope.md` §2 |
| Sandbox implementation | Phase 4 | `domain-boundaries.md` §8.3 |
| Backups full automation | Phase 3 (commands) → Phase 8 (full) | `workflows.md` §4.3 |
| DR drill automation | Phase 3 (manual) → Phase 8 (auto) | `workflows.md` §4.3 |

## 7. Handoff sign-off

The handoff is signed off by:

- **Engineering Lead** — confirms Phase 2 acceptance criteria met
  and Phase 3 entry criteria satisfied.
- **Architecture Lead** — confirms the architecture inventory is
  complete and the ADR-DEC mapping law holds.
- **Security Lead** — confirms the STRIDE threat model stub is
  complete and the PII register exists.
- **Infrastructure Lead** — confirms the capacity table and risk
  register are reviewed.
- **Data Protection Officer** — confirms the PII register satisfies
  GDPR Art.30.

Sign-off is recorded in the worklog with the sign-off date, the
signer's role, and the gate status at sign-off. If any sign-off
is BLOCKED, Phase 3 does not start.

## 8. Worklog pointer

The shared worklog is at `/home/z/my-project/worklog.md`. The
Phase 2 close-out entry is the last entry before the Phase 3
kick-off entry. The Phase 3 kick-off entry references this
document and the signed-off gate status.
