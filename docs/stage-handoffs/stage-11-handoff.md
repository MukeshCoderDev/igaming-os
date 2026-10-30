# Stage 11 Handoff — Phase 12 Entry Criteria

| Field | Value |
|---|---|
| Document | `docs/stage-handoffs/stage-11-handoff.md` |
| Version | 6.2 (Phase 11 — Ledger & FX) |
| Status | Stage A Design (Stage B merge stop active) |
| Owner | Architecture Lead |

## 1. Phase 11 deliverables (Stage A)

### 1.1 ADRs (7 PROPOSED — Stage A; Stage B requires CFO/Auditor/Treasury signatures)
ADR-0059 (Ledger Architecture), ADR-0060 (Balance Derivation),
ADR-0061 (Overdraft Policy), ADR-0061b (Currency Exponents),
ADR-0062 (Reversals & Restatements), ADR-0062b (FX Rate Snapshots),
ADR-0063 (Financial Audit Chain).

### 1.2 Code modules
- `src/noventra/modules/ledger/` — models (Account, JournalEntry,
  JournalLine, AccountBalance, FinancialAuditEvent, ReconciliationLog),
  services (PostingService, ReversalService, BalanceService).
- `src/noventra/modules/fx/` — models (FxRateSnapshot).

### 1.3 Design doc
`docs/architecture/ledger-design.md` — schema topology, 6 posting
invariants, event taxonomy, 6 concurrency tests, linter rules 71-80,
cross-phase continuity (PII, NFR, threat model, RLS, service identity,
audit chain).

## 2. Contracts Phase 12 must honor

### 2.1 Ledger contract
- Payments MUST post via PostingService (no direct journal_entry inserts).
- Every payment generates a ledger.posted outbox event.
- Payment reversals use ReversalService (terminal, source_ref).

### 2.2 Balance contract
- Authorization reads use BalanceService.get_authoritative_balance()
  (row lock, from journal_line).
- Display reads use BalanceService.get_display_balance() (projection).

### 2.3 FX contract
- Cross-currency payments lock an fx_rate_snapshot at posting time.
- FX snapshots are immutable (insert-only trigger).

### 2.4 Financial audit chain contract
- Every ledger operation generates a financial_audit_event.
- Financial chain verifier runs in CI (rule 79).
- noventra_auditor role has SELECT-only access.

## 3. Phase 12 entry criteria
- Stage B complete: CI green, 9 ratified humans named, CFO/Auditor/Treasury
  named and signed on ADR-0059..0063b.
- Coverage ≥95% on ledger + fx modules.
- Linter rules 1-80 green.
- 6 concurrency tests pass.
- Financial audit chain verifier passes.
- Reconciliation job tested (HALT on mismatch).
