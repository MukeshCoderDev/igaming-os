# Architectural Risk Register

| Field | Value |
|---|---|
| Document | `docs/architecture/risk-register.md` |
| Version | 5.3 (Phase 2) |
| Status | Approved |
| Owner | Architecture Lead |
| Authority | DEC-0025; Phase 2 hard acceptance |
| Coverage | ≥1 row per Increment-1 pillar + vendor lock-in + scaling ceilings + single points of failure |

This register records the architectural risks inherited by Phase 3
and beyond. Each risk has: an ID, a title, a description, the
pillar or category, a likelihood and impact rating, an owner, a
mitigation, a due date, and a status. Risks are reviewed at each
phase boundary; new risks are added as they are identified.

## §1. Rating scheme

| Rating | Likelihood | Impact |
|---|---|---|
| 5 | Almost certain (>80%) | Catastrophic (programme failure) |
| 4 | Likely (50–80%) | Major (phase delay, regulatory exposure) |
| 3 | Possible (20–50%) | Moderate (rework, cost overrun) |
| 2 | Unlikely (5–20%) | Minor (local delay) |
| 1 | Rare (<5%) | Negligible |

Risk score = likelihood × impact. Score ≥ 16 → P0; ≥ 9 → P1; ≥ 4 →
P2; < 4 → P3.

## §2. Pillar risks

### 2.1 Tenancy pillar

| ID | Title | Description | L | I | Score | Owner | Mitigation | Due | Status |
|---|---|---|---|---|---|---|---|---|---|
| R-TNC-01 | RLS bypass via application bug | A service runs a query without setting `app.tenant_id`, exposing cross-tenant data. | 3 | 5 | 15 (P1) | Architecture Lead | Static analyzer (Phase 2) + integration test per service (Phase 3) + red-team (Phase 4) | Phase 4 | Open |
| R-TNC-02 | Tenant deletion data leak | Tenant deletion purges tenant data but leaves orphaned references in audit log or analytics replica. | 2 | 4 | 8 (P1) | Architecture Lead | Tenant deletion is multi-step (disable, archive, purge after retention); audit log retains per Law-REQ-0009; analytics replica purged separately | Phase 11 | Open |
| R-TNC-03 | Tenant configuration drift | Tenant self-serves a configuration that breaks the platform's invariants (e.g., disables audit). | 3 | 4 | 12 (P1) | Architecture Lead | Configuration schema validates invariants; dangerous changes require two-person approval | Phase 4 | Open |

### 2.2 Identity pillar

| ID | Title | Description | L | I | Score | Owner | Mitigation | Due | Status |
|---|---|---|---|---|---|---|---|---|---|
| R-IDT-01 | OIDC provider outage | Identity service depends on external OIDC provider; outage locks out all users. | 3 | 5 | 15 (P1) | Identity Lead | Multi-region OIDC provider; cached token validation (≤1h); break-glass admin access | Phase 4 | Open |
| R-IDT-02 | Token signing key compromise | Signing key leaked; attacker forges tokens. | 2 | 5 | 10 (P1) | Identity Lead | Key rotation (90d); key store (KMS); revocation list; short token lifetime (≤1h) | Phase 4 | Open |
| R-IDT-03 | Delegation chain depth DoS | Attacker creates deep delegation chain to slow authorization checks. | 2 | 3 | 6 (P2) | Identity Lead | Chain depth limit (default 3); per-request chain-walk budget | Phase 5 | Open |
| R-IDT-04 | SAML XML signature wrapping | Enterprise SAML assertion is wrapped to bypass signature verification. | 3 | 5 | 15 (P1) | Identity Lead | SAML library with strict wrapping checks; penetration test (Phase 5) | Phase 5 | Open |

### 2.3 Audit pillar

| ID | Title | Description | L | I | Score | Owner | Mitigation | Due | Status |
|---|---|---|---|---|---|---|---|---|---|
| R-AUD-01 | Hash chain break | Concurrent appends produce a chain break; verifier flags mismatch. | 2 | 5 | 10 (P1) | Architecture Lead | Append is serialized (single-threaded hash computation); load test (Phase 8) verifies integrity under contention | Phase 8 | Open |
| R-AUD-02 | Audit append latency exceeds 50ms | Audit append is synchronous on the mutating path; latency breach cascades to all mutations. | 3 | 4 | 12 (P1) | Architecture Lead | Append-optimized storage; partitioning; capacity C-06 load test | Phase 8 | Open |
| R-AUD-03 | Audit storage growth exceeds projection | 5y retention at 5k events/s grows faster than projected (C-17). | 3 | 3 | 9 (P1) | Infrastructure Lead | Quarterly growth review (C-17); compression; tiered storage | Ongoing | Open |
| R-AUD-04 | Daily verifier false negative | Verifier has a bug; mismatch goes undetected. | 2 | 5 | 10 (P1) | Architecture Lead | Verifier is itself audited; cross-verification by external chain-head publication | Phase 8 | Open |

### 2.4 Reliable Core pillar

| ID | Title | Description | L | I | Score | Owner | Mitigation | Due | Status |
|---|---|---|---|---|---|---|---|---|---|
| R-REL-01 | Idempotency store loss | Redis (idempotency store) loses data; replays succeed. | 2 | 4 | 8 (P1) | Architecture Lead | Redis persistence (AOF); multi-AZ replication; fail-open to reject on store unavailability | Phase 3 | Open |
| R-REL-02 | Circuit breaker cascade | All circuits open simultaneously under load shedding; system halts. | 3 | 4 | 12 (P1) | Architecture Lead | Tiered breakers (per-dependency, per-service, per-tenant); coordinated load shedding; capacity headroom | Phase 4 | Open |
| R-REL-03 | Backpressure ignored | A caller ignores backpressure signals and overloads a queue. | 3 | 3 | 9 (P1) | Architecture Lead | CI gate rejecting callers without backpressure handling; runtime alert on queue depth | Phase 3 | Open |
| R-REL-04 | Feature flag misconfiguration | Flag misconfiguration disables a critical path (e.g., audit). | 3 | 5 | 15 (P1) | Architecture Lead | Critical-path flags require two-person approval; canary rollout; instant rollback | Phase 4 | Open |
| R-REL-05 | Telemetry overhead | OpenTelemetry SDK overhead exceeds 3% CPU at production load. | 3 | 3 | 9 (P1) | Infrastructure Lead | Sampling strategy; SDK version pinning; load test (Phase 4) | Phase 4 | Open |

## §3. Vendor lock-in risks

| ID | Title | Description | L | I | Score | Owner | Mitigation | Due | Status |
|---|---|---|---|---|---|---|---|---|---|
| R-VND-01 | Cloud provider lock-in (Q9) | Platform uses cloud-specific services (KMS, RDS, S3) that complicate migration. | 4 | 3 | 12 (P1) | Infrastructure Lead | Cloud-agnostic abstractions where possible; multi-cloud for critical paths; document migration path | Ongoing | Open (Q9) |
| R-VND-02 | KYC vendor lock-in (Q6) | KYC workflow is tightly coupled to one vendor's API. | 4 | 3 | 12 (P1) | Compliance Lead | Anti-corruption layer around vendor API; contract portability tested at vendor selection | Phase 12+ | Open (Q6) |
| R-VND-03 | Sanctions/PEP vendor lock-in (Q7) | Screening workflow tightly coupled to one vendor. | 4 | 3 | 12 (P1) | Compliance Lead | Anti-corruption layer; list-format standardization | Phase 12+ | Open (Q7) |
| R-VND-04 | IdP vendor lock-in (Q8) | OIDC provider switch cost is high. | 3 | 3 | 9 (P1) | Identity Lead | Standards-based OIDC; avoid vendor-specific extensions; document migration | Phase 4 | Open (Q8) |
| R-VND-05 | Database vendor lock-in (Q10) | PostgreSQL-specific features (RLS, JSONB) complicate migration. | 3 | 3 | 9 (P1) | Architecture Lead | Limit PG-specific features to RLS + JSONB; document migration path | Ongoing | Open (Q10) |
| R-VND-06 | Event store vendor lock-in (Q11) | Event store choice (Phase 2) creates long-term lock-in. | 3 | 4 | 12 (P1) | Architecture Lead | Abstract behind port (DEC-0002); evaluate EventStoreDB vs Postgres-based vs DynamoDB at Phase 2 | Phase 2 | Open (Q11) |
| R-VND-07 | Workflow engine vendor lock-in (Q13) | If "buy" chosen, engine vendor becomes critical dependency. | 3 | 3 | 9 (P1) | Architecture Lead | Evaluate at Phase 8; anti-corruption layer if bought | Phase 8 | Open (Q13) |

## §4. Scaling ceiling risks

| ID | Title | Description | L | I | Score | Owner | Mitigation | Due | Status |
|---|---|---|---|---|---|---|---|---|---|
| R-SCL-01 | Audit append throughput ceiling | Hash chain is serialized; append throughput bounded by single-thread hash rate (~50k/s). | 2 | 4 | 8 (P1) | Architecture Lead | Shard by tenant (multiple chains); capacity C-06 load test verifies headroom | Phase 8 | Open |
| R-SCL-02 | Database connection ceiling | 100 tenants × 10 services × 10 connections = 10k connections; exceeds PG default. | 4 | 3 | 12 (P1) | Infrastructure Lead | Connection pooling (PgBouncer); read replicas; capacity C-18 sizing | Phase 3 | Open |
| R-SCL-03 | Webhook delivery queue ceiling | Single queue cannot sustain 1k deliveries/s (C-12). | 3 | 3 | 9 (P1) | Infrastructure Lead | Per-tenant queues; horizontal consumers; capacity C-12 load test | Phase 6 | Open |
| R-SCL-04 | Realtime connection ceiling | Single server sustains ~10k WebSocket connections; 1k Phase 1 concurrency (C-19) leaves headroom but production may exceed. | 3 | 3 | 9 (P1) | Infrastructure Lead | Horizontal scaling; sticky sessions; capacity C-19 load test | Phase 7 | Open |
| R-SCL-05 | Storage growth ceiling | Audit log 5y projection (C-17) is 160GB compressed; manageable but grows with tenant count. | 3 | 3 | 9 (P1) | Infrastructure Lead | Tiered storage (hot → cold → archive); quarterly growth review | Ongoing | Open |

## §5. Single points of failure

| ID | Title | Description | L | I | Score | Owner | Mitigation | Due | Status |
|---|---|---|---|---|---|---|---|---|---|
| R-SPOF-01 | Identity service SPOF | Identity service is sole token issuer; outage blocks all auth. | 3 | 5 | 15 (P1) | Identity Lead | Multi-AZ deployment; cached token validation; break-glass admin | Phase 4 | Open |
| R-SPOF-02 | Audit service SPOF | Audit append is synchronous on mutating path; outage blocks all mutations. | 3 | 5 | 15 (P1) | Architecture Lead | Multi-AZ audit service; append queue with fail-open policy for read endpoints; mutating endpoints degrade to 503 | Phase 8 | Open |
| R-SPOF-03 | Idempotency store SPOF | Loss of idempotency store breaks dedup. | 2 | 4 | 8 (P1) | Architecture Lead | Multi-AZ Redis; AOF persistence; fail-open to reject (R-REL-01) | Phase 3 | Open |
| R-SPOF-04 | Configuration store SPOF | Loss of config store blocks service startup. | 2 | 4 | 8 (P1) | Infrastructure Lead | Multi-AZ config store; local cache with TTL; fail-latest | Phase 3 | Open |
| R-SPOF-05 | Cloud provider region SPOF | Single-region deployment; region outage takes platform down. | 2 | 5 | 10 (P1) | Infrastructure Lead | Multi-region deployment (Phase 12+); DR plan (NFR §2.2) | Phase 12+ | Open |
| R-SPOF-06 | Workflow engine SPOF (Phase 8+) | Engine stops; no workflow progresses. | 3 | 4 | 12 (P1) | Architecture Lead | Multi-AZ engine; idempotent re-drive; dead-letter queue | Phase 8 | Open |

## §6. Risk review cadence

| Cadence | Owner | Action |
|---|---|---|
| Per phase boundary | Architecture Lead | Review all open risks; close mitigated; add new |
| Monthly | Engineering Lead | Review P0/P1 risks; track mitigation progress |
| Quarterly | Architecture Lead + Engineering Lead | Full register review; likelihood/impact re-rating |

## §7. Cross-references

- Phase 2 handoff (risks inherited by Phase 3): `docs/stage-handoffs/stage-02-handoff.md`
- Capacity assumptions (capacity-driven risks): `docs/architecture/capacity-assumptions.md`
- STRIDE threat model (security risks): `docs/architecture/security.md`
- Open questions (vendor selection risks): `docs/requirements/unresolved-decisions.md`
- ADRs (decisions that generate risks): `docs/adr/INDEX.md`
