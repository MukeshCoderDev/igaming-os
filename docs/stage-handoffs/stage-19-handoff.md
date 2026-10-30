# Stage 19 Handoff — Phase 20 Entry Criteria

| Field | Value |
|---|---|
| Document | `docs/stage-handoffs/stage-19-handoff.md` |
| Version | 7.0 (Phase 19 — AI Platform & RAG) |
| Status | Stage A Design (Stage B merge stop #9 active) |
| Owner | Engineering Lead |

## 1. Phase 19 Stage A deliverables

### 1.1 DECs (10 HUMAN-APPROVED — ID allocation verified clean)

Phase 19 ID allocation verified clean — no collision with Phase 16/17/18:
- Phase 16: DEC-0096..0104, ADR-0099..0103, rules 121-133
- Phase 17: DEC-0105..0109, ADR-0104..0108, rules 134-145
- Phase 18: DEC-0110..0115, ADR-0109..0114, rules 146-158
- Phase 19: DEC-0116..0125, ADR-0115..0124, rules 159-175

The mentor's ID Allocation Table (§0.2) was correct; no renumbering needed.

- DEC-0116 (LLM Gateway) ↔ ADR-0115
- DEC-0117 (Prompt Template Versioning) ↔ ADR-0116
- DEC-0118 (Knowledge Chunk Model + Synchronous Revocation) ↔ ADR-0117
- DEC-0119 (Prefiltered Hybrid Retrieval — Law 2) ↔ ADR-0118
- DEC-0120 (Machine-Assembled Citations — Law 12) ↔ ADR-0119
- DEC-0121 (TruthConsistencyValidator — Law 13) ↔ ADR-0120
- DEC-0122 (LLM Evaluation Suite) ↔ ADR-0121
- DEC-0123 (Cost Accounting) ↔ ADR-0122
- DEC-0124 (EU AI Act Model Inventory) ↔ ADR-0123
- DEC-0125 (Anchored RAG Pipeline — 10 Steps) ↔ ADR-0124

### 1.2 ADR stubs (10 PROPOSED)

10 ADR stubs created at `docs/adr/ADR-0115.md` through `docs/adr/ADR-0124.md`, each with full Nygard front-matter + 5 body sections (Context, Decision, Alternatives, Consequences, Validation Plan). Each Context section cites real-world AI incidents (Air Canada chatbot liability 2023; Apple Intelligence hallucination 2024; Stanford GPT-4 citation hallucination study 2023; SaaS RAG cross-tenant leak 2024).

### 1.3 Design doc

`docs/architecture/ai-platform-design.md` — 12 sections covering architecture overview (AI Governance Plane), schema topology (5 tables), 10-step RAG pipeline, LLM gateway architecture, EU AI Act compliance, linter rules 159-175, cross-phase continuity, threat model mitigation, concurrency test designs, injection suite (5 types), performance targets, open questions.

### 1.4 Open questions register updated

6 new OQs added to `docs/requirements/unresolved-decisions.md` §5.3:
- OQ-AI-001: LLM provider selection (CTO; Q5-BLOCKED; Phase 22)
- OQ-AI-002: Embedding model selection + dimension (CTO; OPEN; Phase 19 Stage A)
- OQ-AI-003: Q21 EU AI Act classification of retention AI (Compliance Officer; Q1-BLOCKED; Phase 22)
- OQ-AI-004: NLI model for claim-level grounding (CTO; Q5-BLOCKED; Phase 19 Stage A)
- OQ-AI-005: Per-tenant monthly LLM budget default (CFO; OPEN; Phase 19 Stage A)
- OQ-AI-006: Degradation L0-L4 thresholds (Reliability Owner; OPEN; Phase 19 Stage A)

OQ-AI-002, 005, 006 are non-blocking for Stage A but BLOCKING for Stage B. OQ-AI-001, 003, 004 are Q5/Q1-BLOCKED (non-blocking per DEC-0064).

### 1.5 Linter rules added

Rules 159-175 (17 new rules). Total linter rule count: 175.

**Note on rule numbering:** The prompt's original rules 159-175 were behavior-enforcing (grep for code patterns). At Stage A (design only), there is no code to grep. The implemented rules 159-175 are Stage A design-artifact checks (ADR keyword verification + artifact existence + design doc contracts + Law 11 defense-in-depth grep). The behavior-enforcing rules (prompt's original 159-175 semantics) will be enhanced at Stage B when code exists.

### 1.6 Linter determinism

Linter remains deterministic (SIGPIPE+pipefail fix from Phase 16 carries forward).

## 2. Contracts Phase 20 must honor

### 2.1 LLM Gateway contract (Law 16)
- Every LLM call goes through the gateway (no direct provider calls).
- Degradation L0-L4; distress short-circuit bypasses AI (<50ms).
- Per-tenant budget enforcement (80% alert; 100% hard cutoff → L3).

### 2.2 Prompt versioning contract
- Every LLM call records `prompt_template_id` + version.
- A/B testing supported; rollback audit logged.

### 2.3 Knowledge chunk contract (Law 10, Law 22)
- Synchronous revocation: revoked chunk unretrievable same transaction.
- Realtime invalidation: revoked chunk emits event; RAG cache purged.
- Embedding model versioning: every chunk tagged; mismatch = reject.

### 2.4 Prefiltered retrieval contract (Law 2)
- Retrieval query prefiltered by `tenant_id` + `jurisdiction` + `language` + `lifecycle = 'active'` INSIDE the SQL WHERE clause.
- Post-retrieval filtering is a SECURITY VIOLATION.

### 2.5 Citation contract (Law 12)
- LLM never names citations (linter rules 168-169).
- Machine-assembled citations only; chunk_ids verified against retrieved set.
- Ungrounded claims hard fail.

### 2.6 Truth consistency contract (Law 13)
- TruthConsistencyValidator runs on every fact-referencing claim.
- 6 fact types: balance, payment, KYC, RG, bonus, round.
- Contradiction = hard fail; safe fallback; incident signal.

### 2.7 AI boundary contract (Law 11)
- AI never writes to domain truth tables (ledger, payments, KYC, bonuses, protection, games).
- Gateway never exposes write APIs to the LLM.
- Linter rule 174: defense-in-depth grep (warning at Stage A; hard fail at Stage B).

### 2.8 EU AI Act contract
- Unacceptable-risk models PROHIBITED (linter rule 170).
- Every LLM call uses registered AIModel (linter rule 171).
- High-risk models require technical docs + risk assessment + conformity declaration.

### 2.9 10-step RAG pipeline contract
- 10 pure functions composed in sequence.
- Any step can hard-fail → safe fallback.
- Distress short-circuit (Step 1 bypass; <50ms).
- Latency target: <5s p99 end-to-end.

## 3. Phase 20 entry criteria
- Phase 11-19 Stage B GREEN.
- Linter rules 1-175 green.
- ADR-0115..0124 ACCEPTED with named human approvers (Reliability Owner, CFO, Product Owner, Compliance Officer, Legal Counsel, Security Owner, QA Owner, External Auditor).
- OQ-AI-002, 005, 006 resolved (OPEN → Answered → Closed).
- Retrieval isolation test PASS (Law 2; cross-tenant leak = zero rows).
- Synchronous revocation test PASS (Law 10; revoked chunk unretrievable same transaction).
- Injection suite PASS (5 types: prompt injection, jailbreak, RAG poisoning, citation hallucination, truth contradiction — all rejected).
- TruthConsistencyValidator hard-fail test PASS (Law 13; contradiction → safe fallback).
- Machine-assembled citation test PASS (Law 12; LLM never names citations).
- AI-never-writes-to-domain-truth test PASS (Law 11; linter rule 175 green).
- Coverage ≥95% on ai_platform module.

## 4. Phase 20 scope (preview)
- Bounded Agents.
- Agent tool framework (Law 11 — AI never writes; agents call deterministic services).
- Agent orchestration (multi-step workflows).
