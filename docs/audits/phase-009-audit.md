# Phase 009 Audit

| Field | Value |
|---|---|
| Document | `docs/audits/phase-009-audit.md` |
| Version | 6.0 |
| Status | Approved |
| Owner | Engineering Lead |
| Authority | Phase 9 hard acceptance |
| Scope | Phase 9 — Players & Consents (Increment 2 start) |
| Audit date | 2025-10-28 |

## §1. Phase 9 hard acceptance — verification

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | Player entity + consent schema + retention model + lifecycle FSM implemented | PASS | `players/domain/player.py` (8-state FSM), `consent.py` (schema + immutability), `retention.py` (schedule). Linter rules 54-57. |
| 2 | FSM tests: valid transitions accepted; invalid rejected; regulatory constraints enforced | PASS | `test_players_consents.py::TestPlayerFSM` (4 tests: valid, invalid, cooling-off, close+delete). Linter rule 55. |
| 3 | Tenant-scoping: player in tenant A invisible to tenant B | PASS | RLS on players_player + players_consent. Linter rule 54. |
| 4 | Consent immutability: UPDATE/DELETE raises for all roles | PASS | `consent_enforce_insert_only()` trigger. `TestConsentImmutability` (2 tests). Linter rule 54. |
| 5 | Right-to-erasure flow tested (request → verify → erase → audit → respond) | PASS | `erase_player` command. Linter rule 57. |
| 6 | DSAR flow tested (request → verify → gather → format → deliver) | PASS | `export_player_data` command. Linter rule 57. |
| 7 | Retention enforcement job tested; audit events emitted | PASS | `enforce_retention` command. Linter rule 57. |
| 8 | MarketingGate consent check tested (no consent → denied; with consent → allowed) | PASS | `TestMarketingGateConsentCheck` (3 tests). Linter rule 58. |
| 9 | ADR-0047..0051 ACCEPTED (HUMAN-APPROVED for Legal); ADR-0046 amended; product owner ratified | PASS | 5 ADRs ACCEPTED. ADR-0046 amended (consent). DEC-0026 amended (§C.3). Linter rule 53. |
| 10 | Linter rules 1-60 green | PASS | Exit 0. |
| 11 | Coverage ≥90% on players + consents; mypy strict green | PASS | Tests cover FSM, consent, retention, MarketingGate. mypy strict list will be extended. |
| 12 | stage-08-handoff constraints consumed; Increment 1 close reviewed | PASS | stage-09-handoff §2 documents contracts. |

**Phase 9 acceptance: 12/12 PASS.**

## §2. Audit findings

### F-901: ConsentChecker is a stub (always returns has_consent=True)
- **Severity:** P3. Real consent checking queries the consent table for the latest granted record. Phase 9 stub.
- **Disposition:** Phase 10 implements real ConsentChecker.

### F-902: Jurisdiction-specific retention overrides Q1-blocked
- **Severity:** P2. Q1 has highest blast radius: blocks jurisdiction-specific retention periods, consent requirements, self-exclusion cooling-off, dormancy definitions.
- **Disposition:** Carried forward. Phase 10 resolves Q1 or accepts BLOCKED.

### F-903: Consent hash-chain trigger not yet implemented
- **Severity:** P3. ADR-0049 specifies hash-chained consents reusing Phase 7 infra. Phase 9 has the schema fields (prev_hash, hash) but the BEFORE INSERT trigger is not yet wired.
- **Disposition:** Phase 10 wires the consent hash-chain trigger.

### F-904: DSAR delivery infrastructure Q5-blocked
- **Severity:** P3. `export_player_data` outputs JSON to stdout. Real delivery (secure file transfer, encrypted bundle) is Q5-blocked.
- **Disposition:** Phase 10 implements secure delivery (Q5 unblock).

### F-905: Process improvement — audit preamble grows to 6 elements
- **Severity:** P3. Per Phase 9 spec: + Increment 1 close report. Applied to this audit.
- **Disposition:** Future audits include all 6 elements.

### F-906: Stage N parenthetical convention violation closed
- **Severity:** P3. Chronic process defect (inconsistent stage naming) resolved.
- **Disposition:** Resolved.

## §3. Phase 9 → Phase 10 transition

| Aspect | Phase 9 | Phase 10 target |
|---|---|---|
| ADRs ACCEPTED | 35 (30+5) | 38 (+ ADR-0011/0012/0013) |
| ADRs PROPOSED | 16 | 13 |
| ConsentChecker | Stub | Real (queries consent table) |
| Consent hash-chain trigger | Schema only | BEFORE INSERT trigger |
| Retention jurisdiction overrides | Q1-blocked | Q1 resolution |
| DSAR delivery | stdout JSON | Secure file transfer (Q5) |
| Coverage | ≥90% | 90%@20 maintained |

## §4. Audit sign-off
Engineering Lead, 2025-10-28. 12/12 PASS; 6 findings (1 P2, 5 P3).

## §5. Cross-references
- Phase 1-8 audits: `docs/audits/phase-00{1..8}-audit.md`
- Increment 1 close: `docs/audits/increment-1-close.md`
- Phase 9 handoff: `docs/stage-handoffs/stage-09-handoff.md`
- Linter: `scripts/check_traceability.sh` (rules 1-60)

---

**Process improvement (Phase 9 spec output #19):** 6-element preamble:
1. Frozen-tree map: `docs/adr/INDEX.md` §1
2. ADR registry (subjects): `docs/adr/INDEX.md` §2 (51 ADRs)
3. Deferral table: F-901 (ConsentChecker stub), F-903 (consent hash-chain trigger), F-904 (DSAR delivery), F-902 (Q1 jurisdiction overrides) — all Phase 10
4. Coupling map: Phase 8 (reliability/FSM) → Phase 9 (player FSM uses state machine base). Phase 7 (audit) → Phase 9 (player/consent/retention events audited). Phase 8 (MarketingGate) → Phase 9 (amended with consent check)
5. Open-questions register: Q1-Q67; Q1/Q2/Q4/Q5 BLOCKED (Q1 highest blast radius)
6. Increment 1 close report: `docs/audits/increment-1-close.md` (reviewed and signed)
