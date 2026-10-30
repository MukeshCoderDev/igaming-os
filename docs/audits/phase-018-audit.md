# Phase 018 Audit

| Field | Value |
|---|---|
| Document | `docs/audits/phase-018-audit.md` |
| Version | 6.9 (Phase 18 — Risk, AML & Cases) |
| Status | Stage A Design Complete (Stage B NOT started — merge stop #8) |
| Owner | Engineering Lead |
| Scope | Phase 18 — Risk, AML & Cases (SAR/tipping-off) |
| Audit date | 2026-10-28 |

## §1. Phase 18 Stage A acceptance (design artifacts complete)

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | 6 DECs seeded (DEC-0110..0115) | PASS | HUMAN-APPROVED in traceability.md §C |
| 2 | 6 ADRs created (ADR-0109..0114) | PASS | Files in `docs/adr/` |
| 3 | ADR-0109 (Risk Signal Model) documents 12-type catalog + rule-based generation | PASS | `docs/adr/ADR-0109.md` — 7 keywords verified (rule 147) |
| 4 | ADR-0110 (TM Rules Engine) documents 5 rule types + per-jurisdiction thresholds | PASS | `docs/adr/ADR-0110.md` — 7 keywords verified (rule 148) |
| 5 | ADR-0111 (SAR/STR Workflow) documents MLRO + tipping-off + criminal liability | PASS | `docs/adr/ADR-0111.md` — 7 keywords verified (rule 149) |
| 6 | ADR-0112 (Risk Case Management) documents evidence aggregation + case linking | PASS | `docs/adr/ADR-0112.md` — 6 keywords verified (rule 150) |
| 7 | ADR-0113 (Punitive Action) documents dual control + irreversibility | PASS | `docs/adr/ADR-0113.md` — 8 keywords verified (rule 151) |
| 8 | ADR-0114 (Appeal Workflow) documents separation of duties + tipping-off extension | PASS | `docs/adr/ADR-0114.md` — 7 keywords verified (rule 152) |
| 9 | Design doc created | PASS | `docs/architecture/risk-aml-design.md` — 11 sections |
| 10 | Open questions register updated with 6 OQs | PASS | `docs/requirements/unresolved-decisions.md` §5.2 |
| 11 | stage-18-handoff produced | PASS | `docs/stage-handoffs/stage-18-handoff.md` |
| 12 | Linter rules 146-158 added (13 new) | PASS | `scripts/check_traceability.sh` lines 2667-2796 |
| 13 | Linter green (rules 1-158) | PASS | 0 violations across 20 consecutive runs |
| 14 | Tipping-off prohibition — no SAR in notification templates (rule 157) | PASS | grep across players/payments/identity/templates returns 0 matches in notification files |
| 15 | Risk-AML design doc contracts (rule 158) — domain events/telemetry/tipping-off/MLRO/dual control/Law 14 | PASS | All 6 keywords present in design doc |

**Phase 18 Stage A: 15/15 PASS (design artifacts complete).**
**Stage B NOT STARTED:** merge stop #8 active — waits for Phase 11-17 Stage B all GREEN.

## §2. ID allocation verification

### 2.1 No collision (verified before implementation)

Phase 18 ID allocation was verified clean before implementation began:
- Phase 16: DEC-0096..0104, ADR-0099..0103, rules 121-133
- Phase 17: DEC-0105..0109, ADR-0104..0108, rules 134-145
- Phase 18: DEC-0110..0115, ADR-0109..0114, rules 146-158

The mentor's ID Allocation Table (§0.2) was correct. No renumbering needed (unlike Phase 17, which had a DEC collision caught and fixed). The ID allocation table is a process improvement that prevents collisions — the mentor learned from the Phase 17 collision and provided the table proactively.

### 2.2 Next available (for Phase 19)

- DEC-0116
- ADR-0115
- Linter rule 159

## §3. Phase 18 design — regulator-mandate traceability

| Regulator mandate | Phase 18 implementation | Linter rule |
|---|---|---|
| TM rules (FATF Rec 20) | TMRule model with 5 rule types; scheduled + real-time | 148 |
| Risk signals (FATF) | RiskSignal model with 12-type catalog; rule-based | 147 |
| SAR/STR workflow (FATF, UK MLR 2017, US BSA) | SARCase FSM; MLRO decision; FIU submission | 149 |
| Tipping-off prohibition (criminal liability) | Linter rule 157; MLRO-only visibility; grep zero findings | 157 |
| MLRO single named human | MLRO role (Phase 10 ratified); personal legal liability | 149 |
| Punitive action approval (Law 14) | PunitiveAction model; approval workflow; no execution without approval | 151 |
| Dual control for high-severity | account_closure + se_block require requester != approver | 151 |
| SAR retention 5-10 years | Insert-only trigger; retention_expires_at field | 149 |
| Appeal workflow (regulator-mandated some jurisdictions) | Appeal model; FSM; separation of duties | 152 |
| Bifurcated truth (Law 6; Phase 17) | TM uses domain events only (NOT telemetry) | 158 |

## §4. Stage B requirements (pending — merge stop #8)

Phase 18 Stage B **does not start** until Phase 11, 12, 13, 14, 15, 16, AND 17 Stage B are all GREEN. This is merge stop #8 — the most regulator-sensitive gate in the programme, because Phase 18 implements the AML layer (failure is regulator-reportable; tipping-off is criminal liability).

### 4.1 Stage B execution order

1. **Migrations:** `risk_signal`, `tm_rule`, `sar_case`, `risk_case`, `punitive_action`, `appeal` tables + RLS + triggers + constraints.
2. **Code:** Django models, services (`SignalService`, `TMRuleService`, `SARService`, `RiskCaseService`, `PunitiveActionService`, `AppealService`), selectors, API endpoints.
3. **TM engine:** scheduled Celery job (every 5 min) + real-time outbox consumer.
4. **Tests:** 6 concurrency tests + 12 signal generation tests (one per type) + TM rule evaluation tests + SAR filing end-to-end test + tipping-off grep test (zero findings) + MLRO-only visibility test + punitive action approval test + dual control test + appeal workflow test + reversal test.
5. **Coverage:** ≥95% on `src/noventra/modules/risk/` and `src/noventra/modules/compliance/` (extended).
6. **Linter rules 146-158:** implemented in `check_traceability.sh` (already done at Stage A).
7. **OpenAPI:** risk endpoints (admin/internal); drift check green.
8. **Name the humans:** Security Owner, Compliance Officer, MLRO, Legal Counsel.
9. **Sign ADRs:** ADR-0109..0114 transition PROPOSED → ACCEPTED with named approvers.
10. **stage-18-handoff.md:** produced (already done at Stage A; updated at Stage B with GREEN status).
11. **phase-018-audit.md:** produced (already done at Stage A; updated at Stage B with GREEN status).

### 4.2 Stage B gate

**Gate:** Signals + TM rules + SAR/STR workflow + cases + approvals + appeals all implemented; ADR-0109..0114 transitioned PROPOSED → ACCEPTED with recorded approvers (HUMAN-APPROVED for Legal/Regulatory); punitive action requires approval (negative test passes — no execution without approval); SAR path fully audited (tipping-off prohibition enforced; MLRO-only visibility; grep zero findings); TM rules run on schedule + real-time; SAR filing workflow tested end-to-end; dual control enforced for high-severity; stage-18-handoff.md produced. **If any missing or BLOCKED → Phase 19 does not start.** Phase 18 is the AML layer — failure here is regulator-reportable (FATF, FCA, FinCEN).

## §5. Audit sign-off

Engineering Lead, 2026-10-28. Stage A: 15/15 PASS. Stage B: NOT STARTED (merge stop #8).

The Phase 18 ID allocation was clean (no collision). The tipping-off prohibition is enforced at the linter level (rule 157 — grep zero findings). The MLRO role is the single named human with personal legal liability for SAR decisions. Dual control is enforced for high-severity punitive actions. The audit chain holds.

Phase 18 is the AML layer. Tipping-off is criminal liability. MLRO is the named human. Dual control is the law. Law 14 is the law. The audit chain holds. 🛡️
