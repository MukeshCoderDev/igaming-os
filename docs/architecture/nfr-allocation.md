# NFR Allocation — Every NFR → ≥1 Mechanism

| Field | Value |
|---|---|
| Document | `docs/architecture/nfr-allocation.md` |
| Version | 5.3 (Phase 2) |
| Status | Approved |
| Owner | Architecture Lead |
| Authority | DEC-0025; Phase 2 hard acceptance (every NFR → ≥1 mechanism) |
| Linter | `scripts/check_traceability.sh` rule 8 enforces coverage |

This document maps every NFR in `docs/requirements/nfr.md` to ≥1
implementation mechanism. The linter (rule 8) cross-checks the NFR
IDs against `nfr.md` and fails if any NFR is missing a mechanism
row here. The mapping is the contract between requirements and
architecture: an NFR without a mechanism is unimplementable; a
mechanism without an NFR is unjustified.

## §1. How to read this document

Each row in the tables below corresponds to one NFR. The columns
are:

- **NFR ID** — the section number in `nfr.md` (e.g., §1.1).
- **NFR title** — short title.
- **Mechanism(s)** — one or more concrete implementation artefacts
  (component, library, configuration, runbook) that satisfy the NFR.
- **Owner** — the role accountable for the mechanism.
- **Phase delivered** — when the mechanism is implemented.
- **Validation** — how the mechanism is verified.

## §2. Security NFRs (nfr.md §1)

| NFR ID | NFR title | Mechanism(s) | Owner | Phase | Validation |
|---|---|---|---|---|---|
| §1.1 | Encryption at rest | PostgreSQL TDE via cloud-managed KMS (AWS KMS / GCP KMS); per-tenant key isolation where supported; 90-day auto-rotation; weekly storage-config scan | Infrastructure Lead | Phase 1 (config); Phase 3 (enforced) | Automated scan; P0 alert on gap |
| §1.2 | Encryption in transit (TLS 1.2+) | TLS termination at load balancer; mTLS for service-to-service via service mesh; continuous TLS scanner (sslyze / testssl) | Infrastructure Lead | Phase 2 (mesh); Phase 3 (services) | Continuous scan; P0 alert on downgrade |
| §1.3 | Authentication strength | Identity service (ADR-0004) issues short-lived tokens (≤1h access, ≤30d refresh); MFA enforcement via OIDC provider; service tokens ≤1h | Identity Lead | Phase 4–7 | Weekly identity-service telemetry report |
| §1.4 | Secrets management | Managed secret store (AWS Secrets Manager / GCP Secret Manager); runtime injection via sidecar; pre-commit secret scanner (gitleaks); CI pipeline check; rotation compliance report | Infrastructure Lead | Phase 2 (scanner); Phase 3 (store) | Pre-commit + CI gates; monthly rotation report |

## §3. Reliability NFRs (nfr.md §2)

| NFR ID | NFR title | Mechanism(s) | Owner | Phase | Validation |
|---|---|---|---|---|---|
| §2.1 | Uptime (control plane 99.9%; audit append 99.95%) | Multi-AZ deployment; blue/green per tenant (ADR-0017); synthetic probes every 30s; uptime computed monthly | Infrastructure Lead | Phase 2 (probes); Phase 3 (multi-AZ) | Synthetic monitoring; monthly uptime report |
| §2.2 | RTO and RPO (provisional: ≤4h / ≤1h) | Quarterly DR drill (WF-10); backup manifest verification (WF-09); RPO bounded by hourly incremental backups; RTO bounded by automated restore | Operations Lead | Phase 1 (workflow); Phase 3 (auto-restore) | Quarterly DR drill report; root-cause review on miss |
| §2.3 | Backpressure and circuit breaking | Reliability context (domain-boundaries.md §6): `reliability.lib.CircuitBreaker` on every outbound call; `reliability.lib.BackpressureSignal` published by inbound queues; CI code-level audit | Architecture Lead | Phase 1 (lib); Phase 3 (enforced) | CI audit; runtime circuit-state telemetry |
| §2.4 | Idempotency | `reliability.middleware.IdempotencyMiddleware` on every mutating endpoint; idempotency-key store (Redis) with 24h TTL; integration test for every mutating endpoint | Architecture Lead | Phase 1 (middleware); Phase 3 (store) | Integration test suite; P1 alert on uncovered endpoint |

## §4. Performance NFRs (nfr.md §3)

| NFR ID | NFR title | Mechanism(s) | Owner | Phase | Validation |
|---|---|---|---|---|---|
| §3.1 | API latency (P95 read ≤200ms; P95 mutate ≤500ms) | Read-model projections (DEC-0018); DB connection pooling; query plan review at PR; continuous synthetic monitoring | Infrastructure Lead | Phase 8 (read models); Phase 3 (pooling) | Continuous synthetic; P2 alert on breach |
| §3.2 | Throughput (10k req/s aggregate; 100 req/s per tenant default) | Per-tenant rate limiter (Pain-REQ-0008); horizontal autoscaling; weekly staging load test | Infrastructure Lead | Phase 1 (limiter); Phase 3 (autoscale) | Weekly load test; production telemetry |
| §3.3 | Audit log append latency (P95 ≤50ms) | Append-optimized storage (PostgreSQL `INSERT` only); hash-chain computation in-process (no network hop); partitioning by tenant + month | Architecture Lead | Phase 1 (contract); Phase 8 (impl) | Audit-service telemetry; P1 alert on breach |

## §5. Compliance NFRs (nfr.md §4)

| NFR ID | NFR title | Mechanism(s) | Owner | Phase | Validation |
|---|---|---|---|---|---|
| §4.1 | Audit log retention (5y min; 7y max) | Forward-only archival to S3 Object Lock ( Compliance Mode); retention scanner; monthly compliance report | Compliance Lead | Phase 1 (policy); Phase 8 (archival) | Monthly retention scanner; P0 alert on under-retention |
| §4.2 | Audit log tamper-evidence | Hash chain (DEC-0007); daily verifier scan; external chain-head publication to S3 Object Lock | Architecture Lead | Phase 1 (contract); Phase 8 (verifier) | Daily verifier; P0 alert on mismatch |
| §4.3 | Data residency | Per-tenant residency tag at provisioning (WF-01); storage topology scanner; replication policy enforced per tag | Data Protection Officer | Phase 1 (tag); Phase 3 (scanner) | Weekly scanner; P0 alert on violation |
| §4.4 | Breach notification within 72h | Incident response runbook with DPO owner; 72h SLA timer starts at detection; IR log records detection-to-notification time | Data Protection Officer | Phase 1 (runbook); Phase 2 (drill) | Post-incident review; P0 on the incident itself |

## §6. Observability NFRs (nfr.md §5)

| NFR ID | NFR title | Mechanism(s) | Owner | Phase | Validation |
|---|---|---|---|---|---|
| §5.1 | Telemetry coverage (100% boundary) | OpenTelemetry SDK (ADR-0020); `telemetry.middleware.SpanMiddleware` on every boundary; CI coverage scanner | Infrastructure Lead | Phase 2 (SDK); Phase 3 (middleware) | CI scanner; weekly coverage report; P2 on gap |
| §5.2 | Log retention (30d hot; 90d cold) | Log backend (Loki / Elasticsearch) with retention policy; monthly retention audit | Infrastructure Lead | Phase 2 (backend); Phase 3 (audit) | Monthly audit; P2 on policy drift |
| §5.3 | Alerting latency (≤60s detection-to-page) | Synthetic alert injection monthly; alert routing via PagerDuty; alert-on-alert for routing failure | Infrastructure Lead | Phase 2 (router); Phase 3 (synthetic) | Monthly synthetic; P1 on routing failure |

## §7. Operability NFRs (nfr.md §6)

| NFR ID | NFR title | Mechanism(s) | Owner | Phase | Validation |
|---|---|---|---|---|---|
| §6.1 | Deployment frequency (≥1/day per service; zero-downtime) | Blue/green per tenant (ADR-0017); CI/CD pipeline; deployment success-rate telemetry | Infrastructure Lead | Phase 2 (pipeline); Phase 3 (blue/green) | Deployment log; P2 on rollback |
| §6.2 | MTTR (P0 ≤30min; P1 ≤2h) | Incident runbooks per service; on-call rotation; incident postmortem records detection-to-restore | Operations Lead | Phase 2 (runbooks); Phase 3 (on-call) | Monthly MTTR aggregate; P2 review on miss |
| §6.3 | Backup verification (within 24h) | `backups.service.BackupExecutor` (WF-09) with manifest checksums; sample-restore job; daily verification report | Operations Lead | Phase 1 (workflow); Phase 3 (auto-verify) | Daily verification log; P1 on failure |

## §8. Cross-cutting NFRs (nfr.md §7)

| NFR ID | NFR title | Mechanism(s) | Owner | Phase | Validation |
|---|---|---|---|---|---|
| §7.1 | Testability (100% domain unit-testable in isolation) | Hexagonal architecture (ADR-0002); static analyzer rejecting infra imports from `domain/`; CI test suite runs without external deps | Architecture Lead | Phase 2 (analyzer); Phase 3 (tests) | CI suite; coverage report; P2 on gap |
| §7.2 | Determinism (100% command handlers deterministic) | Injectable time (MB-REQ-0016) and random (MB-REQ-0017); property-based tests; replay tests; CI gate | Architecture Lead | Phase 1 (contracts); Phase 3 (tests) | Property-based test suite; P2 on nondeterminism |
| §7.3 | Forward-only migrations | Linter rejecting down-migrations (ADR-0019); expand-contract pattern; migration review at PR | Architecture Lead | Phase 2 (linter); Phase 3 (pattern) | CI linter; P1 on attempted down-migration |

## §9. Coverage verification

The linter (rule 8) verifies that every NFR section in `nfr.md`
(§1.1 through §7.3) has at least one row in this document. The
NFR IDs are extracted from `nfr.md` section headings; the
mechanism rows are extracted from this document's tables. A
missing NFR ID is a linter failure.

As of Phase 2, the NFR set is:

- §1.1, §1.2, §1.3, §1.4 (Security; 4 NFRs)
- §2.1, §2.2, §2.3, §2.4 (Reliability; 4 NFRs)
- §3.1, §3.2, §3.3 (Performance; 3 NFRs)
- §4.1, §4.2, §4.3, §4.4 (Compliance; 4 NFRs)
- §5.1, §5.2, §5.3 (Observability; 3 NFRs)
- §6.1, §6.2, §6.3 (Operability; 3 NFRs)
- §7.1, §7.2, §7.3 (Cross-cutting; 3 NFRs)

**Total: 24 NFRs.** All 24 have at least one mechanism row above.
Coverage = 24 / 24 = 100%.

## §10. Cross-references

- NFR definitions: `docs/requirements/nfr.md`
- Domain boundaries (mechanism homes): `docs/requirements/domain-boundaries.md`
- ADR INDEX (mechanism owners): `docs/adr/INDEX.md`
- Capacity assumptions (throughput, latency validation): `docs/architecture/capacity-assumptions.md`
- Risk register (mechanism failure modes): `docs/architecture/risk-register.md`
- Linter rule 8: `scripts/check_traceability.sh`
