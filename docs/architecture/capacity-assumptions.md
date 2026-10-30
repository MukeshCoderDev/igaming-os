# Capacity Assumptions

| Field | Value |
|---|---|
| Document | `docs/architecture/capacity-assumptions.md` |
| Version | 5.3 (Phase 2) |
| Status | Approved |
| Owner | Infrastructure Lead |
| Authority | DEC-0025; Phase 2 hard acceptance |
| Schema | Assumption \| Source \| RPS/QPS \| p99 \| Peak concurrency \| Headroom factor \| Owner \| Validation plan |
| Pillar coverage | ≥1 row per Increment-1 pillar (Tenancy, Identity, Audit, Reliable Core) |

This document records the capacity assumptions that underwrite the
Phase 1 NFRs (especially `nfr.md` §3 Performance). Every assumption
is tagged with a source; assumptions that depend on the budget
question Q5 carry status **ASSUMED** until Q5 is resolved. The
validation plan column records how the assumption will be tested
(load test, production telemetry, pilot partner volume).

## §1. Schema

Each row carries eight columns:

| Column | Meaning |
|---|---|
| Assumption | The quantitative or qualitative capacity claim. |
| Source | Where the number came from (industry benchmark, customer interview, internal estimate, regulatory floor). |
| RPS/QPS | Sustained requests/queries per second the system must handle for this assumption. |
| p99 | 99th-percentile latency target for this assumption's operation. |
| Peak concurrency | Maximum simultaneous in-flight operations. |
| Headroom factor | Multiplier above expected peak (typical: 2×–5×). |
| Owner | Role accountable for validating the assumption. |
| Validation plan | How and when the assumption will be tested. |

Rows whose validation depends on Q5 (budget for Phases 1–3) are
marked **ASSUMED** in the Source column. Q5 is BLOCKED per
`unresolved-decisions.md`; resolution is required before the
validation plan can be executed.

## §2. Capacity table

| # | Assumption | Source | RPS/QPS | p99 | Peak concurrency | Headroom factor | Owner | Validation plan |
|---|---|---|---|---|---|---|---|---|
| C-01 | Tenant provisioning throughput: 10 new tenants/hour sustained | DEC-0014; pilot partner onboarding estimate (Q4) | 0.003 req/s (10/hr) | 5s | 1 concurrent provisioning | 5× | Architecture Lead | Phase 3 load test: 50 tenants/hr; pilot partner onboarding (Q4 unblock) |
| C-02 | Tenant configuration update throughput: 100 updates/min per tenant | Pain-REQ-0002; discovery interview #2 | 1.7 req/s per tenant | 500ms | 10 concurrent updates per tenant | 3× | Infrastructure Lead | Phase 3 load test: 300 updates/min per tenant |
| C-03 | User invitation acceptance throughput: 1k invitations/hour platform-wide | Discovery interview #1 (Customer A); pre-Phase-1 discovery | 0.28 req/s | 2s | 50 concurrent invitations | 5× | Identity Lead | Phase 4 load test: 5k invitations/hour |
| C-04 | SSO authentication throughput: 1k logins/min platform-wide at peak | Pain-REQ-0003; discovery interview #3 (Customer C) | 16.7 req/s | 1s | 100 concurrent logins | 3× | Identity Lead | Phase 4 load test: 3k logins/min; verify p99 ≤1s |
| C-05 | Role assignment throughput: 500 assignments/min platform-wide | Pain-REQ-0012; discovery interview #12 (Customer L) | 8.3 req/s | 500ms | 50 concurrent assignments | 3× | Identity Lead | Phase 5 load test: 1.5k assignments/min |
| C-06 | Audit log append throughput: 5k events/s sustained | NFR §3.3; Law-REQ-0010; DEC-0006 | 5k req/s | 50ms (NFR §3.3) | 5k concurrent appends | 2× | Architecture Lead | Phase 8 load test: 10k events/s for 1h; verify hash chain integrity |
| C-07 | Audit log query throughput: 100 queries/min compliance-team peak | Pain-REQ-0004; discovery interview #4 (Customer D) | 1.7 req/s | 2s (1y range scan) | 20 concurrent queries | 3× | Architecture Lead | Phase 8 load test: 300 queries/min; verify p99 ≤2s for 1y range |
| C-08 | Audit log export throughput: 10 exports/hour; each up to 10M entries | Pain-REQ-0004; compliance team workflow | 0.003 req/s | 30min per export | 5 concurrent exports | 3× | Architecture Lead | Phase 8 load test: 30 exports/hour; verify ≤30min per 10M entry export |
| C-09 | API read endpoint throughput: 10k req/s aggregate platform-wide | NFR §3.2 | 10k req/s | 200ms (NFR §3.1) | 1k concurrent reads | 2× | Infrastructure Lead | Phase 4 staging load test: 20k req/s for 1h; verify p99 ≤200ms |
| C-10 | API mutate endpoint throughput: 5k req/s aggregate platform-wide | NFR §3.1 (mutate p95 ≤500ms) | 5k req/s | 500ms (NFR §3.1) | 500 concurrent mutations | 2× | Infrastructure Lead | Phase 4 staging load test: 10k req/s for 1h; verify p99 ≤500ms |
| C-11 | Per-tenant rate limit default: 100 req/s; configurable up to 1k req/s | Pain-REQ-0008; discovery interview #8 (Customer H) | 100 req/s default | n/a | 100 per tenant | n/a | Infrastructure Lead | Phase 3 load test: verify limit enforcement; verify per-tenant isolation |
| C-12 | Webhook delivery throughput: 1k deliveries/s platform-wide | Pain-REQ-0010; discovery interview #10 (Integrator J) | 1k deliveries/s | 5s (tenant-dependent) | 1k concurrent deliveries | 3× | Infrastructure Lead | Phase 6 load test: 3k deliveries/s; verify retry semantics |
| C-13 | Heartbeat telemetry throughput: 100 services × 6 heartbeat/min = 600 signals/min | NFR §5.1; DEC-0020 | 10 signals/s | 100ms | 100 concurrent | 5× | Infrastructure Lead | Phase 2 staging test: verify 600/min sustained for 24h |
| C-14 | Backup execution: 1 full + 24 incremental per day per tenant; 100 tenants Phase 1 | Law-REQ-0021; DEC-0020 | 25 backup jobs/day/tenant | 1h full; 5min incremental | 10 concurrent jobs | 3× | Operations Lead | Phase 3 load test: 100 tenants × 25 jobs/day; verify ≤1h full |
| C-15 | DR restore (quarterly drill): full restore of 100 tenants in ≤4h RTO | NFR §2.2 (provisional); Q22 | n/a | 4h (RTO) | 1 concurrent restore | n/a | Operations Lead | Phase 3 DR drill: verify ≤4h for 100 tenants; Q22 unblock required |
| C-16 | Database storage: 100 tenants × 1GB/tenant Phase 1 = 100GB; growth 10%/month | Internal estimate; ASSUMED pending Q5 | n/a | n/a | n/a | 2× | Infrastructure Lead | Phase 3: verify 100GB baseline; quarterly growth review |
| C-17 | Audit log storage: 5k events/s × 86400 s/day × 365d × 5y retention ≈ 790GB uncompressed; 5:1 compression → 160GB | Law-REQ-0009 (5y floor); DEC-0006 | n/a | n/a | n/a | 2× | Infrastructure Lead | Phase 8: verify storage projection; quarterly growth review |
| C-18 | Compute capacity: 100 tenants × 5 services × 2 replicas = 1k pods Phase 1 | Internal estimate; ASSUMED pending Q5 | n/a | n/a | n/a | 2× | Infrastructure Lead | Phase 3: verify 1k pod baseline; Q5 unblock required for production sizing |
| C-19 | Concurrent realtime connections: 1k concurrent WebSocket/SSE clients platform-wide | Discovery interview #4 (Customer D); Phase 7 scope | n/a (connection-bound) | 100ms event push | 1k concurrent connections | 3× | Infrastructure Lead | Phase 7 load test: 3k concurrent connections; verify p99 push ≤100ms |
| C-20 | Q5-dependent production sizing: cloud spend ≤ $X/month for Phases 1–3 | Q5 (BLOCKED); ASSUMED | n/a | n/a | n/a | n/a | Commercial Lead | Q5 unblock; then re-baseline C-16, C-18 with funder-approved budget |

## §3. Pillar coverage

The Phase 2 hard acceptance requires ≥1 row per Increment-1 pillar.
The four pillars are Tenancy, Identity, Audit, Reliable Core. The
mapping below confirms coverage.

| Pillar | Capacity rows | Notes |
|---|---|---|
| Tenancy | C-01, C-02, C-16, C-18 | Provisioning + config + storage + compute |
| Identity | C-03, C-04, C-05 | Invitation + SSO + role assignment |
| Audit | C-06, C-07, C-08, C-17 | Append + query + export + storage |
| Reliable Core | C-09, C-10, C-11, C-12, C-13, C-14, C-15, C-19, C-20 | API throughput + rate limit + webhooks + heartbeat + backup + DR + realtime + Q5-dependent sizing |

All four pillars have ≥1 row. Reliable Core has the most rows
because it is the substrate for all other pillars.

## §4. ASSUMED status (Q5-dependent)

Rows C-16, C-18, and C-20 carry **ASSUMED** status because their
validation depends on Q5 (budget for Phases 1–3) being resolved.
Q5 is BLOCKED per `unresolved-decisions.md`. Until Q5 is resolved:

- C-16 and C-18 are baseline estimates only; production sizing is
  not validated.
- C-20 is the budget envelope itself; no validation is possible
  without funder commitment.

The Phase 0 evidence pack (`phase-0-evidence.md` Gate 3 — Financial)
records the Q5 status. If Q5 is BLOCKED at the gate, Phase 3 does
not start (per the Phase 2 gate criterion: "If any missing or
BLOCKED → Phase 3 does not start").

## §5. Validation cadence

| Validation type | Cadence | Owner |
|---|---|---|
| Staging load test | Weekly | Infrastructure Lead |
| Production telemetry review | Weekly | Infrastructure Lead |
| Pilot-partner volume validation | On pilot partner activation (Q4 unblock) | Commercial Lead |
| Quarterly growth review | Quarterly | Infrastructure Lead |
| Quarterly DR drill | Quarterly | Operations Lead |
| Q5 unblock review | At Phase 0 gate | Commercial Lead |

## §6. Cross-references

- NFR §3 (Performance): `docs/requirements/nfr.md`
- NFR §2.2 (RTO/RPO, provisional pending Q22): `docs/requirements/nfr.md`
- Open question Q5 (budget BLOCKED): `docs/requirements/unresolved-decisions.md`
- Phase 0 evidence Gate 3 (Financial): `docs/phase-0-evidence.md`
- Risk register (capacity risks): `docs/architecture/risk-register.md`
- ADR INDEX (mechanism owners): `docs/adr/INDEX.md`
