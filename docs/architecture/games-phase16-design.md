# Proprietary Game Framework Design Document (Phase 16)

| Field | Value |
|---|---|
| Authority | DEC-0100..0104 | ADR-0099..0103 |
| Status | Stage A Design (Stage B merge stop active) |
| Coverage floor | 95% (per ADR-0027 v2) |
| Owner | Architecture Lead |
| Law mandate | Law 19 (lab certification of math + RNG + game logic) |

## 1. Math Version Model — Immutability + Hash Verification

Per ADR-0099 / DEC-0100. Game math config is regulator-sensitive. The model enforces:

1. **Immutability after certification.** `MathVersion` is a `@dataclass(frozen=True)`.
   The DB trigger (migration, when DB layer lands) forbids UPDATE/DELETE. Supersession
   is recorded as a new row.

2. **Hash verification at game launch.** Every math version carries `math_config_hash`
   (SHA-256 over canonical JSON of `math_config`). Round initiation recomputes the hash
   and verifies it before accepting any bet. Mismatch → round refuses bet.

The `canonical_json()` function is pinned to `json.dumps(obj, sort_keys=True,
separators=(',', ':'), ensure_ascii=False, allow_nan=False)` for stability across
Python versions.

## 2. RNG Port — Production + Deterministic + Certification Adapters

Per ADR-0100 / DEC-0101. Three adapters share one port interface (`RngPort`):

1. **ProductionRngAdapter** — `secrets.token_hex(32)` for seed generation (CSPRNG).
   Outputs unpredictable; seed logged post-generation for audit.

2. **DeterministicRngAdapter** — caller-provided seed. Same seed → same output
   sequence. Used in sandbox (ADR-0095) and certification evidence generator.

3. **CertificationRngAdapter** — wraps DeterministicRngAdapter with hash-chained
   audit log. Every call records (seed, call_index, output, round_id, method,
   timestamp, prev_hash, entry_hash). The lab can verify no call was inserted or removed.

All three adapters share the same `(seed, call_index) → output` determinism property
via the shared `_derive_bytes()` HMAC-SHA256 counter-mode PRNG core.

Linter rule 124 forbids direct use of `random.Random`, `random.randint`,
`random.random`, `random.choice` in the games module — all RNG must go through `RngPort`.

## 3. Game Round Lifecycle — Math Version Lock + RNG Seed Lock + Round Hash

Per ADR-0101 / DEC-0102. Extends Phase 15 GameRound with three regulator-mandated properties:

1. **Math version locked at round initiation.** `math_version_uuid` and
   `math_config_hash` are set at initiation and immutable thereafter. Linter
   rule 125 forbids mutation after initiation.

2. **RNG seed locked at round initiation.** `rng_seed_hex` is set at initiation
   and immutable. The seed is part of the round hash, so any post-initiation
   change is detected.

3. **Round hash for tamper-evidence.** `round_hash` = SHA-256 over canonical
   JSON of `{math_version_hash, rng_seed, bet_config, outcome}`. Computed at
   settlement (or void with outcome=None). Verified at every downstream read
   (audit, dispute evidence, regulator inquiry).

The `GameRoundPhase16` subclass extends Phase 15's `GameRound` with these fields
and methods: `initiate()`, `freeze_bet_config()`, `settle_with_outcome()`,
`void_with_hash()`, `verify_round_hash()`.

## 4. Certification Evidence + Lab Registry + Auto-Suspend on Expiry

Per ADR-0102 / DEC-0103. Three subsystems:

1. **LabRegistry** — configurable list of approved labs per jurisdiction.
   GLI, BMM, iTechLabs. Q1-blocked for per-jurisdiction config (env-dependent).

2. **CertificationEvidence** — stores lab certification artifacts (RNG cert,
   math cert, RTP verification, game logic cert). Linked to a MathVersion.
   Stored via Phase 10 storage port (immutable, retention 7+ years).
   `evidence_hash` (SHA-256) allows tamper detection.

3. **Auto-suspend on expiry** — daily Celery task `check_cert_expiry`:
   - 30-day pre-expiry alert to Compliance Lead + Product Owner.
   - On expiry: math version REVOKED (synchronous, Law 10), release SUSPENDED
     (ADR-0103), active rounds VOIDED (ADR-0093).

## 5. Release FSM — Evidence-Gated Transitions (No Skipping)

Per ADR-0103 / DEC-0104. 9 states:

```
draft → math_configured → rng_certified → math_certified → lab_tested
    → ready_for_release → published → suspended / revoked
```

Each transition requires specific evidence:
- `draft → math_configured`: `active_math_version_uuid` set
- `math_configured → rng_certified`: `rng_cert_evidence_uuid` set + non-expired
- `rng_certified → math_certified`: `math_cert_evidence_uuid` set + non-expired
- `math_certified → lab_tested`: `lab_test_evidence_uuid` set + non-expired
- `lab_tested → ready_for_release`: all three evidence verified non-expired
- `ready_for_release → published`: operator approval (named human, regulator-mandated)
- `published → suspended`: cert expired, operator action, regulator mandate
- `suspended → published`: re-certification + operator re-approval
- `published/suspended → revoked`: terminal, regulator-mandated

Linter rule 132 forbids skipping states (each `@transition` decorator has exactly
one source state). Linter rule 131 forbids publishing without all evidence verified.
Linter rule 133 requires every `published` release to have a non-expired cert chain.

## 6. Cross-Phase Continuity

- **Phase 7 (Audit):** Every math version create/certify/revoke emits an audit event.
  Every certification evidence attach emits an audit event. Every release transition
  emits an audit event.
- **Phase 8 (Outbox):** Every state change emits an outbox event for downstream consumers.
- **Phase 10 (Storage port):** Certification evidence artifacts stored immutably.
- **Phase 11 (Ledger):** Round settlement posts to ledger (Phase 15 ADR-0092 contract).
- **Phase 14 (Kill switch):** Kill switch trigger voids all OPEN/CLOSED rounds using
  any math version (Phase 15 ADR-0093).
- **Phase 15 (Game rounds):** GameRoundPhase16 extends Phase 15 GameRound; the
  RoundVoidingAdapter is reused for cert-expiry voiding.

## 7. Validation Plan (Stage B)

- Immutability test: UPDATE/DELETE on math_version raises at DB layer.
- Hash verification test: tamper with math_config; recompute; mismatch detected.
- RNG determinism test: same seed + same call_index → identical output across 1000 calls.
- Cross-adapter equivalence: ProductionRngAdapter.next_int(seed=X, call_index=0) ==
  DeterministicRngAdapter.next_int(seed=X, call_index=0).
- Certification audit log: 100-call run; hash chain verifies; tamper breaks chain.
- Round hash test: settle round; recompute hash; assert match. Tamper outcome; assert mismatch.
- Release FSM: full happy-path (draft→published); skip-state refused; expired-evidence refused.
- Auto-suspend: set expires_at to past; run task; assert math version REVOKED, release SUSPENDED,
  active rounds VOIDED.
- Coverage ≥95% on games module.

## 8. Linter rules added (Phase 16)

Rules 121-133 (13 new regulator-mandate rules):
- 121: Phase 16 ADRs 0099-0103 exist
- 122: MathVersion model exists with immutability + hash fields
- 123: RNG port + 3 adapters exist
- 124: No direct use of random.Random in games module
- 125: GameRound Phase 16 extension exists with lock fields
- 126: CertificationEvidence + LabRegistry + auto-suspend
- 127: Release FSM exists with 9 states + evidence-gated transitions
- 128: ADR-0099 documents immutability + hash verification
- 129: ADR-0100 documents 3 adapters + determinism
- 130: ADR-0101 documents math version lock + RNG seed lock + round hash
- 131: ADR-0102 documents lab registry + auto-suspend on expiry
- 132: ADR-0103 documents release FSM + evidence-gated transitions
- 133: Phase 16 design doc + handoff + audit exist
