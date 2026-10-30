# Ledger & FX Design Document (Phase 11)

| Field | Value |
|---|---|
| Authority | DEC-0065..0071 | ADR-0059..0063, 0061b, 0062b |
| Status | Stage A Design (Stage B merge stop active) |
| Coverage floor | 95% (per ADR-0027 v2) |
| Owner | Architecture Lead |

## 1. Schema Topology

### 1.1 Tables (with RLS — Phase 5 continuity)

Per ADR-0059 / DEC-0065. All tables tenant-scoped (RLS). All financial
tables insert-only (Phase 7 pattern). Integer minor units only (no floats,
rule 78).

**account** (chart of accounts): id UUID PK, tenant_id, account_class
ENUM (player/house/settlement/fee/fx_gain/fx_loss/suspense/revenue),
currency_code CHAR(3) ISO 4217, status ENUM (active/suspended/closed),
metadata JSONB, created_at, updated_at (only metadata/status mutable;
balance NEVER stored here).

**journal_entry** (parent, append-only): id UUID PK, tenant_id, posted_at,
journal_type ENUM (POSTING/REVERSAL/RESTATEMENT/FX_REVALUATION/SETTLEMENT),
source_ref UUID NULLABLE (FK for reversals), correlation_id, idempotency_key,
fx_pair_id UUID NULLABLE, status ENUM (POSTED/REVERSED), prev_hash, hash,
created_at. UNIQUE(tenant_id, idempotency_key).

**journal_line** (children, append-only): id UUID PK, journal_entry_id FK,
account_id FK, tenant_id (denormalized for RLS), currency_code CHAR(3),
exponent_at_time SMALLINT, debit_minor BIGINT, credit_minor BIGINT.
CHECK (debit_or_credit), CHECK (non_negative).

**account_balance** (cached projection — NOT truth; Law 4): account_id PK,
tenant_id, balance_minor BIGINT, as_of_journal_entry_id FK,
last_reconciled_at, last_reconciled_status.

**fx_rate_snapshot** (immutable, insert-only): id UUID PK, tenant_id
(NULL=global), source ENUM, base_currency, quote_currency, rate_minor
BIGINT, rate_exponent SMALLINT, bid_minor, ask_minor, captured_at, created_at.

**financial_audit_event** (separate WORM chain): same schema as Phase 7
audit_event. Separate chain ID (audit.financial). Separate retention (7y).
Separate access (noventra_auditor role). BEFORE INSERT trigger computes
hash; BEFORE UPDATE/DELETE raises.

**reconciliation_log**: id UUID PK, tenant_id, account_id NULLABLE,
started_at, completed_at, status ENUM (running/matched/mismatched/halted),
mismatched_accounts JSONB, correlation_id.

### 1.2 DB Constraints (defense in depth)

- CHECK (balance_minor >= 0) on account_balance WHERE account_class='player'
- CHECK (SUM(debit-credit)=0) per (journal_entry_id, currency_code) via trigger
- CHECK (base_currency != quote_currency) on fx_rate_snapshot
- RLS on all tables (Phase 5 pattern)
- Insert-only triggers on journal_entry, journal_line, fx_rate_snapshot,
  financial_audit_event (Phase 7 pattern)

## 2. The 6 Posting Invariants

1. **Double-entry balance**: Sum(debit-credit)=0 per (entry, currency). DB trigger.
2. **Atomicity**: All lines commit with parent. Django transaction.atomic().
3. **Immutability**: No UPDATE/DELETE. DB trigger + GRANT INSERT,SELECT only.
4. **Idempotency**: UNIQUE(tenant_id, idempotency_key) + application check.
5. **Tenant Scoping**: RLS on all tables.
6. **Audit Chain**: Hash-chained into financial_audit_event.

## 3. Event Taxonomy Extension (Phase 7 + Phase 8 continuity)

### 3.1 Outbox events (Phase 8)
ledger.posted, ledger.reversed, ledger.restatement_posted, ledger.fx_locked,
ledger.balance_reconciled, ledger.balance_mismatch_halted, ledger.partition_dropped.

### 3.2 Financial audit events (Phase 7 — financial chain)
Every outbox event also generates a financial_audit_event. Separate chain.

### 3.3 Consumer registration
reporting (Phase 17), risk (Phase 18), compliance (Phase 21) — via Phase 8 inbox.

## 4. Concurrency Test Designs (6 tests)

1. Same account concurrent debits — serialized via row lock; no negative balance.
2. Same account concurrent debit+credit — both succeed (commute).
3. Cross-account atomic transfer — both commit or neither.
4. Concurrent reversal of same entry — only one succeeds (idempotency).
5. Concurrent postings same Idempotency-Key — only one succeeds.
6. Balance read during write — REPEATABLE READ; no intermediate state.

## 5. Linter Rules 71-80

71: Double-entry balance trigger. 72: No double-reversal. 73: No
UPDATE/DELETE on financial tables. 74: Cross-currency has fx_pair_id.
75: Every ledger table has RLS. 76: Player account CHECK>=0. 77:
Financial audit has correlation_id. 78: No floats in ledger. 79:
Financial chain verifier in CI. 80: noventra_auditor SELECT-only.

## 6. Cross-Phase Continuity

### 6.1 PII Register Extension
New: account_number, account_balance, transaction_history, fx_rate_exposure.

### 6.2 NFR Allocation Trace
NFR-LDGR-001 (durability) → ACID + WAL + backup.
NFR-LDGR-002 (throughput) → outbox; 500 TPS target.
NFR-LDGR-003 (auth-read latency) → row lock + index; <50ms p99.
NFR-LDGR-004 (reconciliation) → 5-min cadence; HALT on mismatch.
NFR-LDGR-005 (FX immutability) → insert-only + legal hold.

### 6.3 Threat Model Trace
T-TAMPER-LEDGER → WORM hash-chain + insert-only (CRITICAL).
T-INFO-FINANCIAL → RLS + noventra_auditor separation.
T-DOS-LEDGER → row locks + idempotency + DLQ.
T-REPLAY-LEDGER → Idempotency-Key.
T-EOP-LEDGER → RBAC + service identities.

### 6.4 Phase 5 RLS Extension
All Phase 11 tables have RLS. Reconciliation runs as noventra_reconciler
service identity with documented BYPASSRLS for cross-tenant sweeps.

### 6.5 Phase 6 Service Identity Extension
noventra_reconciler + noventra_fx_fetcher service identities (shadow→live
per DEC-0022). Both typ=service JWT (rule 33).

### 6.6 Phase 7 Audit Chain Extension
financial_audit_event reuses Phase 7 hash-chain infra. Separate chain ID:
audit.financial. Separate retention: 7y. Separate access: noventra_auditor.
Financial chain verifier: manage.py verify_financial_audit_chain.

## 7. Coverage Thresholds (per ADR-0027 v2)

| Module | Floor | Branch |
|---|---|---|
| src/noventra/modules/ledger/ | ≥95% | mandatory |
| src/noventra/modules/fx/ | ≥95% | mandatory |
| Diff coverage | ≥80% | mandatory |

CI: `pytest --cov=src/noventra/modules/ledger --cov=src/noventra/modules/fx --cov-fail-under=95 --cov-branch`
