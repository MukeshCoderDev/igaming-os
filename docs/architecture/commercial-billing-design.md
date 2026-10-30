# Commercial & Billing Design Document (Phase 23)

| Field | Value |
|---|---|
| Authority | DEC-0143..0147 | ADR-0142..0146 |
| Status | Stage A Design (Stage B merge stop #13 active) |
| Coverage floor | 95% (per ADR-0027 v2) |
| Owner | CFO + Legal Counsel + External Auditor |
| Law mandate | Law 4 (Ledger — invoices reconcile against ledger), Law 9 (Immutable Audit — billing changes hash-chained), Law 7 (Event — billing events via outbox); DEC-0024 (B2B OS provider model — HUMAN-APPROVED) |

## 1. Architecture Overview

### 1.1 Commercial Layer

1. **Contract Model** (B2B operator contracts; versioning; lifecycle FSM)
2. **Fee Schedule Model** (rev_share, fixed, hybrid, tiered; per-product; per-jurisdiction)
3. **Rev-Share Invoice Generation** (from GGR; reconciliation; ledger posting)
4. **Operator Statements** (financial reporting; per-jurisdiction breakdown)
5. **Billing Change Audit** (Phase 7 continuity; hash-chained; immutable)

### 1.2 Laws Enforced

- **Law 4 (Ledger):** invoices reconcile against ledger (source of truth).
- **Law 9 (Immutable Audit):** billing changes audited; hash-chained.
- **Law 7 (Event):** billing events via outbox.

### 1.3 Business Model

DEC-0024 (HUMAN-APPROVED): B2B OS provider model. Noventra charges operators via:
- Rev-share (% of GGR/NGR)
- Fixed monthly fee
- Hybrid (rev-share + minimum)
- Tiered (volume-based)

## 2. Schema Topology

### 2.1 Tables (with RLS — Phase 5 continuity)

**contract** (B2B operator contracts): `contract_uuid` UUID PK, `tenant_uuid` UUID (RLS — operator is the tenant), `contract_type` ENUM (rev_share/fixed_fee/hybrid/white_label), `start_date` DATE, `end_date` DATE (nullable), `status` ENUM (draft/active/suspended/terminated/expired), `jurisdiction_codes` TEXT[], `product_scope` JSONB, `fee_schedule_uuid` UUID FK, `billing_cycle` ENUM (monthly/quarterly), `payment_terms` ENUM (net_30/net_60/net_90), `created_by` VARCHAR, `created_at`/`updated_at`.

**contract_version** (contract versioning): `version_uuid` UUID PK, `contract_uuid` FK, `version_number` INT, `snapshot` JSONB, `effective_from` DATE, `effective_until` DATE (nullable), `amended_by` VARCHAR, `amendment_reason` TEXT, `created_at`. UNIQUE(contract_uuid, version_number).

**fee_schedule** (fee structure): `schedule_uuid` UUID PK, `tenant_uuid` UUID (RLS), `contract_uuid` FK, `fee_type` ENUM (rev_share/fixed_fee/hybrid/tiered), `fee_structure` JSONB, `effective_from` DATE, `effective_until` DATE (nullable), `status` ENUM (active/superseded), `created_by` VARCHAR, `created_at`/`updated_at`.

**invoice** (generated invoices): `invoice_uuid` UUID PK, `tenant_uuid` UUID (RLS), `contract_uuid` FK, `invoice_number` VARCHAR (sequential per tenant), `period` VARCHAR, `billing_date`/`due_date` DATE, `ggr_amount_minor`/`ngr_amount_minor` BIGINT, `deductions` JSONB, `rev_share_rate` DECIMAL(5,4), `rev_share_amount_minor`/`fixed_fee_amount_minor`/`total_amount_minor` BIGINT, `currency_code` CHAR(3), `status` ENUM (draft/generated/sent/paid/overdue/disputed/voided/closed), `payment_uuid` UUID (nullable; FK Phase 12), `reconciliation_status` ENUM (matched/mismatched/pending), `reconciliation_mismatch_details` JSONB (nullable), `created_at`/`updated_at`. Insert-only (Phase 7). UNIQUE(tenant_uuid, invoice_number).

**credit_note** (invoice corrections): `credit_note_uuid` UUID PK, `tenant_uuid` UUID (RLS), `invoice_uuid` FK, `amount_minor` BIGINT, `reason` TEXT, `created_by` VARCHAR, `created_at`. Insert-only.

**operator_statement** (financial reporting): `statement_uuid` UUID PK, `tenant_uuid` UUID (RLS), `contract_uuid` FK, `period` VARCHAR, `statement_type` ENUM (monthly/quarterly/annual), `ggr_summary`/`ngr_summary`/`fee_breakdown` JSONB, `invoice_uuid` FK, `generated_at`/`sent_at` TIMESTAMPTZ, `sent_to` VARCHAR (nullable), `status` ENUM (generated/sent/acknowledged), `reconciliation_status` ENUM (matched/mismatched/pending), `created_at`/`updated_at`.

### 2.2 DB Constraints

- RLS policies on all tables per Phase 5 pattern.
- Insert-only triggers on `invoice`, `credit_note` (Phase 7 pattern).
- CHECK: `invoice` `reconciliation_status` NOT NULL.
- CHECK: `contract_version` `effective_from` < `effective_until` (when `effective_until` NOT NULL).

## 3. Invoice Generation Flow

### 3.1 Scheduled Job (Monthly)

1. For each active contract with `billing_cycle=monthly`:
   - Determine billing period (previous month).
   - Pull ContractVersion effective at billing period.
   - Pull FeeSchedule effective at billing period.
   - Pull GGR/NGR from Phase 17 read models (per-jurisdiction, per-game_class).
   - Calculate `rev_share_amount = GGR × rate` (or tiered calc).
   - Calculate `total = rev_share_amount + fixed_fee_amount` (if hybrid).
   - Create Invoice (`status=draft`, `reconciliation_status=pending`).
   - Post to Phase 11 ledger: journal_entry (debit accounts_receivable, credit revenue).
   - Emit outbox event: `billing.invoice_generated`.
   - Audit event per Phase 7.

### 3.2 Reconciliation Job

1. For each invoice with `reconciliation_status=pending`:
   - Verify: `rev_share_amount = GGR × rate` (or tiered calc).
   - Verify: GGR read model matches Phase 11 ledger (Phase 17 reconciliation).
   - If match: `reconciliation_status=matched`; `status=generated`.
   - If mismatch: `reconciliation_status=mismatched`; alert + HALT; details recorded.

### 3.3 Invoice Lifecycle FSM

```
draft → generated (reconciliation matched) → sent → paid → closed
                                                ↘ disputed → resolved → paid/voided
                                                ↘ overdue → collected → paid
draft → mismatched (reconciliation failed) → draft (re-investigate)
any → voided (correction; credit note issued)
```

## 4. Fee Calculation

### 4.1 Rev-Share
- `rev_share_amount = NGR × rate`
- Rate configurable per product, per jurisdiction.

### 4.2 Fixed Fee
- `fixed_fee_amount = configured amount` (per billing cycle).

### 4.3 Hybrid
- `rev_share_amount = NGR × rate`
- `total = max(rev_share_amount, minimum_monthly)`

### 4.4 Tiered
- Determine tier based on cumulative GGR.
- `rev_share_amount = GGR × tier_rate`.

## 5. Linter Rules 206-215 (Phase 23)

| Rule | Description |
|---|---|
| 206 | Phase 23 ADRs 0142-0146 all exist |
| 207 | ADR-0142 documents contract model + versioning + FSM + multi-jurisdiction + HUMAN-APPROVED |
| 208 | ADR-0143 documents fee schedule + 4 types + per-product/jurisdiction + versioning + immutable |
| 209 | ADR-0144 documents invoice generation + reconciliation + ledger posting + credit notes + FSM |
| 210 | ADR-0145 documents operator statements + per-jurisdiction + transactional bypass + reconciliation |
| 211 | ADR-0146 documents billing audit + 16 events + hash-chained + immutable + external auditor |
| 212 | Phase 23 design doc exists |
| 213 | Phase 23 stage handoff exists |
| 214 | Phase 23 audit exists |
| 215 | OQ-COMM-001..006 + design doc contracts (Law 4/9 + reconciliation + GGR + ledger + DEC-0024 + Contract + FeeSchedule + Invoice + HUMAN-APPROVED + hash) |

## 6. Cross-Phase Continuity

### Phase 4 contracts
- Error format: `E_INVOICE_RECONCILIATION_MISMATCH`, `E_CONTRACT_NOT_ACTIVE`, `E_FEE_SCHEDULE_EXPIRED`, `E_INVOICE_ALREADY_PAID`, `E_CREDIT_NOTE_EXCEEDS_INVOICE`
- Structured logging with `correlation_id`, `tenant_id`, `contract_id`, `invoice_id`
- mypy strict on commercial module; coverage ≥95%

### Phase 5 RLS extension
- All commercial tables tenant-scoped.

### Phase 7 audit extension
- 16 new `billing.*` event types.
- Billing events hash-chained into operational audit chain.
- `noventra_auditor` role SELECT access.

### Phase 8 outbox continuity
- Billing events via outbox; consumers idempotent (Phase 17 pattern).

### Phase 9 retention continuity
- Contracts retained 7+ years (financial contracts).
- Fee schedules retained 7+ years.
- Invoices retained 7+ years (financial regulations).

### Phase 11 ledger continuity
- Invoice generation posts to ledger (debit AR, credit revenue).
- Invoice payment posts to ledger (debit cash, credit AR).
- Credit notes post reversal entries (terminal).
- Reconciliation against ledger (source of truth).

### Phase 12 payments continuity
- Invoice payment via Phase 12 payment service.
- Operator payout (rev-share payment to operator if operator is net creditor).
- `payment_uuid` linked on invoice.

### Phase 17 reporting continuity
- GGR/NGR read models are invoice source.
- Phase 17 reconciliation (GGR vs ledger) is prerequisite for invoice reconciliation.
- Per-jurisdiction GGR for operator statements.

### Phase 21 compliance continuity
- Billing audit events available for external auditor review.
- ComplianceReview covers billing changes.
- Vendor registry for billing vendors (payment processors for operator payouts).

### Phase 22 engagement continuity
- Operator statements are transactional (bypass MarketingGate — linter rule 209/210).
- No cross-contamination between marketing sends (Phase 22) and financial statements (Phase 23).

## 7. Threat Model Mitigation

| Threat | Mitigation |
|---|---|
| Invoice diverges from GGR (revenue leakage) | Reconciliation job + HALT (linter rule 206); Phase 17 GGR reconciliation |
| Billing changes unaudited (Law 9 violation) | Linter rule 207; hash-chained audit (rule 215) |
| Fee schedule changed mid-period (billing integrity) | Versioning; effective_from/effective_until (rule 208); immutability |
| Invoice tampered (financial fraud) | Insert-only triggers (Phase 7); hash-chained audit |
| Operator statement inaccuracy | Reconciliation against ledger (rule 210); per-jurisdiction breakdown |
| Contract without HUMAN-APPROVED signature (governance gap) | Linter rule 214; Legal Counsel + CFO required |
| MarketingGate blocks operator statement (transactional blocked as marketing) | Linter rule 209; transactional bypass |
| Credit note exceeds invoice (financial error) | Linter rule 213; reversal reference check |
| Cross-tenant invoice leak (Info Disclosure) | RLS on all commercial tables (Phase 5) |

## 8. Concurrency Test Designs (Stage B)

1. Concurrent invoice generation (per-tenant; per-period; idempotent).
2. Concurrent reconciliation (only one job per invoice; row lock).
3. Concurrent contract amendment (only one active version per period).
4. Concurrent invoice payment (only one payment per invoice).
5. Concurrent credit note (cannot exceed invoice total).
6. Concurrent statement generation (per-tenant; per-period; idempotent).

## 9. Reconciliation Test (Acceptance Criterion)

### 9.1 Invoice-GGR Reconciliation
- Generate invoice for period.
- Verify: `rev_share_amount = GGR × rate` (or tiered calc).
- Verify: GGR read model matches Phase 11 ledger.
- `reconciliation_status=matched`.

### 9.2 Mismatch Detection
- Inject GGR mismatch (ledger ≠ read model).
- Invoice reconciliation fails.
- `reconciliation_status=mismatched`.
- Alert + HALT.
- Details recorded.

### 9.3 Statement Reconciliation
- Generate statement for period.
- Verify: statement GGR summary matches invoice GGR.
- Verify: statement reconciles against Phase 11 ledger.
- `reconciliation_status=matched`.

## 10. Performance Targets

- Invoice generation: <5 minutes for 1000 contracts (monthly job).
- Reconciliation job: <30 minutes for 1M ledger entries.
- Statement generation: <30 seconds per contract.
- Fee calculation: <100ms per invoice.
- Audit event write: <50ms p99.

## 11. Open Questions (OQ-COMM-001..006)

| ID | Question | Owner | Due | Status |
|---|---|---|---|---|
| OQ-COMM-001 | Default rev-share rate per product (casino 15%, live_casino 18%) | CFO + Product Owner | Phase 23 Stage A | OPEN |
| OQ-COMM-002 | Tiered fee schedule thresholds (volume-based) | CFO | Phase 23 Stage A | OPEN |
| OQ-COMM-003 | Operator payout mechanism (Phase 12 payment integration) | CFO + Reliability Owner | Phase 23 Stage B | OPEN |
| OQ-COMM-004 | Contract retention period per jurisdiction (7+ years; Q1-blocked) | Legal Counsel | Phase 25 | Q1-BLOCKED |
| OQ-COMM-005 | Statement delivery method (portal vs email vs both) | Product Owner | Phase 23 Stage A | OPEN |
| OQ-COMM-006 | Invoice currency (per-operator vs per-jurisdiction) | CFO | Phase 23 Stage A | OPEN |
