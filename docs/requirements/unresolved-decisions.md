# Unresolved Decisions — Open Questions Register

| Field | Value |
|---|---|
| Document | `docs/requirements/unresolved-decisions.md` |
| Version | 6.1 (Phase 10 update — Increment 2 second pillar) |
| Status | Approved |
| Owner | Engineering Lead |
| Authority | BLUEPRINT §10; `roles.md` §3 (small-team blocker rule) |

This document lists the open questions that must be resolved (or
explicitly marked BLOCKED) before the Phase 0 gate can pass. The
register was seeded with 27 questions in Phase 1; Phase 2 extends
it with architectural questions (Q28–Q34); Phase 3 extends with
environment naming (Q35), secret strategy (Q36), and CI runner
cost (Q37, Q5-blocked ASSUMED).

Four questions — Q1, Q2, Q4, Q5 — are BLOCKERS requiring external
validation. The small-team blocker rule (`roles.md` §3) escalates
these four to BLOCKED if the named team has fewer than three humans.

Each question has: an ID, a title, an owner, a due date, a status,
dependencies on other questions, and the gate it feeds.

## 1. Status enum for questions

| Status | Meaning |
|---|---|
| Open | Active; owner is working it. |
| Answered | Owner has produced an answer; answer recorded in §3. |
| Blocked | Cannot progress without external validation. |
| Closed | Answer accepted; superseded by a DEC row in `traceability.md`. |

## 2. The questions (Q1–Q34)

The table below is the authoritative register. Per the Phase 2 hard
acceptance, Q1, Q2, Q4, Q5 carry an explicit **carry-over status**
column showing whether they were resolved in Phase 1, carried into
Phase 2, or carried into Phase 3. Phase 2 adds seven architectural
questions (Q28–Q34) that emerged during ADR authoring and risk-
register compilation.

| Q ID | Title | Owner | Due date | Status | Carry-over (Phase 2) | Carry-over (Phase 3) | Depends on | Gate | External validation required |
|---|---|---|---|---|---|---|---|---|---|
| Q1 | Target jurisdictions (countries the provider will operate in) | Legal Lead | Phase 0 gate | Blocked | Carried (still Blocked) | Carried (BLOCKS Phase 3) | — | Legal | Yes — counsel qualified in each target jurisdiction |
| Q2 | Licensing regime per jurisdiction | Legal Lead | Phase 0 gate | Blocked | Carried (still Blocked) | Carried (BLOCKS Phase 3) | Q1 | Legal | Yes — counsel |
| Q3 | Data residency per jurisdiction | Data Protection Officer | Phase 2 start | Open | Carried (Open) | Carried (Open) | Q1 | Legal | Yes — counsel (typically same engagement as Q1) |
| Q4 | Pilot partner identification | Commercial Lead | Phase 0 gate | Blocked | Carried (still Blocked) | Carried (BLOCKS Phase 3) | — | Commercial | Yes — signed letter of intent from a regulated institution |
| Q5 | Budget allocation for Phases 1–3 | Commercial Lead | Phase 0 gate | Blocked | Carried (still Blocked) | Carried (BLOCKS Phase 3) | — | Financial | Yes — funder commitment letter |
| Q6 | Choice of KYC vendor | Compliance Lead | Phase 4–7 start | Open | Carried (Open) | Carried (Open) | Q1 | — | No |
| Q7 | Choice of sanctions/PEP screening vendor | Compliance Lead | Phase 4–7 start | Open | Carried (Open) | Carried (Open) | Q1 | — | No |
| Q8 | Choice of identity provider (IdP) | Identity Lead | Phase 4–7 start | Open | Carried (Open) | Carried (Open) | — | — | No |
| Q9 | Choice of cloud provider | Infrastructure Lead | Phase 2 start | Open | Carried (Open) | Carried (Open) | Q3 | — | No |
| Q10 | Choice of relational database | Architecture Lead | Phase 2 start | Open | Carried (Open); Postgres 16 locked in `stage-02-handoff.md` §3.2 | Resolved (Postgres 16) → close in Phase 3 | — | — | No |
| Q11 | Choice of event store | Architecture Lead | Phase 2 start | Open | Carried (Open); R-VND-06 in `risk-register.md` flags lock-in risk | Carried (Open; Phase 3 evaluation) | Q10 | — | No |
| Q12 | Choice of message bus | Infrastructure Lead | Phase 2 start | Open | Carried (Open) | Carried (Open) | — | — | No |
| Q13 | Workflow engine: build vs buy | Architecture Lead | Phase 8–10 start | Open | Carried (Open) | Carried (Open) | — | — | No |
| Q14 | Audit log retention period per jurisdiction | Compliance Lead | Phase 8–10 start | Open | Carried (Open) | Carried (Open) | Q1 | — | Yes — counsel (jurisdiction-specific) |
| Q15 | SAR/STR submission channel per jurisdiction | Compliance Lead | Phase 11 start | Open | Carried (Open) | Carried (Open) | Q1, Q2 | — | Yes — counsel + jurisdictional FIU |
| Q16 | Currency support list (Phase 1 onward) | Product Lead | Phase 2 start | Open | Carried (Open) | Carried (Open) | — | — | No |
| Q17 | Supported SSO protocols (OIDC vs SAML priority) | Identity Lead | Phase 4–7 start | Open | Carried (Open); both supported per DEC-0004, DEC-0005 | Resolved (both) → close in Phase 4 | — | — | No |
| Q18 | Mobile client requirement | Product Lead | Phase 4–7 start | Open | Carried (Open) | Carried (Open) | — | — | No |
| Q19 | Localization scope (languages) | Product Lead | Phase 4–7 start | Open | Carried (Open) | Carried (Open) | — | — | No |
| Q20 | Multi-tenant vs single-tenant deployment option | Architecture Lead | Phase 2 start | Open | Carried (Open); multi-tenant locked in DEC-0003 | Resolved (multi-tenant via RLS) → close in Phase 3 | Q1, Q3 | — | No |
| Q21 | Backup strategy (frequency, location) | Infrastructure Lead | Phase 2 start | Open | Carried (Open); WF-09 defines daily full + hourly incremental | Resolved (per WF-09) → close in Phase 3 | Q3, Q9 | — | No |
| Q22 | Disaster recovery RTO/RPO targets | Infrastructure Lead | Phase 2 start | Open | Carried (Open); provisional RTO ≤4h, RPO ≤1h in NFR §2.2 | Carried (Open; final targets Phase 3) | Q20 | — | No |
| Q23 | Penetration testing cadence | Security Lead | Phase 2 start | Open | Carried (Open) | Carried (Open) | — | — | No |
| Q24 | Bug bounty program scope | Security Lead | Phase 4–7 start | Open | Carried (Open) | Carried (Open) | — | — | No |
| Q25 | SLA tiers for tenants | Product Lead | Phase 4–7 start | Open | Carried (Open); NFR §2.1 records provisional floor 99.9% | Carried (Open) | — | — | No |
| Q26 | Pricing model | Commercial Lead | Phase 0 gate | Open | Carried (Open) | Carried (Open; BLOCKED if Q4 BLOCKED) | Q4 | Commercial | Yes — pilot partner feedback |
| Q27 | Open-source vs proprietary license for SDK | Legal Lead | Phase 4–7 start | Open | Carried (Open) | Carried (Open) | — | — | Yes — counsel (IP review) |
| Q28 | Event store: EventStoreDB vs Postgres-based vs DynamoDB | Architecture Lead | Phase 3 start | Open | New in Phase 2 (R-VND-06) | Carried (Open; Phase 3 evaluation) | Q11 | — | No |
| Q29 | Service mesh: Istio vs Linkerd vs cloud-native (e.g., App Mesh) | Infrastructure Lead | Phase 3 start | Open | New in Phase 2 (NFR §1.2 mTLS) | Carried (Open; Phase 3 selection) | Q9 | — | No |
| Q30 | Connection pooler: PgBouncer vs Pgcat vs Odyssey | Infrastructure Lead | Phase 3 start | Open | New in Phase 2 (R-SCL-02) | Carried (Open; Phase 3 selection) | Q10 | — | No |
| Q31 | Idempotency store: Redis vs Redis Cluster vs managed (ElastiCache) | Architecture Lead | Phase 3 start | Open | New in Phase 2 (R-REL-01, R-SPOF-03) | Carried (Open; Phase 3 selection) | Q9 | — | No |
| Q32 | Webhook delivery: Celery vs dedicated queue (SQS/RabbitMQ) | Infrastructure Lead | Phase 3 start | Open | New in Phase 2 (R-SCL-03) | Carried (Open; Phase 3 selection) | Q12 | — | No |
| Q33 | Realtime transport: WebSocket vs SSE vs both | Infrastructure Lead | Phase 7 start | Open | New in Phase 2 (R-SCL-04) | Carried (Open; Phase 7 selection) | — | — | No |
| Q34 | Audit log archival: S3 Object Lock vs Glacier vs dedicated WORM | Infrastructure Lead | Phase 8 start | Open | New in Phase 2 (Law-REQ-0009 retention) | Carried (Open; Phase 8 selection) | Q9 | — | No |
| Q35 | Environment variable naming convention (UPPER_SNAKE vs camelCase; prefix NOVENTRA_?) | Architecture Lead | Phase 3 start | Open | New in Phase 3 (DEC-0028 settings split) | Resolved (UPPER_SNAKE, no prefix) → close in Phase 4 | — | — | No |
| Q36 | Secret management strategy per environment (dev=.env, CI=GH secrets, prod=k8s/ECS secrets) | Security Lead | Phase 3 start | Open | New in Phase 3 (DEC-0028 secrets env-only) | Resolved (per-env strategy in settings-split.md §6) → close in Phase 4 | — | — | No |
| Q37 | CI runner cost (GitHub-hosted ubuntu-latest) — Q5-blocked ASSUMED | Commercial Lead | Phase 0 gate | Open | New in Phase 3 (ADR-0024); ASSUMED pending Q5 | Carried (Open; ASSUMED pending Q5) | Q5 | Financial | Yes — funder commitment (via Q5) |
| Q38 | Logging vendor / log backend (Datadog, Loki, Elasticsearch, etc.) | Infrastructure Lead | Phase 5 start | Open | New in Phase 4 (ADR-0025); scaffolding vendor-neutral | Carried (Open; Phase 5 selection) | Q5 | — | No |
| Q39 | OTel backend (Jaeger, Tempo, Honeycomb, Datadog APM) | Infrastructure Lead | Phase 5 start | Open | New in Phase 4 (ADR-0017); no-op exporter; OPEN-DEPENDENT backend | Carried (Open; Phase 5 selection) | Q5 | — | No |
| Q40 | Secret rotation strategy (gitleaks scan-forward; rotation policy) | Security Lead | Phase 5 start | Open | New in Phase 4 (ADR-0028); scan-forward, no history rewrite | Carried (Open; Phase 5 policy) | — | — | No |
| Q41 | pgbouncer vs Pgcat vs Odyssey (connection pooler selection) | Infrastructure Lead | Phase 5 start | Open | New in Phase 2 (R-SCL-02); Q30 carry-over | Resolved (pgbouncer per ADR-0030) → close in Phase 6 | Q10 | — | No |
| Q42 | Break-glass approval tooling (ops console vs manual DBA) | Security Lead | Phase 6 start | Open | New in Phase 5 (break-glass-admin.md); manual workflow in Phase 5 | Carried (Open; Phase 6+ automation) | — | — | No |
| Q43 | MFA scope (TOTP now; WebAuthn Phase 8+; SMS out-of-scope) | Identity Lead | Phase 7 start | Open | New in Phase 6 (ADR-0031); TOTP fields in Phase 6; verification Phase 7 | Carried (Open; Phase 7 TOTP; Phase 8+ WebAuthn) | Q5 | — | No |
| Q44 | SMS provider for MFA (out-of-scope; Q5-blocked) | Identity Lead | Phase 8+ | Open | New in Phase 6 (ADR-0031); SMS explicitly out-of-scope until Q5 | Carried (Open; Phase 8+ if Q5 resolves) | Q5 | — | Yes — funder (via Q5) |
| Q45 | Password policy (min length, complexity, history, expiry) | Security Lead | Phase 7 start | Open | New in Phase 6 (ADR-0031); Argon2id params from env; policy TBD | Carried (Open; Phase 7 policy) | — | — | No |
| Q46 | Invitation flow (token format, TTL, acceptance endpoint) | Identity Lead | Phase 7 start | Open | New in Phase 6 (ADR-0033); schema in Phase 6; endpoints Phase 7 | Carried (Open; Phase 7 endpoints) | — | — | No |
| Q47 | ADR-0014 subject clarification (tenancy vs identity/RBAC) | Architecture Lead | Phase 7 start | Open | New in Phase 6 (phase-006-audit F-601); ADR-0014 covers tenancy, not identity | Resolved (ADR-0014 = tenancy; recommend ACCEPTED in Phase 7) → close in Phase 7 | — | — | No |
| Q48 | Token storage strategy (Redis cache + DB fallback vs DB-only) | Identity Lead | Phase 7 start | Open | New in Phase 6 (ADR-0031); DB-only in Phase 6; Redis Phase 7 | Carried (Open; Phase 7 Redis) | Q5 | — | No |
| Q49 | Audit retention period per jurisdiction (default 7y; Q1-blocked) | Compliance Lead | Phase 8 start | Open | New in Phase 7 (Law-REQ-0009; audit-retention-policy.md); 7y default | Carried (Open; Q1-blocked) | Q1 | Legal | Yes — counsel (via Q1) |
| Q50 | Audit archival vendor (S3 Glacier / GCS Coldline / Azure Archive; Q5-blocked) | Infrastructure Lead | Phase 8 start | Open | New in Phase 7 (audit-retention-policy.md §5); ASSUMED-scaffolding | Carried (Open; Q5-blocked) | Q5 | Financial | Yes — funder (via Q5) |
| Q51 | Alerting channel for chain breaks (PagerDuty / Slack / Opsgenie) | Security Lead | Phase 8 start | Open | New in Phase 7 (ADR-0035 chain break handling); structured logging + dedicated channel | Carried (Open; Phase 8 selection) | Q5 | — | No |
| Q52 | Privacy owner identity (who holds the role; DPO may hold both) | Architecture Lead | Phase 7 start | Open | New in Phase 7 (DEC-0026 amendment); role ratified; identity TBD | Carried (Open; Phase 7 assignment) | — | — | No |
| Q53 | Audit write mode (sync vs async; sync = stronger consistency; async = higher throughput) | Architecture Lead | Phase 8 start | Open | New in Phase 7 (ADR-0035); sync in Phase 7; async evaluation Phase 8 | Carried (Open; Phase 8 evaluation) | — | — | No |
| Q54 | ADR-0014 subject clarification (audit) — covers tenancy, not audit | Architecture Lead | Phase 8 start | Open | New in Phase 7 (phase-007-audit F-701); ADR-0014 = tenancy | Resolved (ADR-0014 = tenancy; ACCEPTED Phase 8) → CLOSED | — | — | No |
| Q55 | Relay topology (Celery beat 50ms vs dedicated worker pool) | Engineering Lead | Phase 9 start | Open | New in Phase 8 (ADR-0040); relay_batch manual in Phase 8 | Carried (Open; Phase 9 selection) | — | — | No |
| Q56 | Redis retention policy (TTL for idempotency keys, inbox entries, DLQ) | Infrastructure Lead | Phase 9 start | Open | New in Phase 8 (ADR-0040..0043); Postgres TTL in Phase 8 | Carried (Open; Phase 9 Redis TTL) | Q5 | — | No |
| Q57 | Notification vendors (SendGrid/Twilio; Q5-blocked) | Product Lead | Phase 9 start | Open | New in Phase 8 (ADR-0045); stubs in Phase 8 | Carried (Open; Q5-blocked) | Q5 | Financial | Yes — funder (via Q5) |
| Q58 | Jurisdiction caps for MarketingGate (Q1-blocked) | Compliance Lead | Phase 9 start | Open | New in Phase 8 (ADR-0046); no jurisdiction caps until Q1 | Carried (Open; Q1-blocked) | Q1 | Legal | Yes — counsel (via Q1) |
| Q59 | Deployment topology (single-region vs multi-region; k8s vs ECS) | Infrastructure Lead | Phase 9 start | Open | New in Phase 8 (ADR-0017 blue/green); single-region in Phase 8 | Carried (Open; Phase 9 selection) | Q5 | — | No |
| Q60 | ADR-0014 subject — CLOSED (chronic deferral loop resolved) | Architecture Lead | Phase 8 | Closed | New in Phase 6; resolved Phase 8 (ADR-0014 → ACCEPTED) | CLOSED (Phase 8) | — | — | No |
| Q61 | Multi-tenant players (player belongs to multiple tenants) | Product Owner | Phase 10 start | Open | New in Phase 9 (ADR-0047); single-tenant in Phase 9 | Carried (Open; Phase 10+ evaluation) | — | — | No |
| Q62 | KYC scope (which KYC checks per jurisdiction; Q1-blocked) | Compliance Lead | Phase 10 start | Open | New in Phase 9 (player onboarding); Q1-blocked | Carried (Open; Q1-blocked) | Q1 | Legal | Yes — counsel (via Q1) |
| Q63 | Consent versioning grace period (how long before re-consent required) | Product Owner | Phase 10 start | Open | New in Phase 9 (ADR-0048); grace period documented but not enforced | Carried (Open; Phase 10 policy) | — | — | No |
| Q64 | Self-exclusion cooling-off period per jurisdiction (Q1-blocked) | Compliance Lead | Phase 10 start | Open | New in Phase 9 (ADR-0050); default 24h; jurisdiction-specific Q1-blocked | Carried (Open; Q1-blocked) | Q1 | Legal | Yes — counsel (via Q1) |
| Q65 | DSAR delivery infrastructure (secure file transfer; Q5-blocked) | Infrastructure Lead | Phase 10 start | Open | New in Phase 9 (ADR-0051); stdout JSON in Phase 9; secure delivery Q5-blocked | Carried (Open; Q5-blocked) | Q5 | Financial | Yes — funder (via Q5) |
| Q66 | Consent policy version store (where consent text + versions are stored) | Product Owner | Phase 10 start | Open | New in Phase 9 (ADR-0048); policy_version field exists; store TBD | Carried (Open; Phase 10 store) | — | — | No |
| Q67 | Dormancy definition per jurisdiction (inactivity threshold; Q1-blocked) | Compliance Lead | Phase 10 start | Open | New in Phase 9 (ADR-0050); default 365d; jurisdiction-specific Q1-blocked | Carried (Open; Q1-blocked) | Q1 | Legal | Yes — counsel (via Q1) |
| Q68 | KYC vendor selection (Onfido/Jumio/Veriff; Q5-blocked) | Compliance Lead | Phase 11 start | Open | New in Phase 10 (ADR-0057); stub in Phase 10 | Carried (Open; Q5-blocked) | Q5 | Financial | Yes — funder (via Q5) |
| Q69 | PEP/sanctions screening vendor (Q5-blocked) | Compliance Lead | Phase 11 start | Open | New in Phase 10 (ADR-0056); stub in Phase 10 | Carried (Open; Q5-blocked) | Q5 | Financial | Yes — funder (via Q5) |
| Q70 | Storage backend selection (S3/GCS/Azure Blob; Q5-blocked) | Infrastructure Lead | Phase 11 start | Open | New in Phase 10 (ADR-0054); stub in Phase 10 | Carried (Open; Q5-blocked) | Q5 | Financial | Yes — funder (via Q5) |
| Q71 | MLRO appointment (regulator-mandated human role; FATF Rec.18) | Compliance Lead | Phase 11 start | Open | New in Phase 10 (DEC-0026 amendment); role ratified; appointment evidence required | Carried (Open; Phase 11 documented appointment) | — | Legal | Yes — regulator-mandated |
| Q72 | SAR filing jurisdiction (which FIU per jurisdiction; Q1-blocked) | MLRO | Phase 11 start | Open | New in Phase 10 (ADR-0056); SAR flow implemented; jurisdiction Q1-blocked | Carried (Open; Q1-blocked) | Q1 | Legal | Yes — counsel (via Q1) |
| Q73 | Re-KYC period per jurisdiction (Q1-blocked) | Compliance Lead | Phase 11 start | Open | New in Phase 10 (ADR-0052); re-verification triggers implemented; period Q1-blocked | Carried (Open; Q1-blocked) | Q1 | Legal | Yes — counsel (via Q1) |
| Q74 | Risk model choice (rule-based vs ML-based; rule-based recommended) | Compliance Lead | Phase 11 start | Open | New in Phase 10 (ADR-0056); rule-based in Phase 10; ML evaluation Phase 11+ | Carried (Open; Phase 11 evaluation) | — | — | No |
| Q75 | Affordability check method (Open Banking vs credit bureau vs self-declaration; Q1/Q5-blocked) | Product Owner | Phase 11 start | Open | New in Phase 10 (ADR-0056); triggers Q1-blocked; methods Q5-blocked | Carried (Open; Q1+Q5-blocked) | Q1, Q5 | Financial | Yes — counsel + funder |

## 2.1 Carry-over summary (Phase 10 — highest combined Q1+Q5 blast radius)

Phase 10 has the **highest combined Q1+Q5 blast radius in the plan**:
- Q1 blocks: Q72 (SAR filing jurisdiction), Q73 (re-KYC period),
  Q62 (KYC scope), Q64 (self-exclusion cooling-off), Q67 (dormancy),
  Q58 (jurisdiction caps), Q49 (retention per jurisdiction), Q75 (affordability triggers).
- Q5 blocks: Q68 (KYC vendor), Q69 (PEP/sanctions vendor), Q70 (storage
  backend), Q65 (DSAR delivery), Q57 (notification vendors), Q75 (affordability methods).

| Q ID | Phase 1-9 | Phase 10 | Blocks Phase 11? | Blast radius |
|---|---|---|---|---|
| Q1 | Blocked | Blocked | YES | **HIGHEST** (blocks 8 dependent questions) |
| Q2 | Blocked | Blocked | YES | High |
| Q4 | Blocked | Blocked | YES | High |
| Q5 | Blocked | Blocked | YES | **HIGHEST** (blocks 6 dependent questions) |

**Without Q1+Q5 resolution, the system cannot legally onboard customers.**
Phase 11 must resolve Q1+Q5 or formally accept BLOCKED (system cannot
go to production).

## 2.2 Architectural questions added in Phase 2, 3, and 4

Phase 2 ADR authoring and risk-register compilation surfaced seven
new architectural questions (Q28–Q34). Phase 3 settings-split and
CI work surfaced three more (Q35–Q37). Phase 4 observability and
scanning work surfaced three more (Q38–Q40). None of Q28–Q40 are
BLOCKERs; all are Open with target resolution phases. Q35 and Q36
are marked "Resolved → close in Phase 4" because the Phase 3 work
effectively resolved them (UPPER_SNAKE naming; per-env secret
strategy). Q37 (CI runner cost), Q38 (logging vendor), and Q39
(OTel backend) are Q5-blocked ASSUMED — their validation depends
on Q5 (budget) being resolved. Q40 (secret rotation) is OPEN
with a Phase 5 target for the rotation policy.

## 3. Answers in progress

This section records answers that have been produced but not yet
closed (i.e., not yet recorded as DEC rows in `traceability.md`).
Once an answer is accepted, it is migrated to a DEC row and the
question is marked Closed.

(Empty in seed. Answers are appended as they are produced. Each
answer records: the Q ID, the proposed answer, the owner, the date,
and the next step — typically "draft DEC row" or "external
review".)

## 4. Blocker dependencies and escalation

The four BLOCKER questions form a dependency graph:

- **Q1** (jurisdictions) is the root blocker. Q2, Q3, Q6, Q7, Q14,
  Q15, Q20, and (transitively) several others cannot be answered
  until Q1 is resolved. Q1 requires external counsel.
- **Q2** (licensing) depends on Q1 and also requires external
  counsel (typically the same engagement as Q1).
- **Q4** (pilot partner) is independent of Q1/Q2 in principle but
  in practice a pilot partner wants to know the jurisdictions
  before signing. Q4 requires a signed letter of intent.
- **Q5** (budget) is independent of Q1/Q2/Q4. Q5 requires a funder
  commitment letter. If Q5 is BLOCKED, no Phases 1–3 work can be
  resourced; the programme does not start.

### 4.1 Escalation path

If any of Q1, Q2, Q4, Q5 is BLOCKED at the Phase 0 gate review:

1. The Engineering Lead records the BLOCKED status in §2 above.
2. The Phase 0 evidence pack (`phase-0-evidence.md`) is marked
   FAIL.
3. Phase 2 does not start. No exceptions.
4. The Architecture Lead and the Commercial Lead jointly decide
   whether to pivot (re-scope to a different jurisdiction or
   business model) or kill (terminate the programme).

There is no override mechanism. The "no exceptions" rule is
deliberate: it forces the team to resolve the blockers before
investing in Phase 2 code.

### 4.2 Small-team escalation

Per `roles.md` §3, if the named team has fewer than three humans
across the role roster, Q1, Q2, Q4, and Q5 are auto-marked
BLOCKED regardless of their underlying status. The team-size check
is performed at the Phase 0 gate review by the Engineering Lead.

## 5. Question change protocol

A new question may be added at any time. The change requires:

1. An ID assigned by the Engineering Lead (next available Q ID).
2. An owner from the role roster in `roles.md` §1.
3. A due date. If the question feeds a Phase 0 gate, the due date
   is "Phase 0 gate".
4. A status. Default is Open.
5. Dependencies listed (or "—" if none).
6. The gate it feeds (or "—" if none).
7. Whether external validation is required (Yes/No).

A question may be retired only by being Closed (answered and
migrated to a DEC row) or by being marked Deprecated (no longer
relevant; superseded by a different question). Retired questions
remain in §2 for audit; they are not deleted.

## 5.1 Phase 17 open questions (OQ-DATA-001..006)

Per Phase 17 Stage A prompt §2.4, six new open questions are registered
for the Data Platform & GGR phase. These questions are OPEN or BLOCKED
at Stage A; they must be resolved (or explicitly marked BLOCKED) before
Stage B merge.

| ID | Question | Owner | Due Date | Status | Notes |
|---|---|---|---|---|---|
| OQ-DATA-001 | Telemetry backend (separate Redis stream vs time-series DB) | Reliability Owner | Phase 17 Stage A | OPEN | Stub uses separate Redis stream `telemetry.events`. Time-series DB (e.g., InfluxDB, TimescaleDB) is Q5-blocked for vendor selection. Stage A proceeds with stub; Stage B picks backend. |
| OQ-DATA-002 | Regulatory report format per jurisdiction | Compliance Officer | Phase 22 | Q1-BLOCKED | UK GC (monthly GGR CSV), MGA (quarterly GGR/NGR Excel), AGCO (quarterly JSON). Specific formats per jurisdiction are Q1-blocked (jurisdiction list is environment-dependent). Stage A: generic JSON stub. |
| OQ-DATA-003 | Regulator portal API integration | Compliance Officer | Phase 22 | Q5-BLOCKED | Automated submission via regulator portal API. Q5-blocked for vendor selection (each regulator has its own portal API). Stage A: manual submission only. |
| OQ-DATA-004 | Schema registry compatibility mode default (backward recommended) | API Owner | Phase 17 Stage A | OPEN | Recommended: `backward` (new schema can read old data; adding optional fields is safe). May tighten to `full` for financial events in a future ADR. |
| OQ-DATA-005 | Consumer lag threshold (1000 messages or 60s recommended) | Reliability Owner | Phase 17 Stage A | OPEN | Recommended: alert if lag > 1000 messages OR (now - last_processed_at) > 60 seconds, whichever first. Per-consumer override in production config. |
| OQ-DATA-006 | Reconciliation cadence (daily recommended) | CFO | Phase 17 Stage A | OPEN | Recommended: daily at 04:00 UTC. May tighten to hourly for high-volume tenants. Daily catches drift in both real-time + scheduled read models. |

These OQs are non-blocking for Phase 17 Stage A (design). They become
blocking for Phase 17 Stage B (merge stop #7) — Stage B cannot proceed
until OQ-DATA-001, OQ-DATA-004, OQ-DATA-005, OQ-DATA-006 are answered
(OPEN status resolved) and OQ-DATA-002, OQ-DATA-003 are explicitly
marked BLOCKED (already done above).

## 5.2 Phase 18 open questions (OQ-RISK-001..006)

Per Phase 18 Stage A prompt §2.4, six new open questions are registered
for the Risk, AML & Cases phase. These questions are OPEN or BLOCKED
at Stage A; they must be resolved (or explicitly marked BLOCKED) before
Stage B merge.

| ID | Question | Owner | Due Date | Status | Notes |
|---|---|---|---|---|---|
| OQ-RISK-001 | ML-based TM (Phase 19+ or vendor — Q5-blocked) | CTO | Phase 19+ | Q5-BLOCKED | Phase 18 ships rule-based TM only (explainable for regulators). ML-based TM deferred to Phase 19+ or vendor selection (Q5-blocked). |
| OQ-RISK-002 | FIU submission API integration | Compliance Officer | Phase 22 | Q5-BLOCKED | Each FIU has its own portal API (NCA SAR Online, FinCEN BSA E-Filing, BaFin, Tracfin). Q5-blocked for vendor selection. Stage A: manual portal submission only. |
| OQ-RISK-003 | CTR threshold per jurisdiction (default $10,000) | Compliance Officer | Phase 22 | Q1-BLOCKED | US: $10,000; UK: £6,500; EU: €10,000. Per-jurisdiction thresholds Q1-blocked (jurisdiction list is environment-dependent). Stage A: stub returns US default. |
| OQ-RISK-004 | SAR retention period per jurisdiction (5-10 years) | Legal Counsel | Phase 22 | Q1-BLOCKED | UK: 5 years; US: 5 years; EU: 5 years (AMLD5; some 10); Germany: 10 years (GwG §8). Per-jurisdiction retention Q1-blocked. Stage A: default 5 years. |
| OQ-RISK-005 | Appeal window per jurisdiction (default 30 days) | Legal Counsel | Phase 22 | Q1-BLOCKED | UK GC: 30 days; MGA: 60 days; other jurisdictions vary. Per-jurisdiction window Q1-blocked. Stage A: default 30 days. |
| OQ-RISK-006 | Risk scoring weights (configurable per tenant) | Compliance Officer | Phase 18 Stage B | OPEN | Default weights per signal type (low: 1-10, medium: 11-25, high: 26-50, critical: 51+). Per-tenant override in production config. Must be resolved before Stage B merge. |

These OQs are non-blocking for Phase 18 Stage A (design). They become
blocking for Phase 18 Stage B (merge stop #8) — Stage B cannot proceed
until OQ-RISK-006 is answered (OPEN status resolved) and OQ-RISK-001,
OQ-RISK-002, OQ-RISK-003, OQ-RISK-004, OQ-RISK-005 are explicitly
marked BLOCKED (already done above; Q5/Q1-blocked per DEC-0064).

## 5.3 Phase 19 open questions (OQ-AI-001..006)

Per Phase 19 Stage A prompt §3.4, six new open questions are registered
for the AI Platform & RAG phase. These questions are OPEN or BLOCKED
at Stage A; they must be resolved (or explicitly marked BLOCKED) before
Stage B merge.

| ID | Question | Owner | Due Date | Status | Notes |
|---|---|---|---|---|---|
| OQ-AI-001 | LLM provider selection (OpenAI, Anthropic, Google, local) | CTO | Phase 22 | Q5-BLOCKED | Provider selection Q5-blocked for vendor evaluation. Stage A uses StubLLMAdapter; Stage B picks provider(s). Multi-provider support via LLMProviderPort abstraction (ADR-0115). |
| OQ-AI-002 | Embedding model selection + dimension (1536 for OpenAI) | CTO | Phase 19 Stage A | OPEN | Default: OpenAI text-embedding-3-small (1536 dims). May switch to text-embedding-3-large (3072 dims) for better quality. Must resolve before Stage B (embedding dimension affects schema: vector(1536) vs vector(3072)). |
| OQ-AI-003 | Q21: EU AI Act classification of retention AI | Compliance Officer | Phase 22 | Q1-BLOCKED | Retention AI (Phase 9) makes automated decisions affecting players. EU AI Act may classify as high-risk. Default: high-risk until proven otherwise. Legal Counsel review required (ADR-0123). |
| OQ-AI-004 | NLI model for claim-level grounding (vendor or in-house) | CTO | Phase 19 Stage A | Q5-BLOCKED | NLI model for Step 6 Claim-Level Grounder (ADR-0119). Options: DeBERTa-v3 NLI (in-house), vendor API (Q5-blocked). Stage A: span mapping fallback; Stage B: NLI model selection. |
| OQ-AI-005 | Per-tenant monthly LLM budget default | CFO | Phase 19 Stage A | OPEN | Default: $500/month per tenant (recommended). Configurable per tenant. Must resolve before Stage B (affects budget enforcement thresholds in ADR-0122). |
| OQ-AI-006 | Degradation L0-L4 thresholds (when to degrade) | Reliability Owner | Phase 19 Stage A | OPEN | When to degrade: L0→L1 on cache hit OR latency >2s; L1→L2 on provider unavailable OR cost >80%; L2→L3 on cost >100%; L3→L4 on all fallbacks failed. Must confirm thresholds before Stage B. |

These OQs are non-blocking for Phase 19 Stage A (design). They become
blocking for Phase 19 Stage B (merge stop #9) — Stage B cannot proceed
until OQ-AI-002, OQ-AI-005, OQ-AI-006 are answered (OPEN status
resolved) and OQ-AI-001, OQ-AI-003, OQ-AI-004 are explicitly marked
BLOCKED (already done above; Q5/Q1-blocked per DEC-0064).

## 5.4 Phase 20 open questions (OQ-AGENT-001..006)

Per Phase 20 Stage A prompt §3.4, six new open questions are registered
for the Bounded Agents phase. These questions are OPEN at Stage A;
they must be resolved (or explicitly marked BLOCKED) before Stage B
merge.

| ID | Question | Owner | Due Date | Status | Notes |
|---|---|---|---|---|---|
| OQ-AGENT-001 | LLM provider for agents (same as Phase 19 or separate) | CTO | Phase 19 Stage A | OPEN | Default: same provider as Phase 19 LLM Gateway (ADR-0115). May use separate provider for agents (e.g., cheaper model for high-volume agent calls). Must resolve before Stage B (affects cost accounting ADR-0122). |
| OQ-AGENT-002 | Approval SLA default (24h recommended) | Compliance Officer | Phase 20 Stage A | OPEN | Default: 24h for all approval gates. Per-gate configurable: punitive_actions 4h; math_changes 8h; campaign_approval 24h; code_review 48h. Must confirm defaults before Stage B (affects SLA enforcement in ADR-0127). |
| OQ-AGENT-003 | Shadow→live promotion criteria (test results + review notes) | Product Owner | Phase 20 Stage B | OPEN | Criteria for promotion: N successful shadow interactions (recommended N=100); zero critical failures; human review notes; Compliance Officer sign-off for high-risk agents (Retention, Fraud/AML). Must define before Stage B promotion tests. |
| OQ-AGENT-004 | Agent scheduling (RG Triage hourly; Fraud/AML event-driven) | Reliability Owner | Phase 20 Stage A | OPEN | RG Triage: hourly scheduled (Celery beat). Fraud/AML: event-driven (on risk signal from Phase 18). Support Knowledge: on-demand (user query). Retention: daily scheduled (segment evaluation). Must confirm schedule before Stage B. |
| OQ-AGENT-005 | Agent cost allocation (per-tenant; per-agent) | CFO | Phase 20 Stage A | OPEN | Default: per-tenant (same as Phase 19 ADR-0122). May add per-agent allocation for chargeback granularity (e.g., Retention agent costs billed to marketing budget). Must confirm before Stage B (affects LLMCostRecord schema). |
| OQ-AGENT-006 | Distress short-circuit threshold (Phase 14 RGPort integration) | Compliance Officer | Phase 20 Stage B | OPEN | Threshold for distress short-circuit: any distress signal (SE activation, reality check failure, RG distress) bypasses AI. RG Triage agent: distress detection is primary function; always short-circuits. Must confirm threshold before Stage B distress tests. |

These OQs are non-blocking for Phase 20 Stage A (design). They become
blocking for Phase 20 Stage B (merge stop #10) — Stage B cannot proceed
until OQ-AGENT-001, OQ-AGENT-002, OQ-AGENT-004, OQ-AGENT-005 are
answered (OPEN status resolved) and OQ-AGENT-003, OQ-AGENT-006 are
resolved before their respective Stage B tests (promotion tests;
distress tests).

## 5.5 Phase 21 open questions (OQ-COMP-001..006)

Per Phase 21 Stage A prompt §2.4, six new open questions are registered
for the Compliance, DSAR & Vendors phase. These questions are OPEN or
BLOCKED at Stage A; they must be resolved (or explicitly marked BLOCKED)
before Stage B merge.

| ID | Question | Owner | Due Date | Status | Notes |
|---|---|---|---|---|---|
| OQ-COMP-001 | Compliance frameworks in scope (UK GC LCCP, MGA BLC, GDPR, AML, ISO 27001, SOC 2 — all?) | Compliance Officer | Phase 21 Stage A | OPEN | Default: all 6 frameworks in scope. Some tenants may not need all (e.g., non-UK operator skips UK GC LCCP). Must confirm scope before Stage B (affects control registry + framework mapping). |
| OQ-COMP-002 | Evidence retention period per jurisdiction (5-10 years) | Legal Counsel | Phase 22 | Q1-BLOCKED | UK: 5 years; US: 5 years (SEC 17a-4); EU: 5-10 years (AMLD5; member state varies); Germany: 10 years (GwG §8). Per-jurisdiction retention Q1-blocked (jurisdiction list is environment-dependent). Stage A: default 5 years. |
| OQ-COMP-003 | External auditor vendor selection | Compliance Officer | Phase 22 | Q5-BLOCKED | External auditor engagement for annual external_audit (ADR-0133). Q5-blocked for vendor selection (Big 4 or specialist gaming audit firm). Stage A: stub; Stage B: vendor selected. |
| OQ-COMP-004 | DSAR statutory window per jurisdiction (30 days default) | Legal Counsel | Phase 22 | Q1-BLOCKED | GDPR Art 12(3): 30 days default; UK GC: 30 days; MGA: 30 days; some jurisdictions allow extension to 90 days for complex requests. Per-jurisdiction window Q1-blocked. Stage A: default 30 days. |
| OQ-COMP-005 | Regulator portal API integration (per jurisdiction) | Compliance Officer | Phase 22 | Q5-BLOCKED | Each regulator has its own portal API (UK GC portal, MGA portal, FinCEN BSA E-Filing, BaFin, Tracfin). Q5-blocked for vendor selection. Stage A: manual portal submission only. |
| OQ-COMP-006 | Vendor expiry T-30/7/1 thresholds (configurable per vendor type) | Compliance Officer | Phase 21 Stage A | OPEN | Default: T-30/T-7/T-1 for all PSP/KYC/Geo vendors. May tighten per vendor type (e.g., KYC vendor T-45/T-14/T-3 for longer transition). Must confirm thresholds before Stage B (affects expiry job schedule in ADR-0136). |

These OQs are non-blocking for Phase 21 Stage A (design). They become
blocking for Phase 21 Stage B (merge stop #11) — Stage B cannot proceed
until OQ-COMP-001, OQ-COMP-006 are answered (OPEN status resolved) and
OQ-COMP-002, OQ-COMP-003, OQ-COMP-004, OQ-COMP-005 are explicitly
marked BLOCKED (already done above; Q1/Q5-blocked per DEC-0064).

## 5.6 Phase 22 open questions (OQ-ENG-001..006)

Per Phase 22 Stage A prompt §2.4, six new open questions are registered
for the Engagement & Retention phase. These questions are OPEN or
BLOCKED at Stage A; they must be resolved (or explicitly marked BLOCKED)
before Stage B merge.

| ID | Question | Owner | Due Date | Status | Notes |
|---|---|---|---|---|---|
| OQ-ENG-001 | Propensity model vendor (in-house vs vendor; Q5-blocked) | CTO | Phase 22 Stage A | Q5-BLOCKED | Options: in-house (DeBERTa-v3 / XGBoost), vendor (FeatureBase, Tecton). Q5-blocked for vendor selection. Stage A: stub (rule-based heuristic features); Stage B: vendor selected. |
| OQ-ENG-002 | Propensity model recompute cadence (nightly recommended) | Product Owner | Phase 22 Stage A | OPEN | Default: nightly (03:00 UTC). May need more frequent for high-volatility features (churn_risk may need hourly). Must confirm cadence before Stage B (affects Celery beat schedule in ADR-0139). |
| OQ-ENG-003 | Journey step retry policy (retry vs advance on send-time denial) | Product Owner | Phase 22 Stage A | OPEN | When send-time MarketingGate denies (cap/consent): retry after delay (configurable) OR advance to next step. Default: advance (don't retry; player already at cap). Must confirm before Stage B (affects JourneyService logic in ADR-0138). |
| OQ-ENG-004 | Segment membership expiry (TTL; configurable per segment) | Product Owner | Phase 22 Stage B | OPEN | Default: 30 days (membership expires; re-evaluated on next nightly rebuild). Some segments may need longer (VIP segment 90 days) or shorter (active-player segment 7 days). Must confirm TTL before Stage B segment tests. |
| OQ-ENG-005 | Marketing channel priority (email > SMS > push; configurable) | Product Owner | Phase 22 Stage A | OPEN | When player has multiple channels consented, which to use first? Default: email (cheapest; highest engagement). May differ per segment (VIP segment: SMS first). Must confirm priority before Stage B (affects JourneyStep channel selection in ADR-0138). |
| OQ-ENG-006 | Propensity feature transparency (privacy policy wording; EU AI Act limited risk) | Legal Counsel + Privacy Owner | Phase 22 Stage B | Q1-BLOCKED | EU AI Act limited risk mandates player transparency. Privacy policy must state: "We use behavioral data to compute propensity features (churn risk, LTV, deposit propensity, bonus sensitivity, RG risk) for marketing targeting." Exact wording Q1-blocked (jurisdiction-dependent privacy law). Stage A: generic wording stub. |

These OQs are non-blocking for Phase 22 Stage A (design). They become
blocking for Phase 22 Stage B (merge stop #12) — Stage B cannot proceed
until OQ-ENG-002, OQ-ENG-003, OQ-ENG-004, OQ-ENG-005 are answered
(OPEN status resolved) and OQ-ENG-001, OQ-ENG-006 are explicitly marked
BLOCKED (already done above; Q5/Q1-blocked per DEC-0064).

## 5.7 Phase 23 open questions (OQ-COMM-001..006)

Per Phase 23 Stage A prompt §2.4, six new open questions are registered
for the Commercial & Billing phase. These questions are OPEN or BLOCKED
at Stage A; they must be resolved (or explicitly marked BLOCKED) before
Stage B merge.

| ID | Question | Owner | Due Date | Status | Notes |
|---|---|---|---|---|---|
| OQ-COMM-001 | Default rev-share rate per product (casino 15%, live_casino 18%) | CFO + Product Owner | Phase 23 Stage A | OPEN | Default: casino 15%, live_casino 18%. These are industry-standard B2B rev-share rates. May vary per operator contract (FeeSchedule is configurable). Must confirm defaults before Stage B (affects FeeSchedule seed data in ADR-0143). |
| OQ-COMM-002 | Tiered fee schedule thresholds (volume-based) | CFO | Phase 23 Stage A | OPEN | Default tiers: 0-$10M GGR @ 15%; $10M-$100M @ 12%; $100M+ @ 10%. Must confirm thresholds before Stage B (affects tiered calculation tests in ADR-0143). |
| OQ-COMM-003 | Operator payout mechanism (Phase 12 payment integration) | CFO + Reliability Owner | Phase 23 Stage B | OPEN | When operator is net creditor (GGR < deductions + fees), Noventra owes operator. Payout via Phase 12 payment service (bank transfer). Must confirm payout flow before Stage B payment integration tests. |
| OQ-COMM-004 | Contract retention period per jurisdiction (7+ years; Q1-blocked) | Legal Counsel | Phase 25 | Q1-BLOCKED | UK: 7 years (Limitation Act 1980); US: 7 years (IRS); EU: 7-10 years (member state varies); Germany: 10 years (HGB §257). Per-jurisdiction retention Q1-blocked (jurisdiction list is environment-dependent). Stage A: default 7 years. |
| OQ-COMM-005 | Statement delivery method (portal vs email vs both) | Product Owner | Phase 23 Stage A | OPEN | Default: both (portal self-service + email PDF). Some operators may prefer portal only (reduces email risk). Must confirm default before Stage B (affects delivery logic in ADR-0145). |
| OQ-COMM-006 | Invoice currency (per-operator vs per-jurisdiction) | CFO | Phase 23 Stage A | OPEN | Default: per-operator (contract specifies currency). Some operators may need per-jurisdiction invoicing (UK GBP + MGA EUR). Must confirm before Stage B (affects Invoice.currency_code logic in ADR-0144). |

These OQs are non-blocking for Phase 23 Stage A (design). They become
blocking for Phase 23 Stage B (merge stop #13) — Stage B cannot proceed
until OQ-COMM-001, OQ-COMM-002, OQ-COMM-003, OQ-COMM-005, OQ-COMM-006
are answered (OPEN status resolved) and OQ-COMM-004 is explicitly marked
BLOCKED (already done above; Q1-blocked per DEC-0064).

## 5.8 Phase 24 open questions (OQ-DEV-001..006)

Per Phase 24 Stage A prompt §2.4, six new open questions are registered
for the Developer Platform & Player SDK phase. These questions are OPEN
or BLOCKED at Stage A; they must be resolved (or explicitly marked
BLOCKED) before Stage B merge.

| ID | Question | Owner | Due Date | Status | Notes |
|---|---|---|---|---|---|
| OQ-DEV-001 | Partner key scope catalog (read_players, write_webhooks, etc. — closed?) | API Owner + Product Owner | Phase 24 Stage A | OPEN | Default: closed catalog of ~10 scopes (read_players, write_webhooks, read_ledger, launch_games, read_bonus, read_rg, write_payment, read_invoice, read_statement, manage_conformance). Must confirm closed vs open before Stage B (affects scope validation in ADR-0147). |
| OQ-DEV-002 | Sandbox tenant TTL (30 days recommended) | Product Owner | Phase 24 Stage A | OPEN | Default: 30 days. Some partners may need longer (90 days for complex integrations). Must confirm TTL before Stage B (affects sandbox expiry in ADR-0149). |
| OQ-DEV-003 | Reference lobby license (MIT or Apache 2.0) | Legal Counsel | Phase 24 Stage A | OPEN | MIT is simpler (fewer clauses); Apache 2.0 has patent grant clause (better enterprise adoption). Must confirm before Stage B (affects reference lobby publication in ADR-0151). |
| OQ-DEV-004 | Conformance suite hosting (Noventra-hosted vs partner-hosted) | Product Owner + Reliability Owner | Phase 24 Stage A | OPEN | Noventra-hosted: partner submits frontend URL; Noventra runs suite. Partner-hosted: partner runs suite locally; submits results. Must confirm before Stage B (affects conformance run in ADR-0151). |
| OQ-DEV-005 | Docs portal AI search (Phase 19 RAG integration; Q5-blocked) | Product Owner | Phase 25 | Q5-BLOCKED | Phase 19 RAG pipeline for natural-language docs search. Q5-blocked for LLM provider (OQ-AI-001). Stage A: no AI search; Stage B: add after LLM provider selected. |
| OQ-DEV-006 | Partner webhook retry schedule (1min/5min/30min/2hr/6hr recommended) | Reliability Owner | Phase 24 Stage A | OPEN | Default: 5 attempts at 1min, 5min, 30min, 2hr, 6hr (total ~8.5 hours). Some partners may need faster (1min, 5min, 15min, 1hr, 4hr = ~5 hours). Must confirm before Stage B (affects webhook retry in ADR-0148). |

These OQs are non-blocking for Phase 24 Stage A (design). They become
blocking for Phase 24 Stage B (merge stop #14) — Stage B cannot proceed
until OQ-DEV-001, OQ-DEV-002, OQ-DEV-003, OQ-DEV-004, OQ-DEV-006 are
answered (OPEN status resolved) and OQ-DEV-005 is explicitly marked
BLOCKED (already done above; Q5-blocked per DEC-0064).

## 5.9 Phase 25 FINAL open questions (OQ-LAUNCH-001..006)

Per Phase 25 Stage A prompt §2.4, six final open questions are
registered for the Validation, Readiness & Launch phase. These are
the LAST OQs of the programme. They must be resolved before launch.

| ID | Question | Owner | Due Date | Status | Notes |
|---|---|---|---|---|---|
| OQ-LAUNCH-001 | Q1 (jurisdictions) — RESOLVE before launch | Legal Counsel | Launch | Q1-BLOCKED | The jurisdiction list (which jurisdictions Noventra operates in) has been Q1-BLOCKED since Phase 1. Must be resolved (or explicitly accepted with documented deferral per DEC-0064) before launch. Affects: AML thresholds (Phase 18), regulatory reports (Phase 21), fee schedules (Phase 23), vendor registry (Phase 21). |
| OQ-LAUNCH-002 | Q5 (budget) — RESOLVE before launch | CFO | Launch | Q5-BLOCKED | The budget (vendor selections, infrastructure scale, team size) has been Q5-BLOCKED since Phase 1. Must be resolved (or explicitly accepted with documented deferral per DEC-0064) before launch. Affects: LLM provider (Phase 19), KYC vendor (Phase 10), PSP (Phase 12), embedding model (Phase 19), external auditor (Phase 21). |
| OQ-LAUNCH-003 | All prior OQs (Phase 11-24) — resolve or document deferral | CTO | Launch | OPEN | 30+ OPEN OQs across Phases 11-24 (OQ-DATA, OQ-RISK, OQ-AI, OQ-AGENT, OQ-COMP, OQ-ENG, OQ-COMM, OQ-DEV). Each must be resolved (OPEN → Answered → Closed) or explicitly documented with target phase for resolution. Cannot launch with unresolved OPEN OQs. |
| OQ-LAUNCH-004 | MLRO appointment (regulator-mandated human) | CTO | Launch | OPEN | The MLRO (Money Laundering Reporting Officer) is a regulator-mandated named human with personal criminal liability for SAR decisions (Phase 18 ADR-0111). Must be appointed before launch. Cannot launch without MLRO. |
| OQ-LAUNCH-005 | External Auditor engagement | Compliance Officer | Launch | Q5-BLOCKED | External auditor engagement for annual external_audit (Phase 21 ADR-0133) + financial audit access (Phase 11 noventra_auditor role). Q5-blocked for vendor selection. Must be resolved before launch. |
| OQ-LAUNCH-006 | Launch communication plan (internal + external + regulator) | Product Owner | Launch | OPEN | Launch communication plan: internal (staff briefing; on-call rotation activated), external (status page; customer notification), regulator (launch notification to UK GC/MGA/FinCEN per jurisdiction). Must be documented before launch. |

These OQs are ALL blocking for launch. Phase 25 Stage B (the final
Ubuntu push) must resolve ALL of them before the Go/No-Go decision.
No launch with unresolved OPEN OQs. No launch with Q1/Q5 blocking
(not documented deferral per DEC-0064).

## 6. Cross-references

- Phase 0 evidence pack: `docs/phase-0-evidence.md`.
- Small-team blocker rule: `docs/requirements/roles.md` §3.
- DEC rows (for Closed questions): `docs/requirements/traceability.md` §C.
- Supersessions (for question re-numbering or merges):
  `docs/requirements/traceability.md` §D.
- BLUEPRINT §10 (Phase 0 evidence gates): `docs/BLUEPRINT.md`.
