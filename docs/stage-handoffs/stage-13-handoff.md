# Stage 13 Handoff — Phase 14 Entry Criteria

| Field | Value |
|---|---|
| Document | `docs/stage-handoffs/stage-13-handoff.md` |
| Version | 6.4 (Phase 13 — Bonuses & Wagering) |
| Status | Stage A Design (Stage B merge stop active) |
| Owner | Engineering Lead |

## 1. Phase 13 Stage A deliverables

### 1.1 ADRs (6 PROPOSED — Stage A)
ADR-0078 (Bonus Offer FSM), ADR-0079 (Bonus Award + Wagering),
ADR-0080 (Abuse Detection), ADR-0081 (RGPort + JurisdictionPort stubs),
ADR-0082 (RealtimePort stub), ADR-0083 (Bonus→Ledger Contract).

### 1.2 Code modules
`src/noventra/modules/bonuses/` — domain (offer.py with 7-type FSM +
synchronous revocation; award.py with wagering + max bet + bonus-first
consumption + conversion; ports.py with RGPort + JurisdictionPort +
RealtimePort interfaces) + adapters (stubs.py with 3 permissive/log
stub adapters).

### 1.3 Design doc
`docs/architecture/bonuses-design.md`

## 2. Contracts Phase 14 must honor

### 2.1 Port implementation contract
- Phase 14 MUST implement RealRGAdapter (actual RG enforcement).
- Phase 14 MUST implement RealJurisdictionAdapter (actual jurisdiction rules).
- Adapters must satisfy the interfaces defined in `ports.py`.

### 2.2 Bonus contract
- Bonus awards require KYC pass (Phase 10 continuity).
- Bonus→ledger posting is exactly-once (ADR-0083).
- Synchronous revocation: revoked offer unretrievable same transaction.

## 3. Phase 14 entry criteria
- Phase 11+12+13 Stage B all GREEN.
- Linter rules 1-100 green.

## 4. Phase 14 scope
- Real RG enforcement (replaces stub).
- Real jurisdiction rules (replaces stub).
- Player protection features (deposit limits, loss limits, session limits).
- Self-exclusion cooling-off enforcement.
