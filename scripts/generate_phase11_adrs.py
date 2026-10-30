#!/usr/bin/env python3
"""Generate Phase 11 ADR stubs: ADR-0059..0063, 0061b, 0062b (7 ADRs, PROPOSED Stage A).

Per the Phase 11 spec: 5 decisions seeded as DEC-0065..0069 (HUMAN-APPROVED);
ADRs are PROPOSED (Stage A design only; Stage B merge stop active).

Run:  python3 /home/z/my-project/scripts/generate_phase11_adrs.py
"""

from pathlib import Path

OUT_DIR = Path("/home/z/my-project/docs/adr")
LR = "2026-10-28"
CR = "2026-10-28"

ADRS = [
    (59, "DEC-0065", "Ledger Architecture (Journal + Lines, double-entry, append-only)",
     "Architecture Lead", "Phase11",
     "The money layer requires a financial ledger. Law 4 mandates double-entry, append-only, derived balances. The ledger must support: multi-currency postings, reversals, restatements, FX revaluation, and reconciliation. It must be immutable (posted entries never change) and hash-chained for evidentiary integrity.",
     "Adopt a journal-entry + journal-line architecture. journal_entry is the parent (append-only; carries journal_type, correlation_id, idempotency_key, hash chain). journal_line are children (carry account_id, debit_minor, credit_minor, currency_code, exponent_at_time). 6 posting invariants: double-entry balance (sum debit-credit=0 per entry+currency), atomicity (all lines commit with parent), immutability (no UPDATE/DELETE), idempotency (unique key+tenant+type), tenant scoping (RLS), audit chain (hash-chained into financial_audit_event). Integer minor units only (no floats). Per-line exponent_at_time (ISO 4217). Account classes: player, house, settlement, fee, fx_gain, fx_loss, suspense, revenue.",
     "Alternatives: (a) single-table ledger — no double-entry structure; (b) mutable ledger with audit trail — tamper risk; (c) event-sourced ledger (no projection) — slow balance reads; (d) float amounts — rounding errors. All rejected.",
     "Journal + lines is more complex than single-table. Balance derivation requires projection (account_balance). Reconciliation must verify projection vs. journal truth. Hash chain adds insert overhead. Per-line exponent captures currency precision at posting time (immutable).",
     "Phase 11: schema + migrations + RLS + triggers. Phase 11: 6 concurrency tests. Phase 11: double-entry balance trigger. Phase 12: payment integration.",
     "PROPOSED", "CFO + Architecture Lead + External Auditor"),

    (60, "DEC-0066", "Balance Derivation & Authorization-Read Rule",
     "Architecture Lead", "Phase11",
     "Balances must be derived from journal_line (the truth), not stored as mutable state. But reading all journal_lines for every authorization is too slow. The authorization-read rule: display reads from a cached projection (account_balance); authorization (e.g., 'can this player afford this bet?') reads from journal_line under a row lock to guarantee correctness.",
     "Adopt a two-tier balance model: (1) account_balance is a cached projection (NOT truth; Law 4) — updated by a trigger or service after each posting; (2) authorization reads use SELECT ... FOR UPDATE on the account_balance row (or a direct SUM from journal_line) to get an authoritative balance under lock. Display reads use the projection (fast, eventually consistent). Reconciliation verifies projection vs. journal truth every 5 minutes; HALT on mismatch.",
     "Alternatives: (a) always read from journal_line — too slow for authorization; (b) always read from projection — not authoritative; (c) stored procedure for balance — complex. All rejected.",
     "Projection can lag (eventually consistent). Reconciliation catches mismatches. Authorization reads under row lock serialize on the account (bottleneck for hot accounts). REPEATABLE READ for balance reads during writes.",
     "Phase 11: account_balance projection + reconciliation job. Phase 11: auth-read <50ms p99 load test. Phase 11: reconciliation HALT test.",
     "PROPOSED", "CFO + Architecture Lead + External Auditor"),

    (61, "DEC-0067", "Overdraft Policy per Account Class",
     "Compliance Lead", "Phase11",
     "Different account classes have different overdraft policies. Player accounts must never go negative (regulatory requirement: player funds are protected). House/settlement/suspense accounts may go negative (they're internal operational accounts). The overdraft policy must be enforced at the DB level (CHECK constraint) and at the application level.",
     "Adopt per-account-class overdraft policy: player accounts enforce CHECK (balance_minor >= 0) at the DB level; house, settlement, fee, fx_gain, fx_loss, suspense, revenue accounts allow negative balances (no CHECK constraint). The posting service checks overdraft before posting for player accounts. The DB CHECK is defense-in-depth (catches application bugs). HUMAN-APPROVED per linter rule 5 (Compliance/Legal category).",
     "Alternatives: (a) no overdraft check — regulatory violation; (b) application-only check — bypassable via direct DB; (c) all accounts non-negative — blocks internal operations. All rejected.",
     "Player account CHECK constraint means reversals that would make a player account negative are rejected (must use restatement instead). House accounts going negative is normal (they absorb losses).",
     "Phase 11: CHECK constraint on account_balance WHERE account_class='player'. Phase 11: overdraft rejection test. Phase 12: payment integration uses overdraft check.",
     "PROPOSED", "Compliance Lead + CFO + Legal Lead"),

    ("0061b", "DEC-0068", "Currency Exponents & Migration Strategy",
     "Treasury Lead", "Phase11",
     "Different currencies have different decimal exponents (e.g., USD=2, JPY=0, BHD=3). The ledger must store amounts in integer minor units with the exponent recorded per-line (exponent_at_time) to handle currency redenominations and precision changes. The migration strategy must handle adding new currencies and changing exponents.",
     "Adopt per-line exponent_at_time (SMALLINT) on journal_line, recording the ISO 4217 exponent at posting time. Amounts stored as BIGINT minor units (debit_minor, credit_minor). account_balance stores balance_minor (BIGINT) + the account's currency exponent (from account.currency_code → ISO 4217 lookup). Migration: new currencies added via seed data; exponent changes (rare; redenomination) require a new currency code (e.g., old_GHF → new_GHS) rather than mutating existing lines. HUMAN-APPROVED per linter rule 5 (Treasury/Financial category).",
     "Alternatives: (a) fixed exponent (2 for all) — wrong for JPY/BHD; (b) DecimalField — float risk; (c) per-account exponent (not per-line) — breaks on redenomination. All rejected.",
     "Per-line exponent adds storage (SMALLINT per line). Redenomination is rare but must be handled (new currency code, not mutation). Currency code lookup must be fast (cached ISO 4217 table).",
     "Phase 11: exponent_at_time on journal_line. Phase 11: currency-mismatch tests (wrong exponent rejected). Phase 12: multi-currency payment tests.",
     "PROPOSED", "Treasury Lead + CFO + Architecture Lead"),

    (62, "DEC-0069", "Reversals & Restatements",
     "Architecture Lead", "Phase11",
     "Posted entries are immutable. Errors must be corrected via reversals (new entries that negate the original) or restatements (new entries that supersede the original). Reversals are terminal (cannot be reversed themselves). Double-reversal must be prevented. Restatements are for regulatory corrections (e.g., misclassified revenue).",
     "Adopt: (1) Reversals: new journal_entry with journal_type=REVERSAL, source_ref=original_entry_id, lines that negate the original. UNIQUE constraint on (source_ref, journal_type) where journal_type=REVERSAL prevents double-reversal. Reversals are terminal (cannot be reversed themselves — no source_ref pointing to a REVERSAL). (2) Restatements: new journal_entry with journal_type=RESTATEMENT, source_ref=original_entry_id. The original entry's status changes to REVERSED (but the entry itself is not mutated — the status change is via a new financial_audit_event, not an UPDATE). HUMAN-APPROVED per linter rule 5.",
     "Alternatives: (a) mutate the original entry — violates immutability; (b) delete + repost — loses audit trail; (c) reversible reversals — infinite loop risk. All rejected.",
     "Reversals are terminal — if a reversal is itself wrong, a new restatement is needed (not a reversal-of-reversal). The status field on journal_entry (POSTED, REVERSED) appears to be mutable, but it's actually managed via a separate status tracking mechanism (trigger-based view) to preserve immutability.",
     "Phase 11: ReversalService + restatement support. Phase 11: double-reversal prevention test. Phase 11: terminal reversal test. Phase 12: payment reversal flow.",
     "PROPOSED", "CFO + Architecture Lead + External Auditor"),

    ("0062b", "DEC-0069", "FX Rate Snapshots (immutable, locked at posting time)",
     "Treasury Lead", "Phase11",
     "Cross-currency postings require an FX rate. The rate must be captured at posting time (immutable snapshot) to ensure the ledger is deterministic. The snapshot is separate from live rates (which fluctuate). Volatility monitoring alerts if the locked rate diverges from current market rate beyond a threshold.",
     "Adopt fx_rate_snapshot table (insert-only): id, tenant_id (NULL=global), source (ECB/REFINITIV/INTERNAL_TREASURY/STUB), base_currency, quote_currency, rate_minor (BIGINT), rate_exponent (SMALLINT), bid_minor, ask_minor, captured_at, created_at. Cross-currency journal_entries reference fx_pair_id (FK to fx_rate_snapshot). The rate is locked at posting time — the snapshot is immutable. Volatility monitoring: if |locked_rate - current_rate| > threshold, alert (but do NOT change the locked rate).",
     "Alternatives: (a) live rate at read time — non-deterministic; (b) mutable rate snapshot — tamper risk; (c) no FX support — blocks multi-currency. All rejected.",
     "FX rate source is Q5-blocked (stub for dev). Volatility threshold is configurable. Bid/ask spread is captured but optional (NULL for mid-rate sources). Rate_minor uses integer representation (e.g., 110000 = 1.10000 USD per EUR at exponent 5).",
     "Phase 11: fx_rate_snapshot table + insert-only trigger. Phase 11: cross-currency posting with fx_pair_id. Phase 11: FX immutability test. Phase 12: real FX vendor (Q5).",
     "PROPOSED", "Treasury Lead + CFO + Architecture Lead"),

    (63, "DEC-0065", "Financial Audit Chain (Separate WORM)",
     "Architecture Lead", "Phase11",
     "The operational audit chain (Phase 7) is for operational events. Financial events (ledger postings, reversals, FX locks) need a separate WORM (Write-Once-Read-Many) chain with: separate retention (7 years financial), separate access (noventra_auditor role), separate verifier. The financial chain reuses Phase 7's hash-chain infrastructure (SHA-256, Merkle-style, pgbouncer-compatible).",
     "Adopt financial_audit_event table (separate from Phase 7 audit_event). Same schema (UUID PK, tenant_id, actor_id, actor_type, event_type, target_type, target_id, payload, prev_hash, hash, correlation_id, created_at). Separate chain ID: audit.financial. Separate retention: 7 years. Separate access: noventra_auditor role (new — amend DEC-0026 v7). BEFORE INSERT trigger computes hash; BEFORE UPDATE/DELETE raises. Financial chain verifier: manage.py verify_financial_audit_chain (extends Phase 7 verify_audit_chain). Insert-only enforcement per Phase 7 pattern.",
     "Alternatives: (a) use Phase 7 audit_event — conflates operational and financial; (b) no financial chain — no evidentiary integrity for money; (c) external chain (blockchain) — over-engineered. All rejected.",
     "Separate chain adds a table + trigger + verifier. noventra_auditor role needs governance (DEC-0026 v7 amendment). Financial chain retention aligns with Phase 9 retention schedule. Partitioning by month (same as Phase 7).",
     "Phase 11: financial_audit_event + trigger + verifier. Phase 11: noventra_auditor role ratified. Phase 11: financial chain tamper test. Phase 12: payment events in financial chain.",
     "PROPOSED", "CFO + External Auditor + Architecture Lead + Security Lead"),
]


def render(n, d, t, o, s, c, dec, a, cons, v, st, ap):
    aid = f"ADR-{n:04d}" if isinstance(n, int) else f"ADR-{n}"
    return f"""---
ADR: {aid}
Title: {t}
Status: {st}
DEC: {d}
Owner: {o}
Scope: {s}
Created: {CR}
Last-Reviewed: {LR}
Supersedes: ""
Superseded-By: ""
Approver: {ap}
---

# {aid} — {t}

## Context

{c}

## Decision

{dec}

## Alternatives

{a}

## Consequences

{cons}

## Validation Plan

{v}

## Decision statement (one line)

{d} → {t}. Owner: {o}. Status: {st}.
Stage A design only — Stage B merge stop active.
Approver: {ap}.

## DEC link

This ADR cites {d} per the ADR-DEC mapping law (DEC-0023, errata E7).
1:1: {d} ↔ {aid}.
"""


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for (n, d, t, o, s, c, dec, a, cons, v, st, ap) in ADRS:
        p = OUT_DIR / f"ADR-{n:04d}.md" if isinstance(n, int) else OUT_DIR / f"ADR-{n}.md"
        p.write_text(render(n, d, t, o, s, c, dec, a, cons, v, st, ap))
        print(f"wrote {p} (status={st})")
    print(f"\n{len(ADRS)} new ADRs.")


if __name__ == "__main__":
    main()
