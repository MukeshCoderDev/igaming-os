# AI Platform & RAG Design Document (Phase 19)

| Field | Value |
|---|---|
| Authority | DEC-0116..0125 | ADR-0115..0124 |
| Status | Stage A Design (Stage B merge stop #9 active) |
| Coverage floor | 95% (per ADR-0027 v2) |
| Owner | Security Owner + Compliance Officer + External Auditor |
| Law mandate | Laws 11 (AI Boundary), 12 (Machine-Assembled Citations), 13 (Truth Consistency), 2 (Prefiltered Isolation), 16 (Voice & Degradation), 6 (Bifurcated Truth), 22 (Edge) |

## 1. Architecture Overview

### 1.1 AI Governance Plane (Blueprint §5 Plane 3)

1. LLM Gateway (provider abstraction, routing, cost, degradation L0-L4)
2. Prompt Template Versioning
3. Knowledge Chunk Model + Lifecycle + Synchronous Revocation
4. Prefiltered Hybrid Retrieval (pgvector + FTS)
5. Machine-Assembled Citations
6. TruthConsistencyValidator
7. LLM Evaluation Suite
8. Cost Accounting
9. EU AI Act Model Inventory
10. Anchored RAG Pipeline (10 steps)

### 1.2 Laws Enforced

- **Law 2 (Prefiltered Isolation):** retrieval prefiltered by tenant_id + jurisdiction + language INSIDE the SQL query. Post-retrieval filtering is a security violation.
- **Law 6 (Bifurcated Truth):** RAG is forbidden from touching Process Truth (SQL/FSM). Static Knowledge lives in RAG.
- **Law 10 (Synchronous Revocation):** revoked chunks unretrievable same transaction.
- **Law 11 (AI Boundary):** AI never writes ledger entries, balances, RNG seeds, RTP/math config, odds, RG controls, KYC status, or compliance approvals.
- **Law 12 (Machine-Assembled Citations):** LLM never names citations; machine maps claims to chunk IDs.
- **Law 13 (Truth Consistency):** TruthConsistencyValidator checks every RAG answer against SQL facts; contradiction = hard fail.
- **Law 16 (Voice & Degradation):** distress signals bypass AI; L0-L4 degradation; never abandons the user.
- **Law 22 (Edge):** revoked chunks propagate to client via realtime invalidation.

## 2. Schema Topology

### 2.1 Tables (with RLS — Phase 5 continuity)

**prompt_template** (versioned prompts):
- `template_uuid` UUID PK, `tenant_uuid` UUID (RLS), `name` VARCHAR, `version` VARCHAR (semver), `template` TEXT, `variables` JSONB, `status` ENUM (draft/active/deprecated), `created_at`, `created_by`, `updated_at`
- UNIQUE(tenant_uuid, name, version)

**knowledge_chunk** (RAG knowledge base):
- `chunk_uuid` UUID PK, `tenant_uuid` UUID (RLS), `content` TEXT, `embedding` vector(1536) (pgvector), `metadata` JSONB (source, doc_type, language, jurisdiction), `lifecycle` ENUM (draft/active/superseded/revoked), `source` TEXT, `embedding_model_version` VARCHAR, `created_at`, `updated_at`
- Insert-only (Phase 7 pattern; lifecycle transitions via service)

**ai_model** (EU AI Act inventory):
- `model_uuid` UUID PK, `provider` VARCHAR, `model_name` VARCHAR, `version` VARCHAR, `risk_classification` ENUM (minimal/limited/high/unacceptable), `intended_use` TEXT, `documentation_url` TEXT, `technical_docs_url` TEXT, `risk_assessment_url` TEXT, `conformity_declaration_url` TEXT, `status` ENUM (approved/suspended/prohibited), `created_at`, `updated_at`
- UNIQUE(provider, model_name, version)

**llm_cost_record** (cost tracking):
- `cost_uuid` UUID PK, `tenant_uuid` UUID (RLS), `request_id` UUID, `model` VARCHAR, `prompt_template_uuid` UUID (nullable), `input_tokens` INT, `output_tokens` INT, `cost_usd` DECIMAL(10,6), `created_at`
- Insert-only (Phase 7 pattern)

**llm_tenant_budget** (per-tenant budget):
- `budget_uuid` UUID PK, `tenant_uuid` UUID, `monthly_budget_usd` DECIMAL, `current_month_spend_usd` DECIMAL, `budget_month` DATE, `alert_threshold_pct` DECIMAL (default 80.00), `cutoff_threshold_pct` DECIMAL (default 100.00), `created_at`, `updated_at`

### 2.2 DB Constraints

- RLS policies on all tables per Phase 5 pattern.
- Insert-only triggers on `knowledge_chunk`, `llm_cost_record` (Phase 7 pattern).
- pgvector index on `knowledge_chunk.embedding` (filtered by tenant_id + lifecycle).
- FTS index on `knowledge_chunk.content` (tsvector + GIN).

## 3. The 10-Step Anchored RAG Pipeline

### Step 1: Unified Router
- Deterministic regex first (FAQ, simple lookups)
- LLM last (complex queries)
- **Distress short-circuits ALL (Law 16):** distress signals bypass AI entirely; deterministic response via Phase 14 RGPort (<50ms)

### Step 2: Retrieval Planner
- Persona + Tenant + Language context

### Step 3: Prefiltered Hybrid Retrieval (ADR-0118)
- pgvector + FTS
- **Prefiltered: tenant_id + jurisdiction + language + lifecycle=active (Law 2)**
- Post-retrieval filtering is a SECURITY VIOLATION

### Step 4: Ingestion Sandbox
- All chunk fields wrapped in `<evidence trusted="false">` tags
- LLM treats as untrusted data (prevents prompt injection from retrieved chunks)

### Step 5: LLM Answer Composer
- Outputs claims (structured: {claim_id, claim_text, fact_references})
- **FORBIDDEN from naming citations (Law 12)**

### Step 6: Claim-Level Grounder (ADR-0119)
- NLI or span mapping: does this claim exist in the evidence?
- Maps claims to chunk_ids

### Step 7: Truth Consistency Validator (ADR-0120)
- **Checks fact-referencing claims against SQL facts (Law 13)**
- 6 fact types: balance, payment, KYC, RG, bonus, round
- **Contradiction = hard fail; safe fallback; incident signal**

### Step 8: Output Guardrails
- Injection scan, PII leak scan, tone check, schema validation

### Step 9: Machine-Assembled Citation Builder (ADR-0119)
- **Attaches real chunk_ids to grounded claims (Law 12)**
- Verifies chunk_ids exist in retrieved set

### Step 10: Safe Renderer
- **Injects SQL facts as placeholders (amounts, dates, IDs — never machine-translated)**
- Translates prose only (Law 15 — Mother Tongue)

## 4. LLM Gateway Architecture

### 4.1 Provider Abstraction
- `LLMProviderPort` interface; adapters for OpenAI, Anthropic, Google, local (Ollama), `StubLLMAdapter` (dev)
- Q5-blocked for real providers; stub for dev

### 4.2 Routing
- Per query type (chat, RAG, agent tool); per tenant config

### 4.3 Rate Limiting
- Per tenant, per user, per prompt type; Redis-based (token bucket)

### 4.4 Cost Tracking
- Per request (tokens × rate); per tenant aggregation; per prompt version

### 4.5 Degradation (Law 16)
- L0: full AI
- L1: cached responses (semantic cache hit)
- L2: template responses (pre-written)
- L3: deterministic fallback (regex/FAQ)
- L4: refuse + log ("AI unavailable; please contact support")

### 4.6 Distress Short-Circuit
- Phase 14 RGPort integration
- Distress signals bypass AI entirely
- Deterministic response (<50ms; no LLM call)

## 5. EU AI Act Compliance

### 5.1 Risk Classifications
- **minimal:** no additional obligations
- **limited:** transparency obligations (user must know they're interacting with AI)
- **high:** additional documentation (technical docs, risk assessment, conformity declaration)
- **unacceptable:** PROHIBITED (linter rule 170)

### 5.2 Model Inventory
- Every LLM model registered in AIModel table
- Cannot use unregistered model (linter rule 171)
- Default to high-risk until proven otherwise (Q21 OPEN; OQ-AI-003)

## 6. Linter Rules 159-175 (Phase 19)

**Note on rule numbering:** The prompt's original rules 159-175 were behavior-enforcing (grep for actual code patterns). At Stage A (design only), there is no code to grep yet. The implemented rules 159-175 are Stage A design-artifact checks (ADR keyword verification + artifact existence + design doc contracts). The behavior-enforcing rules (the prompt's original 159-175 semantics) will be added at Stage B when code exists, using enhanced checks or additional rule numbers.

| Rule | Description (Stage A implementation) |
|---|---|
| 159 | Phase 19 ADRs 0115-0124 all exist |
| 160 | ADR-0115 documents LLM gateway + degradation L0-L4 |
| 161 | ADR-0116 documents prompt template versioning |
| 162 | ADR-0117 documents knowledge chunk + synchronous revocation (Law 10) |
| 163 | ADR-0118 documents prefiltered retrieval (Law 2) |
| 164 | ADR-0119 documents machine-assembled citations (Law 12) |
| 165 | ADR-0120 documents TruthConsistencyValidator (Law 13) |
| 166 | ADR-0121 documents LLM evaluation suite |
| 167 | ADR-0122 documents cost accounting + budget enforcement |
| 168 | ADR-0123 documents EU AI Act model inventory |
| 169 | ADR-0124 documents 10-step RAG pipeline (all 10 step names) |
| 170 | Phase 19 design doc exists |
| 171 | Phase 19 stage handoff exists |
| 172 | Phase 19 audit exists |
| 173 | Open questions register documents OQ-AI-001..006 |
| 174 | AI never writes to domain truth tables (Law 11) — defense-in-depth grep (warning at Stage A; hard fail at Stage B) |
| 175 | AI platform design doc contracts (Laws 11/12/13/2/16/6 + 10-step + distress + prefiltered + contradiction) |

## 7. Cross-Phase Continuity

### Phase 4 contracts
- Error format: `E_AI_GATEWAY_TIMEOUT`, `E_AI_BUDGET_EXCEEDED`, `E_AI_RETRIEVAL_ISOLATION_VIOLATION`, `E_AI_CITATION_HALLUCINATION`, `E_AI_TRUTH_CONTRADICTION`, `E_AI_INJECTION_DETECTED`
- Structured logging with `correlation_id`, `tenant_id`, `prompt_template_id`, `model`
- PII redaction (player queries are PII)
- mypy strict on ai_platform module; coverage ≥95%

### Phase 5 RLS extension
- All AI tables tenant-scoped (`prompt_template`, `knowledge_chunk`, `llm_cost_record`, `llm_tenant_budget`)

### Phase 7 audit extension
- Event type taxonomy: `ai.gateway_call`, `ai.prompt_used`, `ai.retrieval_completed`, `ai.citation_assembled`, `ai.truth_validated`, `ai.contradiction_detected`, `ai.injection_blocked`, `ai.chunk_revoked`, `ai.degradation_triggered`

### Phase 8 outbox continuity
- AI events via outbox; consumers idempotent (Phase 17 pattern)

### Phase 10 KYC continuity
- KYC status is a SQL fact (TruthConsistencyValidator checks AI claims about KYC status)
- **AI never writes KYC status (Law 11)**

### Phase 11 ledger continuity
- Ledger is SQL truth (TruthConsistencyValidator checks AI claims about balance)
- **AI never writes ledger entries (Law 11)**

### Phase 12-16 continuity
- Payment status, bonus state, RG status, game round results are SQL facts
- **AI never writes any of these (Law 11)**

### Phase 14 protection continuity
- Distress signals from RGPort short-circuit AI (Law 16)
- RealtimePort for chunk revocation invalidation (Law 22)

### Phase 17 reporting continuity
- Telemetry is never-truth (Law 6); AI cannot use telemetry as fact source
- GGR/NGR are SQL facts (TruthConsistencyValidator checks AI claims about revenue)

## 8. Threat Model Mitigation

| Threat | Mitigation |
|---|---|
| AI writes to domain truth (Law 11 violation) | Linter rule 174; gateway enforces (no write APIs exposed to LLM) |
| Post-retrieval filtering (Law 2 violation) | Linter rule 163; prefiltered query mandatory |
| LLM names citations (Law 12 violation) | Linter rules 164; machine-assembled citations only |
| AI contradicts SQL facts (Law 13 violation) | TruthConsistencyValidator (ADR-0120); hard fail on contradiction |
| Prompt injection from retrieved chunks | Ingestion Sandbox (Step 4); `<evidence trusted="false">` wrapping |
| Hallucinated citations | Machine-Assembled Citation Builder (Step 9); chunk_id verification |
| Distress signal missed (Law 16 violation) | Distress short-circuit (Step 1); deterministic response <50ms |
| Cost explosion | Budget enforcement (ADR-0122); hard cutoff at 100%; degradation L3 |
| EU AI Act violation (unacceptable risk) | Linter rule 168; model inventory (ADR-0123) |
| Cross-tenant knowledge leak | RLS on knowledge_chunk (Phase 5); prefiltered retrieval (Law 2) |

## 9. Concurrency Test Designs (Stage B)

1. Concurrent RAG queries (idempotent; per-tenant isolation).
2. Concurrent chunk revocation + retrieval (revocation wins; chunk unretrievable — Law 10).
3. Concurrent prompt template update (only one active version per name).
4. Concurrent cost recording (idempotent per request_id).
5. Concurrent budget check + cutoff (atomic; no overspend).
6. Concurrent TruthConsistencyValidator (deterministic; no race).

## 10. Injection Suite (Stage B)

### 10.1 Prompt Injection
- System prompt override attempts
- Instruction injection in user query
- Instruction injection in retrieved chunks (Ingestion Sandbox test)

### 10.2 Jailbreak
- DAN (Do Anything Now) attempts
- Role-play bypass attempts
- Hypothetical framing attempts

### 10.3 RAG Poisoning
- Malicious chunks injected into knowledge base
- Chunk content attempts to override system prompt
- All caught by Ingestion Sandbox + Output Guardrails

### 10.4 Citation Hallucination
- LLM attempts to name citations → blocked by Law 12 enforcement
- Machine-assembled citations verify chunk_ids exist in retrieved set

### 10.5 Truth Contradiction
- AI claims balance that contradicts ledger → TruthConsistencyValidator hard-fails
- Safe fallback triggered

## 11. Performance Targets

- RAG query end-to-end: <5s p99 (10-step pipeline)
- Retrieval (Step 3): <500ms p99 (pgvector + FTS)
- LLM call (Step 5): <2s p99 (provider-dependent)
- Truth validation (Step 7): <200ms p99 (parallel SQL queries)
- Citation assembly (Step 9): <100ms p99
- Distress short-circuit (Step 1): <50ms p99 (bypass AI entirely)

## 12. Open Questions (OQ-AI-001..006)

| ID | Question | Owner | Due | Status |
|---|---|---|---|---|
| OQ-AI-001 | LLM provider selection (OpenAI, Anthropic, Google, local) | CTO | Phase 22 | Q5-BLOCKED |
| OQ-AI-002 | Embedding model selection + dimension (1536 for OpenAI) | CTO | Phase 19 Stage A | OPEN |
| OQ-AI-003 | Q21: EU AI Act classification of retention AI | Compliance Officer | Phase 22 | Q1-BLOCKED |
| OQ-AI-004 | NLI model for claim-level grounding (vendor or in-house) | CTO | Phase 19 Stage A | Q5-BLOCKED |
| OQ-AI-005 | Per-tenant monthly LLM budget default | CFO | Phase 19 Stage A | OPEN |
| OQ-AI-006 | Degradation L0-L4 thresholds (when to degrade) | Reliability Owner | Phase 19 Stage A | OPEN |
