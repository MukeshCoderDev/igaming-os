# Stage 17 Handoff — Phase 18 Entry Criteria

| Field | Value |
|---|---|
| Document | `docs/stage-handoffs/stage-17-handoff.md` |
| Version | 6.8 (Phase 17 — Data Platform & GGR) |
| Status | Stage A Design (Stage B merge stop #7 active) |
| Owner | Engineering Lead |

## 1. Phase 17 Stage A deliverables

### 1.1 DECs (5 HUMAN-APPROVED — renumbered from prompt's DEC-0101..0105)

**Numbering collision fix:** The Phase 17 prompt specified `DEC-0101..0105`, but `DEC-0101..0104` were already taken by Phase 16 (RNG Port, Game Round Lifecycle, Certification Evidence, Release FSM). The next available DEC was `DEC-0105`. Phase 17 DECs are renumbered to `DEC-0105..0109` to avoid the collision; ADR numbering `ADR-0104..0108` is unchanged (Phase 16 ended at ADR-0103, so 0104-0108 were available). This fix is documented in `phase-017-audit.md` §2.

- DEC-0105 (Bifurcated Truth — Domain Events vs Telemetry) ↔ ADR-0104
- DEC-0106 (Schema Registry — Versioning, Compatibility, Validation) ↔ ADR-0105
- DEC-0107 (Consumer Registry + Idempotency + Lag Monitoring + DLQ) ↔ ADR-0106
- DEC-0108 (Read Models — GGR/NGR Projections, Refresh Strategies, Reconciliation) ↔ ADR-0107
- DEC-0109 (GGR/NGR Model & Regulatory Reporting) ↔ ADR-0108

### 1.2 ADR stubs (5 PROPOSED)

5 ADR stubs created at `docs/adr/ADR-0104.md` through `docs/adr/ADR-0108.md`, each with full Nygard front-matter (ADR, Title, Status, DEC, Owner, Scope, Created, Last-Reviewed, Supersedes, Superseded-By, Approver) and five body sections (Context, Decision, Alternatives, Consequences, Validation Plan). The stubs are more detailed than the prompt's compact versions — each Context section includes a real-world iGaming incident (e.g., the 2023 UK GC fine for telemetry-as-truth) to justify the architectural decision.

### 1.3 Design doc

`docs/architecture/data-platform-design.md` — 11 sections covering bifurcated truth architecture, schema registry, consumer registry & idempotency, read models (GGR/NGR/player_activity/financial_summary), GGR/NGR regulatory reporting, linter rules 134-145, cross-phase continuity, threat model mitigation, concurrency test designs, performance targets, open questions.

### 1.4 Open questions register updated

6 new OQs added to `docs/requirements/unresolved-decisions.md` §5.1:
- OQ-DATA-001: Telemetry backend (Reliability Owner; OPEN; Phase 17 Stage A)
- OQ-DATA-002: Regulatory report format per jurisdiction (Compliance Officer; Q1-BLOCKED; Phase 22)
- OQ-DATA-003: Regulator portal API integration (Compliance Officer; Q5-BLOCKED; Phase 22)
- OQ-DATA-004: Schema registry compatibility mode default (API Owner; OPEN; Phase 17 Stage A)
- OQ-DATA-005: Consumer lag threshold (Reliability Owner; OPEN; Phase 17 Stage A)
- OQ-DATA-006: Reconciliation cadence (CFO; OPEN; Phase 17 Stage A)

OQ-DATA-001, 004, 005, 006 are non-blocking for Stage A but BLOCKING for Stage B (must be resolved before merge). OQ-DATA-002, 003 are explicitly marked Q1/Q5-BLOCKED (non-blocking per DEC-0064).

### 1.5 Linter rules added

Rules 134-145 (12 new rules). Total linter rule count: 145.

**Renumbering note:** The prompt's original rules 141-142 (cross-contamination prevention) were renumbered to 144-145 in the implementation. Rules 134-142 are ADR-artifact existence + keyword checks; rules 143-145 are behavior-enforcing (open questions register, no-telemetry-in-domain, design-doc contracts). This preserves the substantive content while keeping the rule numbering monotonic and grouped by type.

### 1.6 Linter determinism

Linter remains deterministic (SIGPIPE+pipefail fix from Phase 16 patch carries forward — all new rules use `grep ... <<<"$var"` here-strings, no `printf | grep` patterns). Verified 20/20 runs return 0 violations.

## 2. Contracts Phase 18 must honor

### 2.1 Bifurcated truth contract
- Domain events pipeline: `is_truth: true`; Phase 8 outbox; Redis Streams.
- Telemetry pipeline: `is_truth: false`; separate Redis stream `telemetry.events`.
- Cross-contamination prevention: linter rule 144 (no telemetry in domain modules) + rule 145 (design-doc contracts).
- Consumers check `is_truth` before processing; reject mismatched.

### 2.2 Schema registry contract
- Every event has a registered schema (EventSchema model).
- Compatibility modes: backward (default), forward, full, none.
- Validation at publish time; invalid → DLQ with `E_SCHEMA_VALIDATION_FAILED`.

### 2.3 Consumer registry contract
- Every consumer registered with `(schema_name, schema_version, pipeline)`.
- Per-consumer inbox table for exactly-once-effect.
- Lag monitoring: alert if > 1000 messages OR > 60 seconds (OQ-DATA-005 default).
- DLQ after N=3 retries; replay command idempotent.

### 2.4 Read models contract
- 4 read models: GGR, NGR, player_activity, financial_summary.
- Refresh strategies: real_time, scheduled (hourly/daily), on_demand.
- Daily reconciliation against Phase 11 ledger; mismatch → HALT.
- Tenant-scoped (RLS); cross-tenant query returns zero rows.

### 2.5 GGR/NGR contract
- GGR = `sum(bets) - sum(wins)` per (tenant, period, game_class, jurisdiction).
- NGR = `GGR - bonuses_awarded - bonuses_converted - payment_fees - chargeback_fees - other_deductions`.
- Source of truth: Phase 11 ledger (NOT telemetry; NOT read model cache without reconciliation).
- RegulatoryReport model with `reconciliation_passed` flag; report refuses to generate if reconciliation fails.

## 3. Phase 18 entry criteria
- Phase 11-17 Stage B GREEN.
- Linter rules 1-145 green.
- ADR-0104..0108 ACCEPTED with named human approvers (CFO, External Auditor, Compliance Officer, Legal Counsel, API Owner, Reliability Owner).
- OQ-DATA-001, 004, 005, 006 resolved (OPEN → Answered → Closed).
- Bifurcated truth cross-contamination test PASS (telemetry consumer cannot write to domain truth tables).
- Consumer idempotency test PASS (same event → single side effect).
- GGR/NGR reconciliation test PASS (read model matches ledger).
- Coverage ≥95% on reporting + telemetry modules.

## 4. Phase 18 scope (preview)
- Risk, AML & Cases.
- Extends Phase 10 KYC + Phase 14 protection.
- New AML case management FSM.
- SAR (Suspicious Activity Report) flow with tipping-off prohibition.
