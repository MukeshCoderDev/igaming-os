# Engagement & Retention Design Document (Phase 22)

| Field | Value |
|---|---|
| Authority | DEC-0138..0142 | ADR-0137..0141 |
| Status | Stage A Design (Stage B merge stop #12 active) |
| Coverage floor | 95% (per ADR-0027 v2) |
| Owner | Compliance Officer + Privacy Owner + Product Owner |
| Law mandate | Law 24 (Suppression — deterministic join; never cached), Law 18 (Player Protection — excluded/cooling-off never queued), Law 2 (Prefiltered Isolation — segments prefilter INSIDE query), Law 9 (Immutable Audit — every MarketingGate decision audited); EU AI Act (propensity model governance) |

## 1. Architecture Overview

### 1.1 Engagement Layer

1. **Segment Model + RGPort Prefiltering** (Law 2 applied to marketing)
2. **Journey Orchestration** (multi-step flows; 6 exit conditions)
3. **Propensity Features + Feature Store** (EU AI Act limited risk)
4. **MarketingGate Enforcement at Scale** (queue-time + send-time two-stage check)
5. **Campaign Negative Test Suite** (5 categories; 18 tests + 1 comprehensive)

### 1.2 Laws Enforced

- **Law 2 (Prefiltered Isolation):** segments filter INSIDE query (RGPort check before materialization).
- **Law 18 (Player Protection):** excluded/cooling-off players never queued; exit conditions.
- **Law 24 (Suppression):** deterministic join at send time; never cached flag.
- **Law 9 (Immutable Audit):** every MarketingGate decision audited.

### 1.3 Pain Ledger Addressed

- **"Suppression Drift"** (blueprint §3): cured by deterministic join at send time (ADR-0140); no cached suppression (linter rule 200).
- **"Zombie Bonuses (CDN)"** (blueprint §3): real-time invalidation pattern applied to revoked campaigns (journey exit on kill-switch fan-out).

## 2. Schema Topology

### 2.1 Tables (with RLS — Phase 5 continuity)

**segment** (player segments): `segment_uuid` UUID PK, `tenant_uuid` UUID (RLS), `name` VARCHAR, `description` TEXT, `definition` JSONB (demographics, behavior, RFM, propensity), `status` ENUM (draft/active/paused/archived), `created_by` VARCHAR, `created_at`/`updated_at`.

**segment_membership** (materialized): `membership_uuid` UUID PK, `segment_uuid` FK, `player_uuid` UUID, `tenant_uuid` UUID (denormalized RLS), `joined_at` TIMESTAMPTZ, `score` FLOAT (nullable), `expires_at` TIMESTAMPTZ (nullable), `created_at`. UNIQUE(segment_uuid, player_uuid). **No suppression flag** (Law 24; linter rule 200).

**journey** (multi-step flows): `journey_uuid` UUID PK, `tenant_uuid` UUID (RLS), `name` VARCHAR, `segment_uuid` FK, `status` ENUM (draft/scheduled/active/paused/completed/archived), `trigger` ENUM (immediate/scheduled/event_driven), `created_by` VARCHAR, `created_at`/`updated_at`.

**journey_step** (ordered steps): `step_uuid` UUID PK, `journey_uuid` FK, `step_number` INT, `channel` ENUM (email/sms/push/in_app), `template_id` UUID, `delay_minutes` INT, `condition` JSONB (nullable), `created_at`. UNIQUE(journey_uuid, step_number).

**journey_enrollment** (player journey state): `enrollment_uuid` UUID PK, `journey_uuid` FK, `player_uuid` UUID, `tenant_uuid` UUID (denormalized RLS), `current_step` INT, `enrolled_at`/`last_step_at`/`next_step_at` TIMESTAMPTZ, `status` ENUM (active/completed/exited/suppressed), `exit_reason` ENUM (nullable; self_excluded/unsubscribed/cap_exceeded/no_consent/terminal_step/cooling_off), `created_at`/`updated_at`. CHECK: exit_reason NOT NULL when status=exited.

**propensity_feature** (ML-derived): `feature_uuid` UUID PK, `tenant_uuid` UUID (RLS), `player_uuid` UUID, `feature_name` ENUM (churn_risk/ltv/deposit_propensity/bonus_sensitivity/rg_risk), `feature_value` FLOAT, `computed_at` TIMESTAMPTZ, `model_version` VARCHAR, `created_at`. UNIQUE(tenant_uuid, player_uuid, feature_name, model_version). Insert-only per model_version.

### 2.2 DB Constraints

- RLS policies on all tables per Phase 5 pattern.
- Insert-only triggers on `propensity_feature` (immutable per model_version).
- CHECK: `journey_enrollment` `exit_reason` NOT NULL when `status=exited`.

## 3. Two-Stage MarketingGate Check (ADR-0140)

### 3.1 Stage 1 — Queue-Time Check (Player Eligibility)

Before send enters queue:
1. **Suppression list** (Phase 8): player suppressed?
2. **RGPort.check_self_excluded** (Phase 14): player self-excluded?
3. **RGPort.check_cooling_off** (Phase 14): player in cooling-off?

If ANY fails → NOT queued; enrollment `status=suppressed`; `exit_reason`; audit event.

### 3.2 Stage 2 — Send-Time Check (Per-Message Limits)

At adapter call:
1. **Frequency caps** (Phase 8): tenant monthly/daily, recipient daily, channel, jurisdiction.
2. **Consent** (Phase 9): player consented to (purpose, channel)?

If ANY fails → send denied; audit event; step may retry or advance.

### 3.3 Deterministic Join (Law 24)

- Suppression checked via **live join** against `suppression_list` + `frequency_cap` tables at send time.
- **NEVER cached flag** (Suppression Drift pain).
- Real-time: self-exclude between queue and send → send denied.

## 4. Segment Evaluation

### 4.1 Nightly Rebuild (Scheduled)

Celery job: nightly at 02:00 UTC. For each active segment:
1. Query candidate players (demographics, behavior, RFM, propensity).
2. For each candidate: call `RGPort.check_self_excluded` + `check_cooling_off`.
3. If eligible: insert/update SegmentMembership.
4. If ineligible (excluded/cooling-off): skip (not materialized).

### 4.2 On-Demand (Admin Trigger)

For testing; for immediate segment refresh. Same logic as nightly rebuild.

### 4.3 No Cached Suppression

- SegmentMembership does NOT include suppression flag.
- Suppression is always live (checked at send time via MarketingGate).
- Prevents Suppression Drift (cached flag surviving DSAR purge).

## 5. Journey Execution

### 5.1 Enrollment

Player joins segment → enrolled in journey (`status=active`); `current_step=1`; `next_step_at = enrolled_at + step_1.delay_minutes`.

### 5.2 Step Execution

At `next_step_at`:
1. Queue-time MarketingGate check (ADR-0140 Stage 1).
2. If eligible: send queued.
3. If denied: enrollment `status=suppressed`; `exit_reason`; journey continues for others.

At send time:
1. Send-time MarketingGate check (ADR-0140 Stage 2).
2. If eligible: adapter called; send executed.
3. If denied: send skipped; step may retry (configurable) or advance.

Step advancement: `current_step++`; `next_step_at = now + next_step.delay_minutes`.
Terminal step: `status=completed`; `exit_reason=terminal_step`.

### 5.3 Exit Conditions (Law 18)

- **Self-exclusion mid-journey** (Phase 14 kill-switch): enrollment exits; `exit_reason=self_excluded`.
- **Unsubscribe** (suppression list): next send denied; enrollment exits; `exit_reason=unsubscribed`.
- **Cooling-off mid-journey**: next send denied; enrollment exits; `exit_reason=cooling_off`.
- **Terminal step**: `status=completed`; `exit_reason=terminal_step`.
- **Consent revoked** (Phase 9): next send denied at send-time; enrollment exits; `exit_reason=no_consent`.
- **DSAR erasure** (Phase 21 ADR-0135): enrollment `player_uuid` NULLed; journey continues anonymized for analytics.

## 6. Propensity Features

### 6.1 Feature Catalog (5 features)

| Feature | Description | Source | Range |
|---|---|---|---|
| `churn_risk` | Probability of churning | Phase 17 activity + Phase 11 ledger | 0.0-1.0 |
| `ltv` | Lifetime value | Phase 11 ledger (cumulative net deposits) | USD minor units |
| `deposit_propensity` | Probability of depositing in 7 days | Phase 11 + Phase 12 payment history | 0.0-1.0 |
| `bonus_sensitivity` | Responsiveness to bonus offers | Phase 13 bonus history | 0.0-1.0 |
| `rg_risk` | RG risk score | Phase 14 RG records | 0.0-1.0 |

### 6.2 Feature Engineering (Nightly Job)

- Sources: Phase 17 GGR/NGR, Phase 11 ledger, Phase 14 RG, Phase 18 risk.
- Materialized to `propensity_feature` table.
- Versioned by `model_version`.

### 6.3 ML Model Governance (EU AI Act — Phase 19)

- Propensity models registered in `AIModel` table (Phase 19).
- Risk classification: **limited** (transparency obligations).
- Player must know features used for marketing (privacy policy + consent).
- Model changes: new `model_version`; recompute; audit trail.

## 7. Linter Rules 196-205 (Phase 22)

**Note on rule numbering:** The prompt's §7 specified rules 196-205 as behavior-enforcing. At Stage A (design only), there is no code to grep. The implemented rules 196-205 are Stage A design-artifact checks (ADR keyword verification + artifact existence + design doc contracts + OQ register). The behavior-enforcing rules will be enhanced at Stage B when code exists.

| Rule | Description (Stage A implementation) |
|---|---|
| 196 | Phase 22 ADRs 0137-0141 all exist |
| 197 | ADR-0137 documents segment + RGPort prefiltering + no cached suppression |
| 198 | ADR-0138 documents journey + 6 exit conditions + kill-switch |
| 199 | ADR-0139 documents propensity + 5 features + EU AI Act + AIModel + transparency |
| 200 | ADR-0140 documents MarketingGate two-stage + deterministic join + Law 24 + no cached |
| 201 | ADR-0141 documents negative test suite (5 categories + comprehensive + CI) |
| 202 | Phase 22 design doc exists |
| 203 | Phase 22 stage handoff exists |
| 204 | Phase 22 audit exists |
| 205 | OQ-ENG-001..006 + design doc contracts (Law 24/18/2/9 + MarketingGate + queue-time + send-time + deterministic join + Suppression Drift + RGPort + propensity + EU AI Act) |

## 8. Cross-Phase Continuity

### Phase 4 contracts
- Error format: `E_MARKETING_GATE_DENIED` (reason: suppressed/excluded/cooling_off/cap_exceeded/no_consent), `E_SEGMENT_EVALUATION_FAILED`, `E_JOURNEY_EXITED`, `E_PROPENSITY_MODEL_NOT_REGISTERED`
- Structured logging with `correlation_id`, `tenant_id`, `player_id`, `segment_id`, `journey_id`, `enrollment_id`
- PII redaction (player segment membership, propensity features are PII)
- mypy strict on engagement module; coverage ≥95%

### Phase 5 RLS extension
- All engagement tables tenant-scoped.

### Phase 7 audit extension
- Event type taxonomy: `segment.evaluated`, `segment.membership_added`, `journey.enrolled`, `journey.step_executed`, `journey.exited`, `marketing.gate_decision` (with reason), `propensity.computed`

### Phase 8 MarketingGate continuity
- MarketingGate is the SINGLE gate (ADR-0046); Phase 22 uses it at scale.
- No parallel gate; linter rule 199 (prompt's numbering) enforces.
- Suppression list + frequency_cap tables (Phase 8) are the deterministic join source.

### Phase 9 consent continuity
- Consent check at send-time (Stage 2).
- Player can revoke consent mid-journey → enrollment exits.

### Phase 13 bonuses continuity
- RGPort real adapter used for segment prefiltering.
- Bonus sensitivity propensity feature (Phase 13 bonus history as source).

### Phase 14 protection continuity
- RGPort.check_self_excluded + check_cooling_off for segment prefiltering.
- Kill-switch exits journey enrollment (Law 18 same-transaction enforcement).
- rg_risk propensity feature sourced from Phase 14.

### Phase 17 reporting continuity
- GGR/NGR read models source for propensity features (churn_risk, ltv).
- Player activity read model for segment evaluation.

### Phase 18 risk continuity
- Risk signals source for rg_risk propensity feature.
- Fraud/AML signals may suppress player (suppression list integration).

### Phase 19 AI platform continuity
- Propensity models registered in AIModel table (EU AI Act).
- Feature engineering uses Phase 19 LLM Gateway if ML-based (Q5-blocked; stub for dev).

### Phase 20 bounded agents continuity
- Retention agent (Phase 20) drafts segments and suggests journeys.
- Retention agent cannot target excluded/cooling-off players (4-level bound; Phase 20 ADR-0129).
- Retention agent journey queues go through MarketingGate (Phase 20 linter rule 181; Phase 22 linter rule 197).

### Phase 21 compliance continuity
- DSAR erasure (Phase 21 ADR-0135) anonymizes journey enrollment (player_uuid NULLed).
- Legal hold (Phase 21 ADR-0136) may suspend journey data destruction.

## 9. Threat Model Mitigation

| Threat | Mitigation |
|---|---|
| Suppression Drift (cached flag survives DSAR) | Deterministic join at send time (ADR-0140); no cached suppression (rule 200) |
| Excluded player receives campaign (Law 18 violation) | Queue-time RGPort check (rule 197); segment prefiltering (rule 196) |
| Cooling-off player receives campaign (Law 18 violation) | Queue-time RGPort check (rule 197); segment prefiltering (rule 196) |
| Cap not enforced (Law 24 violation) | Send-time cap check (rule 198); deterministic join |
| Consent bypass (GDPR violation) | Send-time consent check (rule 198); Phase 9 integration |
| Self-exclusion between queue and send (race condition) | Deterministic join at send time catches real-time; send denied |
| Unregistered propensity model (EU AI Act violation) | Linter rule 204; AIModel registry (Phase 19) |
| No player transparency (EU AI Act limited risk violation) | Linter rule 205; privacy policy states features used |
| Cross-tenant segment leak (Info Disclosure) | RLS on all engagement tables (Phase 5) |
| MarketingGate decision not audited (Law 9 violation) | Linter rule 201; audit event for every decision |

## 10. Concurrency Test Designs (Stage B)

1. Concurrent segment evaluation (only one rebuild per segment at a time; row lock).
2. Concurrent journey step execution (per-enrollment; idempotent).
3. Concurrent MarketingGate checks (deterministic; no race).
4. Concurrent propensity feature computation (per-player; per-feature; idempotent).
5. Concurrent enrollment + self-exclusion (kill-switch exits enrollment; no race).
6. Concurrent unsubscribe + send (deterministic join catches; send denied).

## 11. Campaign Negative Test Suite (Acceptance Criterion)

### 11.1 Suppressed Player Tests (5 tests)
1. Unsubscribed → denied (reason=suppressed)
2. Hard bounce → denied
3. Complaint → denied
4. Unsubscribe mid-journey → next step denied; enrollment exits (exit_reason=unsubscribed)
5. DSAR-erased → not in segment (RGPort prefiltering); not queued

### 11.2 Excluded Player Tests (3 tests — Law 18)
6. Self-excluded → denied (reason=excluded)
7. Self-exclude mid-journey (kill-switch) → next step denied; enrollment exits (exit_reason=self_excluded)
8. Self-exclude between queue and send → send denied (deterministic join catches real-time)

### 11.3 Cooling-Off Player Tests (3 tests — Law 18)
9. Cooling-off → denied (reason=cooling_off)
10. Enter cooling-off mid-journey → next step denied; enrollment exits (exit_reason=cooling_off)
11. Exit cooling-off → re-enrolled; eligible

### 11.4 Cap Enforcement Tests (4 tests — Law 24)
12. Recipient daily cap exceeded → denied (reason=cap_exceeded)
13. Tenant monthly cap exceeded → denied
14. Channel cap exceeded (email cap met; SMS allowed) → email denied, SMS allowed
15. Cap reset (daily) → send allowed again

### 11.5 Consent Tests (3 tests — Phase 9)
16. No consent for (purpose, channel) → denied (reason=no_consent)
17. Revoke consent mid-journey → next step denied; enrollment exits (exit_reason=no_consent)
18. Consent mid-journey → re-enrolled; eligible

### 11.6 Comprehensive Negative Test (Acceptance Criterion)
19. Campaign with mixed segment (eligible + suppressed + excluded + cooling-off players).
    - Verify: only eligible players queued; others denied with correct reasons.
    - Verify: audit events for all denials.
    - Verify: journey continues for eligible players.

## 12. Performance Targets

- Segment evaluation (nightly): <30 minutes for 1M players.
- Journey step execution: <5s p99 per enrollment (including MarketingGate checks).
- MarketingGate check (queue-time): <50ms p99.
- MarketingGate check (send-time): <50ms p99.
- Propensity feature computation (nightly): <60 minutes for 1M players.
- Deterministic join (suppression list + frequency_cap): <20ms p99.

## 13. Open Questions (OQ-ENG-001..006)

| ID | Question | Owner | Due | Status |
|---|---|---|---|---|
| OQ-ENG-001 | Propensity model vendor (in-house vs vendor) | CTO | Phase 22 Stage A | Q5-BLOCKED |
| OQ-ENG-002 | Propensity model recompute cadence (nightly recommended) | Product Owner | Phase 22 Stage A | OPEN |
| OQ-ENG-003 | Journey step retry policy (retry vs advance on send-time denial) | Product Owner | Phase 22 Stage A | OPEN |
| OQ-ENG-004 | Segment membership expiry (TTL; configurable per segment) | Product Owner | Phase 22 Stage B | OPEN |
| OQ-ENG-005 | Marketing channel priority (email > SMS > push; configurable) | Product Owner | Phase 22 Stage A | OPEN |
| OQ-ENG-006 | Propensity feature transparency (privacy policy wording; EU AI Act limited risk) | Legal Counsel + Privacy Owner | Phase 22 Stage B | Q1-BLOCKED |
