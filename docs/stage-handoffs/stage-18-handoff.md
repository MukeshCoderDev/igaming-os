# Stage 18 Handoff — Phase 19 Entry Criteria

| Field | Value |
|---|---|
| Document | `docs/stage-handoffs/stage-18-handoff.md` |
| Version | 6.9 (Phase 18 — Risk, AML & Cases) |
| Status | Stage A Design (Stage B merge stop #8 active) |
| Owner | Engineering Lead |

## 1. Phase 18 Stage A deliverables

### 1.1 DECs (6 HUMAN-APPROVED — ID allocation verified clean)

Phase 18 ID allocation verified clean — no collision with Phase 16/17:
- Phase 16: DEC-0096..0104, ADR-0099..0103, rules 121-133
- Phase 17: DEC-0105..0109, ADR-0104..0108, rules 134-145
- Phase 18: DEC-0110..0115, ADR-0109..0114, rules 146-158

The mentor's ID Allocation Table (§0.2) was correct; no renumbering needed.

- DEC-0110 (Risk Signal Model + 12-type catalog + rule-based generation) ↔ ADR-0109
- DEC-0111 (TM Rules Engine + 5 rule types + per-jurisdiction thresholds) ↔ ADR-0110
- DEC-0112 (SAR/STR Workflow + MLRO + tipping-off prohibition) ↔ ADR-0111
- DEC-0113 (Risk Case Management + evidence aggregation + case linking) ↔ ADR-0112
- DEC-0114 (Punitive Action Approval + dual control + audit) ↔ ADR-0113
- DEC-0115 (Player Appeal Workflow + reversal) ↔ ADR-0114

### 1.2 ADR stubs (6 PROPOSED)

6 ADR stubs created at `docs/adr/ADR-0109.md` through `docs/adr/ADR-0114.md`, each with full Nygard front-matter (ADR, Title, Status, DEC, Owner, Scope, Created, Last-Reviewed, Supersedes, Superseded-By, Approver) and five body sections (Context, Decision, Alternatives, Consequences, Validation Plan). Each Context section includes a real-world AML incident (Danske Bank €1.5B fine for signal-generation failure; Capital One $390M for TM-rule misconfiguration; Wells Fargo $3B for punitive action bypass) to justify the architectural decision.

### 1.3 Design doc

`docs/architecture/risk-aml-design.md` — 11 sections covering schema topology (6 tables), signal generation architecture, TM rules engine, SAR/STR workflow (tipping-off prohibition), punitive action approval (dual control), appeal workflow, linter rules 146-158, cross-phase continuity, threat model mitigation, concurrency test designs, open questions.

### 1.4 Open questions register updated

6 new OQs added to `docs/requirements/unresolved-decisions.md` §5.2:
- OQ-RISK-001: ML-based TM (CTO; Q5-BLOCKED; Phase 19+)
- OQ-RISK-002: FIU submission API integration (Compliance Officer; Q5-BLOCKED; Phase 22)
- OQ-RISK-003: CTR threshold per jurisdiction (Compliance Officer; Q1-BLOCKED; Phase 22)
- OQ-RISK-004: SAR retention period per jurisdiction (Legal Counsel; Q1-BLOCKED; Phase 22)
- OQ-RISK-005: Appeal window per jurisdiction (Legal Counsel; Q1-BLOCKED; Phase 22)
- OQ-RISK-006: Risk scoring weights (Compliance Officer; OPEN; Phase 18 Stage B)

OQ-RISK-006 is non-blocking for Stage A but BLOCKING for Stage B (must be resolved before merge). OQ-RISK-001..005 are explicitly marked Q1/Q5-BLOCKED (non-blocking per DEC-0064).

### 1.5 Linter rules added

Rules 146-158 (13 new rules). Total linter rule count: 158.

### 1.6 Linter determinism

Linter remains deterministic (SIGPIPE+pipefail fix from Phase 16 patch carries forward — all new rules use `grep ... <<<"$var"` here-strings, no `printf | grep` patterns).

## 2. Contracts Phase 19 must honor

### 2.1 Risk signal contract
- 12 signal types in closed catalog (velocity/structural/behavioral/jurisdictional/linked).
- Rule-based generation (explainable for regulators; no ML in Phase 18).
- Scheduled (5min) + real-time (outbox consumer).
- Idempotent (Phase 17 inbox pattern; same event + same rule → single signal).

### 2.2 TM rules contract
- 5 rule types (threshold/velocity/structural/behavioral/jurisdictional).
- Per-jurisdiction thresholds (Q1-blocked; stub returns defaults).
- Risk scoring: cumulative per player; critical → auto-escalate to RiskCase.
- Rule versioning: every change = new version (insert-only); `approved_by` recorded.

### 2.3 SAR/STR contract (CRIMINAL LIABILITY)
- MLRO is the single named human with personal legal liability for file/dismiss decision.
- Tipping-off prohibition enforced at code level (linter rule 157) + data level (MLRO-only RLS).
- Retention 5-10 years per jurisdiction (Q1-blocked; OQ-RISK-004).
- Account may freeze on filing (Phase 14 kill-switch pattern).

### 2.4 Risk case contract
- 6-state FSM (open → under_investigation → pending_approval → closed_*).
- 5 case types (aml/fraud/rg/bonus_abuse/payment_dispute).
- Evidence JSONB aggregated from Phase 10/11/12/13/14/15/16/18.
- Bidirectional case linking (KYC case, dispute case, abuse flag, SAR case).

### 2.5 Punitive action contract (Law 14 mandate)
- 5 action types (account_freeze/closure/bonus_clawback/payment_block/se_block).
- Dual control for high-severity (account_closure, se_block): requester != approver.
- 2 irreversible (se_block, account_closure); 3 reversible.
- Reversal = new PunitiveAction (insert-only); original never mutated.

### 2.6 Appeal contract
- 5-state FSM (submitted → under_review → upheld/overturned/rejected).
- Appeal window per jurisdiction (Q1-blocked; default 30 days).
- Separation of duties: reviewer != original approver.
- Tipping-off extends to appeal notifications (no SAR language).
- Reversal for reversible actions only; irreversible actions stand (compensation instead).

## 3. Phase 19 entry criteria
- Phase 11-18 Stage B GREEN.
- Linter rules 1-158 green.
- ADR-0109..0114 ACCEPTED with named human approvers (Security Owner, Compliance Officer, MLRO, Legal Counsel).
- OQ-RISK-006 resolved (OPEN → Answered → Closed).
- Tipping-off prohibition test PASS (grep zero findings across all notification templates).
- Punitive action approval test PASS (no execution without approval).
- Dual control test PASS (high-severity requires requester != approver).
- SAR MLRO-only visibility test PASS (non-MLRO read → 403 + audit flag).
- Coverage ≥95% on risk + compliance modules.

## 4. Phase 19 scope (preview)
- AI Platform & RAG.
- Static Knowledge layer (Law 6 — bifurcated truth; RAG is never-truth for consequential decisions).
- May revisit ML-based TM (OQ-RISK-001; Q5-blocked).
