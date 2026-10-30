# Stage 15 Handoff — Phase 16 Entry Criteria

| Field | Value |
|---|---|
| Document | `docs/stage-handoffs/stage-15-handoff.md` |
| Version | 6.6 (Phase 15 — Game Platform & Realtime) |
| Status | Stage A Design (Stage B merge stop active) |
| Owner | Engineering Lead |

## 1. Phase 15 Stage A deliverables

### 1.1 DECs (7 HUMAN-APPROVED — backfilled 2026-10-28 per mentor audit)
- DEC-0093 (Game Round + FSM + Bet→Ledger) ↔ ADR-0092
- DEC-0094 (Real RoundVoidingAdapter) ↔ ADR-0093
- DEC-0095 (Game Session WebSocket Consumer) ↔ ADR-0094
- DEC-0096 (Deterministic Sandbox — Same Code Path + Seeded RNG) ↔ ADR-0095
- DEC-0097 (Realtime Seam — Extends Phase 14 Infrastructure) ↔ ADR-0096
- DEC-0098 (Provider Callback Validation — HMAC + Replay + Idempotency) ↔ ADR-0097
- DEC-0099 (RoundVoidingPort Real Adapter + Provider Outage Wallet Protection) ↔ ADR-0098

### 1.2 Code modules
`src/noventra/modules/games/` — domain (round.py with GameRound FSM +
Bet model + RoundState/BetType enums) + adapters (real_voiding.py with
RealRoundVoidingAdapter replacing Phase 14 stub).

### 1.3 Design doc
`docs/architecture/games-design.md`

### 1.4 Linter determinism patch
The flaky `printf | grep` patterns (rules 8, 9, 10) have been replaced
with `grep ... <<<"$var"` here-strings. The multi-printf-on-one-line
bug at linter line 495 has been fixed. Linter is now deterministic
across 20 consecutive runs.

## 2. Contracts Phase 16 must honor

### 2.1 Game round contract
- Bets only accepted during OPEN state.
- Settlement posts to Phase 11 ledger.
- Voiding returns bets via RealRoundVoidingAdapter.

### 2.2 Kill switch contract
- Kill switch trigger → void all OPEN/CLOSED rounds.
- RealRoundVoidingAdapter reverses ledger entries.

## 3. Phase 16 entry criteria
- Phase 11-14 Stage B GREEN.
- Phase 15 Stage B GREEN (concurrency tests, coverage ≥95%).
- Linter rules 1-120 green.

## 4. Phase 16 scope
- Reporting read models (GGR/NGR).
- Reconciliation extension for game rounds.
- Operator dashboard.
