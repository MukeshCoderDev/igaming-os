# Stage 16 Handoff — Phase 17 Entry Criteria

| Field | Value |
|---|---|
| Document | `docs/stage-handoffs/stage-16-handoff.md` |
| Version | 6.7 (Phase 16 — Proprietary Game Framework) |
| Status | Stage A Design (Stage B merge stop active) |
| Owner | Engineering Lead |

## 1. Phase 16 Stage A deliverables

### 1.1 DECs (5 HUMAN-APPROVED)
- DEC-0100 (Math Version Model — Immutability + Hash Verification) ↔ ADR-0099
- DEC-0101 (RNG Port + 3 Adapters) ↔ ADR-0100
- DEC-0102 (Game Round Lifecycle — Math Version Lock + RNG Seed Lock + Round Hash) ↔ ADR-0101
- DEC-0103 (Certification Evidence + Lab Registry + Auto-Suspend on Expiry) ↔ ADR-0102
- DEC-0104 (Release FSM with Evidence-Gated Transitions) ↔ ADR-0103

### 1.2 Code modules
`src/noventra/modules/games/domain/`:
- `math_version.py` — MathVersion frozen dataclass + MathVersionStatus enum + canonical_json + compute_math_config_hash
- `rng_port.py` — RngPort interface + ProductionRngAdapter (CSPRNG) + DeterministicRngAdapter (seeded) + CertificationRngAdapter (audit log)
- `round_phase16.py` — GameRoundPhase16 (extends Phase 15 GameRound) with math version lock + RNG seed lock + round hash
- `certification.py` — LabRegistry + CertificationEvidence + EvidenceType + CertExpiryService + AutoSuspendResult + check_cert_expiry_task
- `release.py` — GameRelease FSM with 9 states + 8 evidence-gated transition methods

### 1.3 Design doc
`docs/architecture/games-phase16-design.md`

### 1.4 Linter rules added
Rules 121-133 (13 new regulator-mandate rules). Total linter rule count: 133.

### 1.5 Pre-Phase 16 patches applied
Per mentor audit (2026-10-28), four patches were applied before Phase 16 work began:
1. **Phase 15 underdelivery** — created 4 missing ADRs (0095-0098) + 4 missing DECs (0096-0099).
2. **Phase 15 audit honesty** — corrected "7/7 PASS" claim (was 3/7; now 7/7 after patch).
3. **Phase 12 test suite expansion** — added `tests/test_payments_extended.py` with 26 tests (12 passing in sandbox + 14 DB-pending for CI).
4. **Linter rule 10 flakiness** — root-caused to SIGPIPE+pipefail interaction in `printf | grep` patterns. Fixed by replacing with `grep ... <<<"$var"` here-strings. Verified deterministic across 20 consecutive runs. Also fixed the multi-printf-on-one-line bug at linter line 495.

## 2. Contracts Phase 17 must honor

### 2.1 Math version contract
- Math versions are immutable (frozen dataclass + DB trigger).
- Math config hash is verified at every round initiation.
- Supersession creates a NEW row; old row is `superseded`, never mutated.

### 2.2 RNG contract
- All RNG in games module goes through `RngPort` (linter rule 124).
- Production uses `ProductionRngAdapter` (CSPRNG).
- Sandbox uses `DeterministicRngAdapter` (seeded).
- Certification uses `CertificationRngAdapter` (audit log).
- Same `(seed, call_index)` → same output, regardless of adapter.

### 2.3 Round hash contract
- Round hash = SHA-256(canonical_json({math_version_hash, rng_seed, bet_config, outcome})).
- Hash computed at settlement (or void with outcome=None).
- Hash verified at every downstream read (audit, dispute, regulator inquiry).

### 2.4 Release FSM contract
- No state skipping (linter rule 132).
- Each transition requires specific evidence (linter rule 131).
- Published releases must have non-expired cert chain (linter rule 133).

### 2.5 Auto-suspend contract
- Daily Celery task `check_cert_expiry`.
- 30-day pre-expiry alert.
- On expiry: math version REVOKED, release SUSPENDED, active rounds VOIDED.

## 3. Phase 17 entry criteria
- Phase 11-15 Stage B GREEN.
- Phase 16 Stage B GREEN (concurrency tests, coverage ≥95%).
- Linter rules 1-133 green.
- ADR-0099..0103 ACCEPTED with named human approvers (CTO, Compliance Officer,
  External Auditor, Security Owner, Reliability Owner, Legal Counsel, Product Owner).

## 4. Phase 17 scope (preview)
- Reporting read models (GGR/NGR).
- Reconciliation extension for game rounds.
- Operator dashboard.
- Game launch API (ties together math version + release FSM + round initiation).
