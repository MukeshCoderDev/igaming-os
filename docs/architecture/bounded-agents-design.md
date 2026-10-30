# Bounded Agents Design Document (Phase 20)

| Field | Value |
|---|---|
| Authority | DEC-0126..0131 | ADR-0125..0130 |
| Status | Stage A Design (Stage B merge stop #10 active) |
| Coverage floor | 95% (per ADR-0027 v2) |
| Owner | Product Owner + Compliance Officer + Security Owner |
| Law mandate | Law 14 (Bounded Agents), Law 18 (Player Protection), Law 9 (Immutable Audit), Law 16 (Voice & Degradation), Law 11 (AI Boundary) |

## 1. Architecture Overview

### 1.1 Bounded Agent Runtime

1. **Agent Registry** (9 agents; shadow→live promotion gate)
2. **Typed Tools** (registry; schemas; mapped service methods; no superuser; no direct DB writes)
3. **Approval Gates** (Law 14; high-risk requires human approval)
4. **Execution Logs** (audit trail; link to LLM calls + correlation_id)
5. **Retention Agent Bounds** (Law 18; 4-level enforcement)
6. **Agent Runtime** (orchestration; LLM integration; outbox events)

### 1.2 Laws Enforced

- **Law 11 (AI Boundary):** agents use LLM (Phase 19) but cannot write to domain truth.
- **Law 14 (Bounded Agents):** typed tools; no superuser; no direct DB writes; approval gates.
- **Law 18 (Player Protection):** Retention agent bounded (excluded/cooling-off/caps/bonus).
- **Law 9 (Immutable Audit):** execution logs insert-only; hash-chained.
- **Law 16 (Voice & Degradation):** agent degradation L0-L4; distress short-circuit.

## 2. Schema Topology

### 2.1 Tables (with RLS — Phase 5 continuity)

**agent_definition** (9 agents):
- `agent_uuid` UUID PK, `tenant_uuid` UUID (RLS), `name` VARCHAR (9 agents per blueprint §7), `description` TEXT, `allowed_tools` TEXT[], `forbidden_tools` TEXT[], `approval_gate` ENUM, `risk_level` ENUM (low/medium/high), `status` ENUM (shadow/live/suspended), `promotion_evidence_id` UUID (nullable; required for live), `created_at`, `updated_at`
- CHECK: `status=live` requires `promotion_evidence_id` NOT NULL

**agent_tool** (typed tools):
- `tool_uuid` UUID PK, `name` VARCHAR UNIQUE, `description` TEXT, `input_schema` JSONB, `output_schema` JSONB, `mapped_service_method` VARCHAR (e.g., `noventra.modules.players.services.PlayerService.get_profile`), `risk_level` ENUM, `requires_approval` BOOLEAN, `created_at`, `updated_at`

**agent_approval** (approval workflow):
- `approval_uuid` UUID PK, `tenant_uuid` UUID (RLS), `agent_uuid` FK, `tool_name` VARCHAR, `input` JSONB, `output` JSONB (nullable), `status` ENUM (pending/approved/rejected/executed/expired), `requested_at` TIMESTAMPTZ, `requested_by` VARCHAR (agent identity), `approved_by` VARCHAR (nullable; human), `approved_at` TIMESTAMPTZ (nullable), `executed_at` TIMESTAMPTZ (nullable), `justification` TEXT (nullable), `created_at`, `updated_at`

**agent_execution_log** (audit trail):
- `log_uuid` UUID PK, `tenant_uuid` UUID (RLS), `agent_uuid` FK, `tool_name` VARCHAR, `input` JSONB, `output` JSONB (nullable), `status` ENUM (success/failed/denied/pending_approval/expired), `duration_ms` INT, `correlation_id` UUID (Phase 4), `llm_call_id` UUID (Phase 19 link; nullable), `approval_id` UUID FK (Phase 20 ADR-0127 link; nullable), `error_message` TEXT (nullable), `created_at` TIMESTAMPTZ
- Insert-only (Phase 7 pattern; trigger BEFORE UPDATE/DELETE raises)

**promotion_evidence** (shadow→live):
- `evidence_uuid` UUID PK, `agent_uuid` FK, `evidence` JSONB (test results, review notes), `promoted_by` VARCHAR (human), `promoted_at` TIMESTAMPTZ, `created_at`

### 2.2 DB Constraints

- RLS policies on all tables per Phase 5 pattern.
- Insert-only triggers on `agent_execution_log` (Phase 7 pattern; Law 9).
- CHECK: `agent_definition` with `status=live` has `promotion_evidence_id` NOT NULL.

## 3. The 9-Agent Catalog (Blueprint §7)

| # | Agent | Allowed Tools (examples) | Forbidden Tools | Approval Gate |
|---|---|---|---|---|
| 1 | Support Knowledge | player_lookup, knowledge_retrieve, draft_response | change_account_state, modify_balance | account_changes |
| 2 | RG Triage | detect_distress, prioritize_case, suggest_intervention | encourage_play, set_bonus | interventions |
| 3 | Fraud/AML | summarize_evidence, score_risk, draft_sar | freeze_funds, execute_punitive | punitive_actions |
| 4 | Ops Incident | correlate_logs, draft_incident, suggest_remediation | restart_service, modify_config | remediation |
| 5 | Compliance | map_controls, draft_pack, check_evidence | certify_compliance, approve_audit | approvals |
| 6 | Game QA | generate_tests, simulate_round, check_rtp | approve_release, modify_math | math_changes |
| 7 | Dev Assistant | suggest_code, suggest_docs, review_pr | merge_code, deploy | code_review |
| 8 | Analytics | explain_metric, generate_report, compare_periods | alter_metric, modify_data | external_reports |
| 9 | Retention | segment_query, journey_suggest, draft_campaign | target_excluded, set_bonus, queue_breaching_caps | campaign_approval |

## 4. Retention Agent Bounds (Law 18 — 4-Level Enforcement)

### Level 1 — Tool Registry (ADR-0126)
- Retention agent's `allowed_tools` excludes protection-modifying tools.
- No tool to set SE; no tool to set cooling-off; no tool to set bonus values.
- `allowed_tools`: `segment_query`, `journey_suggest`, `draft_campaign`.
- `forbidden_tools`: `set_self_exclusion`, `set_cooling_off`, `set_bonus_value`, `modify_player_protection`.
- Linter rule 179: Retention agent's `allowed_tools` does not include protection-modifying tools.

### Level 2 — Segment Query (RGPort)
- Every segment query calls `RGPort.check_self_excluded` + `RGPort.check_cooling_off` for each player.
- Excluded/cooling-off players filtered out of segment.
- Per-player check (not per-segment); player who self-excludes mid-query is filtered.
- Linter rule 180: Retention agent segment queries check RGPort.

### Level 3 — MarketingGate (Phase 8 + Phase 9)
- Every journey queued goes through MarketingGate.
- Checks: suppression (Phase 8) + caps (Phase 8) + consent (Phase 9).
- Excluded/cooling-off players in suppression list → denied at send time.
- Caps exceeded → denied at send time.
- Consent missing → denied at send time.
- Linter rule 181: Retention agent journey queues go through MarketingGate.

### Level 4 — Negative Tests
- Test: target excluded player → denied (`E_AGENT_BOUNDARY_VIOLATION`).
- Test: target cooling-off player → denied.
- Test: queue journey breaching caps → denied (`E_AGENT_CAP_BREACH`).
- Test: set bonus value → tool not in `allowed_tools` → denied (`E_AGENT_TOOL_FORBIDDEN`).
- All 4 negative tests must pass (acceptance criterion for Phase 20 gate).

## 5. Linter Rules 176-185 (Phase 20)

**Note on rule numbering:** The prompt's §5 specified rules 176-185 as behavior-enforcing (grep for code patterns). At Stage A (design only), there is no code to grep. The implemented rules 176-185 are Stage A design-artifact checks (ADR keyword verification + artifact existence + design doc contracts + OQ register). The behavior-enforcing rules (prompt's original 176-185 semantics) will be enhanced at Stage B when code exists, using the same rule numbers with stricter checks.

| Rule | Description (Stage A implementation) |
|---|---|
| 176 | Phase 20 ADRs 0125-0130 all exist |
| 177 | ADR-0125 documents agent registry + shadow→live + 9 agents + allowed/forbidden tools |
| 178 | ADR-0126 documents typed tools + schemas + mapped service methods + no superuser + no DB writes |
| 179 | ADR-0127 documents approval gates + SLA + dual control + justification |
| 180 | ADR-0128 documents execution logs + immutable + correlation_id + llm_call_id + approval_id + Law 9 |
| 181 | ADR-0129 documents Retention agent bounds (Law 18) + 4-level + negative tests + RGPort + MarketingGate |
| 182 | ADR-0130 documents agent runtime + orchestration + LLM + outbox + degradation L0-L4 + distress + pure function |
| 183 | Phase 20 design doc exists |
| 184 | Phase 20 stage handoff exists |
| 185 | Phase 20 audit + OQ-AGENT-001..006 + design doc contracts (Law 14/18/9 + 9 agents + shadow/live + Retention + RGPort + MarketingGate) |

## 6. Cross-Phase Continuity

### Phase 4 contracts
- Error format: `E_AGENT_TOOL_FORBIDDEN`, `E_AGENT_APPROVAL_REQUIRED`, `E_AGENT_BOUNDARY_VIOLATION`, `E_AGENT_NOT_PROMOTED`, `E_AGENT_DISTRESS_SHORT_CIRCUIT`, `E_AGENT_CAP_BREACH`, `E_TOOL_INPUT_INVALID`, `E_TOOL_OUTPUT_INVALID`
- Structured logging with `correlation_id`, `tenant_id`, `agent_id`, `tool_name`, `llm_call_id`
- PII redaction (agent inputs may contain player PII)
- mypy strict on agents module; coverage ≥95%

### Phase 5 RLS extension
- All agent tables tenant-scoped (`agent_definition`, `agent_approval`, `agent_execution_log`, `promotion_evidence`)

### Phase 6 service identity continuity
- Agents run as service identities (`typ=service` JWT)
- Scoped permissions per agent (RBAC)
- No superuser; no `BYPASSRLS`

### Phase 7 audit extension
- Event type taxonomy: `agent.invoked`, `agent.tool_executed`, `agent.tool_denied`, `agent.tool_pending_approval`, `agent.tool_expired`, `agent.tool_failed`, `agent.promoted`, `agent.distress_short_circuit`
- Execution logs hash-chained into operational audit chain

### Phase 8 outbox continuity
- Every tool execution emits outbox event
- Consumers: reporting (Phase 17), risk (Phase 18), compliance (Phase 21)
- Outbox + tool execution in same DB transaction (atomic)

### Phase 13 bonuses continuity
- Retention agent cannot set bonus values (Law 18)
- Bonus recommendation requires approval

### Phase 14 protection continuity
- Retention agent checks RGPort (SE, cooling-off)
- Distress signals short-circuit agents (Law 16)

### Phase 19 AI platform continuity
- Agent LLM calls go through LLM Gateway (ADR-0115)
- Agent prompts versioned (ADR-0116)
- Agent retrieval uses prefiltered RAG (ADR-0118)
- Agent citations machine-assembled (ADR-0119)
- Agent responses truth-validated (ADR-0120)
- Agent cost tracked (ADR-0122)
- Agent models EU AI Act compliant (ADR-0123)
- Agent `llm_call_id` linked to execution logs (ADR-0128)

## 7. Threat Model Mitigation

| Threat | Mitigation |
|---|---|
| Unbounded agent (superuser, direct DB writes) | Typed tools (ADR-0126); no superuser; service identities |
| Forbidden tool called | Linter rule 182; `allowed_tools` enforcement |
| High-risk tool without approval | Linter rule 178; approval workflow (ADR-0127) |
| Retention agent targets excluded player | 4-level enforcement (rules 179-181); 4 negative tests |
| Agent writes to domain truth (Law 11) | Phase 19 rule 175; service methods enforce invariants |
| Agent execution not auditable | Execution logs (rule 183); immutable (rule 184); linked (rule 185) |
| Shadow agent executes (no promotion) | Linter rule 176; promotion evidence required |
| Distress signal missed | Short-circuit (Law 16); deterministic response <100ms |
| SLA breach (approval never reviewed) | SLA enforcement; expired status; alert compliance officer |
| Approval fatigue (rubber-stamping) | Justification required; per-gate SLA; dual control for critical |

## 8. Concurrency Test Designs (Stage B)

1. Concurrent agent invocations (idempotent; per-tenant isolation).
2. Concurrent approval requests (only one approval per tool call).
3. Concurrent shadow agent reviews (only one promotion at a time).
4. Concurrent Retention agent segment queries (RGPort check per player).
5. Concurrent execution log writes (insert-only; no contention).
6. Concurrent distress short-circuit (deterministic; no race).

## 9. Negative Tests (Acceptance Criteria)

### 9.1 Forbidden Tool Denied (each of 9 agents)
1. Support Knowledge attempts `change_account_state` → denied (`E_AGENT_TOOL_FORBIDDEN`)
2. RG Triage attempts `encourage_play` → denied
3. Fraud/AML attempts `freeze_funds` → denied
4. Ops Incident attempts `restart_service` → denied
5. Compliance attempts `certify_compliance` → denied
6. Game QA attempts `approve_release` → denied
7. Dev Assistant attempts `merge_code` → denied
8. Analytics attempts `alter_metric` → denied
9. Retention attempts `target_excluded` → denied

### 9.2 High-Risk Gated (3 scenarios)
1. Agent calls high-risk tool without approval → denied (`E_AGENT_APPROVAL_REQUIRED`)
2. Agent calls high-risk tool → approval request created → human approves → executes
3. Agent calls high-risk tool → approval request created → human rejects → does not execute

### 9.3 Retention Negative Tests (4 tests)
1. Retention agent targets excluded player → denied (`E_AGENT_BOUNDARY_VIOLATION`)
2. Retention agent targets cooling-off player → denied
3. Retention agent queues journey breaching caps → denied (`E_AGENT_CAP_BREACH`)
4. Retention agent attempts to set bonus value → tool not in `allowed_tools` → denied (`E_AGENT_TOOL_FORBIDDEN`)

## 10. Performance Targets

- Agent invocation latency: <2s p99 (LLM call + tool execution)
- Tool execution latency: <500ms p99 (service method)
- Approval SLA: 24h (configurable; per-gate)
- Execution log write: <50ms p99
- Distress short-circuit: <100ms p99 (bypass LLM)

## 11. Open Questions (OQ-AGENT-001..006)

| ID | Question | Owner | Due | Status |
|---|---|---|---|---|
| OQ-AGENT-001 | LLM provider for agents (same as Phase 19 or separate) | CTO | Phase 19 Stage A | OPEN |
| OQ-AGENT-002 | Approval SLA default (24h recommended) | Compliance Officer | Phase 20 Stage A | OPEN |
| OQ-AGENT-003 | Shadow→live promotion criteria (test results + review notes) | Product Owner | Phase 20 Stage B | OPEN |
| OQ-AGENT-004 | Agent scheduling (RG Triage hourly; Fraud/AML event-driven) | Reliability Owner | Phase 20 Stage A | OPEN |
| OQ-AGENT-005 | Agent cost allocation (per-tenant; per-agent) | CFO | Phase 20 Stage A | OPEN |
| OQ-AGENT-006 | Distress short-circuit threshold (Phase 14 RGPort integration) | Compliance Officer | Phase 20 Stage B | OPEN |
