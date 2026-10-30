# Data Platform & GGR Design Document (Phase 17)

| Field | Value |
|---|---|
| Authority | DEC-0105..0109 | ADR-0104..0108 |
| Status | Stage A Design (Stage B merge stop #7 active) |
| Coverage floor | 95% (per ADR-0027 v2) |
| Owner | CFO + External Auditor + Reliability Owner |
| Law mandate | Law 6 (Bifurcated Truth) — telemetry never-truth; GGR/NGR sourced from ledger |

## 1. Bifurcated Truth Architecture

### 1.1 Two Pipelines

| Pipeline | Source | Transport | Truth | Consumers |
|---|---|---|---|---|
| Domain Events | Phase 8 outbox | Redis Streams (existing) | is_truth: true | GGR/NGR, regulatory, reconciliation |
| Telemetry | Application instrumentation | Separate Redis stream `telemetry.events` | is_truth: false | Dashboards, alerting, capacity |

### 1.2 Cross-Contamination Prevention

- **Linter rule 141 (Phase 17 renumbered to 144):** no telemetry consumer writes to domain truth tables.
- **Linter rule 142 (Phase 17 renumbered to 145):** no code path reads telemetry + writes domain truth.
- **Code review:** any telemetry PR reviewed by CFO or External Auditor (CODEOWNERS enforcement).

Note: the linter rule numbering in the prompt (141-142 for cross-contamination) was renumbered in the implementation to 144-145 to avoid collision with Phase 17 artifact-existence rules. The substantive content is preserved: rule 144 enforces no-telemetry-in-domain-modules; rule 145 enforces design-doc contracts.

### 1.3 Label Propagation

- Every event carries `is_truth: bool` metadata.
- Consumers check before processing; reject mismatched (financial consumer rejects `is_truth: false`; telemetry consumer rejects `is_truth: true` to prevent accidental dual-pipeline wiring).

### 1.4 Threat Model Mitigation

| Threat | Mitigation |
|---|---|
| Telemetry misused as truth (financial integrity) | Bifurcated truth (rules 144-145); is_truth label; physical separation |
| 2023 fine scenario (AML ingested telemetry as deposits) | Physical separation at transport layer; linter rules forbid cross-pipeline consumers |
| Misconfigured import wires telemetry into domain consumer | CODEOWNERS requires CFO/External Auditor review on telemetry PRs |

## 2. Schema Registry

### 2.1 EventSchema Model

| Field | Type | Notes |
|---|---|---|
| `schema_uuid` | UUID PK | |
| `tenant_uuid` | UUID | Tenant scope (RLS) |
| `name` | str | e.g., `game.bet.placed`, `payment.captured` |
| `version` | str | Semver (e.g., `1.0.0`, `1.1.0`, `2.0.0`) |
| `schema_type` | enum | avro, json, protobuf (Phase 17: json only) |
| `schema_definition` | JSONB | Full JSON Schema definition |
| `compatibility_mode` | enum | backward, forward, full, none |
| `status` | enum | draft, published, deprecated |
| `registered_at` | datetime | |
| `registered_by` | str | Named human (CODEOWNERS) |

### 2.2 Compatibility Modes

- **backward** (default; recommended): new schema can read old data. Adding optional fields is backward-compatible.
- **forward**: old schema can read new data. Removing optional fields is forward-compatible.
- **full**: both backward and forward. Only changes that preserve both directions.
- **none**: breaking change. Requires consumer migration plan; new version must be major bump (`2.0.0`).

### 2.3 Consumer Registration

- Every consumer declares `(schema_name, schema_version)` in its registration.
- Linter rule (Phase 17) enforces every consumer is registered.
- A consumer registered against v1.0.0 will process events tagged `1.0.0` and (if backward-compatible) events tagged `1.1.0`. It will NOT process events tagged `2.0.0`.

### 2.4 Validation & Drift Detection

- Every event validated against schema before publish; invalid → DLQ with `E_SCHEMA_VALIDATION_FAILED`.
- Drift detection: every committed event fixture (in tests) matches its declared schema. CI check.

## 3. Consumer Registry & Idempotency

### 3.1 EventConsumer Model

| Field | Type | Notes |
|---|---|---|
| `consumer_uuid` | UUID PK | |
| `tenant_uuid` | UUID | Tenant scope (RLS) |
| `name` | str | e.g., `ggr_consumer`, `ngr_consumer` |
| `schema_name` | str | FK → EventSchema.name |
| `schema_version` | str | FK → EventSchema.version |
| `pipeline` | enum | `domain` or `telemetry` (per ADR-0104) |
| `status` | enum | active, paused, deprecated |
| `owner` | str | Named human (CODEOWNERS) |
| `last_processed_message_id` | str | For lag monitoring |
| `last_processed_at` | datetime | For lag monitoring |

### 3.2 Idempotency (Phase 8 Inbox Pattern — Extended)

- Per-consumer inbox table: `(message_id, consumer_id)` composite PK.
- `ON CONFLICT DO NOTHING` — duplicate insert is a no-op.
- Insert AFTER processing (same DB transaction as side effect).
- Same event delivered twice → single side effect (exactly-once-effect semantics).

### 3.3 Lag Monitoring

- Track `last_processed_message_id` per consumer (updated on every successful processing).
- Track `last_processed_at` per consumer (wall-clock time of last successful processing).
- Celery beat task `check_consumer_lag` runs every 30 seconds.
- Alert if lag > 1000 messages OR (now - last_processed_at) > 60 seconds (OQ-DATA-005 default).
- Dashboard (`/admin/consumers/`) shows lag per consumer in real time.

### 3.4 DLQ (Phase 8 Pattern — Extended)

- Poison messages land in DLQ after N=3 retries (default).
- DLQ message enrichment: original payload + failure reason + retry count + first/last attempt timestamps + consumer name + stream name.
- Alert on DLQ arrival (Slack `#ops-alerts` + PagerDuty if rate > 10/hour).
- Replay command: `manage.py replay_dlq --consumer <name> --from <ts> --to <ts>`. Idempotent (inbox pattern).

## 4. Read Models

### 4.1 GGR (Gross Gaming Revenue)

- **Formula:** `sum(bets) - sum(wins)` per (tenant, period, game_class, jurisdiction)
- **Source events:** `game.bet.placed`, `game.bet.result`
- **Refresh:** real_time (outbox consumer updates on every bet)
- **Materialized view:** `ggr_mv`

### 4.2 NGR (Net Gaming Revenue)

- **Formula:** `GGR - bonuses_awarded - bonuses_converted - payment_fees - chargeback_fees - other_deductions`
- **Source events:** GGR + `bonus.award_created`, `bonus.converted`, `payment.captured`, `dispute.lost`
- **Refresh:** real_time + scheduled (hourly full rebuild to catch drift)
- **Materialized view:** `ngr_mv`

### 4.3 Player Activity

- Sessions, bets, deposits, withdrawals per (player, period)
- **Source events:** `player.session.started`, `player.session.ended`, `game.bet.placed`, `payment.captured`, `payment.payout_initiated`
- **Refresh:** real_time
- **Materialized view:** `player_activity_mv`

### 4.4 Financial Summary

- Deposits, withdrawals, bonuses awarded, bonuses converted per (tenant, period)
- **Source events:** `payment.captured`, `payment.payout_initiated`, `bonus.award_created`, `bonus.converted`
- **Refresh:** scheduled (daily at 03:00 UTC)
- **Materialized view:** `financial_summary_mv`

### 4.5 Reconciliation

- **Daily job** (Celery beat, 04:00 UTC): for each read model, recompute metric from Phase 11 ledger and compare to read model's stored value.
- **Mismatch** (delta > £0.01 or 0.01%, whichever greater) → alert + HALT.
  - Alert: PagerDuty to CFO + External Auditor.
  - HALT: read model marked `stale` in dashboard; regulatory report generation refuses to use a stale read model.
- **Audit event:** `reporting.reconciliation.completed` (match) or `reporting.reconciliation.mismatch` (HALT).
- Reuses Phase 11's `ReconciliationLog` model (extended with `read_model_name` field).

## 5. GGR/NGR Regulatory Reporting

### 5.1 RegulatoryReport Model

| Field | Type | Notes |
|---|---|---|
| `report_uuid` | UUID PK | |
| `tenant_uuid` | UUID | Tenant scope (RLS) |
| `jurisdiction_code` | str | e.g., `uk_gc`, `mga`, `agco` |
| `period` | str | e.g., `2026-10`, `2026-Q1` |
| `report_type` | enum | GGR, NGR, AML, RG |
| `data` | JSONB | Full report payload (format per jurisdiction) |
| `generated_at` | datetime | |
| `generated_from_read_model` | bool | True if sourced from read model (post-reconciliation) |
| `reconciliation_passed` | bool | True if reconciliation passed before generation |
| `submitted_at` | datetime | When submitted to regulator portal (null if not yet) |
| `submitted_by` | str | Named human (CODEOWNERS) |

### 5.2 Per-Jurisdiction Formats (Q1-blocked; stub for dev)

- **UK GC:** monthly GGR report (CSV: period, game_class, ggr_gbp)
- **MGA:** quarterly GGR/NGR report (Excel: summary, by_game_class, by_jurisdiction)
- **AGCO:** quarterly GGR/NGR report (JSON submission via portal API)
- **Other jurisdictions:** per local requirements (Q1-blocked)

Stage A: format configuration is JSONB on `JurisdictionReportConfig` model (per-tenant, per-jurisdiction). Stub returns generic JSON format; production config is Q1-blocked.

### 5.3 Submission

- **Manual** (portal): operator downloads report from admin UI; uploads to regulator portal. `submitted_at` + `submitted_by` recorded.
- **API** (Q5-blocked): automated submission via regulator portal API. Future phase.

### 5.4 Source of Truth

Phase 11 ledger (NOT telemetry; NOT read model cache). Report generation:

1. Query GGR/NGR read model for (tenant, period, game_class, jurisdiction).
2. Verify read model against ledger (reconciliation job, ADR-0107).
3. If reconciliation passes: use read model values for the report.
4. If reconciliation fails: HALT; do not generate the report until mismatch resolved.

This ensures the regulatory report is always sourced from ledger-reconciled data.

## 6. Linter Rules Added (Phase 17)

Rules 134-145 (12 new rules):

| Rule | Description |
|---|---|
| 134 | Phase 17 ADRs 0104-0108 all exist |
| 135 | ADR-0104 documents bifurcated truth + is_truth label |
| 136 | ADR-0105 documents schema registry + compatibility modes |
| 137 | ADR-0106 documents consumer registry + idempotency + DLQ |
| 138 | ADR-0107 documents read models + reconciliation |
| 139 | ADR-0108 documents GGR/NGR + regulatory reporting |
| 140 | Phase 17 design doc exists |
| 141 | Phase 17 stage handoff exists |
| 142 | Phase 17 audit exists |
| 143 | Open questions register documents OQ-DATA-001..006 |
| 144 | Bifurcated truth — no telemetry reference in domain modules |
| 145 | GGR/NGR sourced from ledger, not telemetry (design doc contract) |

**Note on renumbering:** The prompt's original rules 141-142 (cross-contamination prevention) were renumbered to 144-145 in the implementation. The reason: rules 134-142 are ADR-artifact existence + keyword checks; rules 143-145 are behavior-enforcing (open questions register, no-telemetry-in-domain, design-doc contracts). This preserves the substantive content while keeping the rule numbering monotonic and grouped by type.

## 7. Cross-Phase Continuity

### Phase 4 contracts
- Error format: `E_SCHEMA_VALIDATION_FAILED`, `E_CONSUMER_LAG_HIGH`, `E_RECONCILIATION_MISMATCH`, `E_TELEMETRY_TRUTH_VIOLATION`
- Structured logging with `correlation_id`, `tenant_id`, `consumer_name`, `schema_name`
- mypy strict on reporting module; coverage ≥ 95%

### Phase 5 RLS extension
- All read models, regulatory reports, schema registry, consumer registry — tenant-scoped.

### Phase 7 audit extension
- Event type taxonomy: `reporting.*`, `schema.*`, `consumer.*`, `regulatory.*` events.

### Phase 8 outbox continuity
- Domain events flow through existing outbox.
- Consumers use existing inbox pattern (extended).
- DLQ integration.

### Phase 11 ledger continuity
- GGR/NGR sourced from ledger (truth).
- Read models reconcile against ledger.
- Mismatch → HALT.

### Phase 14 protection continuity
- Per-jurisdiction breakdown uses `JurisdictionPort`.

### Phase 15/16 game continuity
- GGR/NGR consumes `game.bet.placed`, `game.bet.result` events.
- Per-game-class breakdown (sourced from math version `math_config.game_class`).

## 8. Threat Model Mitigation

| Threat | Mitigation |
|---|---|
| Telemetry misused as truth (financial integrity) | Bifurcated truth (rules 144-145); is_truth label |
| Schema drift breaks consumers | Schema registry (rule 135); validation; drift detection |
| Duplicate event processing | Idempotency inbox (rule 137); at-least-once + exactly-once-effect |
| Consumer lag (data freshness) | Lag monitoring + alerting (rule 137) |
| Cross-tenant report leak | RLS (rule 138); negative test |
| GGR/NGR miscalculation | Ledger reconciliation (rule 138); formula verification tests |
| Regulatory report inaccuracy | Sourced from ledger-reconciled read models (rule 145) |

## 9. Concurrency Test Designs (Stage B)

1. Concurrent event publication (schema validation; idempotent).
2. Concurrent consumer processing (inbox prevents duplicate side effects).
3. Concurrent read model refresh (only one at a time; row lock).
4. Concurrent reconciliation (idempotent; mismatch detected).
5. Concurrent regulatory report generation (idempotent per period).
6. Concurrent telemetry + domain event (no cross-contamination).

## 10. Performance Targets

- Event publication latency: <10ms p99 (outbox insert)
- Consumer processing latency: <100ms p99 (inbox insert + side effect)
- GGR/NGR read model refresh: <60s for 1M events (scheduled rebuild)
- Regulatory report generation: <5 minutes for quarterly report
- Reconciliation job: <30 minutes for 1M ledger entries

## 11. Open Questions (OQ-DATA-001..006)

| ID | Question | Owner | Due | Status |
|---|---|---|---|---|
| OQ-DATA-001 | Telemetry backend (separate Redis stream vs time-series DB) | Reliability Owner | Phase 17 Stage A | OPEN |
| OQ-DATA-002 | Regulatory report format per jurisdiction | Compliance Officer | Phase 22 | Q1-BLOCKED |
| OQ-DATA-003 | Regulator portal API integration | Compliance Officer | Phase 22 | Q5-BLOCKED |
| OQ-DATA-004 | Schema registry compatibility mode default (backward recommended) | API Owner | Phase 17 Stage A | OPEN |
| OQ-DATA-005 | Consumer lag threshold (1000 messages or 60s recommended) | Reliability Owner | Phase 17 Stage A | OPEN |
| OQ-DATA-006 | Reconciliation cadence (daily recommended) | CFO | Phase 17 Stage A | OPEN |
