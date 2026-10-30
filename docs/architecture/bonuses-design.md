# Bonuses & Wagering Design Document (Phase 13)

| Field | Value |
|---|---|
| Authority | DEC-0078..0083 | ADR-0078..0083 |
| Status | Stage A Design (Stage B merge stop active — Phase 11+12 GREEN required) |
| Coverage floor | 95% (per ADR-0027 v2) |
| Owner | Product Owner |

## 1. Bonus Offer Model + FSM

Per ADR-0078. 7 offer types (closed catalog): deposit_match, free_spins,
free_bet, cashback, reload, refer_friend, no_deposit.

State FSM: draft→scheduled→published→paused→published→expired/revoked.
Synchronous revocation (Law 10): revoked = unretrievable same transaction.
RealtimePort invalidation on revocation (stub in Phase 13; Phase 22 real).

## 2. Bonus Award + Wagering Requirements

Per ADR-0079. Award FSM: pending→active→wagering_in_progress→
wagering_complete→converted. Or: active→expired/forfeited/cancelled/revoked.

Wagering: multiplier (e.g., 30x), game-class contributions (slots 100%,
table 10%, live 5%), time limit, max bet during wagering (UK GC mandate).
Bonus-first consumption. Conversion: bonus→real via Phase 11 ledger.

## 3. Bonus Abuse Detection

Per ADR-0080. Rule-based (explainable): multi-account (same IP/device),
velocity (too many claims), KYC mismatch (different name/DOB).
Detection flags award for review; freeze prevents conversion.

## 4. Port Interfaces (Forward-Dependency Solution)

Per ADR-0081, ADR-0082. Phase 13 depends on Phase 14 (RG + Jurisdiction)
and Phase 22 (Realtime). Solution: port interfaces + stub adapters.

- RGPort → StubRGAdapter (permissive) → RealRGAdapter (Phase 14)
- JurisdictionPort → StubJurisdictionAdapter (permissive) → RealJurisdictionAdapter (Phase 14)
- RealtimePort → StubRealtimeAdapter (log+no-op) → RealRealtimeAdapter (Phase 22)

## 5. Bonus→Ledger Posting Contract

Per ADR-0083. Same DB transaction as FSM transition:
- Award: credit player-bonus-balance
- Conversion: debit bonus-balance / credit real-balance
- Forfeiture: debit bonus-balance / credit house

## 6. Cross-Phase Continuity

- Phase 4: Error format; structured logging; PII redaction; mypy strict; 95% coverage.
- Phase 5: RLS on bonus_offer, bonus_award, abuse_flag tables.
- Phase 7: Audit events: bonus.offer_published, bonus.award_created, bonus.wagering_progress, bonus.converted, bonus.forfeited, bonus.revoked, bonus.abuse_flagged.
- Phase 8: Outbox events on every FSM transition; state machine base.
- Phase 10: KYC status checked before bonus award (no bonus for unverified players).
- Phase 11: Bonus→ledger posting per ADR-0083; two ledger accounts per player (bonus + real).
