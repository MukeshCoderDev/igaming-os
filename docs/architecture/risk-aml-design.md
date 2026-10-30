# Risk, AML & Cases Design Document (Phase 18)

| Field | Value |
|---|---|
| Authority | DEC-0110..0115 | ADR-0109..0114 |
| Status | Stage A Design (Stage B merge stop #8 active) |
| Coverage floor | 95% (per ADR-0027 v2) |
| Owner | Compliance Officer + MLRO + Security Owner |
| Law mandate | Law 14 (Bounded Agents — punitive action approval + dual control); FATF Rec 20 (TM rules); tipping-off prohibition (criminal liability) |

## 1. Schema Topology

### 1.1 Tables (with RLS — Phase 5 continuity)

**risk_signal** (detected signals):
- `signal_uuid` UUID PK
- `tenant_uuid` UUID NOT NULL (RLS-scoped)
- `signal_type` ENUM (12 types per ADR-0109)
- `player_uuid` UUID NOT NULL
- `severity` ENUM (low, medium, high, critical)
- `evidence` JSONB NOT NULL
- `detected_at` TIMESTAMPTZ NOT NULL
- `status` ENUM (open, investigated, dismissed, escalated)
- `tm_rule_uuid` UUID FK → tm_rule (nullable for real-time signals)
- `risk_score_contribution` DECIMAL(5,2)
- `created_at`, `updated_at`

**tm_rule** (transaction monitoring rules):
- `rule_uuid` UUID PK
- `tenant_uuid` UUID NOT NULL
- `rule_name` VARCHAR(255) NOT NULL
- `rule_type` ENUM (velocity, structural, behavioral, jurisdictional, threshold)
- `parameters` JSONB NOT NULL (thresholds, time windows, per-jurisdiction config)
- `risk_score_weight` DECIMAL(5,2) NOT NULL
- `status` ENUM (active, paused, deprecated)
- `version` INT NOT NULL (insert-only per version)
- `approved_by` VARCHAR(255) NOT NULL (named human)
- `approved_at` TIMESTAMPTZ NOT NULL
- `created_at`, `updated_at`

**sar_case** (SAR/STR workflow):
- `sar_uuid` UUID PK
- `tenant_uuid` UUID NOT NULL
- `player_uuid` UUID NOT NULL
- `trigger_signal_uuid` UUID FK → risk_signal
- `risk_case_uuid` UUID FK → risk_case (nullable)
- `status` ENUM (draft, mlro_review, filed, closed, dismissed)
- `sar_narrative` TEXT
- `filed_at` TIMESTAMPTZ NULLABLE
- `filed_by` VARCHAR(255) NULLABLE (MLRO name)
- `fiu_confirmation_id` VARCHAR(255) NULLABLE
- `fiu_jurisdiction` VARCHAR(50) (e.g., `uk_nca`, `us_fincen`)
- `account_frozen` BOOLEAN DEFAULT FALSE
- `retention_expires_at` TIMESTAMPTZ NOT NULL (5-10 years per jurisdiction)
- `created_at`, `updated_at`
- **MLRO-only visibility** (Phase 10 pattern; RLS policy restricts to `mlro` role)

**risk_case** (case management):
- `case_uuid` UUID PK
- `tenant_uuid` UUID NOT NULL
- `player_uuid` UUID NOT NULL
- `case_type` ENUM (aml_investigation, fraud_investigation, rg_review, bonus_abuse, payment_dispute)
- `status` ENUM (open, under_investigation, pending_approval, closed_resolved, closed_escalated, closed_dismissed)
- `priority` ENUM (low, medium, high, critical)
- `assigned_to` VARCHAR(255) NULLABLE (compliance officer)
- `evidence` JSONB NOT NULL (aggregated from all modules)
- `kyc_case_uuid` UUID NULLABLE (link to Phase 10)
- `dispute_case_uuid` UUID NULLABLE (link to Phase 12)
- `abuse_flag_uuid` UUID NULLABLE (link to Phase 13)
- `sar_case_uuid` UUID NULLABLE (link to SAR)
- `cumulative_risk_score` DECIMAL(8,2)
- `created_at`, `updated_at`

**punitive_action** (approval workflow):
- `action_uuid` UUID PK
- `tenant_uuid` UUID NOT NULL
- `player_uuid` UUID NOT NULL
- `case_uuid` UUID FK → risk_case
- `action_type` ENUM (account_freeze, account_closure, bonus_clawback, payment_block, se_block)
- `status` ENUM (requested, approved, rejected, executed, reversed)
- `severity` ENUM (low, high) — high = dual control required
- `requested_by` VARCHAR(255) NOT NULL
- `requested_at` TIMESTAMPTZ NOT NULL
- `approved_by` VARCHAR(255) NULLABLE
- `approved_at` TIMESTAMPTZ NULLABLE
- `executed_at` TIMESTAMPTZ NULLABLE
- `justification` TEXT NOT NULL
- `reversal_uuid` UUID FK → punitive_action (nullable)
- `created_at`, `updated_at`

**appeal** (player appeals):
- `appeal_uuid` UUID PK
- `tenant_uuid` UUID NOT NULL
- `player_uuid` UUID NOT NULL
- `punitive_action_uuid` UUID FK → punitive_action
- `status` ENUM (submitted, under_review, upheld, overturned, rejected)
- `submitted_at` TIMESTAMPTZ NOT NULL
- `submitted_reason` TEXT
- `reviewed_at` TIMESTAMPTZ NULLABLE
- `reviewed_by` VARCHAR(255) NULLABLE (must NOT be original approver)
- `decision_justification` TEXT NULLABLE
- `reversal_punitive_action_uuid` UUID FK → punitive_action (nullable)
- `created_at`, `updated_at`

### 1.2 DB Constraints

- RLS policies on all tables per Phase 5 pattern.
- Insert-only triggers on `sar_case`, `punitive_action`, `appeal` (Phase 7 pattern).
- MLRO-only access on `sar_case` (Phase 10 pattern; RLS policy restricts to `mlro` role).
- CHECK constraint on `punitive_action`: high-severity actions require `approved_by != requested_by`.

## 2. Signal Generation Architecture

### 2.1 Rule-Based Generation (recommended for regulators)

Scheduled job: Celery beat task `generate_risk_signals` runs every 5 minutes.
- Scans recent transactions (last 5 minutes).
- Evaluates each active TM rule.
- Generates RiskSignal if rule matches.

### 2.2 Real-Time Generation

Phase 8 outbox consumer.
- On event publish (payment, bet, withdrawal, bonus).
- Evaluates real-time rules (high-severity single-event: sanctions match, PEP match, threshold breach).
- Generates RiskSignal immediately for high-severity.

### 2.3 ML-Based (deferred)

Phase 19+ or vendor (Q5-blocked; OQ-RISK-001). Not in Phase 18 scope.

## 3. TM Rules Engine

### 3.1 Rule Types (5)

1. **threshold** — deposit > $10,000 in 24h (CTR threshold per jurisdiction)
2. **velocity** — deposit/bet/withdrawal velocity per time window
3. **structural** — structuring detection (multiple deposits < CTR threshold totaling > CTR in 24h)
4. **behavioral** — unusual bet patterns, chip dumping
5. **jurisdictional** — transactions with high-risk jurisdictions

### 3.2 Rule Evaluation

- Scheduled (every 5 min) + real-time (on event publish)
- Actions: generate_signal, escalate_to_case, auto_freeze, alert_compliance
- Per-jurisdiction thresholds (Q1-blocked; stub returns defaults)
- Rule versioning: every change = new version (insert-only); `approved_by` recorded

### 3.3 Risk Scoring

- Each signal contributes `risk_score_weight` to player's cumulative score
- Cumulative score stored on player's risk profile
- Severity: low (1-10), medium (11-25), high (26-50), critical (51+)
- Critical → auto-escalate to RiskCase (ADR-0112)

## 4. SAR/STR Workflow

### 4.1 FSM

```
signal_escalated → mlro_review → filed → closed (terminal)
                                ↘ dismissed (with justification)
```

### 4.2 Tipping-off Prohibition (CRIMINAL LIABILITY)

- Player NOT informed of SAR
- Linter rule 157: no code path notifies player of SAR (tipping-off grep; zero findings required)
- MLRO-only visibility (Phase 10 pattern; RLS restricts sar_case to `mlro` role)
- Every SAR action audited (Phase 7)
- Non-MLRO read attempts flagged as security incidents

### 4.3 FIU Submission

- Manual (portal) — MLRO composes SAR narrative; submits via FIU portal; confirmation ID stored
- API (Q5-blocked; OQ-RISK-002) — automated submission; deferred to Phase 22+

### 4.4 Account Freeze on Filing

- On SAR filing, account MAY be frozen per jurisdiction rules (Q1-blocked)
- Freeze uses Phase 14 kill-switch pattern (synchronous; <200ms SLO)
- Freeze is a punitive action (ADR-0113); requires dual control if jurisdiction mandates

### 4.5 Retention

- 5-10 years per AML regulations (Q1-blocked; OQ-RISK-004)
- UK: 5 years; US: 5 years; EU: 5 years (some 10); Germany: 10 years
- Insert-only trigger; deletion before retention expiry forbidden at DB layer

## 5. Punitive Action Approval

### 5.1 FSM

```
requested → approved → executed
         ↘ rejected
```

### 5.2 Dual Control (High-Severity)

- `account_closure`, `se_block`: requester != approver (enforced at application + DB layer)
- Linter rule 157 (renumbered to 156 in implementation): no punitive action executes without recorded approval
- Linter rule 158 (renumbered to 157 in implementation): high-severity actions require dual control

### 5.3 Reversibility

| Action | Reversible? | Reversal mechanism |
|---|---|---|
| account_freeze | YES | Unfreeze (new PunitiveAction) |
| bonus_clawback | YES | Re-award via Phase 11 reversal-of-reversal (new ledger entry) |
| payment_block | YES | Unblock (new PunitiveAction) |
| se_block | NO | IRREVERSIBLE (regulator-mandated; Phase 14 ADR-0085) |
| account_closure | NO | IRREVERSIBLE (terminal) |

Reversal = new PunitiveAction (insert-only); original never mutated.

## 6. Appeal Workflow

### 6.1 FSM

```
submitted → under_review → upheld (action stands)
                         ↘ overturned (action reversed)
                         ↘ rejected (procedural)
```

### 6.2 Appeal Window

- Configurable per jurisdiction (Q1-blocked; OQ-RISK-005)
- Default: 30 days
- JurisdictionPort (Phase 14) returns the appeal window
- Appeals after window → auto-rejected

### 6.3 Separation of Duties

- Reviewer (`reviewed_by`) must NOT be the original approver (`approved_by` on PunitiveAction)
- Prevents self-review of one's own decisions

### 6.4 Tipping-off Extends

- If punitive action was SAR-triggered, appeal notification must NOT reveal SAR
- Player sees: "Your appeal regarding [action_type] has been [upheld/overturned]"
- No SAR-related language in any appeal notification

## 7. Linter Rules Added (Phase 18)

Rules 146-158 (13 new rules):

| Rule | Description |
|---|---|
| 146 | Phase 18 ADRs 0109-0114 all exist |
| 147 | ADR-0109 documents risk signal model + 12-type catalog |
| 148 | ADR-0110 documents TM rules engine + 5 rule types |
| 149 | ADR-0111 documents SAR workflow + MLRO + tipping-off |
| 150 | ADR-0112 documents risk case management + evidence |
| 151 | ADR-0113 documents punitive action + dual control |
| 152 | ADR-0114 documents appeal workflow + separation of duties |
| 153 | Phase 18 design doc exists |
| 154 | Phase 18 stage handoff exists |
| 155 | Phase 18 audit exists |
| 156 | Open questions register documents OQ-RISK-001..006 |
| 157 | Tipping-off prohibition — no SAR in notification templates (criminal liability) |
| 158 | Risk-AML design doc contracts (domain events only, not telemetry; tipping-off; MLRO; dual control; Law 14) |

## 8. Cross-Phase Continuity

### Phase 7 audit extension
- Event type taxonomy: `risk.signal_detected`, `risk.case_created`, `risk.case_escalated`, `aml.sar_filed`, `aml.tipping_off_blocked`, `punitive.action_requested`, `punitive.action_approved`, `punitive.action_executed`, `appeal.submitted`, `appeal.reviewed`

### Phase 8 outbox continuity
- Risk events via outbox; consumers idempotent (Phase 17 pattern)
- Domain events only — telemetry never-truth (Phase 17 bifurcated truth)

### Phase 10 KYC continuity
- KYC status feeds risk scoring
- PEP/sanctions matches generate signals (real-time)
- SAR stub from Phase 10 replaced by full workflow (ADR-0111)
- MLRO role ratified in Phase 10 (DEC-0061, ADR-0056)

### Phase 11 ledger continuity
- Transaction data for TM (domain events only)
- Punitive action reversals post to ledger (terminal reversal pattern)
- Appeal reversals post to ledger

### Phase 12 payments continuity
- Payment patterns feed TM
- `payment_block` punitive action

### Phase 13 bonuses continuity
- Bonus abuse signals (`kyc_mismatch`, `device_fingerprint_anomaly`)
- `bonus_clawback` punitive action

### Phase 14 protection continuity
- RG distress signals feed risk scoring
- `se_block` punitive action (Phase 14 SE; irreversible)
- Kill-switch pattern for `account_freeze`

### Phase 15/16 games continuity
- Game round patterns feed TM (bet velocity, unusual patterns)
- Bet patterns feed behavioral signals (`behavioral_unusual_bet`, `behavioral_chip_dumping`)

### Phase 17 reporting continuity
- GGR/NGR for risk scoring context
- Risk reports tenant-scoped
- Bifurcated truth: TM uses domain events only (NOT telemetry)

## 9. Threat Model Mitigation

| Threat | Mitigation |
|---|---|
| Missed suspicious activity (regulator fine) | TM rules engine (12 signal types, 5 rule types); scheduled + real-time |
| SAR tipping-off (criminal liability) | Tipping-off prohibition (rule 157); MLRO-only visibility; grep zero findings |
| Punitive action without approval (Law 14 violation) | Approval workflow (rule 156); dual control (rule 157 for high-severity) |
| SAR visibility leak (regulator) | MLRO-only access (Phase 10 pattern; RLS restricts to `mlro` role) |
| Appeal window bypass | JurisdictionPort check; configurable window (Q1-blocked) |
| False positive overload | Severity escalation; false positive monitoring dashboard |
| Cross-tenant risk leak | RLS on all risk tables (Phase 5) |
| Telemetry misused as TM source | Bifurcated truth (Phase 17 ADR-0104); TM uses domain events only |
| Rogue compliance officer abuse | Dual control for high-severity; separation of duties on appeals |

## 10. Concurrency Test Designs (Stage B)

1. Concurrent signal generation (idempotent; same transaction → single signal).
2. Concurrent TM rule evaluation (only one job instance; row lock).
3. Concurrent SAR filing (only one SAR per case; idempotent).
4. Concurrent punitive action approval (only one approval per action).
5. Concurrent appeal submission (only one appeal per punitive action within window).
6. Concurrent case escalation (only one escalation per case).

## 11. Open Questions (OQ-RISK-001..006)

| ID | Question | Owner | Due | Status |
|---|---|---|---|---|
| OQ-RISK-001 | ML-based TM (Phase 19+ or vendor — Q5-blocked) | CTO | Phase 19+ | Q5-BLOCKED |
| OQ-RISK-002 | FIU submission API integration | Compliance Officer | Phase 22 | Q5-BLOCKED |
| OQ-RISK-003 | CTR threshold per jurisdiction (default $10,000) | Compliance Officer | Phase 22 | Q1-BLOCKED |
| OQ-RISK-004 | SAR retention period per jurisdiction (5-10 years) | Legal Counsel | Phase 22 | Q1-BLOCKED |
| OQ-RISK-005 | Appeal window per jurisdiction (default 30 days) | Legal Counsel | Phase 22 | Q1-BLOCKED |
| OQ-RISK-006 | Risk scoring weights (configurable per tenant) | Compliance Officer | Phase 18 Stage B | OPEN |
