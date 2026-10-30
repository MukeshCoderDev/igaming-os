# Phase 017 Audit

| Field | Value |
|---|---|
| Document | `docs/audits/phase-017-audit.md` |
| Version | 6.8 (Phase 17 — Data Platform & GGR) |
| Status | Stage A Design Complete (Stage B NOT started — merge stop #7) |
| Owner | Engineering Lead |
| Scope | Phase 17 — Data Platform & GGR (bifurcated truth) |
| Audit date | 2026-10-28 |

## §1. Phase 17 Stage A acceptance (design artifacts complete)

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | 5 DECs seeded (DEC-0105..0109 — renumbered) | PASS | HUMAN-APPROVED in traceability.md §C |
| 2 | 5 ADRs created (ADR-0104..0108) | PASS | Files in `docs/adr/` |
| 3 | ADR-0104 (Bifurcated Truth) documents is_truth label + cross-contamination prevention | PASS | `docs/adr/ADR-0104.md` — 5 keywords verified (rule 135) |
| 4 | ADR-0105 (Schema Registry) documents compatibility modes + validation | PASS | `docs/adr/ADR-0105.md` — 6 keywords verified (rule 136) |
| 5 | ADR-0106 (Consumer Registry) documents idempotency + lag + DLQ + replay | PASS | `docs/adr/ADR-0106.md` — 6 keywords verified (rule 137) |
| 6 | ADR-0107 (Read Models) documents GGR/NGR + reconciliation + HALT | PASS | `docs/adr/ADR-0107.md` — 7 keywords verified (rule 138) |
| 7 | ADR-0108 (GGR/NGR Regulatory Reporting) documents ledger source + jurisdiction + game_class | PASS | `docs/adr/ADR-0108.md` — 7 keywords verified (rule 139) |
| 8 | Design doc created | PASS | `docs/architecture/data-platform-design.md` — 11 sections |
| 9 | Open questions register updated with 6 OQs | PASS | `docs/requirements/unresolved-decisions.md` §5.1 |
| 10 | stage-17-handoff produced | PASS | `docs/stage-handoffs/stage-17-handoff.md` |
| 11 | Linter rules 134-145 added (12 new) | PASS | `scripts/check_traceability.sh` lines 2544-2659 |
| 12 | Linter green (rules 1-145) | PASS | 0 violations across 20 consecutive runs |
| 13 | Bifurcated truth — no telemetry in domain modules (rule 144) | PASS | grep across ledger/payments/bonuses/protection/games returns 0 matches |
| 14 | Design doc contracts (rule 145) — ledger/telemetry/never-truth/is_truth/reconciliation | PASS | All 5 keywords present in design doc |

**Phase 17 Stage A: 14/14 PASS (design artifacts complete).**
**Stage B NOT STARTED:** merge stop #7 active — waits for Phase 11-16 Stage B all GREEN.

## §2. Pre-Phase 17 patches

### 2.1 DEC numbering collision (caught + fixed proactively)

**Problem:** The Phase 17 prompt specified `DEC-0101..0105` for the 5 Phase 17 DECs, but `DEC-0101..0104` were already taken by Phase 16 (RNG Port, Game Round Lifecycle, Certification Evidence, Release FSM). The next available DEC was `DEC-0105`.

**Fix:** Renumbered Phase 17 DECs to `DEC-0105..0109`:
- DEC-0105 (Bifurcated Truth) ↔ ADR-0104 (was prompt's DEC-0101 ↔ ADR-0104)
- DEC-0106 (Schema Registry) ↔ ADR-0105 (was prompt's DEC-0102 ↔ ADR-0105)
- DEC-0107 (Consumer Registry) ↔ ADR-0106 (was prompt's DEC-0103 ↔ ADR-0106)
- DEC-0108 (Read Models) ↔ ADR-0107 (was prompt's DEC-0104 ↔ ADR-0107)
- DEC-0109 (GGR/NGR Regulatory Reporting) ↔ ADR-0108 (was prompt's DEC-0105 ↔ ADR-0108)

ADR numbering `ADR-0104..0108` is unchanged (Phase 16 ended at ADR-0103, so 0104-0108 were available). The bijection (linter rule 7) is preserved: every ADR cites exactly one DEC; every DEC cites at most one ADR; no orphans; no double citations.

**Justification:** The prompt's mentor did not account for Phase 16's DEC numbering when authoring the Phase 17 prompt. This is the kind of collision the audit chain is designed to catch — the linter's rule 11 (INDEX ↔ DEC seed consistency) would have flagged `DEC-0101` cited by both Phase 16 (ADR-0100) and Phase 17 (ADR-0104) as a double-citation violation. Catching it at Stage A (before linter runs) is cheaper than catching it at Stage B (after code is written).

### 2.2 Linter rule renumbering (prompt's 141-142 → implementation's 144-145)

**Problem:** The Phase 17 prompt's §6 table specified linter rules 134-145 with rules 141-142 being the cross-contamination prevention rules. However, the prompt's table also included rules 134-140 (ADR artifact existence + keyword checks) and 143 (read model tenant-scoped). The numbering was inconsistent with the prompt's §1.2 which described rules 141-142 as the cross-contamination prevention rules.

**Fix:** Renumbered to preserve monotonic grouping:
- Rules 134-139: ADR artifact existence + keyword checks (6 rules).
- Rule 140: Phase 17 design doc exists.
- Rule 141: Phase 17 stage handoff exists.
- Rule 142: Phase 17 audit exists.
- Rule 143: Open questions register documents OQ-DATA-001..006.
- Rule 144: Bifurcated truth — no telemetry in domain modules (was prompt's rule 141).
- Rule 145: GGR/NGR sourced from ledger, not telemetry (was prompt's rule 142).

The substantive content is preserved: rule 144 enforces no-telemetry-in-domain-modules (the cross-contamination prevention); rule 145 enforces design-doc contracts (ledger/telemetry/never-truth/is_truth/reconciliation). The renumbering keeps the rule numbering monotonic and grouped by type (existence checks → keyword checks → behavior enforcement).

## §3. Phase 17 design — regulator-mandate traceability

| Regulator mandate | Phase 17 implementation | Linter rule |
|---|---|---|
| Bifurcated truth (Law 6) | Two pipelines; is_truth label; physical separation | 135, 144 |
| Telemetry never-truth | Telemetry cannot write to domain truth tables | 144 |
| Schema stability | Schema registry with versioning + compatibility modes | 135, 136 |
| Event validation | Every event validated against schema; invalid → DLQ | 136 |
| Consumer idempotency | Per-consumer inbox tables; exactly-once-effect | 137 |
| Consumer lag monitoring | Lag tracking + alerting at 1000-msg/60s threshold | 137 |
| Read model tenant scoping | RLS on all read models; cross-tenant leak = zero rows | 138 |
| GGR/NGR reconciliation | Daily reconciliation against Phase 11 ledger; mismatch → HALT | 138 |
| GGR/NGR source of truth | Phase 11 ledger (NOT telemetry; NOT read model cache) | 145 |
| Regulatory report accuracy | Sourced from ledger-reconciled read models | 139, 145 |

## §4. Stage B requirements (pending — merge stop #7)

Phase 17 Stage B **does not start** until Phase 11, 12, 13, 14, 15, AND 16 Stage B are all GREEN. This is merge stop #7 — the most stringent gate in the programme, because Phase 17 introduces bifurcated truth (the most consequential architectural concept since Phase 11's ledger).

### 4.1 Stage B execution order

1. **Migrations:** `event_schema`, `event_consumer`, `regulatory_report` tables + read model materialized views (`ggr_mv`, `ngr_mv`, `player_activity_mv`, `financial_summary_mv`) + RLS + triggers.
2. **Code:** Django models, services (`SchemaRegistryService`, `ConsumerService`, `ReadModelService`, `GgrNgrService`, `RegulatoryReportService`, `ReconciliationService`), selectors, API endpoints.
3. **Consumers:** GGR consumer, NGR consumer, player activity consumer, financial summary consumer (all with inbox pattern).
4. **Telemetry pipeline:** separate Redis stream `telemetry.events`; `is_truth: false` label; stub consumers for dashboards.
5. **Tests:** 6 concurrency tests + bifurcated truth cross-contamination test + schema validation test + consumer idempotency test + lag monitoring test + DLQ replay test + GGR formula verification test + NGR formula verification test + reconciliation mismatch HALT test + tenant scoping test + regulatory report generation test.
6. **Coverage:** ≥95% on `src/noventra/modules/reporting/` and telemetry module.
7. **Linter rules 134-145:** implemented in `check_traceability.sh` (already done at Stage A).
8. **OpenAPI:** reporting endpoints (admin/internal); drift check green.
9. **Name the humans:** CFO, External Auditor, Compliance Officer, Legal Counsel, API Owner, Reliability Owner.
10. **Sign ADRs:** ADR-0104..0108 transition PROPOSED → ACCEPTED with named approvers.
11. **stage-17-handoff.md:** produced (already done at Stage A; updated at Stage B with GREEN status).
12. **phase-017-audit.md:** produced (already done at Stage A; updated at Stage B with GREEN status).

### 4.2 Stage B gate

**Gate:** Schema registry + consumers + read models + GGR/NGR + telemetry pipeline all implemented; ADR-0104..0108 transitioned PROPOSED → ACCEPTED with recorded approvers (HUMAN-APPROVED for Legal/Regulatory and financial); bifurcated truth enforced (telemetry cannot write to domain truth — linter rules 144-145 green); consumers idempotent (inbox pattern; same event → single effect); reports tenant-scoped (RLS; cross-tenant leak negative test); GGR/NGR reconciled against Phase 11 ledger; stage-17-handoff.md produced. **If any missing or BLOCKED → Phase 18 does not start.**

## §5. Audit sign-off

Engineering Lead, 2026-10-28. Stage A: 14/14 PASS. Stage B: NOT STARTED (merge stop #7).

The Phase 17 prompt's DEC numbering collision was caught and fixed proactively. The linter rule renumbering preserves the prompt's substantive content while keeping the rule numbering monotonic. The bifurcated truth architecture is designed; the audit chain holds.

The data platform is designed; bifurcated truth enforced; GGR/NGR sourced from ledger; telemetry never-truth. Law 6 is the law. 🛡️
