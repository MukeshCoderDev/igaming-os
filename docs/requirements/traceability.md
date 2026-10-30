# Traceability Matrix

| Field | Value |
|---|---|
| Document | `docs/requirements/traceability.md` |
| Version | 8.0 (Phase 25 FINAL — Validation, Readiness & Launch — 25 phases complete; 158 DECs, 149 ADRs, 235 linter rules; BLUEPRINT v5.2 byte-frozen) |
| Status | Phase 25 Stage A — design (Stage B merge stop #15 — FINAL gate; Stage B IS the final Ubuntu push) |
| Owner | Architecture Lead |
| Linter | `scripts/check_traceability.sh` (rules 1–235; Phase 25 FINAL) |
| Floor | 62 REQs (24 Law + 12 Pain + 26 MB); 156 DECs |

This document is the **sole authority** for REQ IDs and DEC IDs from seed
onward. Any other document that cites a REQ or DEC must match this
document exactly. Mismatches are linter failures (rules 6 and 7).

---

## §A Definitions

### A.1 Status enum

Every REQ and DEC row carries one of these statuses. The linter enforces
this set (rule 2).

| Status | Meaning |
|---|---|
| Proposed | Drafted internally; not yet validated. |
| Accepted | Internally agreed and committed for delivery. |
| Confirmed | Validated by evidence or external authority. (Rule 4 requires a citation; rule 5 may upgrade to HUMAN-APPROVED.) |
| HUMAN-APPROVED | Received written sign-off from a named human approver. Required for Legal/Regulatory/Licensing/Business/Budget/Vendor categories. |
| Superseded | Replaced by a later row; see Supersession section. |
| Deprecated | Still present for audit; do not implement new code against it. |
| Rejected | Considered and not adopted. Retained for audit. |
| Blocked | Cannot progress because a dependency (typically an open question) is BLOCKED. |

### A.2 Scope enum

Every REQ and DEC row carries one of these scopes. The linter enforces
this set (rule 3).

| Scope | Meaning |
|---|---|
| Phase1 | Delivered in Increment 1 (Tenancy, Identity, Audit, Reliable Core). |
| Phase2-3 | Repo skeleton, CI, dev environment, tenant data model. |
| Phase4-7 | Identity: OIDC, SAML, sessions, MFA. |
| Phase8-10 | Audit log: append, hash-chain, query, export. |
| Phase11 | Ledger primitives. |
| Phase12+ | First customer deposit and onward. |
| CrossCutting | Applies to all phases; not a delivery target itself. |
| Foundational | Decisions/requirements that govern the entire programme. |
| OutOfScope-Increment1 | Explicitly out of Increment 1; may be in later increments. |

### A.3 Category enum

| Category | Used for |
|---|---|
| Legal | Legal obligations, contracts, liability. |
| Regulatory | Regulatory obligations (AML, KYC, sanctions, privacy, retention). |
| Licensing | Licensing regimes the provider may need to operate under. |
| Business | Business-model decisions (revenue, pricing, market). |
| Budget | Budget allocation, funding, burn. |
| Vendor | Vendor selection and vendor risk. |
| Functional | User-facing or tenant-facing functional behaviour. |
| NonFunctional | Quality attributes (security, reliability, performance). |
| Architectural | Module boundaries, invariants, technology choices. |
| Operational | Runbooks, agent schedules, processes. |

### A.4 ADR-DEC mapping law

Per DEC-0023 and BLUEPRINT §8:

1. Every ADR file under `docs/adr/` MUST cite exactly one DEC in its YAML
   front-matter, in the literal form `DEC: DEC-00XX` (four-digit,
   zero-padded).
2. Every DEC row MAY cite at most one ADR, in the `ADR` column of §C.
3. Every ADR MUST be cited by exactly one DEC. No orphans; no double
   citations.
4. ADR and DEC IDs are independent number spaces.
5. Supersession: when a DEC is superseded, its ADR gains a
   `Superseded-By: ADR-00YY` field but its `DEC:` citation is unchanged.
   The superseding DEC gets a new ADR.

The linter (rule 7) enforces invariants 1–3 by scanning `docs/adr/` and
cross-checking against §C.

---

## §B Requirements (62 rows: 24 Law + 12 Pain + 26 MB)

The floor is 62. Subsequent phases may add REQs but may not remove
seeded ones without a supersession row in §D.

### B.1 Law-REQ (24 rows)

| ID | Title | Category | Status | Scope | Owner | Source |
|---|---|---|---|---|---|---|
| Law-REQ-0001 | KYC screening mandatory at onboarding | Regulatory | Blocked | Phase4-7 | Compliance Lead | FATF Rec.10; blocked on Q1/Q2/Q6 |
| Law-REQ-0002 | AML transaction monitoring | Regulatory | Blocked | Phase11 | Compliance Lead | FATF Rec.20; blocked on Q1 |
| Law-REQ-0003 | Sanctions screening (OFAC/EU/UN) | Regulatory | Blocked | Phase4-7 | Compliance Lead | OFAC/EU/UN lists; blocked on Q1/Q2/Q7 |
| Law-REQ-0004 | PEP screening at onboarding and ongoing | Regulatory | Blocked | Phase4-7 | Compliance Lead | FATF Rec.12; blocked on Q1/Q2/Q7 |
| Law-REQ-0005 | Beneficial ownership identification | Regulatory | Blocked | Phase4-7 | Compliance Lead | FATF Rec.24; blocked on Q1 |
| Law-REQ-0006 | Customer risk rating at onboarding | Regulatory | Proposed | Phase4-7 | Compliance Lead | FATF RBA guidance |
| Law-REQ-0007 | Suspicious activity reporting (SAR/STR) | Regulatory | Blocked | Phase11 | Compliance Lead | FATF Rec.20; blocked on Q1/Q15 |
| Law-REQ-0008 | Currency transaction reporting (CTR) | Regulatory | Blocked | Phase11 | Compliance Lead | BSA 31 USC 5313; blocked on Q1 |
| Law-REQ-0009 | Record retention 5-7 years | Regulatory | Proposed | CrossCutting | Compliance Lead | FATF Rec.11 (5y floor) |
| Law-REQ-0010 | Audit log immutability (append-only) | Regulatory | Proposed | Phase1 | Compliance Lead | DEC-0006; DEC-0007 |
| Law-REQ-0011 | Right to erasure handling | Regulatory | Blocked | Phase4-7 | Data Protection Officer | GDPR Art.17; blocked on Q1 (EU scope) |
| Law-REQ-0012 | Data residency controls | Regulatory | Blocked | Phase1 | Data Protection Officer | blocked on Q1/Q3 |
| Law-REQ-0013 | Cross-border data transfer controls | Regulatory | Blocked | Phase1 | Data Protection Officer | GDPR Ch.V; blocked on Q1 |
| Law-REQ-0014 | Privacy notice and consent capture | Regulatory | Proposed | Phase4-7 | Data Protection Officer | GDPR Art.13/14 |
| Law-REQ-0015 | Right to access and portability | Regulatory | Proposed | Phase4-7 | Data Protection Officer | GDPR Art.15/20 |
| Law-REQ-0016 | Breach notification within 72h | Regulatory | Proposed | CrossCutting | Data Protection Officer | GDPR Art.33 (72h floor) |
| Law-REQ-0017 | Sub-processor due diligence | Regulatory | Proposed | Phase2-3 | Compliance Lead | GDPR Art.28 |
| Law-REQ-0018 | Vendor risk assessment | Regulatory | Proposed | Phase2-3 | Compliance Lead | SOC 2 CC9.2 |
| Law-REQ-0019 | Information security program | Regulatory | Proposed | CrossCutting | Security Lead | SOC 2 CC6; ISO 27001 |
| Law-REQ-0020 | Incident response plan | Regulatory | Proposed | CrossCutting | Security Lead | SOC 2 CC7.4 |
| Law-REQ-0021 | Business continuity plan | Regulatory | Proposed | CrossCutting | Operations Lead | SOC 2 CP7.1 |
| Law-REQ-0022 | Disaster recovery RTO/RPO defined | Regulatory | Blocked | CrossCutting | Infrastructure Lead | blocked on Q22 |
| Law-REQ-0023 | Encryption at rest | Regulatory | Proposed | Phase1 | Security Lead | SOC 2 CC6.1 |
| Law-REQ-0024 | Encryption in transit (TLS 1.2+) | Regulatory | Proposed | Phase1 | Security Lead | SOC 2 CC6.1; TLS 1.2+ |

### B.2 Pain-REQ (12 rows)

| ID | Title | Category | Status | Scope | Owner | Source |
|---|---|---|---|---|---|---|
| Pain-REQ-0001 | Reduce onboarding time from 14d to <2d | Functional | Accepted | Phase1 | Product Lead | Discovery interview #1 (Customer A) |
| Pain-REQ-0002 | Self-serve tenant provisioning | Functional | Accepted | Phase1 | Product Lead | Discovery interview #2 (Customer B) |
| Pain-REQ-0003 | Single sign-on across modules | Functional | Accepted | Phase4-7 | Identity Lead | Discovery interview #3 (Customer C) |
| Pain-REQ-0004 | Real-time audit trail visibility for compliance | Functional | Accepted | Phase1 | Compliance Lead | Discovery interview #4 (Customer D) |
| Pain-REQ-0005 | Configurable approval workflows (no code) | Functional | Proposed | Phase8-10 | Product Lead | Discovery interview #5 (Customer E) |
| Pain-REQ-0006 | Reversible erroneous transactions within policy | Functional | Proposed | Phase11 | Product Lead | Discovery interview #6 (Customer F) |
| Pain-REQ-0007 | Multi-currency support | Functional | Blocked | Phase11 | Product Lead | Discovery interview #7 (Customer G); blocked on Q16 |
| Pain-REQ-0008 | API rate limits configurable per tenant | NonFunctional | Accepted | Phase1 | Infrastructure Lead | Discovery interview #8 (Customer H) |
| Pain-REQ-0009 | Sandbox environment for integrators | Functional | Proposed | Phase4-7 | Product Lead | Discovery interview #9 (Integrator I) |
| Pain-REQ-0010 | Webhook reliability and retry | NonFunctional | Accepted | Phase1 | Infrastructure Lead | Discovery interview #10 (Integrator J) |
| Pain-REQ-0011 | Idempotency keys on all mutations | NonFunctional | Accepted | Phase1 | Architecture Lead | Discovery interview #11 (Integrator K) |
| Pain-REQ-0012 | RBAC with delegation chains | Functional | Accepted | Phase4-7 | Identity Lead | Discovery interview #12 (Customer L) |

### B.3 MB-REQ (26 rows)

| ID | Title | Category | Status | Scope | Owner | Source |
|---|---|---|---|---|---|---|
| MB-REQ-0001 | Tenant isolation at data layer (row-level security) | Architectural | Accepted | Phase1 | Architecture Lead | DEC-0003 |
| MB-REQ-0002 | Tenant isolation at compute layer (no cross-tenant calls) | Architectural | Accepted | Phase1 | Architecture Lead | DEC-0003 |
| MB-REQ-0003 | Identity service is sole issuer of auth tokens | Architectural | Accepted | Phase1 | Identity Lead | DEC-0004 |
| MB-REQ-0004 | Audit service is append-only (no update/delete API) | Architectural | Accepted | Phase1 | Architecture Lead | DEC-0006 |
| MB-REQ-0005 | No direct DB access from services (only via repositories) | Architectural | Accepted | Phase1 | Architecture Lead | DEC-0002 |
| MB-REQ-0006 | All cross-module calls via published contracts | Architectural | Accepted | Phase1 | Architecture Lead | DEC-0002 |
| MB-REQ-0007 | Workflows defined declaratively; executed by engine | Architectural | Accepted | Phase8-10 | Architecture Lead | DEC-0009 |
| MB-REQ-0008 | No business logic in API controllers | Architectural | Accepted | CrossCutting | Architecture Lead | DEC-0002 |
| MB-REQ-0009 | No business logic in serializers | Architectural | Accepted | CrossCutting | Architecture Lead | DEC-0002 |
| MB-REQ-0010 | Services are stateless | Architectural | Accepted | CrossCutting | Architecture Lead | DEC-0002 |
| MB-REQ-0011 | All I/O at boundary (ports and adapters) | Architectural | Accepted | CrossCutting | Architecture Lead | DEC-0002 |
| MB-REQ-0012 | Domain events emitted on every state change | Architectural | Accepted | Phase1 | Architecture Lead | DEC-0001 |
| MB-REQ-0013 | Idempotency key enforced at API gateway | Architectural | Accepted | Phase1 | Architecture Lead | DEC-0008 |
| MB-REQ-0014 | Backpressure signals honored by callers | Architectural | Accepted | Phase1 | Architecture Lead | DEC-0020 |
| MB-REQ-0015 | Circuit breakers on all outbound calls | Architectural | Accepted | Phase1 | Architecture Lead | DEC-0020 |
| MB-REQ-0016 | Time is injectable (no direct clock calls in domain) | Architectural | Accepted | CrossCutting | Architecture Lead | DEC-0002 |
| MB-REQ-0017 | Random is injectable | Architectural | Accepted | CrossCutting | Architecture Lead | DEC-0002 |
| MB-REQ-0018 | Configuration externalized (no secrets in code) | Architectural | Accepted | Phase1 | Infrastructure Lead | DEC-0016 |
| MB-REQ-0019 | Feature flags evaluated at boundary | Architectural | Accepted | Phase1 | Architecture Lead | DEC-0016 |
| MB-REQ-0020 | Telemetry emitted at boundaries | Architectural | Accepted | Phase1 | Infrastructure Lead | DEC-0020 |
| MB-REQ-0021 | Migrations are forward-only and reversible-via-compensation | Architectural | Accepted | CrossCutting | Architecture Lead | DEC-0019 |
| MB-REQ-0022 | Schema changes go through deprecation cycle | Architectural | Accepted | CrossCutting | Architecture Lead | DEC-0019 |
| MB-REQ-0023 | No synchronous cross-tenant operations | Architectural | Accepted | Phase1 | Architecture Lead | DEC-0003 |
| MB-REQ-0024 | Read models can be rebuilt from event log | Architectural | Accepted | Phase8-10 | Architecture Lead | DEC-0018 |
| MB-REQ-0025 | Command handlers are pure functions | Architectural | Accepted | CrossCutting | Architecture Lead | DEC-0001 |
| MB-REQ-0026 | No domain logic in infrastructure adapters | Architectural | Accepted | CrossCutting | Architecture Lead | DEC-0002 |

---

## §C Decisions (95 rows)

| ID | Title | Category | Status | Scope | Owner | Source | ADR |
|---|---|---|---|---|---|---|---|
| DEC-0001 | Adopt event-sourced domain model | Architectural | Accepted | Foundational | Architecture Lead | ADR-0001 | ADR-0001 |
| DEC-0002 | Adopt hexagonal architecture (ports and adapters) | Architectural | Accepted | Foundational | Architecture Lead | ADR-0002 | ADR-0002 |
| DEC-0003 | Tenant isolation via row-level security | Architectural | Accepted | Phase1 | Architecture Lead | ADR-0003 | ADR-0003 |
| DEC-0004 | OIDC for identity federation | Architectural | Accepted | Phase4-7 | Identity Lead | ADR-0004 | ADR-0004 |
| DEC-0005 | SAML for enterprise tenancy SSO | Architectural | Accepted | Phase4-7 | Identity Lead | ADR-0005 | ADR-0005 |
| DEC-0006 | Append-only audit log (no update/delete API) | Architectural | Accepted | Phase1 | Architecture Lead | ADR-0006 | ADR-0006 |
| DEC-0007 | Hash-chain audit log entries | Architectural | Accepted | Phase1 | Architecture Lead | ADR-0007 | ADR-0007 |
| DEC-0008 | Idempotency keys on all mutations | Architectural | Accepted | Phase1 | Architecture Lead | ADR-0008 | ADR-0008 |
| DEC-0009 | Declarative workflow engine | Architectural | Accepted | Phase8-10 | Architecture Lead | ADR-0009 | ADR-0009 |
| DEC-0010 | Workflow versioning (immutable definitions) | Architectural | Accepted | Phase8-10 | Architecture Lead | ADR-0010 | ADR-0010 |
| DEC-0011 | Immutable ledger entries (no update, no delete) | Architectural | Accepted | Phase11 | Architecture Lead | ADR-0011 | ADR-0011 |
| DEC-0012 | Decimal arithmetic for all money | Architectural | Accepted | Phase11 | Architecture Lead | ADR-0012 | ADR-0012 |
| DEC-0013 | Multi-currency via ISO 4217 | Architectural | Accepted | Phase11 | Architecture Lead | ADR-0013 | ADR-0013 |
| DEC-0014 | Tenant as first-class aggregate root | Architectural | Accepted | Phase1 | Architecture Lead | ADR-0014 | ADR-0014 |
| DEC-0015 | RBAC with delegation chains | Architectural | Accepted | Phase4-7 | Identity Lead | ADR-0015 | ADR-0015 |
| DEC-0016 | Feature flags at boundary | Architectural | Accepted | Phase1 | Architecture Lead | ADR-0016 | ADR-0016 |
| DEC-0017 | Blue/green deployments per tenant | Architectural | Accepted | Phase2-3 | Infrastructure Lead | ADR-0017 | ADR-0017 |
| DEC-0018 | Read models rebuildable from events | Architectural | Accepted | Phase8-10 | Architecture Lead | ADR-0018 | ADR-0018 |
| DEC-0019 | Schema migrations forward-only | Architectural | Accepted | CrossCutting | Architecture Lead | ADR-0019 | ADR-0019 |
| DEC-0020 | Telemetry via OpenTelemetry | Architectural | Accepted | Phase1 | Infrastructure Lead | ADR-0020 | ADR-0020 |
| DEC-0021 | Execution-layer phase grouping (27 stages → 25 phases) | Operational | Accepted | Foundational | Engineering Lead | ADR-0021 | ADR-0021 |
| DEC-0022 | Agent delivery schedule + shadow→live promotion gate (9 agents) | Operational | Accepted | CrossCutting | Engineering Lead | DEC-0022 (self-citing) | none |
| DEC-0023 | Semantic definitions; DEC↔ADR mapping law | Operational | Accepted | Foundational | Architecture Lead | DEC-0023 (self-citing) | none |
| DEC-0024 | B2B OS provider business model (Option A) | Business | HUMAN-APPROVED | Foundational | Commercial Lead | HUMAN-APPROVED sign-off record (2025-09-15) | none |
| DEC-0025 | Architecture inventory map (DEC-0025) — mandates sections in 8 existing docs + 6 new files | Architectural | Accepted | Foundational | Architecture Lead | DEC-0025 (self-citing); Phase 2 inventory | none |
| DEC-0026 | ADR Nygard format adoption (front-matter + body schema for all ADR stubs) | Architectural | Accepted | Foundational | Architecture Lead | DEC-0026 (self-citing); Phase 2 ADR upgrade | none |
| DEC-0027 | Repository skeleton (pyproject.toml, Dockerfile, docker-compose, settings split, Makefile, CI) | Architectural | Accepted | Phase2-3 | Architecture Lead | ADR-0022; Phase 3 repo skeleton | ADR-0022 |
| DEC-0028 | Settings split + named-var loud failure (base/local/test/production; env-only secrets) | Architectural | Accepted | Phase2-3 | Architecture Lead | ADR-0023; Phase 3 settings-split.md | ADR-0023 |
| DEC-0029 | CI pipeline (GitHub Actions: linter 1–16, ruff, check, check --deploy, migrate, pytest, OpenAPI drift) | Architectural | Accepted | Phase2-3 | Engineering Lead | ADR-0024; Phase 3 ci.yml | ADR-0024 |
| DEC-0030 | Structured logging (structlog, JSON Lines, redaction, sampling) | Architectural | Accepted | Phase1 | Architecture Lead | ADR-0025; Phase 4 observability | ADR-0025 |
| DEC-0031 | Error format (RFC 7807 + catalog + i18n-key messages) | Architectural | Accepted | Phase1 | Architecture Lead | ADR-0026; Phase 4 errors catalog | ADR-0026 |
| DEC-0032 | Testing & coverage (mypy gradual + coverage baseline + diff ≥80%) | Architectural | Accepted | CrossCutting | Engineering Lead | ADR-0027; Phase 4 testing | ADR-0027 |
| DEC-0033 | Scanning stack (gitleaks secret scan + pip-audit dep scan) | Architectural | Accepted | CrossCutting | Security Lead | ADR-0028; Phase 4 scanning | ADR-0028 |
| DEC-0034 | Tenant resolution (JWT claim primary + X-Tenant-ID header fallback; 400 on missing/malformed) | Architectural | Accepted | Phase1 | Architecture Lead | ADR-0029; Phase 5 tenant middleware | ADR-0029 |
| DEC-0035 | pgbouncer compatibility (transaction-mode; SET LOCAL only; no session cursors; prepare_threshold=None) | Architectural | Accepted | Phase1 | Infrastructure Lead | ADR-0030; Phase 5 pgbouncer compat | ADR-0030 |
| DEC-0036 | AuthN strategy (JWT JWS + rotating refresh tokens + Argon2id + MFA TOTP + login throttling + API keys + service JWTs) | Architectural | Accepted | Phase4-7 | Identity Lead | ADR-0031; Phase 6 authN | ADR-0031 |
| DEC-0037 | RBAC model (permission-based, closed catalog, baseline roles admin/manager/viewer/service) | Architectural | Accepted | Phase4-7 | Identity Lead | ADR-0032; Phase 6 RBAC | ADR-0032 |
| DEC-0038 | Tenant resolution order (JWT tenant claim primary + X-Tenant-ID fallback + membership validation + tenant-switch flow) | Architectural | Accepted | Phase1 | Architecture Lead | ADR-0033; Phase 6 tenant resolution | ADR-0033 |
| DEC-0039 | Service/agent identity model (service_identity table + shadow→live gate + typ=service JWT + human/service endpoint separation) | Architectural | Accepted | Phase4-7 | Identity Lead | ADR-0034; Phase 6 service identity | ADR-0034 |
| DEC-0040 | Hash-chain architecture (SHA-256, hybrid scope, Merkle-style payload, BEFORE INSERT trigger, chain_head singleton, pgbouncer-compatible concurrency) | Architectural | Accepted | Phase1 | Architecture Lead | ADR-0035; Phase 7 hash-chain | ADR-0035 |
| DEC-0041 | AuditEvent schema + partitioning + event type taxonomy (closed catalog; UUID PK, tenant_id, actor, event_type, payload JSONB, hash chain, partition by month+tenant) | Architectural | Accepted | Phase1 | Architecture Lead | ADR-0036; Phase 7 audit schema | ADR-0036 |
| DEC-0042 | Redaction policy + Merkle-style payload hashing (per-field hashing, redaction without breaking chain, irreversibility, redaction audited) | Architectural | Accepted | Phase1 | Privacy Owner | ADR-0037; Phase 7 redaction | ADR-0037 |
| DEC-0043 | Insert-only enforcement (BEFORE UPDATE/DELETE trigger raises for all roles; GRANT INSERT+SELECT only; superuser bypass monitored; RULE defense-in-depth) | Architectural | Accepted | Phase1 | Security Lead | ADR-0038; Phase 7 insert-only | ADR-0038 |
| DEC-0044 | Audit read API + clearance model (tenant admin own tenant; compliance officer all; external auditor redacted; cursor pagination; meta-audit cut-off) | Architectural | Accepted | Phase1 | Architecture Lead | ADR-0039; Phase 7 audit read | ADR-0039 |
| DEC-0045 | Outbox pattern + relay strategy (polling 50ms, SELECT FOR UPDATE SKIP LOCKED, at-least-once, per-aggregate ordering, backpressure, schema-versioned payloads, replay) | Architectural | Accepted | Phase1 | Architecture Lead | ADR-0040; Phase 8 outbox | ADR-0040 |
| DEC-0046 | Inbox dedup + consumer semantics (inbox table with (message_id, consumer_id) PK, ON CONFLICT DO NOTHING, same-transaction insertion, cleanup) | Architectural | Accepted | Phase1 | Architecture Lead | ADR-0041; Phase 8 inbox | ADR-0041 |
| DEC-0047 | DLQ + poison criteria + monitoring (N=3 retries, deserialization failure, terminal error, TTL exceeded; Redis Stream or Postgres; alerting; replay) | Architectural | Accepted | Phase1 | Architecture Lead | ADR-0042; Phase 8 DLQ | ADR-0042 |
| DEC-0048 | Idempotency keys + cross-service propagation (client Idempotency-Key header UUIDv4, 24h TTL, conflict handling, same-transaction insertion, cross-service header) | Architectural | Accepted | Phase1 | Architecture Lead | ADR-0043; Phase 8 idempotency | ADR-0043 |
| DEC-0049 | State machine library + transition pattern (django-fsm, declarative transitions, guard pattern, side-effect hooks, optimistic locking, every transition audited) | Architectural | Accepted | CrossCutting | Architecture Lead | ADR-0044; Phase 8 state machine | ADR-0044 |
| DEC-0050 | Notifications port + adapter vendors (send(channel, recipient, content, context) -> SendResult; email + SMS in scope; push/webhook deferred; vendor per Q5; fallback) | Architectural | Accepted | Phase1 | Architecture Lead | ADR-0045; Phase 8 notifications | ADR-0045 |
| DEC-0051 | MarketingGate + suppression + caps + send-type taxonomy (joins suppression + caps at send time; transactional bypasses suppression respects caps; marketing respects both; only place sends are gated; every decision audited) | Architectural | Accepted | Phase1 | Architecture Lead | ADR-0046; Phase 8 MarketingGate | ADR-0046 |
| DEC-0052 | Player entity model + User relationship (separate entity, optionally linked to User; tenant-scoped; multi-tenant player decision documented; PII per extended register; lifecycle FSM) | Architectural | Accepted | Phase4-7 | Product Owner | ADR-0047; Phase 9 players | ADR-0047 |
| DEC-0053 | Consent schema + jurisdiction-aware fields (id, player_id, tenant_id, purpose catalog, channel, status, granted_at, revoked_at, policy_version, consent_text_hash, ip_address, user_agent, correlation_id; jurisdiction extensions) | Architectural | HUMAN-APPROVED | Phase4-7 | Product Owner | ADR-0048; Phase 9 consent schema; HUMAN-APPROVED sign-off (Legal) | ADR-0048 |
| DEC-0054 | Consent immutability pattern (hash-chained reusing Phase 7 infra; chain verifier extended; revocation creates NEW record not mutation) | Architectural | Accepted | Phase4-7 | Architecture Lead | ADR-0049; Phase 9 consent immutability | ADR-0049 |
| DEC-0055 | Player lifecycle FSM (states: prospect, registered, active, suspended, self_excluded, dormant, closed, deleted; transitions with regulatory constraints; every transition audited; outbox events) | Architectural | HUMAN-APPROVED | Phase4-7 | Product Owner | ADR-0050; Phase 9 player FSM; HUMAN-APPROVED sign-off (Legal) | ADR-0050 |
| DEC-0056 | Retention model + jurisdiction-aware schedule + DSAR + right-to-erasure (default schedule per data class; jurisdiction overrides; GDPR Art. 15 + 17; retention enforcement job; legal hold; archival Q5-blocked) | Architectural | HUMAN-APPROVED | Phase4-7 | Product Owner | ADR-0051; Phase 9 retention; HUMAN-APPROVED sign-off (Legal) | ADR-0051 |
| DEC-0057 | KYC case FSM (16 states; regulatory constraints PEP→EDD, sanctions→escalate, risk>threshold→EDD; re-verification triggers; Phase 8 state machine base; hash-chained) | Architectural | HUMAN-APPROVED | Phase4-7 | Compliance Lead | ADR-0052; Phase 10 KYC FSM; HUMAN-APPROVED sign-off (Legal) | ADR-0052 |
| DEC-0058 | Document model + versioning + retention (per-document versions; each immutable; supersession audited; one active per player+doc_type; superseded retained per Phase 9 schedule) | Architectural | Accepted | Phase4-7 | Architecture Lead | ADR-0053; Phase 10 documents | ADR-0053 |
| DEC-0059 | Storage port + backend Q5-blocked (put/get/delete/head; per-document encryption key; application-level proxy; Object Lock/WORM for legal hold; retention aligned with Phase 9) | Architectural | Accepted | Phase4-7 | Infrastructure Lead | ADR-0054; Phase 10 storage | ADR-0054 |
| DEC-0060 | Synchronous revocation — soft-delete + cryptographic shredding (DB view unretrievability + DEK deletion in same transaction; supersession ≠ revocation) | Architectural | Accepted | Phase4-7 | Security Lead | ADR-0055; Phase 10 revocation | ADR-0055 |
| DEC-0061 | AML/CFT framework (RBA rule-based; PEP/sanctions screening Q5-blocked stub; SoF/SoW evidence; affordability Q1/Q5-blocked; ongoing monitoring; SAR flow with MLRO + tipping-off prohibition) | Architectural | HUMAN-APPROVED | Phase4-7 | Compliance Lead | ADR-0056; Phase 10 AML/CFT; HUMAN-APPROVED sign-off (Legal) | ADR-0056 |
| DEC-0062 | KYC vendor integration Q5-blocked (vendor choice Q5; stub adapter for dev; fallback strategy; liveness check for selfie) | Architectural | Accepted | Phase4-7 | Compliance Lead | ADR-0057; Phase 10 vendor | ADR-0057 |
| DEC-0063 | Review queue + workflow + SLA + escalation (per-tenant/risk-tier queue; reviewer assignment; SLA tracking; reviewer notes audited; escalation reviewer→senior→MLRO; MLRO decisions regulator-reportable; concurrency) | Architectural | HUMAN-APPROVED | Phase4-7 | Compliance Lead | ADR-0058; Phase 10 review queue; HUMAN-APPROVED sign-off (Legal) | ADR-0058 |
| DEC-0064 | Q1–Q5 Increment 1+2 Non-Blocking Acceptance (accept Q1/Q2/Q4/Q5 as non-blocking for Phases 1-14; conditions enumerated; HUMAN-APPROVED) | Business | HUMAN-APPROVED | Foundational | CTO | Phase 0 Evidence Pack; HUMAN-APPROVED sign-off | none |
| DEC-0065 | Ledger Architecture (Journal + Lines; double-entry; append-only; integer minor units; 6 posting invariants) | Architectural | HUMAN-APPROVED | Phase11 | Architecture Lead | ADR-0059; Phase 11 ledger; HUMAN-APPROVED sign-off (CFO) | ADR-0059 |
| DEC-0066 | Balance Derivation & Authorization-Read Rule (derived from journal_line; display reads projection; auth reads under row lock) | Architectural | HUMAN-APPROVED | Phase11 | Architecture Lead | ADR-0060; Phase 11 balance; HUMAN-APPROVED sign-off (CFO) | ADR-0060 |
| DEC-0067 | Overdraft Policy per Account Class (player no overdraft CHECK>=0; house/settlement/suspense overdraft allowed) | Architectural | HUMAN-APPROVED | Phase11 | Compliance Lead | ADR-0061; Phase 11 overdraft; HUMAN-APPROVED sign-off (Compliance) | ADR-0061 |
| DEC-0068 | Currency Exponents & Migration Strategy (per-ISO-4217 exponents; per-line exponent_at_time; migration plan) | Architectural | HUMAN-APPROVED | Phase11 | Treasury Lead | ADR-0062; Phase 11 exponents; HUMAN-APPROVED sign-off (Treasury) | ADR-0062 |
| DEC-0069 | Reversals & Restatements (terminal reversals; source_ref; no double-reversal; restatements are new entries) | Architectural | HUMAN-APPROVED | Phase11 | Architecture Lead | ADR-0063; Phase 11 reversals; HUMAN-APPROVED sign-off (CFO) | ADR-0063 |
| DEC-0070 | FX Rate Snapshots (immutable, insert-only; locked at posting time; volatility monitoring) | Architectural | HUMAN-APPROVED | Phase11 | Treasury Lead | ADR-0064; Phase 11 FX snapshots; HUMAN-APPROVED sign-off (Treasury) | ADR-0064 |
| DEC-0071 | Financial Audit Chain (separate WORM; SHA-256 hash-chain; noventra_auditor role; 7y retention; separate from operational chain) | Architectural | HUMAN-APPROVED | Phase11 | Architecture Lead | ADR-0065; Phase 11 financial audit chain; HUMAN-APPROVED sign-off (CFO) | ADR-0065 |

| DEC-0072 | PCI Boundary (SAQ-A / Hosted Fields) — card data never touches Noventra DOM, servers, or logs | Regulatory | HUMAN-APPROVED | Phase12+ | CTO | ADR-0072; PCI SSC SAQ-A | ADR-0072 |
| DEC-0073 | Payment Order Model & FSM (deposit + withdrawal FSMs; KYC gate for withdrawals; Phase 8 state machine base) | Architectural | HUMAN-APPROVED | Phase12+ | Product Owner | ADR-0073; Phase 12 payment orders | ADR-0073 |
| DEC-0074 | PSP Port & Sandbox Strategy (PspPort interface; sandbox adapter for dev; real vendor Q5-blocked) | Architectural | HUMAN-APPROVED | Phase12+ | API Owner | ADR-0074; Phase 12 PSP port | ADR-0074 |
| DEC-0075 | Webhook Signatures & Replay Protection (HMAC-SHA256; timestamp tolerance; nonce cache; Phase 8 inbox dedup) | Security | HUMAN-APPROVED | Phase12+ | Security Lead | ADR-0075; Phase 12 webhooks | ADR-0075 |
| DEC-0076 | Chargeback Disputes & Evidence Packs (DisputeCase FSM; auto evidence generation; 7y retention; deadline enforcement) | Regulatory | HUMAN-APPROVED | Phase12+ | Legal Lead | ADR-0076; Phase 12 chargebacks | ADR-0076 |
| DEC-0077 | Payment-to-Ledger Posting Contract (exactly-once; same DB transaction; idempotency; FX locking; reconciliation) | Financial | HUMAN-APPROVED | Phase12+ | CFO | ADR-0077; Phase 12 payment-ledger | ADR-0077 |
| DEC-0078 | Bonus Offer Model + FSM + Synchronous Revocation (7 offer types; state FSM; revoked=unretrievable same transaction; RealtimePort invalidation) | Architectural | HUMAN-APPROVED | Phase12+ | Product Owner | ADR-0078; Phase 13 bonus offers | ADR-0078 |
| DEC-0079 | Bonus Award Model + Wagering Requirements + Max Bet (wagering multiplier; game-class contributions; max bet during wagering; bonus-first consumption; conversion to real) | Architectural | HUMAN-APPROVED | Phase12+ | Product Owner | ADR-0079; Phase 13 bonus awards | ADR-0079 |
| DEC-0080 | Bonus Abuse Detection (multi-account, velocity, KYC mismatch; rule-based detection; flag + freeze) | Security | HUMAN-APPROVED | Phase12+ | Security Lead | ADR-0080; Phase 13 abuse detection | ADR-0080 |
| DEC-0081 | RGPort + JurisdictionPort Stub Interfaces (Phase 14 implements real adapters; stubs permissive in Phase 13) | Architectural | HUMAN-APPROVED | Phase12+ | Compliance Lead | ADR-0081; Phase 13 port stubs | ADR-0081 |
| DEC-0082 | RealtimePort Stub Interface (Phase 22 implements real WebSocket fan-out; stub logs+no-op in Phase 13) | Architectural | HUMAN-APPROVED | Phase12+ | Infrastructure Lead | ADR-0082; Phase 13 realtime stub | ADR-0082 |
| DEC-0083 | Bonus→Ledger Posting Contract (award=credit bonus balance; conversion=debit bonus/credit real; forfeiture=debit bonus/credit house; same DB transaction) | Financial | HUMAN-APPROVED | Phase12+ | CFO | ADR-0083; Phase 13 bonus-ledger | ADR-0083 |
| DEC-0084 | Player Protection Limits Model (Deposit, Loss, Wagering, Session; tightening instant, loosening cooling-off; jurisdiction mandates) | Regulatory | HUMAN-APPROVED | Phase12+ | Product Owner | ADR-0084; Phase 14 limits | ADR-0084 |
| DEC-0085 | Self-Exclusion + Cooling-off + SE-survives-erasure (HMAC pseudonymization; cross-module enforcement Law 18; reactivation cooling-off) | Regulatory | HUMAN-APPROVED | Phase12+ | Compliance Lead | ADR-0085; Phase 14 self-exclusion | ADR-0085 |
| DEC-0086 | Reality Checks Model + Enforcement (UK GC mandate; client timer + server enforcement; configurable interval) | Regulatory | HUMAN-APPROVED | Phase12+ | Product Owner | ADR-0086; Phase 14 reality checks | ADR-0086 |
| DEC-0087 | Jurisdiction Policy Engine (per-jurisdiction rules; bonus eligibility; limit mandates; SE cooling-off; configurable) | Regulatory | HUMAN-APPROVED | Phase12+ | Compliance Lead | ADR-0087; Phase 14 jurisdiction | ADR-0087 |
| DEC-0088 | Geo Port + VPN/Proxy Detection (Q5-blocked stub; MaxMind/IPQualityScore patterns; geo-fencing) | Security | HUMAN-APPROVED | Phase12+ | Security Lead | ADR-0088; Phase 14 geo port | ADR-0088 |
| DEC-0089 | Kill-Switch Architecture + <200ms SLO + Fan-out (regulator-mandated; commit→WS disconnect; ASGI consumer; HALT all play) | Regulatory | HUMAN-APPROVED | Phase12+ | Infrastructure Lead | ADR-0089; Phase 14 kill switch | ADR-0089 |
| DEC-0090 | Round-Voiding Hooks Port Interface (Phase 15 implements; void round on SE/kill-switch/reality-check-fail) | Architectural | HUMAN-APPROVED | Phase12+ | Architecture Lead | ADR-0090; Phase 14 round-voiding | ADR-0090 |
| DEC-0091 | Real-Time Infrastructure (Phase 22 pulled forward; ASGI WebSocket server; kill-switch consumer; <200ms SLO) | Architectural | HUMAN-APPROVED | Phase12+ | Infrastructure Lead | ADR-0091; Phase 14 realtime | ADR-0091 |
| DEC-0092 | Phase 14 Scope Deviation (Phase 22 real-time pulled forward to meet <200ms Kill Switch SLO) | Business | HUMAN-APPROVED | Foundational | CTO | Phase 14 scope deviation; HUMAN-APPROVED | none |
| DEC-0093 | Game Round Model + FSM + Bet→Ledger Posting (round lifecycle; bet acceptance; outcome; settlement; Phase 11 ledger continuity; Phase 13 wagering continuity) | Architectural | HUMAN-APPROVED | Phase12+ | Product Owner | ADR-0092; Phase 15 game rounds | ADR-0092 |
| DEC-0094 | Real RoundVoidingAdapter (replaces Phase 14 stub; actual bet returns via Phase 11 ledger reversal; called by kill switch + SE + reality check) | Architectural | HUMAN-APPROVED | Phase12+ | Architecture Lead | ADR-0093; Phase 15 round voiding | ADR-0093 |
| DEC-0095 | Game Session WebSocket Consumer (builds on Phase 14 real-time infra; player session; bet stream; outcome push; disconnect on kill switch) | Architectural | HUMAN-APPROVED | Phase12+ | Infrastructure Lead | ADR-0094; Phase 15 game sessions | ADR-0094 |
| DEC-0096 | Deterministic Sandbox — Same Code Path + Seeded RNG (sandbox runs production domain code with deterministic adapters; seed logged on round initiation; replay test against production code path) | Architectural | HUMAN-APPROVED | Phase12+ | Architecture Lead | ADR-0095; Phase 15 sandbox determinism | ADR-0095 |
| DEC-0097 | Realtime Seam — Extends Phase 14 Infrastructure (single connection registry + Redis pub/sub; GameSessionConsumer subclasses same base as KillSwitchConsumer; new consumers get kill-switch disconnect for free) | Architectural | HUMAN-APPROVED | Phase12+ | Infrastructure Lead | ADR-0096; Phase 15 realtime seam | ADR-0096 |
| DEC-0098 | Provider Callback Validation — HMAC + Replay + Idempotency (HMAC-SHA256 constant-time verify; 5min timestamp tolerance + Redis nonce cache; Phase 8 inbox dedup by (tenant, provider, event_id); order-of-gates mandatory) | Security | HUMAN-APPROVED | Phase12+ | Security Lead | ADR-0097; Phase 15 callback validation | ADR-0097 |
| DEC-0099 | RoundVoidingPort Real Adapter + Provider Outage Wallet Protection (RealRoundVoidingAdapter reverses ledger entries via Phase 11 ReversalService; provider-outage monitor Celery task with 60s grace window; linter rule 115 forbids stub in prod) | Architectural | HUMAN-APPROVED | Phase12+ | Architecture Lead | ADR-0098; Phase 15 round voiding + outage | ADR-0098 |
| DEC-0100 | Math Version Model — Immutability + Hash Verification (insert-only trigger per Phase 7; math_config_hash SHA-256 over canonical JSON; verified at round launch; supersession by new row, never mutation) | Regulatory | HUMAN-APPROVED | Phase12+ | Architecture Lead | ADR-0099; Phase 16 math versions | ADR-0099 |
| DEC-0101 | RNG Port + 3 Adapters (ProductionRngAdapter CSPRNG from secrets module; DeterministicRngAdapter seeded for sandbox; CertificationRngAdapter with hash-chained audit log; (seed, call_index) → output determinism; linter rule 124 forbids random.Random in games) | Regulatory | HUMAN-APPROVED | Phase12+ | CTO | ADR-0100; Phase 16 RNG port | ADR-0100 |
| DEC-0102 | Game Round Lifecycle — Math Version Lock + RNG Seed Lock + Round Hash (math_version_uuid + math_config_hash + rng_seed_hex locked at initiation; round_hash SHA-256 over (math_version_hash, rng_seed, bet_config, outcome); verified at audit reads) | Regulatory | HUMAN-APPROVED | Phase12+ | Architecture Lead | ADR-0101; Phase 16 round lifecycle | ADR-0101 |
| DEC-0103 | Certification Evidence + Lab Registry + Auto-Suspend on Expiry (LabRegistry configurable per jurisdiction; CertificationEvidence stored via Phase 10 immutable storage port; daily Celery task; 30-day pre-alert; auto-suspend on expiry voids active rounds) | Regulatory | HUMAN-APPROVED | Phase12+ | Compliance Lead | ADR-0102; Phase 16 certification | ADR-0102 |
| DEC-0104 | Release FSM with Evidence-Gated Transitions (9 states: draft→math_configured→rng_certified→math_certified→lab_tested→ready_for_release→published→suspended/revoked; no skipping; each transition requires specific evidence; operator approval gate) | Regulatory | HUMAN-APPROVED | Phase12+ | Product Owner | ADR-0103; Phase 16 release FSM | ADR-0103 |
| DEC-0105 | Bifurcated Truth — Domain Events vs Telemetry Pipeline (two physically separate pipelines; is_truth: true/false metadata label on every event; telemetry cannot be source of truth for consequential decisions; linter rules 141-142 enforce cross-contamination prevention) | Financial | HUMAN-APPROVED | Phase12+ | CFO + External Auditor + Reliability Owner | ADR-0104; Phase 17 bifurcated truth; Law 6 | ADR-0104 |
| DEC-0106 | Schema Registry — Versioning, Compatibility, Validation (EventSchema model with semver, compatibility_mode backward/forward/full/none, validation at publish time, drift detection; linter rules 137-138 enforce registration + validation) | Architectural | HUMAN-APPROVED | Phase12+ | API Owner + Reliability Owner | ADR-0105; Phase 17 schema registry | ADR-0105 |
| DEC-0107 | Consumer Registry + Idempotency + Lag Monitoring + DLQ (EventConsumer model; per-consumer inbox tables for exactly-once-effect; lag monitoring Celery beat task with 1000-msg/60s threshold; DLQ after N=3 retries with replay command) | Architectural | HUMAN-APPROVED | Phase12+ | Reliability Owner | ADR-0106; Phase 17 consumer registry; Phase 8 inbox extension | ADR-0106 |
| DEC-0108 | Read Models — GGR/NGR Projections, Refresh Strategies, Reconciliation (4 read models: GGR/NGR/player_activity/financial_summary; real_time + scheduled refresh; daily reconciliation against Phase 11 ledger; mismatch → HALT; linter rules 143-144 enforce RLS + reconciliation) | Financial | HUMAN-APPROVED | Phase12+ | CFO + External Auditor | ADR-0107; Phase 17 read models | ADR-0107 |
| DEC-0109 | GGR/NGR Model & Regulatory Reporting (GGR=sum(bets)-sum(wins); NGR=GGR-bonuses-fees; per-jurisdiction + per-game-class breakdown; source of truth is Phase 11 ledger not telemetry; RegulatoryReport model with reconciliation_passed flag; linter rule 145 enforces ledger-reconciled source) | Regulatory | HUMAN-APPROVED | Phase12+ | CFO + Compliance Officer + Legal Counsel | ADR-0108; Phase 17 GGR/NGR regulatory reporting | ADR-0108 |
| DEC-0110 | Risk Signal Model + 12-type Signal Catalog + Rule-Based Generation (velocity/structural/behavioral/jurisdictional/linked; scheduled 5min + real-time outbox consumer; rule-based explainable not ML; severity escalation; linter rules 147-148 enforce catalog + TM rules) | Regulatory | HUMAN-APPROVED | Phase12+ | Security Owner + Compliance Officer | ADR-0109; Phase 18 risk signals; FATF | ADR-0109 |
| DEC-0111 | TM Rules Engine + Rule Evaluation + Per-Jurisdiction Thresholds (5 rule types: threshold/velocity/structural/behavioral/jurisdictional; scheduled 5min + real-time; per-jurisdiction config Q1-blocked; risk scoring cumulative; rule versioning + audit; linter rule 148) | Regulatory | HUMAN-APPROVED | Phase12+ | Compliance Officer + Legal Counsel | ADR-0110; Phase 18 TM rules; FATF Rec 20 | ADR-0110 |
| DEC-0112 | SAR/STR Workflow + MLRO Decision + FIU Submission + Tipping-off Prohibition (SARCase FSM: draft→mlro_review→filed→closed/dismissed; MLRO single named human with personal legal liability; tipping-off prohibition criminal liability; MLRO-only visibility; retention 5-10 years; linter rules 149/155/158) | Regulatory | HUMAN-APPROVED | Phase12+ | MLRO + Legal Counsel | ADR-0111; Phase 18 SAR/STR; FATF; UK MLR 2017; US BSA; criminal liability | ADR-0111 |
| DEC-0113 | Risk Case Management + Evidence Aggregation + Case Linking (RiskCase 6-state FSM; 5 case types: aml/fraud/rg/bonus_abuse/payment_dispute; evidence JSONB aggregated from Phase 10/11/12/13/14/15/16/18; bidirectional case linking; linter rule 151) | Regulatory | HUMAN-APPROVED | Phase12+ | Compliance Officer | ADR-0112; Phase 18 risk cases | ADR-0112 |
| DEC-0114 | Punitive Action Approval + Dual Control + Audit (5 action types: account_freeze/closure/bonus_clawback/payment_block/se_block; dual control for high-severity requester!=approver; 2 irreversible se_block+account_closure; reversal = new action insert-only; linter rules 156-157; Law 14 mandate) | Regulatory | HUMAN-APPROVED | Phase12+ | Compliance Officer + MLRO | ADR-0113; Phase 18 punitive actions; Law 14 | ADR-0113 |
| DEC-0115 | Player Appeal Workflow + Reversal (Appeal 5-state FSM: submitted→under_review→upheld/overturned/rejected; appeal window per jurisdiction Q1-blocked; separation of duties reviewer!=original approver; tipping-off extends to appeal notifications; reversal for reversible actions only; linter rule 153) | Regulatory | HUMAN-APPROVED | Phase12+ | Compliance Officer + Legal Counsel | ADR-0114; Phase 18 appeals; regulator-mandated some jurisdictions | ADR-0114 |
| DEC-0116 | LLM Gateway — Provider Abstraction, Routing, Rate Limiting, Cost & Degradation L0-L4 (LLMProviderPort interface; adapters for OpenAI/Anthropic/Google/local; StubLLMAdapter for dev Q5-blocked; per-tenant budget enforcement 80% alert/100% hard cutoff→L3; distress short-circuit bypasses AI <50ms; linter rules 159/161) | Technical | HUMAN-APPROVED | Phase12+ | Reliability Owner + CFO | ADR-0115; Phase 19 LLM gateway; Law 16 | ADR-0115 |
| DEC-0117 | Prompt Template Versioning (PromptTemplate semver versioning; insert-only per Phase 7; A/B testing two active versions traffic split; rollback audit logged; every LLM call records prompt_template_id; missing variable = hard fail; linter rule 160) | Technical | HUMAN-APPROVED | Phase12+ | Product Owner | ADR-0116; Phase 19 prompt versioning | ADR-0116 |
| DEC-0118 | Knowledge Chunk Model + Lifecycle + Synchronous Revocation (KnowledgeChunk with pgvector embedding; lifecycle FSM draft→active→superseded/revoked; Law 10 synchronous revocation DB trigger; Law 22 realtime invalidation via RealtimePort; embedding_model_version NOT NULL; ReindexJob; linter rules 162-164) | Regulatory | HUMAN-APPROVED | Phase12+ | Compliance Officer | ADR-0117; Phase 19 knowledge chunks; Law 10; Law 22 | ADR-0117 |
| DEC-0119 | Prefiltered Hybrid Retrieval (Law 2; pgvector + FTS) (prefiltered query: tenant_id + jurisdiction + language + lifecycle=active INSIDE the SQL WHERE clause; post-retrieval filtering is SECURITY VIOLATION; hybrid scoring 0.7 semantic + 0.3 FTS configurable; per-tenant filtered index; linter rules 165-167) | Security | HUMAN-APPROVED | Phase12+ | Security Owner + Reliability Owner | ADR-0118; Phase 19 prefiltered retrieval; Law 2; errata E3 | ADR-0118 |
| DEC-0120 | Machine-Assembled Citations (Law 12; Claim-Level Grounding) (LLM never names citations; Claim-Level Grounder NLI/span mapping; Citation Builder attaches real chunk_ids verified against retrieved set; ungrounded claims hard fail; linter rules 168-169 enforce LLM citation prohibition) | Security | HUMAN-APPROVED | Phase12+ | Security Owner + Compliance Officer | ADR-0119; Phase 19 citations; Law 12 | ADR-0119 |
| DEC-0121 | TruthConsistencyValidator (Law 13; SQL Fact Checking; Hard Fail) (6 fact types: balance/payment/KYC/RG/bonus/round; SQL queries against Phase 11/12/10/14/13/15-16; CONSISTENT/CONTRADICTION/UNVERIFIABLE; contradiction=hard fail + safe fallback + incident signal; pure function <200ms p99; linter rules 172-173) | Financial | HUMAN-APPROVED | Phase12+ | CFO + External Auditor | ADR-0120; Phase 19 truth consistency; Law 13; financial integrity | ADR-0120 |
| DEC-0122 | LLM Evaluation Suite (Regression, Injection, Hallucination, Citation, Truth) (5-type eval suite; golden datasets per query/tenant/jurisdiction; continuous CI on every model/prompt change; nightly full suite; property-based Hypothesis tests; targets: regression<5%, injection 100% rejection, hallucination<1%, citation>95%, truth 0% contradiction) | Technical | HUMAN-APPROVED | Phase12+ | QA Owner + Security Owner | ADR-0121; Phase 19 evals | ADR-0121 |
| DEC-0123 | Cost Accounting (Per-Request, Per-Tenant, Budget Enforcement) (LLMCostRecord insert-only; per-request tokens×rate; per-tenant monthly budget 80% alert/100% hard cutoff→L3; per-prompt-version A/B cost comparison; monthly chargeback cost×1.2 markup; grace period 1h for in-flight; linter rule 161) | Financial | HUMAN-APPROVED | Phase12+ | CFO | ADR-0122; Phase 19 cost accounting; B2B chargeback | ADR-0122 |
| DEC-0124 | EU AI Act Model Inventory (Risk Classification; Unacceptable Prohibited) (AIModel registry: minimal/limited/high/unacceptable; unacceptable PROHIBITED linter rule 170; high-risk requires technical docs+risk assessment+conformity declaration; unregistered models prohibited linter rule 171; Q21 retention AI classification OPEN default high-risk; linter rules 170-171) | Regulatory | HUMAN-APPROVED | Phase12+ | Compliance Officer + Legal Counsel | ADR-0123; Phase 19 EU AI Act; Q21 | ADR-0123 |
| DEC-0125 | Anchored RAG Pipeline (10 Steps; Integrated End-to-End) (Step 1 Unified Router + distress short-circuit; Step 2 Retrieval Planner; Step 3 Prefiltered Hybrid Retrieval; Step 4 Ingestion Sandbox; Step 5 LLM Answer Composer; Step 6 Claim-Level Grounder; Step 7 TruthConsistencyValidator; Step 8 Output Guardrails; Step 9 Citation Builder; Step 10 Safe Renderer; Laws 11/12/13/2/16/6/22; <5s p99) | Architectural | HUMAN-APPROVED | Phase12+ | Security Owner + Compliance Officer + External Auditor | ADR-0124; Phase 19 RAG pipeline; Blueprint §6; Laws 11/12/13 | ADR-0124 |
| DEC-0126 | Agent Registry (9 Agents from DEC-0022) + Shadow→Live Promotion (AgentDefinition model; 9 agents per blueprint §7; allowed_tools + forbidden_tools defense-in-depth; shadow→live promotion gate via PromotionEvidence; status FSM shadow→live→suspended; linter rule 176 no live without promotion; Law 14) | Regulatory | HUMAN-APPROVED | Phase12+ | Product Owner + Compliance Officer | ADR-0125; Phase 20 agent registry; Law 14; DEC-0022; blueprint §7 | ADR-0125 |
| DEC-0127 | Typed Tools — Registry, Schemas, Mapped Service Methods, No Superuser, No Direct DB Writes (AgentTool model with JSON Schema input/output; mapped_service_method deterministic Python; agents run as service identities typ=service Phase 6; no BYPASSRLS; all writes via service methods enforcing Phase 11/7/5/8 invariants; linter rule 177) | Security | HUMAN-APPROVED | Phase12+ | Security Owner + Architecture Lead | ADR-0126; Phase 20 typed tools; Law 14 | ADR-0126 |
| DEC-0128 | Approval Gates (Law 14; High-Risk Requires Human Approval) (AgentApproval 5-state FSM: pending→approved/rejected→executed/expired; SLA enforcement default 24h per-gate configurable; dual control agent!=approver; high-risk tools: journey_queue/bonus_recommend/evidence_summarize_for_sar/test_approve/code_merge/report_external; linter rule 178) | Regulatory | HUMAN-APPROVED | Phase12+ | Compliance Officer + MLRO | ADR-0127; Phase 20 approval gates; Law 14; regulator-mandated | ADR-0127 |
| DEC-0129 | Execution Logs (Audit Trail; Link to LLM Calls + Correlation_ID) (AgentExecutionLog immutable insert-only Law 9; 5 statuses success/failed/denied/pending_approval/expired; links to Phase 19 llm_call_id + Phase 4 correlation_id + Phase 20 approval_id; hash-chained into Phase 7 audit; queryable per agent/tool/player/correlation; linter rules 183-185) | Security | HUMAN-APPROVED | Phase12+ | Security Owner + External Auditor | ADR-0128; Phase 20 execution logs; Law 9; Law 14 | ADR-0128 |
| DEC-0130 | Retention Agent Bounds (Law 18; Excluded/Cooling-off/Caps/Bonus) (4-level defense-in-depth: L1 tool registry excludes protection-modifying; L2 segment query RGPort check per-player; L3 MarketingGate suppression+caps+consent; L4 4 negative tests; May NOT target excluded/cooling-off, set bonus values, queue breaching caps; linter rules 179-181) | Regulatory | HUMAN-APPROVED | Phase12+ | Compliance Officer + Legal Counsel | ADR-0129; Phase 20 retention bounds; Law 18; blueprint §7 | ADR-0129 |
| DEC-0131 | Agent Runtime (Orchestration; LLM Integration; Outbox Events) (AgentRuntime pure-function composition: trigger→LLM→tool_check→approval→execute→log→outbox; Phase 19 LLM Gateway integration; Phase 8 outbox events; degradation L0-L4 per-agent; distress short-circuit <100ms mandatory for RG Triage; linter rule 182 forbidden tool denied) | Architectural | HUMAN-APPROVED | Phase12+ | Reliability Owner + Architecture Lead | ADR-0130; Phase 20 agent runtime; Phase 19 LLM Gateway; Phase 8 outbox | ADR-0130 |
| DEC-0132 | Compliance Control Framework (Model, Framework Mapping, Testing) (ComplianceControl model with 6 frameworks: ISO_27001/SOC_2/UK_GC_LCCP/MGA_BLC/GDPR/AML; ControlFrameworkMapping multi-framework; scheduled testing pass/fail/remediation; named owner per control; linter rule 191; Star Ocean Casino £5M fine cited) | Regulatory | HUMAN-APPROVED | Phase12+ | Compliance Officer + External Auditor | ADR-0131; Phase 21 compliance controls; UK GC LCCP; MGA BLC; GDPR; ISO 27001; SOC 2 | ADR-0131 |
| DEC-0133 | Evidence Repository (Immutable Storage; Retention; Access Audit) (ComplianceEvidence model via Phase 10 storage port WORM; immutable Law 9 + SEC 17a-4; EvidenceAccessLog insert-only; retention 5-10y Q1-blocked; supersession not deletion; linter rules 192-193; 2021 SEC $70M tampering fine cited) | Regulatory | HUMAN-APPROVED | Phase12+ | Compliance Officer + External Auditor | ADR-0132; Phase 21 evidence repository; Law 9; SEC 17a-4 | ADR-0132 |
| DEC-0134 | Periodic Compliance Reviews (Cadence, Findings, Remediation) (ComplianceReview 4 types: internal_audit annual/external_audit annual/regulator_inspection ad-hoc/self_assessment quarterly; findings with severity+owner+due_date+remediation_status; escalation overdue/critical/repeated; linter rule 195; Casino Royale £2M untracked findings cited) | Regulatory | HUMAN-APPROVED | Phase12+ | Compliance Officer + Legal Counsel | ADR-0133; Phase 21 compliance reviews | ADR-0133 |
| DEC-0135 | Reporting Adapters (Per-Jurisdiction; Per-Report-Type; Submission) (ReportingAdapter interface per-jurisdiction; 7 report types GGR/NGR/AML_CTR/AML_SAR/RG_SE/RG_LIMITS/KYC_STATS; RegulatoryReport extends Phase 17; submission tracking draft→generated→submitted→acknowledged/rejected; rejection triggers remediation; linter rule 194; BetBright £600K manual reporting error cited) | Regulatory | HUMAN-APPROVED | Phase12+ | CFO + Compliance Officer + Legal Counsel | ADR-0134; Phase 21 reporting adapters; Phase 17 GGR/NGR extension | ADR-0134 |
| DEC-0136 | DSAR Drill (Verify → Export → Shred; Errata E1; SE-Survives-Erasure) (DSARRequest E1 fixed order pending→verified→exported→shredded no skipping; SE-survives-erasure via HMAC pseudonymization Phase 14 ADR-0085; export pack from 11 modules; statutory window 30 days GDPR Art 12(3); linter rules 186-188; 2023 GDPR €4M fine cited) | Regulatory | HUMAN-APPROVED | Phase12+ | Compliance Officer + Legal Counsel + Privacy Owner | ADR-0135; Phase 21 DSAR drill; errata E1; GDPR Art 12/15/17; Phase 9 + Phase 14 | ADR-0135 |
| DEC-0137 | Legal-Hold Matrix + Vendor Registry with Deterministic Expiry (LegalHold model 4 types litigation/regulatory_investigation/audit/compliance_review; LegalHoldMatrix data_class×jurisdiction×hold_type; VendorRegistry 9 types; blueprint §8.3 deterministic expiry: lab/studio auto-suspend; PSP/KYC/Geo T-30/7/1 + operator decision; daily Celery job; linter rules 189-190; 2021 spoliation + 2022 uncertified KYC vendor cited) | Regulatory | HUMAN-APPROVED | Phase12+ | Compliance Officer + Legal Counsel + External Auditor | ADR-0136; Phase 21 legal-hold + vendor expiry; blueprint §8.3; Law 19 | ADR-0136 |
| DEC-0138 | Segment Model + RGPort Prefiltering (Law 2 Applied to Marketing) (Segment + SegmentMembership models; RGPort.check_self_excluded + check_cooling_off INSIDE segment query before materialization; no cached suppression flag — Suppression Drift cure; nightly rebuild Celery job; on-demand admin trigger; linter rules 196/200; 2022 UK GC £3M suppression incident cited) | Regulatory | HUMAN-APPROVED | Phase12+ | Compliance Officer + Privacy Owner | ADR-0137; Phase 22 segments; Law 2; Law 24; GDPR marketing consent | ADR-0137 |
| DEC-0139 | Journey Orchestration + Multi-Step Flows + Exit Conditions (Journey + JourneyStep + JourneyEnrollment models; 6 exit conditions: self_excluded/unsubscribed/cooling_off/terminal_step/no_consent/DSAR erasure; kill-switch fan-out exits enrollment same-transaction Law 18; DSAR anonymizes enrollment player_uuid NULLed; linter rule 202; 2022 UK GC + 2023 Caesars £2M journey incidents cited) | Technical | HUMAN-APPROVED | Phase12+ | Product Owner + Reliability Owner | ADR-0138; Phase 22 journey orchestration; Law 18 exit | ADR-0138 |
| DEC-0140 | Propensity Features + Feature Store + ML Model Governance (EU AI Act) (PropensityFeature model 5-feature catalog: churn_risk/ltv/deposit_propensity/bonus_sensitivity/rg_risk; nightly feature engineering Celery job; insert-only per model_version; EU AI Act limited risk + transparency; propensity models registered in AIModel Phase 19; linter rules 203-205; 2024 EU AI Act enforcement guidance cited) | Regulatory | HUMAN-APPROVED | Phase12+ | Product Owner + Compliance Officer + Legal Counsel | ADR-0139; Phase 22 propensity features; EU AI Act limited risk; Phase 19 model inventory | ADR-0139 |
| DEC-0141 | MarketingGate Enforcement at Scale (Queue-Time + Send-Time Two-Stage Check) (Stage 1 queue-time: suppression_list + RGPort.check_self_excluded + check_cooling_off; Stage 2 send-time: frequency_caps + consent; deterministic join Law 24 NEVER cached flag; MarketingGate reused no parallel gate; linter rules 197-201; 2021 Bet365 £1M race condition + Suppression Drift pain cited) | Regulatory | HUMAN-APPROVED | Phase12+ | Compliance Officer + Privacy Owner + Legal Counsel | ADR-0140; Phase 22 MarketingGate at scale; Law 24; Law 18; blueprint pain ledger Suppression Drift | ADR-0140 |
| DEC-0142 | Campaign Negative Test Suite (Suppressed, Excluded, Cooling-Off, Caps, Consent) (5 categories 18 tests + 1 comprehensive mixed-segment; CI-enforced every commit + nightly; audit event verification per denial; acceptance criterion: campaign never queues to suppressed/excluded/cooling-off; caps enforced at send time; linter rules 196-205; 2022 UK GC £3M testing deficiency cited) | Regulatory | HUMAN-APPROVED | Phase12+ | Compliance Officer + External Auditor | ADR-0141; Phase 22 negative test suite; Law 24; Law 18; regulator-reportable | ADR-0141 |
| DEC-0143 | Contract Model (B2B Operator Contracts; Versioning; Lifecycle FSM) (Contract + ContractVersion models; 4 contract types: rev_share/fixed_fee/hybrid/white_label; lifecycle FSM draft→active→suspended/terminated/expired; multi-jurisdiction TEXT[]; 7+ year retention; HUMAN-APPROVED Legal Counsel+CFO; linter rule 214; 2023 GAN/Tabcorp A$45M unversioned contract dispute cited) | Business | HUMAN-APPROVED | Phase12+ | Legal Counsel + CFO | ADR-0142; Phase 23 contracts; DEC-0024 B2B OS provider model | ADR-0142 |
| DEC-0144 | Fee Schedule Model (Rev-Share, Fixed, Hybrid, Tiered; Per-Product; Per-Jurisdiction) (FeeSchedule model 4 fee types; JSONB fee_structure per product/game_class/jurisdiction; versioned + immutable insert-only; billing uses schedule effective at billing period not current; HUMAN-APPROVED CFO+Product Owner; linter rule 208; 2022 Pala Interactive $12M hardcoded fee dispute cited) | Business | HUMAN-APPROVED | Phase12+ | CFO + Product Owner | ADR-0143; Phase 23 fee schedules; DEC-0024; iGaming B2B pricing | ADR-0143 |
| DEC-0145 | Rev-Share Invoice Generation (From GGR; Reconciliation; Ledger Posting) (Invoice model insert-only immutable; scheduled monthly job from Phase 17 GGR/NGR; reconciliation job verifies against Phase 11 ledger mismatch→HALT; credit notes Phase 11 terminal reversal; FSM draft→generated→sent→paid→closed; payment integration Phase 12; linter rules 206/211/212/213; 2021 DraftKings $30M unreconciled invoice restatement cited) | Financial | HUMAN-APPROVED | Phase12+ | CFO + External Auditor | ADR-0144; Phase 23 invoices; Phase 17 GGR; Phase 11 ledger; Law 4 | ADR-0144 |
| DEC-0146 | Operator Statements (Financial Reporting; Per-Jurisdiction Breakdown) (OperatorStatement model; GGR/NGR per game_class per jurisdiction; portal+email delivery transactional bypasses MarketingGate; reconciliation against ledger+GGR; acknowledgment tracking; linter rules 209-210; 2022 BetBright £600K inaccurate statement cited) | Financial | HUMAN-APPROVED | Phase12+ | CFO + Compliance Officer | ADR-0145; Phase 23 operator statements; regulator-reportable | ADR-0145 |
| DEC-0147 | Billing Change Audit (Phase 7 Continuity; Hash-Chained; Immutable) (16 billing.* event types; every billing mutation audited linter rule 207; hash-chained into Phase 7 operational audit chain linter rule 215; immutable insert-only; noventra_auditor role SELECT; 7+ year retention; 2020 Wirecard €1.9B opaque billing cited) | Audit | HUMAN-APPROVED | Phase12+ | External Auditor + Compliance Officer | ADR-0146; Phase 23 billing audit; Law 9; Phase 7 audit chain | ADR-0146 |
| DEC-0148 | Partner Key Model (Prefixed, Scoped, Rotatable; Hash Storage) (PartnerKey model; sk_test_/sk_live_ prefix prevents sandbox↔prod confusion blueprint §12; SHA-256 hash storage no plaintext linter rule 216; scope per contract Phase 23; rotation supports breach response; key shown once at creation; linter rules 219/220/225; 2023 Slack $4M + 2022 CircleCI breach cited) | Security | HUMAN-APPROVED | Phase12+ | Security Owner + API Owner | ADR-0147; Phase 24 partner keys; Phase 12 key separation; blueprint §12 | ADR-0147 |
| DEC-0149 | Partner Webhooks (Signed, DLQ, Retry) — Phase 12 Pattern Extended (PartnerWebhook + PartnerWebhookEndpoint models; HMAC-SHA256 signatures Phase 12 ADR-0075 pattern; retry exponential backoff 1min/5min/30min/2hr/6hr; DLQ per partner; 10 event types; per-partner secret key rotation; linter rules 222-223; 2023 Cash App forgery + 2022 Twilio loss cited) | Security | HUMAN-APPROVED | Phase12+ | Security Owner + Reliability Owner | ADR-0148; Phase 24 partner webhooks; Phase 12 ADR-0075; Phase 8 DLQ | ADR-0148 |
| DEC-0150 | Sandbox Tenant (Isolation; Stub Adapters; Self-Provisioning) (tenant.status=sandbox; RLS isolation linter rule 217 no cross-env data; stub adapters Phase 12/19/14; self-provisioning <60s via dev portal; time-limited 30 days; regulatory exclusion Phase 17/21/23; blueprint §21 B2B wedge; 2022 Plaid sandbox leak cited) | Technical | HUMAN-APPROVED | Phase12+ | Product Owner + Security Owner | ADR-0149; Phase 24 sandbox; blueprint §21; industry sandbox patterns | ADR-0149 |
| DEC-0151 | Docs Portal (API Reference; Integration Guides; SDK Docs; Versioned) (MkDocs + OpenAPI drf-spectacular; partner key auth for partner docs linter rule 221; versioned per API version; optional AI search Phase 19 RAG Q5-blocked; 2023 Twilio survey 73% integration failures from poor docs cited) | Technical | HUMAN-APPROVED | Phase12+ | Product Owner + API Owner | ADR-0150; Phase 24 docs portal; Stripe Docs benchmark | ADR-0150 |
| DEC-0152 | Player SDK + Reference Lobby + Conformance Suite (Production-Key Gate) (Player SDK Spec 8 integration areas; open-source reference lobby MIT/Apache; conformance suite 9 categories; production-key gate linter rule 218 non-conforming cannot obtain sk_live_; ADR-0020 closure Phase 2→24; blueprint §21; 2022 FanDuel $2M lost deposits cited) | Regulatory | HUMAN-APPROVED | Phase12+ | Product Owner + Security Owner + External Auditor | ADR-0151; Phase 24 Player SDK; blueprint §21; ADR-0020 conformance gate | ADR-0151 |
| DEC-0153 | Validation Suite (Security + Concurrency + Chaos + Load) (4 suites: security OWASP ASVS L2 + 19 pen scenarios + cross-tenant + tipping-off grep + PCI + AI Boundary + injection; concurrency 6 financial invariants under load; chaos 8 failure injection Netflix-style; load errata E5 capacity table + Kill Switch <200ms; all must pass for GO; 2019 Knight Capital $440M cited) | Quality | HUMAN-APPROVED | Phase12+ | Security Owner + Reliability Owner + External Auditor | ADR-0152; Phase 25 validation; blueprint §14 Stages 26-27; errata E5; Google SRE; Netflix chaos | ADR-0152 |
| DEC-0154 | Vulnerability Scan + Restore Drill + DR Plan (SAST bandit + DAST OWASP ZAP + dependency pip-audit + secret gitleaks + container Trivy + ASV PCI quarterly; restore drill fresh env RTO <4h RPO <15min data integrity verified; DR plan documented quarterly cadence; 2021 Accenture ransomware $400M no restore drill cited) | Security | HUMAN-APPROVED | Phase12+ | Security Owner + External Auditor + Compliance Officer | ADR-0153; Phase 25 vuln scan + DR; PCI DSS; blueprint §19 DoD | ADR-0153 |
| DEC-0155 | SLOs + Incident Response + Release Gates (SLOs blueprint §11 availability 99.9%+ Kill Switch <200ms error budgets Google SRE; incident response 24/7 on-call SEV1/2/3 blameless postmortem Amazon COE quarterly tabletop; 20 release gates all must be GREEN for GO; 2023 CrowdStrike $5.4B no release gate cited) | Reliability | HUMAN-APPROVED | Phase12+ | Reliability Owner + Compliance Officer + CFO | ADR-0154; Phase 25 SLOs + gates; blueprint §11; Google SRE; Amazon COE | ADR-0154 |
| DEC-0156 | Go/No-Go Decision + Launch Authorization (20 release gates all GREEN; 16 named human approvers all signed; Go/No-Go document docs/launch/go-no-go.md; NO-GO if any gate RED or any human unsigned; no auto-approval no partial GO; 2023 FTX $8B no governance cited) | Governance | HUMAN-APPROVED | Phase12+ | CTO + CFO + External Auditor + MLRO + Compliance Officer + Legal Counsel + Privacy Owner + PCI Owner | ADR-0155; Phase 25 Go/No-Go; blueprint §19 DoD; Phase 1 gate pattern; regulator-mandated | ADR-0155 |
| DEC-0157 | Jurisdiction Removal — Global Mode (Remove ALL jurisdiction-specific logic; no JurisdictionPort; no per-jurisdiction rules; no jurisdiction fields; system operates with single global defaults; tenant_id isolation preserved; all 24 Laws preserved) | Governance | HUMAN-APPROVED | Foundational | CTO | User decision 2026-10-29; DEC-0157 | none |
### C.1 Notes on DEC-0022, DEC-0023, DEC-0025, DEC-0026 (self-citation)

DEC-0022, DEC-0023, DEC-0025, and DEC-0026 are self-citing: their
`Source` column carries their own ID. This is intentional and explicit.
These four decisions are governance-layer definitions that have no
upstream authority other than the decision to adopt them. The
self-citation makes the provenance traceable without inventing an
external source. The linter (rule 4) does not flag self-citations
because rule 4 only fires on `Confirmed` status, and all four rows
are `Accepted`.

### C.2 Note on DEC-0024 (HUMAN-APPROVED)

DEC-0024 is the only row in the seed with `HUMAN-APPROVED` status. The
sign-off record (dated 2025-09-15, retained by the Commercial Lead) is
the authoritative evidence. Per linter rule 5, any future
Legal/Regulatory/Licensing/Business/Budget/Vendor row that attains
`Confirmed` status must be upgraded to `HUMAN-APPROVED` and carry an
equivalent sign-off record reference in its `Source` column.

### C.3 Phase 2 additions (DEC-0025, DEC-0026) — narrative

**DEC-0025 — Architecture inventory map.** Mandates that the
governance baseline is composed of (a) the eight Phase 1 requirement
documents under `docs/requirements/` plus `docs/phase-0-evidence.md`
and `docs/BLUEPRINT.md`, and (b) six new Phase 2 files: the five
under `docs/architecture/` (`security.md`, `nfr-allocation.md`,
`capacity-assumptions.md`, `data-classification.md`,
`risk-register.md`) and `docs/adr/INDEX.md`. DEC-0025 is the
authority for any future additions or retirements to this inventory;
the change protocol is the same as the boundary change protocol in
`domain-boundaries.md` §10. The full inventory map is reproduced in
`docs/adr/INDEX.md` §1 and in `docs/stage-handoffs/stage-02-handoff.md`
§3.

**DEC-0026 — ADR Nygard format adoption.** Mandates that every ADR
file under `docs/adr/` carries Nygard-style front-matter
(`ADR`, `Title`, `Status`, `DEC`, `Owner`, `Created`, `Supersedes`,
`Last-Reviewed`) and a body with five sections (`Context`,
`Decision`, `Alternatives`, `Consequences`, `Validation Plan`). The
Phase 1 stubs (which carried a thinner front-matter and body) are
upgraded in Phase 2 to the Nygard format. The status of all 21 stubs
transitions from `Accepted` (Phase 1) to `PROPOSED` (Phase 2) pending
formal review. The linter (rule 10) enforces the Nygard schema.

**DEC-0021 — status review (Phase 2).** DEC-0021 was seeded in Phase 1
as `Accepted` (27 stages → 25 phases). Phase 2 review confirms the
regrouping is still valid: the two merges (MFA + session management
into Phase 7; recon rules + recon runs into Phase 22) remain
correct, and no further merges or splits are required. DEC-0021
remains `Accepted`; the narrative is recorded here per the Phase 2
hard acceptance.

**DEC-0026 — Phase 7 amendment (privacy owner role).** Per Phase 7
spec output #1: "Amend DEC-0026 to add `privacy owner` role
(governance gap)." The Nygard format already requires an `Approver`
line per ADR; the privacy owner role is now a recognized approver
for ADRs in the privacy/redaction category (ADR-0037 redaction
policy). The privacy owner role is distinct from the DPO
(Data Protection Officer, defined in `roles.md` §1): the DPO owns
GDPR compliance; the privacy owner owns the redaction policy and
Merkle-style payload hashing decisions. In small teams, the DPO may
hold both roles. The privacy owner role is ratified in
`roles.md` §1 (Phase 7 update).

**DEC-0026 — Phase 8 amendment (architect role).** Per Phase 8
spec output #1: "Amend DEC-0026 to add `architect` role (governance
gap)." The `architect` role is a recognized approver for ADRs in
the architectural/reliability category (ADR-0040..0046). The
architect role is distinct from the Architecture Lead (who owns
the ADR): the architect role is a peer reviewer who validates
architectural coherence across ADRs. In small teams, the
Architecture Lead may hold both roles. The architect role is
ratified in `roles.md` §1 (Phase 8 update).

**ADR-0014 subject RESOLVED (Phase 8 — chronic deferral loop closed).**
Per Phase 8 spec output #1: "ADR-0014 subject RESOLVED (chronic
deferral loop closed)." ADR-0014 ("Tenant as first-class aggregate
root") was repeatedly deferred (Phase 6 audit F-601, Phase 7 audit
F-701). The subject is now RESOLVED: ADR-0014 covers tenancy (the
Tenant aggregate root), NOT identity/RBAC or audit. It was
implemented in Phase 5 (Tenant model with tenant_uuid PK + RLS).
ADR-0014 transitions to ACCEPTED in Phase 8 (retroactive to Phase
5). The chronic deferral loop is closed; no future audit should
re-raise this question. DEC-0014's status transitions from
`Accepted` (DEC row) to `Accepted` (ADR row, now consistent).

**DEC-0026 — Phase 9 amendment (product owner role).** Per Phase 9
spec output #2: "Amend DEC-0026 to add `product owner` role
(governance gap)." The `product owner` role is a recognized approver
for ADRs in the product/compliance category (ADR-0047 Player entity,
ADR-0048 Consent schema, ADR-0050 Player FSM, ADR-0051 Retention
model). The product owner role is distinct from the Product Lead
(who owns pain-ledger REQs): the product owner owns the player +
consent + retention product decisions. In small teams, the Product
Lead may hold both roles. The product owner role is ratified in
`roles.md` §1 (Phase 9 update).

**ADR-0046 amendment (Phase 9 — consent check added to MarketingGate).**
Per Phase 9 spec output #2: "ADR-0046 (Phase 8) AMENDED to add
consent check to MarketingGate." The Phase 8 MarketingGate
suppressed + capped sends. The Phase 9 amendment adds a consent
check: marketing sends require a valid (granted, not expired, not
revoked) consent for the (player, purpose, channel) tuple. The gate
decision now has 5 outcomes: allow, deny-suppression, deny-cap,
deny-consent, deny-jurisdiction. Transactional sends bypass the
consent check (they are not marketing). HUMAN-APPROVED for this
amendment per linter rule 5 (Business/Legal category).

**DEC-0026 — Phase 10 amendment (compliance officer + MLRO roles).**
Per Phase 10 spec output #2: "Amend DEC-0026 to add `compliance
officer` and `MLRO` roles (governance gap)." The `compliance officer`
role is a recognized approver for ADRs in the compliance/AML category.
The `MLRO` (Money Laundering Reporting Officer) is a **regulator-
mandated human role** — it requires documented appointment per
FATF Recommendation 18 and jurisdictional regulation. The MLRO:
- Owns SAR filing decisions (regulator-reportable).
- Has restricted audit visibility (SAR events are MLRO-only per
  Phase 10 ADR-0058).
- Cannot be a service identity (must be a named human).
- Requires documented appointment evidence (retained per Law-REQ-0009).
The compliance officer role is distinct from the Compliance Lead
(department head): the compliance officer is the operational reviewer.
The MLRO is distinct from both: the MLRO is the legal appointee.
In small teams, the Compliance Lead may hold all three roles, but the
MLRO appointment must be documented separately. Both roles are
ratified in `roles.md` §1 (Phase 10 update).

---

## §D Supersessions

| Old ID | Old label | New ID | New label | Authority | Date |
|---|---|---|---|---|---|
| DEC-001 (v3.1) | Business model (Option A) | DEC-0024 | B2B OS provider business model (Option A) | Errata E1 | 2025-10-27 |
| DEC-0022 (Phase Plan Rev 2) | Semantic definitions; mapping law | DEC-0023 | Semantic definitions; DEC↔ADR mapping law | Errata E2 | 2025-10-27 |

No REQ supersessions in the seed. Future REQ supersessions must record
the old REQ ID, the new REQ ID, the rationale, and the authority (DEC or
erratum) in this section.

---

## §E Open questions summary

There are 27 open questions. Each carries an ID, an owner, and a due
date. Four of them — Q1 (jurisdictions), Q2 (licensing), Q4 (pilot
partner), Q5 (budget) — are BLOCKERS requiring external validation. If
any of those four is BLOCKED at the Phase 0 gate review, the gate
fails and Phase 2 does not start.

The full list lives in `docs/requirements/unresolved-decisions.md`.
This section is a pointer, not a duplicate.
