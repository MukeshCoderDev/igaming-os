# Non-Functional Requirements (NFRs)

| Field | Value |
|---|---|
| Document | `docs/requirements/nfr.md` |
| Version | 5.2 |
| Status | Approved |
| Owner | Architecture Lead (overall); per-section owners noted inline |
| Authority | BLUEPRINT §2 (Reliable Core in scope); `traceability.md` |

This document records the non-functional requirements that govern
Increment 1 (Phase 1) and the cross-cutting NFRs that apply to every
phase. Each NFR is given a target, a measurement method, and a
failure consequence. NFRs without a measurement method are
non-actionable and are forbidden here.

Where an NFR depends on an open question (Q1–Q27), the dependency is
noted. If the question is BLOCKED, the NFR's target may be provisional;
the provisional target is flagged as such.

## 1. Security NFRs

Owner: Security Lead.

### 1.1 Encryption at rest

All persisted data — tenant data, audit log, configuration store,
backups — must be encrypted at rest with AES-256 (or stronger).
Key management uses a managed KMS with per-tenant key isolation
where the cloud provider supports it. Key rotation is automatic at
90-day intervals.

- **Target:** 100% of persisted data encrypted at rest.
- **Measurement:** Automated scan of storage configurations; report
  to Security Lead weekly.
- **Failure consequence:** P0 alert; tenant onboarding halted until
  remediated.
- **REQs/DECs:** Law-REQ-0023.

### 1.2 Encryption in transit

All network communication — internal service-to-service, external
API, webhook delivery — must use TLS 1.2 or stronger. TLS 1.0 and
1.1 are forbidden. Mutual TLS is required for service-to-service
calls inside the cluster.

- **Target:** 100% of connections use TLS 1.2+; 100% of
  service-to-service calls use mTLS.
- **Measurement:** Continuous TLS scanner; alert on any downgrade.
- **Failure consequence:** P0 alert; the affected endpoint is
  disabled.
- **REQs/DECs:** Law-REQ-0024.

### 1.3 Authentication strength

All human authentication must support MFA. Tenant admins may enforce
MFA for their users. Service-to-service authentication uses
short-lived (≤ 1h) tokens issued by the identity service
(MB-REQ-0003).

- **Target:** 100% of human accounts support MFA; 100% of service
  tokens ≤ 1h lifetime.
- **Measurement:** Identity service telemetry; weekly report.
- **Failure consequence:** P1 alert; non-compliant tokens revoked.
- **REQs/DECs:** DEC-0004, MB-REQ-0003.

### 1.4 Secrets management

No secrets in source code, configuration files, or container images.
All secrets are stored in a managed secret store and injected at
runtime. Secret rotation is automated for database credentials, API
keys, and signing keys.

- **Target:** Zero secrets in committed artefacts; 100% of secrets
  rotated per their rotation policy.
- **Measurement:** Pre-commit secret scanner; CI pipeline check;
  rotation compliance report monthly.
- **Failure consequence:** P0 alert; commit blocked; secret rotated
  immediately.
- **REQs/DECs:** MB-REQ-0018, DEC-0016.

## 2. Reliability NFRs

Owner: Infrastructure Lead.

### 2.1 Uptime

The platform targets 99.9% monthly availability for the control
plane (tenant provisioning, identity, audit query) and 99.95% for
the audit append path (because state changes are conditional on
audit write success — see WF-06).

- **Target:** Control plane 99.9% monthly; audit append 99.95%
  monthly.
- **Measurement:** Synthetic probes every 30s; uptime computed
  monthly.
- **Failure consequence:** SLA penalty per tenant contract (deferred
  to Q25 SLA tiers); root-cause review.
- **Note:** SLA tiers per tenant are an open question (Q25); the
  NFR target here is the floor.
- **REQs/DECs:** DEC-0020, MB-REQ-0015.

### 2.2 RTO and RPO

Recovery Time Objective and Recovery Point Objective are BLOCKED on
Q22 (DR RTO/RPO targets). Provisional targets — pending Q22
resolution — are RTO ≤ 4h, RPO ≤ 1h.

- **Target (provisional):** RTO ≤ 4h; RPO ≤ 1h.
- **Measurement:** Quarterly DR drill (WF-10); drill report records
  actual RTO and RPO.
- **Failure consequence:** If drill exceeds target, the platform's
  DR plan is reworked and the drill is repeated within 30 days.
- **REQs/DECs:** Law-REQ-0022, Law-REQ-0021.

### 2.3 Backpressure and circuit breaking

Every outbound call (to a database, a third-party API, or another
service) must be wrapped in a circuit breaker (MB-REQ-0015). Every
inbound queue must publish backpressure signals that callers honor
(MB-REQ-0014).

- **Target:** 100% of outbound calls circuit-broken; 100% of inbound
  queues publish backpressure.
- **Measurement:** Code-level audit at CI; runtime telemetry on
  circuit state.
- **Failure consequence:** P1 alert on uncovered call path; PR
  blocked until wrapped.
- **REQs/DECs:** MB-REQ-0014, MB-REQ-0015, DEC-0020.

### 2.4 Idempotency

Every state-changing API endpoint must accept an idempotency key
and deduplicate requests within the key's lifetime (default 24h).
The identity service, audit service, and tenant provisioning API
all enforce this (MB-REQ-0013).

- **Target:** 100% of mutating endpoints idempotent; duplicate
  requests return the original response.
- **Measurement:** Integration test suite includes a duplicate-key
  test for every mutating endpoint.
- **Failure consequence:** P1 alert; endpoint disabled until fixed.
- **REQs/DECs:** DEC-0008, MB-REQ-0013, Pain-REQ-0011.

## 3. Performance NFRs

Owner: Infrastructure Lead.

### 3.1 API latency

P95 latency for read endpoints under nominal load (1k req/s
aggregate): ≤ 200ms. P95 latency for mutating endpoints under
nominal load: ≤ 500ms (the higher bound accounts for audit write
synchronous append).

- **Target:** P95 read ≤ 200ms; P95 mutate ≤ 500ms.
- **Measurement:** Continuous synthetic monitoring; alert on
  threshold breach.
- **Failure consequence:** P2 alert; capacity review triggered.
- **REQs/DECs:** DEC-0020, MB-REQ-0014.

### 3.2 Throughput

The platform must sustain 10k req/s aggregate across all tenants in
Phase 1 capacity. Per-tenant rate limits are configurable
(Pain-REQ-0008) and default to 100 req/s per tenant.

- **Target:** 10k req/s aggregate sustained; per-tenant default 100
  req/s.
- **Measurement:** Load test in staging weekly; production telemetry
  continuously.
- **Failure consequence:** P2 alert; capacity added.
- **REQs/DECs:** Pain-REQ-0008, DEC-0020.

### 3.3 Audit log append latency

Audit log append (the synchronous step in WF-06) must complete in
P95 ≤ 50ms. This is the binding constraint on mutating endpoint
latency (§3.1).

- **Target:** P95 ≤ 50ms.
- **Measurement:** Audit service telemetry; alert on threshold
  breach.
- **Failure consequence:** P1 alert; capacity added; if persistent,
  mutating endpoints degrade gracefully (return 503 with
  backpressure).
- **REQs/DECs:** DEC-0006, MB-REQ-0004.

## 4. Compliance NFRs

Owner: Compliance Lead.

### 4.1 Audit log retention

Audit log entries must be retained for a minimum of 5 years and a
maximum of 7 years (subject to jurisdiction; Q1 may extend the
minimum). Deletion before the minimum is forbidden. Deletion after
the maximum is mandated unless a litigation hold is in place.

- **Target:** 5y minimum retention; 7y maximum retention.
- **Measurement:** Retention scanner; monthly compliance report.
- **Failure consequence:** P0 alert; regulatory exposure.
- **Note:** Jurisdiction-specific extensions blocked on Q1.
- **REQs/DECs:** Law-REQ-0009.

### 4.2 Audit log tamper-evidence

The audit log must be tamper-evident: any modification of a past
entry must be detectable on read. The hash chain (DEC-0007) provides
this. A daily verifier scans the chain and alerts on any mismatch.

- **Target:** 100% of mismatches detected within 24h.
- **Measurement:** Daily verifier run; alert on mismatch.
- **Failure consequence:** P0 alert; platform mutations halted for
  affected tenants; Security Lead investigation.
- **REQs/DECs:** DEC-0007, MB-REQ-0004.

### 4.3 Data residency

Tenant data must reside in the jurisdiction the tenant was
provisioned for. Cross-jurisdiction replication is forbidden unless
the tenant's contract explicitly permits it and the relevant
data-protection regime allows it (blocked on Q1, Q3).

- **Target:** 100% of tenant data in provisioned jurisdiction.
- **Measurement:** Storage topology scanner; weekly compliance
  report.
- **Failure consequence:** P0 alert; data repatriated; root-cause
  review.
- **Note:** Provisional until Q1/Q3 resolved.
- **REQs/DECs:** Law-REQ-0012, Law-REQ-0013.

### 4.4 Breach notification

A confirmed personal-data breach must be notified to the relevant
supervisory authority within 72h of detection (GDPR Art.33 floor).
The DPO owns the notification. The clock starts at detection, not
at confirmation.

- **Target:** Notification within 72h of detection.
- **Measurement:** Incident response log; post-incident review
  records detection-to-notification time.
- **Failure consequence:** Regulatory exposure; P0 alert on the
  incident itself.
- **REQs/DECs:** Law-REQ-0016.

## 5. Observability NFRs

Owner: Infrastructure Lead.

### 5.1 Telemetry coverage

Every service boundary (inbound request, outbound call, domain
event emission, audit write) must emit OpenTelemetry spans. Span
coverage is measured as the fraction of boundaries with spans.

- **Target:** 100% boundary coverage.
- **Measurement:** Coverage scanner in CI; weekly report.
- **Failure consequence:** P2 alert; PR blocked until coverage
  added.
- **REQs/DECs:** DEC-0020, MB-REQ-0020.

### 5.2 Log retention

Application logs (distinct from audit logs) are retained for 30
days hot, 90 days cold. Audit logs follow §4.1, not this section.

- **Target:** 30d hot; 90d cold.
- **Measurement:** Log backend retention policy audit; monthly.
- **Failure consequence:** P2 alert; retention policy corrected.
- **REQs/DECs:** DEC-0020.

### 5.3 Alerting latency

An alert condition (e.g., heartbeat missing, error rate spike) must
trigger a page within 60s of the condition arising.

- **Target:** ≤ 60s detection-to-page.
- **Measurement:** Synthetic alert injection monthly; actual alert
  telemetry continuously.
- **Failure consequence:** P1 alert on the alerting system itself;
  alert routing reviewed.
- **REQs/DECs:** DEC-0020, MB-REQ-0020.

## 6. Operability NFRs

Owner: Operations Lead.

### 6.1 Deployment frequency

The platform must support at least one deployment per day per
service without downtime. Blue/green deployments per tenant
(DEC-0017) are the mechanism.

- **Target:** ≥ 1 deployment per day per service; zero-downtime.
- **Measurement:** Deployment log; success-rate telemetry.
- **Failure consequence:** P2 alert on rollback; deployment
  pipeline reviewed.
- **REQs/DECs:** DEC-0017.

### 6.2 Mean time to recovery (MTTR)

The mean time from incident detection to service restoration must
be ≤ 30 minutes for P0 incidents and ≤ 2h for P1 incidents.

- **Target:** P0 MTTR ≤ 30min; P1 MTTR ≤ 2h.
- **Measurement:** Incident postmortem records detection-to-restore
  time; monthly aggregate.
- **Failure consequence:** P2 review; runbook improvements.
- **REQs/DECs:** DEC-0020, Law-REQ-0020.

### 6.3 Backup verification

Backups must be verified (manifest checks + sample restore) within
24h of creation. A backup that fails verification is treated as a
failed backup (WF-09).

- **Target:** 100% of backups verified within 24h.
- **Measurement:** Verification log; daily report.
- **Failure consequence:** P1 alert; backup re-run.
- **REQs/DECs:** Law-REQ-0021, MB-REQ-0020.

## 7. Cross-cutting NFRs

Owner: Architecture Lead.

### 7.1 Testability

Every domain module must be unit-testable without external
dependencies (no database, no network, no filesystem). This is
enforced structurally by DEC-0002 (hexagonal architecture) and
MB-REQ-0011 (all I/O at boundary).

- **Target:** 100% of domain modules unit-testable in isolation.
- **Measurement:** Test suite runs in CI without external
  dependencies; coverage report.
- **Failure consequence:** P2 alert; PR blocked.
- **REQs/DECs:** DEC-0002, MB-REQ-0011, MB-REQ-0016, MB-REQ-0017,
  MB-REQ-0025, MB-REQ-0026.

### 7.2 Determinism

Domain logic must be deterministic given the same inputs and the
same injected time and random sources (MB-REQ-0016, MB-REQ-0017).
Non-determinism is forbidden in command handlers (MB-REQ-0025).

- **Target:** 100% of command handlers deterministic.
- **Measurement:** Property-based tests in CI; replay tests.
- **Failure consequence:** P2 alert; PR blocked.
- **REQs/DECs:** MB-REQ-0016, MB-REQ-0017, MB-REQ-0025.

### 7.3 Forward-only migrations

Database migrations must be forward-only (MB-REQ-0021). A migration
that requires a destructive down-migration is forbidden; the
compensation path is a forward migration that restores the prior
state.

- **Target:** 100% of migrations forward-only.
- **Measurement:** Migration review at PR; linter rejects down
  migrations.
- **Failure consequence:** P1 alert; PR blocked.
- **REQs/DECs:** DEC-0019, MB-REQ-0021, MB-REQ-0022.
