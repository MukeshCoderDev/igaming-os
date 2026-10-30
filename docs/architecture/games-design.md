# Game Platform & Realtime Design Document (Phase 15)

| Field | Value |
|---|---|
| Authority | DEC-0093..0095 | ADR-0092..0094 |
| Status | Stage A Design (Stage B merge stop active) |
| Coverage floor | 95% (per ADR-0027 v2) |
| Owner | Product Owner |

## 1. Game Round Model + FSM

Per ADR-0092. Round lifecycle: OPEN → CLOSED → SETTLED (or VOIDED/CANCELLED).
Bets accepted during OPEN; no bets after CLOSED.
Settlement posts to Phase 11 ledger (debit house, credit player for winnings).
Voiding returns bets via RealRoundVoidingAdapter (ADR-0093).

## 2. Bet Model

Per ADR-0092. Bets consume player balance (real or bonus) via Phase 11 ledger.
Bonus bets contribute to wagering requirements (Phase 13).
Game-class contributions: slots 100%, table 10%, live 5%.

## 3. Real RoundVoidingAdapter

Per ADR-0093. Replaces Phase 14 StubRoundVoidingAdapter.
Actual bet returns via Phase 11 ledger reversal.
Called by: kill switch trigger, SE activation, reality check failure.

## 4. Game Session WebSocket Consumer

Per ADR-0094. Builds on Phase 14 real-time infrastructure.
Player session: bet stream, outcome push, disconnect on kill switch.

## 5. Cross-Phase Continuity

- Phase 11: Bet → ledger posting; settlement → ledger; void → reversal.
- Phase 13: Bonus bets → wagering progress; max bet enforcement.
- Phase 14: Kill switch → void all rounds; SE → block games; limits → check before bet.
- Phase 8: Outbox events on every round state change.
- Phase 7: Audit events for every bet, settlement, void.
