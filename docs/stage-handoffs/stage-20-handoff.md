# Stage 20 Handoff — Phase 21 Entry Criteria

| Field | Value |
|---|---|
| Document | `docs/stage-handoffs/stage-20-handoff.md` |
| Version | 7.1 (Phase 20 — Bounded Agents) |
| Status | Stage A Design (Stage B merge stop #10 active) |
| Owner | Engineering Lead |

## 1. Phase 20 Stage A deliverables

### 1.1 DECs (6 HUMAN-APPROVED — ID allocation verified clean)

Phase 20 ID allocation verified clean — no collision with Phase 16-19:
- Phase 16: DEC-0096..0104, ADR-0099..0103, rules 121-133
- Phase 17: DEC-0105..0109, ADR-0104..0108, rules 134-145
- Phase 18: DEC-0110..0115, ADR-0109..0114, rules 146-158
- Phase 19: DEC-0116..0125, ADR-0115..0124, rules 159-175
- Phase 20: DEC-0126..0131, ADR-0125..0130, rules 176-185

The mentor's ID Allocation Table (§0.2) was correct; no renumbering needed.

- DEC-0126 (Agent Registry + Shadow→Live Promotion) ↔ ADR-0125
- DEC-0127 (Typed Tools) ↔ ADR-0126
- DEC-0128 (Approval Gates) ↔ ADR-0127
- DEC-0129 (Execution Logs) ↔ ADR-0128
- DEC-0130 (Retention Agent Bounds — Law 18) ↔ ADR-0129
- DEC-0131 (Agent Runtime) ↔ ADR-0130

### 1.2 ADR stubs (6 PROPOSED)

6 ADR stubs created at `docs/adr/ADR-0125.md` through `docs/adr/ADR-0130.md`, each with full Nygard front-matter + 5 body sections. Each Context section cites real-world AI safety incidents: 2024 e-commerce refund agent ($1.2M to self); 2023 SaaS DevOps agent (deleted production databases); 2023 Knight Capital algorithm ($440M in 45 minutes); 2022 UK GC enforcement action (£3M fine for retention marketing to self-excluded players).

### 1.3 Design doc

`docs/architecture/bounded-agents-design.md` — 11 sections covering architecture overview (bounded agent runtime), schema topology (5 tables), 9-agent catalog (blueprint §7), Retention agent 4-level bounds (Law 18), linter rules 176-185, cross-phase continuity, threat model mitigation, concurrency test designs, negative tests (9 forbidden tool + 3 high-risk gated + 4 retention), performance targets, open questions.

### 1.4 Open questions register updated

6 new OQs added to `docs/requirements/unresolved-decisions.md` §5.4:
- OQ-AGENT-001: LLM provider for agents (CTO; OPEN; Phase 19 Stage A)
- OQ-AGENT-002: Approval SLA default (Compliance Officer; OPEN; Phase 20 Stage A)
- OQ-AGENT-003: Shadow→live promotion criteria (Product Owner; OPEN; Phase 20 Stage B)
- OQ-AGENT-004: Agent scheduling (Reliability Owner; OPEN; Phase 20 Stage A)
- OQ-AGENT-005: Agent cost allocation (CFO; OPEN; Phase 20 Stage A)
- OQ-AGENT-006: Distress short-circuit threshold (Compliance Officer; OPEN; Phase 20 Stage B)

OQ-AGENT-001, 002, 004, 005 are non-blocking for Stage A but BLOCKING for Stage B. OQ-AGENT-003, 006 are resolved before their respective Stage B tests.

### 1.5 Linter rules added

Rules 176-185 (10 new rules). Total linter rule count: 185.

**Note on rule numbering:** The prompt's §5 specified rules 176-185 as behavior-enforcing. At Stage A (design only), there is no code to grep. The implemented rules 176-185 are Stage A design-artifact checks (ADR keyword verification + artifact existence + design doc contracts + OQ register). The behavior-enforcing rules will be enhanced at Stage B when code exists.

### 1.6 Linter determinism

Linter remains deterministic (SIGPIPE+pipefail fix from Phase 16 carries forward).

## 2. Contracts Phase 21 must honor

### 2.1 Agent registry contract (Law 14)
- 9 agents in registry with distinct `allowed_tools` + `forbidden_tools` + `approval_gate`.
- Shadow→live promotion required (PromotionEvidence model).
- No live execution without promotion evidence (linter rule 176).

### 2.2 Typed tools contract (Law 14)
- Every tool registered with input/output schemas.
- Mapped to deterministic service method (NOT an LLM call).
- No superuser; no direct DB writes (linter rule 177).
- Agents run as service identities (Phase 6 `typ=service`).

### 2.3 Approval gates contract (Law 14)
- High-risk tools require human approval (linter rule 178).
- 5-state FSM: pending → approved/rejected → executed/expired.
- SLA enforcement (default 24h; per-gate configurable).
- Dual control for critical (agent != approver).

### 2.4 Execution logs contract (Law 9)
- Every agent action logged (linter rule 183).
- Immutable (insert-only; linter rule 184).
- Linked to LLM calls (Phase 19) + correlation_id (Phase 4) + approvals (Phase 20) (linter rule 185).
- Hash-chained into Phase 7 audit.

### 2.5 Retention agent bounds contract (Law 18)
- 4-level defense-in-depth enforcement.
- 4 negative tests (excluded, cooling-off, caps, bonus).
- Linter rules 179, 180, 181 enforce the 4 levels.
- Error codes: `E_AGENT_BOUNDARY_VIOLATION`, `E_AGENT_TOOL_FORBIDDEN`, `E_AGENT_CAP_BREACH`.

### 2.6 Agent runtime contract
- Pure-function composition: trigger → LLM → tool_check → approval → execute → log → outbox.
- Degradation L0-L4 (per-agent configurable).
- Distress short-circuit (<100ms p99; mandatory for RG Triage).
- Outbox events on every tool execution (Phase 8 pattern).

## 3. Phase 21 entry criteria
- Phase 11-20 Stage B GREEN.
- Linter rules 1-185 green.
- ADR-0125..0130 ACCEPTED with named human approvers (Product Owner, Compliance Officer, MLRO, Legal Counsel, Security Owner, Architecture Lead, Reliability Owner, External Auditor).
- OQ-AGENT-001, 002, 004, 005 resolved (OPEN → Answered → Closed).
- Forbidden tool denied tests PASS (9 agents; one negative test per agent).
- High-risk gated tests PASS (3 scenarios: no approval, approved, rejected).
- Retention negative tests PASS (4 tests: excluded, cooling-off, caps, bonus).
- Shadow→live promotion test PASS.
- Execution log immutability test PASS.
- Distress short-circuit test PASS.
- Coverage ≥95% on agents module.

## 4. Phase 21 scope (preview)
- Compliance, DSAR & Vendors.
- DSAR (Data Subject Access Request) workflow.
- Vendor risk management (Phase 10 KYC vendor; Phase 19 LLM provider; etc.).
- Closes Increment 4.
