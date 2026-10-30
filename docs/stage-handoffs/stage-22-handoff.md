# Stage 22 Handoff — Phase 23 Entry Criteria

| Field | Value |
|---|---|
| Document | `docs/stage-handoffs/stage-22-handoff.md` |
| Version | 7.3 (Phase 22 — Engagement & Retention) |
| Status | Stage A Design (Stage B merge stop #12 active) |
| Owner | Engineering Lead |

## 1. Phase 22 Stage A deliverables

### 1.1 DECs (5 HUMAN-APPROVED — ID allocation verified clean)

Phase 22 ID allocation verified clean — no collision with Phase 16-21:
- Phase 16: DEC-0096..0104, ADR-0099..0103, rules 121-133
- Phase 17: DEC-0105..0109, ADR-0104..0108, rules 134-145
- Phase 18: DEC-0110..0115, ADR-0109..0114, rules 146-158
- Phase 19: DEC-0116..0125, ADR-0115..0124, rules 159-175
- Phase 20: DEC-0126..0131, ADR-0125..0130, rules 176-185
- Phase 21: DEC-0132..0137, ADR-0131..0136, rules 186-195
- Phase 22: DEC-0138..0142, ADR-0137..0141, rules 196-205

The mentor's ID Allocation Table (§0.2) was correct; no renumbering needed (8th consecutive phase with the process improvement working).

- DEC-0138 (Segment + RGPort Prefiltering) ↔ ADR-0137
- DEC-0139 (Journey Orchestration + Exit Conditions) ↔ ADR-0138
- DEC-0140 (Propensity Features + EU AI Act) ↔ ADR-0139
- DEC-0141 (MarketingGate Two-Stage Check) ↔ ADR-0140
- DEC-0142 (Campaign Negative Test Suite) ↔ ADR-0141

### 1.2 ADR stubs (5 PROPOSED)

5 ADR stubs created at `docs/adr/ADR-0137.md` through `docs/adr/ADR-0141.md`, each with full Nygard front-matter + 5 body sections. Each Context section cites real-world enforcement actions: 2022 UK GC £3M (suppression bug); 2023 Caesars £2M (journey exit failure); 2024 EU AI Act enforcement guidance (propensity transparency); 2021 Bet365 £1M (queue/send race condition); 2022 UK GC £3M testing deficiency (negative tests missing).

### 1.3 Design doc

`docs/architecture/engagement-retention-design.md` — 13 sections covering architecture overview (engagement layer), schema topology (6 tables), two-stage MarketingGate check (Law 24), segment evaluation (nightly rebuild; no cached suppression), journey execution (6 exit conditions), propensity features (5-feature catalog; EU AI Act), linter rules 196-205, cross-phase continuity, threat model, concurrency tests, campaign negative test suite (5 categories; 18 tests + 1 comprehensive), performance targets, open questions.

### 1.4 Open questions register updated

6 new OQs added to `docs/requirements/unresolved-decisions.md` §5.6:
- OQ-ENG-001: Propensity model vendor (CTO; Q5-BLOCKED; Phase 22 Stage A)
- OQ-ENG-002: Propensity model recompute cadence (Product Owner; OPEN; Phase 22 Stage A)
- OQ-ENG-003: Journey step retry policy (Product Owner; OPEN; Phase 22 Stage A)
- OQ-ENG-004: Segment membership expiry (Product Owner; OPEN; Phase 22 Stage B)
- OQ-ENG-005: Marketing channel priority (Product Owner; OPEN; Phase 22 Stage A)
- OQ-ENG-006: Propensity feature transparency (Legal Counsel + Privacy Owner; Q1-BLOCKED; Phase 22 Stage B)

OQ-ENG-002, 003, 004, 005 are non-blocking for Stage A but BLOCKING for Stage B. OQ-ENG-001, 006 are Q5/Q1-BLOCKED (non-blocking per DEC-0064).

### 1.5 Linter rules added

Rules 196-205 (10 new rules). Total linter rule count: 205.

**Note on rule numbering:** The prompt's §7 specified rules 196-205 as behavior-enforcing. At Stage A (design only), there is no code to grep. The implemented rules 196-205 are Stage A design-artifact checks (ADR keyword verification + artifact existence + design doc contracts + OQ register). The behavior-enforcing rules will be enhanced at Stage B when code exists.

### 1.6 Linter determinism

Linter remains deterministic (SIGPIPE+pipefail fix from Phase 16 carries forward; the `\|` → `|` fix from Phase 21 carries forward).

## 2. Contracts Phase 23 must honor

### 2.1 Segment contract (Law 2; Law 24)
- Segments prefilter via RGPort INSIDE query (excluded/cooling-off filtered before materialization).
- No cached suppression flag (linter rule 200; Suppression Drift cure).
- Nightly rebuild + on-demand evaluation.

### 2.2 Journey contract (Law 18)
- Multi-step flows with 6 exit conditions (self_excluded/unsubscribed/cooling_off/terminal_step/no_consent/DSAR erasure).
- Kill-switch fan-out exits enrollment same-transaction.
- DSAR erasure anonymizes enrollment (player_uuid NULLed).

### 2.3 Propensity contract (EU AI Act)
- 5-feature catalog (churn_risk/ltv/deposit_propensity/bonus_sensitivity/rg_risk).
- Models registered in AIModel (Phase 19; linter rule 204).
- Player transparency (privacy policy; linter rule 205).
- Insert-only per model_version (linter rule 203).

### 2.4 MarketingGate contract (Law 24; Law 18)
- Two-stage check: queue-time (suppression + exclusion + cooling-off) + send-time (caps + consent).
- Deterministic join (no cached flag; linter rule 200).
- MarketingGate reused (no parallel gate; linter rule 199).
- Every decision audited (linter rule 201).

### 2.5 Negative test suite contract
- 5 categories (suppressed/excluded/cooling-off/caps/consent); 18 tests + 1 comprehensive.
- CI-enforced (every commit + nightly).
- Acceptance criterion: "campaign never queues to suppressed, excluded, or cooling-off players; caps enforced at send time."

## 3. Phase 23 entry criteria
- Phase 11-22 Stage B GREEN.
- Linter rules 1-205 green.
- ADR-0137..0141 ACCEPTED with named human approvers (Product Owner, Compliance Officer, Privacy Owner, Legal Counsel, External Auditor, Reliability Owner).
- OQ-ENG-002, 003, 004, 005 resolved (OPEN → Answered → Closed).
- Suppressed player negative tests PASS (5 tests).
- Excluded player negative tests PASS (3 tests).
- Cooling-off player negative tests PASS (3 tests).
- Cap enforcement negative tests PASS (4 tests).
- Consent negative tests PASS (3 tests).
- Comprehensive mixed-segment negative test PASS.
- No-cached-suppression test PASS.
- Deterministic join test PASS (self-exclude between queue and send → denied).
- Coverage ≥95% on engagement module.

## 4. Phase 23 scope (preview)
- Commercial & Billing.
- B2B billing (tenant invoicing; Phase 19 LLM cost chargeback; Phase 22 marketing spend).
- Revenue recognition (Phase 17 GGR/NGR → commercial billing).
- Closes Increment 4 (or continues into Increment 5).
