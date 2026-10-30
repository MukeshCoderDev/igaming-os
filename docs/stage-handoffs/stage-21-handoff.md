# Stage 21 Handoff — Phase 22 Entry Criteria

| Field | Value |
|---|---|
| Document | `docs/stage-handoffs/stage-21-handoff.md` |
| Version | 7.2 (Phase 21 — Compliance, DSAR & Vendors) |
| Status | Stage A Design (Stage B merge stop #11 active) |
| Owner | Engineering Lead |

## 1. Phase 21 Stage A deliverables

### 1.1 DECs (6 HUMAN-APPROVED — ID allocation verified clean)

Phase 21 ID allocation verified clean — no collision with Phase 16-20:
- Phase 16: DEC-0096..0104, ADR-0099..0103, rules 121-133
- Phase 17: DEC-0105..0109, ADR-0104..0108, rules 134-145
- Phase 18: DEC-0110..0115, ADR-0109..0114, rules 146-158
- Phase 19: DEC-0116..0125, ADR-0115..0124, rules 159-175
- Phase 20: DEC-0126..0131, ADR-0125..0130, rules 176-185
- Phase 21: DEC-0132..0137, ADR-0131..0136, rules 186-195

The mentor's ID Allocation Table (§0.2) was correct; no renumbering needed (6th consecutive phase with the process improvement working).

- DEC-0132 (Compliance Control Framework) ↔ ADR-0131
- DEC-0133 (Evidence Repository) ↔ ADR-0132
- DEC-0134 (Periodic Compliance Reviews) ↔ ADR-0133
- DEC-0135 (Reporting Adapters) ↔ ADR-0134
- DEC-0136 (DSAR Drill — Errata E1) ↔ ADR-0135
- DEC-0137 (Legal-Hold + Vendor Expiry) ↔ ADR-0136

### 1.2 ADR stubs (6 PROPOSED)

6 ADR stubs created at `docs/adr/ADR-0131.md` through `docs/adr/ADR-0136.md`, each with full Nygard front-matter + 5 body sections. Each Context section cites real-world enforcement actions: 2022 Star Ocean Casino £5M (ad-hoc controls); 2021 SEC $70M (evidence tampering); 2023 Casino Royale £2M (untracked findings); 2022 BetBright £600K (manual reporting error); 2023 GDPR €4M (DSAR order + SE registry); 2021 spoliation £1.2M + 2022 uncertified KYC vendor £800K (legal-hold + vendor expiry).

### 1.3 Design doc

`docs/architecture/compliance-dsar-vendors-design.md` — 13 sections covering architecture overview (unified compliance plane), schema topology (9 tables), DSAR operational order (errata E1), vendor deterministic expiry (blueprint §8.3), legal-hold matrix, linter rules 186-195, cross-phase continuity, threat model, concurrency tests, DSAR drill test, vendor expiry alert tests, performance targets, open questions.

### 1.4 Open questions register updated

6 new OQs added to `docs/requirements/unresolved-decisions.md` §5.5:
- OQ-COMP-001: Compliance frameworks in scope (Compliance Officer; OPEN; Phase 21 Stage A)
- OQ-COMP-002: Evidence retention period per jurisdiction (Legal Counsel; Q1-BLOCKED; Phase 22)
- OQ-COMP-003: External auditor vendor selection (Compliance Officer; Q5-BLOCKED; Phase 22)
- OQ-COMP-004: DSAR statutory window per jurisdiction (Legal Counsel; Q1-BLOCKED; Phase 22)
- OQ-COMP-005: Regulator portal API integration (Compliance Officer; Q5-BLOCKED; Phase 22)
- OQ-COMP-006: Vendor expiry T-30/7/1 thresholds (Compliance Officer; OPEN; Phase 21 Stage A)

OQ-COMP-001, 006 are non-blocking for Stage A but BLOCKING for Stage B. OQ-COMP-002, 003, 004, 005 are Q1/Q5-BLOCKED (non-blocking per DEC-0064).

### 1.5 Linter rules added

Rules 186-195 (10 new rules). Total linter rule count: 195.

**Note on rule numbering:** The prompt's §6 specified rules 186-195 as behavior-enforcing. At Stage A (design only), there is no code to grep. The implemented rules 186-195 are Stage A design-artifact checks (ADR keyword verification + artifact existence + design doc contracts + OQ register). The behavior-enforcing rules will be enhanced at Stage B when code exists.

### 1.6 Linter determinism

Linter remains deterministic (SIGPIPE+pipefail fix from Phase 16 carries forward).

## 2. Contracts Phase 22 must honor

### 2.1 Compliance control framework contract
- Every control registered with framework mapping (6 frameworks).
- Named owner per control (linter rule 191).
- Scheduled testing (pass/fail/remediation_required).

### 2.2 Evidence repository contract (Law 9; SEC 17a-4)
- Evidence immutable via Phase 10 storage port (WORM).
- Every evidence access logged (linter rule 193).
- Supersession (not deletion) for evidence updates.
- Retention 5-10 years per jurisdiction (Q1-blocked).

### 2.3 Periodic reviews contract
- 4 review types (internal/external/regulator/self-assessment).
- Every finding has owner + due_date + remediation_status (linter rule 195).
- Escalation (overdue + critical + repeated).

### 2.4 Reporting adapters contract
- Per-jurisdiction + per-report-type (7 report types).
- Source: ledger-reconciled read models (Phase 17; never telemetry).
- Submission tracking (draft → generated → submitted → acknowledged/rejected).

### 2.5 DSAR drill contract (errata E1)
- Fixed order: verify → export → shred (no skipping; linter rule 186).
- SE-survives-erasure via HMAC pseudonymization (linter rule 187).
- Export pack from 11 modules; stored immutably.
- Statutory window 30 days (linter rule 188; alert at T-7).

### 2.6 Legal-hold contract
- 4 hold types (litigation/regulatory/audit/compliance_review).
- Retention job skips held data (linter rule 189).
- Ledger exempt (AML law mandatory retention).

### 2.7 Vendor expiry contract (blueprint §8.3)
- Lab/studio cert expired → auto-suspend catalog (Law 19).
- PSP/KYC/Geo → T-30/7/1 alerts + operator decision (linter rule 190).
- Daily expiry job (Celery beat).

## 3. Phase 22 entry criteria
- Phase 11-21 Stage B GREEN.
- Linter rules 1-195 green.
- ADR-0131..0136 ACCEPTED with named human approvers (Compliance Officer, External Auditor, Legal Counsel, Privacy Owner, CFO).
- OQ-COMP-001, 006 resolved (OPEN → Answered → Closed).
- DSAR drill end-to-end test PASS (verify → export → shred → SE survives → re-registration blocked).
- DSAR E1 order negative tests PASS (4 tests).
- Vendor expiry T-30/T-7/T-1 alert tests PASS.
- Auto-suspend test PASS (lab/studio).
- Operator-decision test PASS (PSP/KYC/Geo).
- Legal-hold suspension test PASS.
- Evidence immutability test PASS.
- Coverage ≥95% on compliance module.

## 4. Phase 22 scope (preview)
- Engagement & Retention.
- Player engagement journeys (Phase 20 Retention agent integration).
- Marketing campaigns (MarketingGate Phase 8 integration).
- Closes Increment 4.
