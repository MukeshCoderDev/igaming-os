# Stage 14 Handoff — Phase 15 Entry Criteria

| Field | Value |
|---|---|
| Document | `docs/stage-handoffs/stage-14-handoff.md` |
| Version | 6.5 (Phase 14 — Protection & Jurisdiction) |
| Status | Stage A Design (Stage B merge stop active) |
| Owner | Engineering Lead |

## 1. Phase 14 Stage A deliverables

### 1.1 ADRs (8 PROPOSED — Stage A)
ADR-0084 (Limits), ADR-0085 (Self-Exclusion + SE-survives-erasure),
ADR-0086 (Reality Checks), ADR-0087 (Jurisdiction Engine),
ADR-0088 (Geo Port), ADR-0089 (Kill Switch <200ms SLO),
ADR-0090 (Round-Voiding Port), ADR-0091 (Real-Time Infrastructure).

### 1.2 DECs (9 HUMAN-APPROVED)
DEC-0084..0092 (including DEC-0092 scope deviation for Phase 22 pull-forward).

### 1.3 Code modules
- `src/noventra/modules/protection/` — domain (limits, self_exclusion,
  reality_check, kill_switch, jurisdiction, ports) + adapters (real_adapters
  with RealRGAdapter, RealJurisdictionAdapter, RealRealtimeAdapter,
  StubRoundVoidingAdapter, StubGeoAdapter).
- `src/noventra/modules/realtime/` — structure for Phase 22 pull-forward.

### 1.4 Design doc
`docs/architecture/protection-design.md` — Kill Switch <200ms SLO architecture,
limits model, SE-survives-erasure, reality checks, jurisdiction engine,
real adapters replacing Phase 13 stubs, Phase 22 pull-forward.

### 1.5 Design debt register
`docs/audits/design-debt-register.md` — tracks Stage A phases needing Stage B.

## 2. Contracts Phase 15 must honor

### 2.1 RoundVoidingPort contract
- Phase 15 MUST implement RealRoundVoidingAdapter (actual bet returns via Phase 11 ledger reversal).
- Called by: kill switch trigger, SE activation, reality check failure.

### 2.2 Kill Switch contract
- Phase 15 game platform MUST check kill switch flag on every bet (<1ms Redis check).
- On kill switch trigger: void all in-progress rounds via RoundVoidingPort.

### 2.3 Limits contract
- Phase 15 MUST check wagering limits before accepting bet.
- Phase 15 MUST check session time limits on every API call.

### 2.4 SE contract
- Phase 15 MUST block games for self-excluded players (via RGPort).

## 3. Phase 15 entry criteria
- Phase 11+12+13+14 Stage B all GREEN.
- Linter rules 1-110 green.
- Kill Switch <200ms SLO verified in load test (Stage B).

## 4. Phase 15 scope
- Game platform integration (rounds, bets, outcomes).
- RealRoundVoidingAdapter (replaces stub).
- Game-session WebSocket consumers (builds on Phase 14 real-time infra).
- Bet → ledger posting (Phase 11 continuity).
- Bet → bonus wagering (Phase 13 continuity).
- Bet → limit check (Phase 14 continuity).
