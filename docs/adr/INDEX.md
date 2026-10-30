# ADR Index — Phase 2

| Field | Value |
|---|---|
| Document | `docs/adr/INDEX.md` |
| Version | 5.3 (Phase 2) |
| Status | Approved |
| Owner | Architecture Lead |
| Authority | DEC-0025 (architecture inventory map); DEC-0026 (Nygard format) |
| Consistency target | INDEX ↔ DEC seed (`traceability.md` §C) |

This index is the **single authority** for ADR status and ADR↔DEC
consistency. The linter (rule 11) cross-checks this index against the
DEC seed in `traceability.md` §C. The two must agree exactly:

- DEC-0001…0020 ↔ ADR-0001…0020 (1:1)
- DEC-0021 ↔ ADR-0021 (1:1)
- DEC-0022, DEC-0023, DEC-0024, DEC-0025, DEC-0026 carry `ADR: none`
  (no ADR file; these are governance-layer decisions that don't
  require an ADR per the ADR-DEC mapping law in §A.4).

## §1. Architecture inventory map (DEC-0025)

The Phase 2 architecture inventory comprises the eight Phase 1
requirement documents, the Phase 0 evidence template, the BLUEPRINT,
and six new Phase 2 files. This is the authoritative inventory per
DEC-0025.

### 1.1 Existing (Phase 1) — eight requirement documents + two authority docs

| Path | Authority | Phase 2 status |
|---|---|---|
| `docs/BLUEPRINT.md` | Master blueprint (v5.2) | Byte-frozen (per Phase 2 hard acceptance) |
| `docs/ERRATA-v5.2.1.md` | Errata E1–E7 | Byte-frozen; verification in `docs/errata/v5.2.1-verification.md` |
| `docs/requirements/traceability.md` | Sole authority for REQ and DEC IDs | Updated (v5.3) — DEC-0025, DEC-0026 added |
| `docs/requirements/scope.md` | Capability-level triage | Unchanged |
| `docs/requirements/roles.md` | RACI + small-team blocker rule | Unchanged |
| `docs/requirements/workflows.md` | 10 in-scope workflow specs | Unchanged |
| `docs/requirements/nfr.md` | Non-functional requirements | Unchanged; mechanisms allocated in `nfr-allocation.md` |
| `docs/requirements/domain-boundaries.md` | Bounded contexts | Unchanged; components mapped in §3 of this file |
| `docs/requirements/triage-table.md` | 10 workflows triaged | Unchanged |
| `docs/requirements/unresolved-decisions.md` | 27+ open questions | Updated — carry-over explicit, architectural Qs added |
| `docs/requirements/stage-1-handoff.md` | Phase 2 entry criteria | Unchanged |
| `docs/phase-0-evidence.md` | Phase 0 gate template | Unchanged |

### 1.2 New (Phase 2) — six files mandated by DEC-0025

| Path | Authority | Purpose |
|---|---|---|
| `docs/adr/INDEX.md` | This file | ADR status table; ADR↔DEC consistency; architecture inventory map |
| `docs/architecture/security.md` | DEC-0025; STRIDE | Threat model across 5 external surfaces; vendor surfaces in `risk-register.md` |
| `docs/architecture/nfr-allocation.md` | DEC-0025 | Every NFR in `nfr.md` → ≥1 mechanism (linter rule 8) |
| `docs/architecture/capacity-assumptions.md` | DEC-0025 | Capacity table; ≥1 row per Increment-1 pillar (linter rule 9 input) |
| `docs/architecture/data-classification.md` | DEC-0025 | PII register; data classification scheme |
| `docs/architecture/risk-register.md` | DEC-0025 | Architectural risk register; ≥1 row per pillar + vendor / SPOF / scaling ceilings |

### 1.3 Inventory change protocol

Per DEC-0025, additions or retirements to this inventory follow the
same protocol as boundary changes (`domain-boundaries.md` §10): an
ADR, an update to this section, an update to `traceability.md` §C
if a DEC is affected, and a supersession row if a DEC is retired.

## §2. ADR status table

All 21 ADRs are in PROPOSED status as of Phase 2 (per DEC-0026). The
status transitions to ACCEPTED on a per-ADR basis as each is
formally reviewed. The status column here is the authoritative
status; the linter (rule 11) cross-checks it against the ADR files'
front-matter `Status:` field.

| ADR | Title | DEC | Owner | Status | Created | Last-Reviewed | Supersedes | Superseded-By |
|---|---|---|---|---|---|---|---|---|
| ADR-0001 | Adopt event-sourced domain model | DEC-0001 | Architecture Lead | ACCEPTED | 2025-10-27 | 2025-10-28 | — | — |
| ADR-0002 | Adopt hexagonal architecture (ports and adapters) | DEC-0002 | Architecture Lead | ACCEPTED | 2025-10-27 | 2025-10-28 | — | — |
| ADR-0003 | Tenant isolation via row-level security | DEC-0003 | Architecture Lead | PROPOSED | 2025-10-27 | 2025-10-28 | — | — |
| ADR-0004 | OIDC for identity federation | DEC-0004 | Identity Lead | PROPOSED | 2025-10-27 | 2025-10-28 | — | — |
| ADR-0005 | SAML for enterprise tenancy SSO | DEC-0005 | Identity Lead | PROPOSED | 2025-10-27 | 2025-10-28 | — | — |
| ADR-0006 | Append-only audit log (no update/delete API) | DEC-0006 | Architecture Lead | ACCEPTED | 2025-10-27 | 2025-10-28 | — | — |
| ADR-0007 | Hash-chain audit log entries | DEC-0007 | Architecture Lead | PROPOSED | 2025-10-27 | 2025-10-28 | — | — |
| ADR-0008 | Idempotency keys on all mutations | DEC-0008 | Architecture Lead | PROPOSED | 2025-10-27 | 2025-10-28 | — | — |
| ADR-0009 | Declarative workflow engine | DEC-0009 | Architecture Lead | PROPOSED | 2025-10-27 | 2025-10-28 | — | — |
| ADR-0010 | Workflow versioning (immutable definitions) | DEC-0010 | Architecture Lead | PROPOSED | 2025-10-27 | 2025-10-28 | — | — |
| ADR-0011 | Immutable ledger entries (no update, no delete) | DEC-0011 | Architecture Lead | PROPOSED | 2025-10-27 | 2025-10-28 | — | — |
| ADR-0012 | Decimal arithmetic for all money | DEC-0012 | Architecture Lead | PROPOSED | 2025-10-27 | 2025-10-28 | — | — |
| ADR-0013 | Multi-currency via ISO 4217 | DEC-0013 | Architecture Lead | PROPOSED | 2025-10-27 | 2025-10-28 | — | — |
| ADR-0014 | Tenant as first-class aggregate root | DEC-0014 | Architecture Lead | ACCEPTED | 2025-10-27 | 2025-10-28 | — | — |
| ADR-0015 | RBAC with delegation chains | DEC-0015 | Identity Lead | PROPOSED | 2025-10-27 | 2025-10-28 | — | — |
| ADR-0016 | Feature flags at boundary | DEC-0016 | Architecture Lead | PROPOSED | 2025-10-27 | 2025-10-28 | — | — |
| ADR-0017 | Blue/green deployments per tenant | DEC-0017 | Infrastructure Lead | ACCEPTED | 2025-10-27 | 2025-10-28 | — | — |
| ADR-0018 | Read models rebuildable from events | DEC-0018 | Architecture Lead | PROPOSED | 2025-10-27 | 2025-10-28 | — | — |
| ADR-0019 | Schema migrations forward-only | DEC-0019 | Architecture Lead | PROPOSED | 2025-10-27 | 2025-10-28 | — | — |
| ADR-0020 | Telemetry via OpenTelemetry | DEC-0020 | Infrastructure Lead | PROPOSED | 2025-10-27 | 2025-10-28 | — | — |
| ADR-0021 | Execution-layer phase grouping (27 stages → 25 phases) | DEC-0021 | Engineering Lead | PROPOSED | 2025-10-27 | 2025-10-28 | — | — |
| ADR-0022 | Repository skeleton (pyproject, Docker, compose, Makefile, CI) | DEC-0027 | Architecture Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0023 | Settings split + named-var loud failure | DEC-0028 | Architecture Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0024 | CI pipeline (GitHub Actions) | DEC-0029 | Architecture Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0025 | Structured logging (structlog, JSON Lines, redaction, sampling) | DEC-0030 | Architecture Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0026 | Error format (RFC 7807 + catalog + i18n) | DEC-0031 | Architecture Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0027 | Testing & coverage (mypy gradual + coverage baseline + diff ≥80%) | DEC-0032 | Engineering Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0028 | Scanning stack (gitleaks + pip-audit) | DEC-0033 | Security Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0029 | Tenant resolution (JWT claim primary + X-Tenant-ID fallback) | DEC-0034 | Architecture Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0030 | pgbouncer compatibility (transaction-mode; SET LOCAL only) | DEC-0035 | Infrastructure Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0031 | AuthN strategy (JWT + refresh + Argon2id + MFA + API keys + service JWTs) | DEC-0036 | Identity Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0032 | RBAC model (permission-based, closed catalog, baseline roles) | DEC-0037 | Identity Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0033 | Tenant resolution order (JWT claim + membership validation + switch) | DEC-0038 | Architecture Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0034 | Service/agent identity (shadow→live gate + typ=service JWT + endpoint separation) | DEC-0039 | Identity Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0035 | Hash-chain architecture (SHA-256, hybrid scope, Merkle-style payload) | DEC-0040 | Architecture Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0036 | AuditEvent schema + partitioning + event type taxonomy | DEC-0041 | Architecture Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0037 | Redaction policy + Merkle-style payload hashing | DEC-0042 | Privacy Owner | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0038 | Insert-only enforcement (trigger + GRANT + monitoring) | DEC-0043 | Security Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0039 | Audit read API + clearance model + meta-audit cut-off | DEC-0044 | Architecture Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0040 | Outbox pattern + relay strategy | DEC-0045 | Architecture Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0041 | Inbox dedup + consumer semantics | DEC-0046 | Architecture Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0042 | DLQ + poison criteria + monitoring | DEC-0047 | Architecture Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0043 | Idempotency keys + cross-service propagation | DEC-0048 | Architecture Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0044 | State machine library + transition pattern | DEC-0049 | Architecture Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0045 | Notifications port + adapter vendors | DEC-0050 | Architecture Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0046 | MarketingGate + suppression + caps + send-type taxonomy | DEC-0051 | Architecture Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0047 | Player entity model + User relationship | DEC-0052 | Product Owner | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0048 | Consent schema + jurisdiction-aware fields | DEC-0053 | Product Owner | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0049 | Consent immutability pattern — hash-chained | DEC-0054 | Architecture Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0050 | Player lifecycle FSM — states, transitions, regulatory constraints | DEC-0055 | Product Owner | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0051 | Retention model + jurisdiction-aware schedule + DSAR + right-to-erasure | DEC-0056 | Product Owner | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0052 | KYC case FSM (16 states, regulatory constraints, hash-chained) | DEC-0057 | Compliance Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0053 | Document model + versioning + retention | DEC-0058 | Architecture Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0054 | Storage port + backend Q5-blocked | DEC-0059 | Infrastructure Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0055 | Synchronous revocation — soft-delete + cryptographic shredding | DEC-0060 | Security Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0056 | AML/CFT framework (RBA, PEP/sanctions, SoF/SoW, SAR) | DEC-0061 | Compliance Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0057 | KYC vendor integration Q5-blocked | DEC-0062 | Compliance Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |
| ADR-0058 | Review queue + workflow + SLA + escalation | DEC-0063 | Compliance Lead | ACCEPTED | 2025-10-28 | 2025-10-28 | — | — |

## §3. DEC ↔ ADR consistency matrix

This matrix is the single authority for the ADR-DEC mapping law
(DEC-0023). The linter (rule 11) cross-checks this matrix against
`traceability.md` §C.

| DEC | DEC title | ADR | DEC `ADR` column | INDEX ↔ DEC consistent? |
|---|---|---|---|---|
| DEC-0001 | Adopt event-sourced domain model | ADR-0001 | ADR-0001 | ✓ |
| DEC-0002 | Adopt hexagonal architecture | ADR-0002 | ADR-0002 | ✓ |
| DEC-0003 | Tenant isolation via RLS | ADR-0003 | ADR-0003 | ✓ |
| DEC-0004 | OIDC for identity federation | ADR-0004 | ADR-0004 | ✓ |
| DEC-0005 | SAML for enterprise tenancy SSO | ADR-0005 | ADR-0005 | ✓ |
| DEC-0006 | Append-only audit log | ADR-0006 | ADR-0006 | ✓ |
| DEC-0007 | Hash-chain audit log entries | ADR-0007 | ADR-0007 | ✓ |
| DEC-0008 | Idempotency keys on all mutations | ADR-0008 | ADR-0008 | ✓ |
| DEC-0009 | Declarative workflow engine | ADR-0009 | ADR-0009 | ✓ |
| DEC-0010 | Workflow versioning | ADR-0010 | ADR-0010 | ✓ |
| DEC-0011 | Immutable ledger entries | ADR-0011 | ADR-0011 | ✓ |
| DEC-0012 | Decimal arithmetic for money | ADR-0012 | ADR-0012 | ✓ |
| DEC-0013 | Multi-currency via ISO 4217 | ADR-0013 | ADR-0013 | ✓ |
| DEC-0014 | Tenant as first-class aggregate root | ADR-0014 | ADR-0014 | ✓ |
| DEC-0015 | RBAC with delegation chains | ADR-0015 | ADR-0015 | ✓ |
| DEC-0016 | Feature flags at boundary | ADR-0016 | ADR-0016 | ✓ |
| DEC-0017 | Blue/green deployments per tenant | ADR-0017 | ADR-0017 | ✓ |
| DEC-0018 | Read models rebuildable from events | ADR-0018 | ADR-0018 | ✓ |
| DEC-0019 | Schema migrations forward-only | ADR-0019 | ADR-0019 | ✓ |
| DEC-0020 | Telemetry via OpenTelemetry | ADR-0020 | ADR-0020 | ✓ |
| DEC-0021 | Execution-layer phase grouping | ADR-0021 | ADR-0021 | ✓ |
| DEC-0022 | Agent delivery schedule + promotion gate | none | none | ✓ (explicit `none`) |
| DEC-0023 | Semantic definitions; DEC↔ADR mapping law | none | none | ✓ (explicit `none`) |
| DEC-0024 | B2B OS provider business model (Option A) | none | none | ✓ (explicit `none`) |
| DEC-0025 | Architecture inventory map | none | none | ✓ (explicit `none`) |
| DEC-0026 | ADR Nygard format adoption | none | none | ✓ (explicit `none`) |
| DEC-0027 | Repository skeleton | ADR-0022 | ADR-0022 | ✓ |
| DEC-0028 | Settings split + named-var loud failure | ADR-0023 | ADR-0023 | ✓ |
| DEC-0029 | CI pipeline (GitHub Actions) | ADR-0024 | ADR-0024 | ✓ |
| DEC-0030 | Structured logging | ADR-0025 | ADR-0025 | ✓ |
| DEC-0031 | Error format (RFC 7807) | ADR-0026 | ADR-0026 | ✓ |
| DEC-0032 | Testing & coverage | ADR-0027 | ADR-0027 | ✓ |
| DEC-0033 | Scanning stack | ADR-0028 | ADR-0028 | ✓ |
| DEC-0034 | Tenant resolution | ADR-0029 | ADR-0029 | ✓ |
| DEC-0035 | pgbouncer compatibility | ADR-0030 | ADR-0030 | ✓ |
| DEC-0036 | AuthN strategy | ADR-0031 | ADR-0031 | ✓ |
| DEC-0037 | RBAC model | ADR-0032 | ADR-0032 | ✓ |
| DEC-0038 | Tenant resolution order | ADR-0033 | ADR-0033 | ✓ |
| DEC-0039 | Service/agent identity | ADR-0034 | ADR-0034 | ✓ |
| DEC-0040 | Hash-chain architecture | ADR-0035 | ADR-0035 | ✓ |
| DEC-0041 | AuditEvent schema + taxonomy | ADR-0036 | ADR-0036 | ✓ |
| DEC-0042 | Redaction policy + Merkle hashing | ADR-0037 | ADR-0037 | ✓ |
| DEC-0043 | Insert-only enforcement | ADR-0038 | ADR-0038 | ✓ |
| DEC-0044 | Audit read API + clearance model | ADR-0039 | ADR-0039 | ✓ |
| DEC-0045 | Outbox pattern + relay | ADR-0040 | ADR-0040 | ✓ |
| DEC-0046 | Inbox dedup + consumer semantics | ADR-0041 | ADR-0041 | ✓ |
| DEC-0047 | DLQ + poison criteria | ADR-0042 | ADR-0042 | ✓ |
| DEC-0048 | Idempotency keys + cross-service | ADR-0043 | ADR-0043 | ✓ |
| DEC-0049 | State machine library | ADR-0044 | ADR-0044 | ✓ |
| DEC-0050 | Notifications port + adapters | ADR-0045 | ADR-0045 | ✓ |
| DEC-0051 | MarketingGate + suppression + caps | ADR-0046 | ADR-0046 | ✓ |
| DEC-0052 | Player entity model | ADR-0047 | ADR-0047 | ✓ |
| DEC-0053 | Consent schema | ADR-0048 | ADR-0048 | ✓ |
| DEC-0054 | Consent immutability | ADR-0049 | ADR-0049 | ✓ |
| DEC-0055 | Player lifecycle FSM | ADR-0050 | ADR-0050 | ✓ |
| DEC-0056 | Retention model + DSAR + erasure | ADR-0051 | ADR-0051 | ✓ |
| DEC-0057 | KYC case FSM | ADR-0052 | ADR-0052 | ✓ |
| DEC-0058 | Document model + versioning | ADR-0053 | ADR-0053 | ✓ |
| DEC-0059 | Storage port | ADR-0054 | ADR-0054 | ✓ |
| DEC-0060 | Synchronous revocation | ADR-0055 | ADR-0055 | ✓ |
| DEC-0061 | AML/CFT framework | ADR-0056 | ADR-0056 | ✓ |
| DEC-0062 | KYC vendor integration | ADR-0057 | ADR-0057 | ✓ |
| DEC-0063 | Review queue + SLA + escalation | ADR-0058 | ADR-0058 | ✓ |

Total: 58 ADRs ↔ 58 DECs (DEC-0001…0021, DEC-0027…0063 excluding 0022-0026);
5 DECs with explicit `none` (DEC-0022…0026). Registry total: 63 DECs.

## §4. Component view (03-view) — boundaries → components

Per the Phase 2 hard acceptance, every bounded context in
`domain-boundaries.md` must map to ≥1 component in this 03-view
table. The linter (rule 9) cross-checks the boundary list against
this component list.

| Boundary (from `domain-boundaries.md`) | Component(s) | Tech stack (Phase 3+ target) | Owner |
|---|---|---|---|
| Tenancy | `tenancy.service.TenantService` (command handler); `tenancy.projections.TenantView` (read model); `tenancy.adapters.TenantRepository` (event store adapter) | Django app `tenancy/`; PostgreSQL RLS; event store adapter | Architecture Lead |
| Identity | `identity.service.AuthService`; `identity.service.UserService`; `identity.service.RoleService`; `identity.adapters.OIDCProvider`; `identity.adapters.SAMLProvider` | Django app `identity/`; OIDC provider (Keycloak or Auth0); SAML SP library | Identity Lead |
| Audit | `audit.service.AppendService`; `audit.service.QueryService`; `audit.service.HashChainVerifier`; `audit.projections.AuditReadModel` | Django app `audit/`; PostgreSQL append-only table; daily verifier cron | Architecture Lead |
| Workflow Engine | `workflow.engine.Engine`; `workflow.registry.DefinitionRegistry`; `workflow.executor.Executor` | Django app `workflow/` (Phase 8+); declarative YAML definitions | Architecture Lead |
| Ledger | `ledger.service.PostingService`; `ledger.projections.BalanceView`; `ledger.adapters.LedgerRepository` | Django app `ledger/` (Phase 11+); event-sourced entries | Architecture Lead |
| Configuration | `config.service.ConfigService`; `config.adapters.ConfigStore` | Django app `config/`; managed config store (AWS AppConfig or equivalent) | Infrastructure Lead |
| Feature Flags | `flags.service.FlagService`; `flags.adapters.FlagStore`; `flags.middleware.BoundaryEvaluator` | Django app `flags/`; flag store (LaunchDarkly or self-hosted) | Architecture Lead |
| Telemetry | `telemetry.adapters.OTelExporter`; `telemetry.middleware.SpanMiddleware` | OpenTelemetry SDK; Jaeger (local); vendor (prod) | Infrastructure Lead |
| Reliability | `reliability.middleware.IdempotencyMiddleware`; `reliability.lib.CircuitBreaker`; `reliability.lib.BackpressureSignal` | Django middleware + library; Redis for circuit state | Architecture Lead |
| Backups & DR | `backups.service.BackupExecutor`; `backups.service.RestoreExecutor`; `backups.adapters.StorageBackend` | Django management commands; S3 + Object Lock; quarterly DR drill | Operations Lead |
| Sandbox | `sandbox.service.SandboxProvisioner`; `sandbox.service.DataSynthesizer` | Django app `sandbox/` (Phase 4+); synthetic data factory | Product Lead |
| Webhooks | `webhooks.service.DeliveryService`; `webhooks.service.RetryScheduler`; `webhooks.adapters.HttpClient` | Django app `webhooks/`; Celery for retries; outbound HTTP | Infrastructure Lead |

The component list above is the C4 level-3 (component) view for
Increment 1. Phase 3 begins implementation of the Tenancy,
Identity, Audit, Configuration, Feature Flags, Telemetry,
Reliability, Backups & DR, and Webhooks components. The Workflow
Engine, Ledger, and Sandbox components are deferred to later
phases per the triage rule.

## §5. ADR lifecycle

Per DEC-0026, the ADR lifecycle is:

1. **PROPOSED** — the ADR stub exists with Nygard front-matter and
   all five body sections. Owner, decision statement, DEC link,
   supersede history, last-reviewed, and validation plan are all
   present. (All 21 ADRs are at this stage as of Phase 2.)
2. **ACCEPTED** — the ADR has been formally reviewed and approved
   by the owner and the Architecture Lead. The `Last-Reviewed` date
   is updated.
3. **DEPRECATED** — the ADR is no longer recommended for new code
   but is retained for audit. A `Superseded-By` reference points to
   the replacing ADR.
4. **SUPERSEDED** — the ADR has been replaced by a newer ADR. The
   `Superseded-By` reference is populated; the superseding ADR's
   `Supersedes` reference points back.
5. **REJECTED** — the ADR was considered and not adopted. Retained
   for audit.

The status transitions are recorded in this index (§2) and in the
ADR file's front-matter. The linter (rule 11) cross-checks the two.

## §6. Cross-references

- DEC seed: `docs/requirements/traceability.md` §C
- ADR-DEC mapping law: `docs/requirements/traceability.md` §A.4
- Boundary definitions: `docs/requirements/domain-boundaries.md`
- NFR definitions: `docs/requirements/nfr.md`
- NFR → mechanism allocation: `docs/architecture/nfr-allocation.md`
- Capacity assumptions: `docs/architecture/capacity-assumptions.md`
- Threat model: `docs/architecture/security.md`
- PII register: `docs/architecture/data-classification.md`
- Risk register: `docs/architecture/risk-register.md`
- Errata verification: `docs/errata/v5.2.1-verification.md`
- Phase 2 handoff: `docs/stage-handoffs/stage-02-handoff.md`
- Phase audits: `docs/audits/phase-001-audit.md`, `docs/audits/phase-002-audit.md`
- Linter: `scripts/check_traceability.sh` (rules 1–12)
