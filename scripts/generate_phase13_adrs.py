#!/usr/bin/env python3
"""Generate Phase 13 ADR stubs: ADR-0078..0083 (6 ADRs, PROPOSED Stage A)."""

from pathlib import Path

OUT_DIR = Path("/home/z/my-project/docs/adr")
LR = "2026-10-28"
CR = "2026-10-28"

ADRS = [
    (78, "DEC-0078", "Bonus Offer Model, FSM & Synchronous Revocation",
     "Product Owner", "Phase12+",
     "Bonus offers require explicit FSM, regulatory constraints (per-jurisdiction), and synchronous revocation (Law 10).",
     "BonusOffer model with 7 offer types (deposit_match, free_spins, free_bet, cashback, reload, refer_friend, no_deposit). State FSM: draft→scheduled→published→paused→published→expired/revoked. Synchronous revocation (Law 10): revoked offer unretrievable same transaction. RealtimePort invalidation on revocation (stub in Phase 13). JurisdictionPort.check_bonus_eligibility (stub permissive).",
     "Alternatives: open offer type catalog (rejected — closed enumeration is regulator-friendly).",
     "7 offer types. Adding new types requires ADR amendment. Synchronous revocation + realtime invalidation require DB triggers + RealtimePort.",
     "Phase 13: FSM transition tests; synchronous revocation atomicity test; RealtimePort stub emits event.",
     "PROPOSED", "Product Owner + Compliance Lead + Legal Counsel"),

    (79, "DEC-0079", "Bonus Award Model, Wagering Requirements & Max Bet Enforcement",
     "Product Owner", "Phase12+",
     "UK GC mandates clear display of wagering requirements and max bet during wagering. Bonus awards must track wagering progress and convert to real money on completion.",
     "BonusAward model with FSM: pending→active→wagering_in_progress→wagering_complete→converted. Wagering requirements: multiplier (e.g., 30x), game-class contributions (slots 100%, table 10%, live 5%), time limit, max bet during wagering. Bonus-first consumption order. Conversion: bonus_balance→real_balance via Phase 11 ledger entry.",
     "Alternatives: real-first consumption (rejected — bonus-first is industry standard); hidden wagering (rejected — UK GC mandate).",
     "Two ledger accounts per player: player-bonus-balance + player-real-balance. Max bet enforcement on every bet (Phase 15 integration).",
     "Phase 13: wagering progress tests; max bet tests; conversion test; expiry forfeiture test; consumption order tests.",
     "PROPOSED", "Product Owner + Compliance Lead + CFO"),

    (80, "DEC-0080", "Bonus Abuse Detection (Multi-account, Velocity, KYC Mismatch)",
     "Security Lead", "Phase12+",
     "Bonus abuse (multi-accounting, velocity attacks, KYC mismatches) is a top fraud vector in iGaming. Detection must be rule-based (explainable) with flag + freeze capability.",
     "Rule-based abuse detection: (1) multi-account (same IP/device/fingerprint across accounts claiming same offer); (2) velocity (too many claims in time window); (3) KYC mismatch (different name/DOB across accounts). Detection flags award for review; freeze prevents conversion until reviewed. Every flag audited per Phase 7.",
     "Alternatives: ML-based detection (rejected — explainability gap for regulators).",
     "Rule tuning required. False positives impact player experience. Freeze requires manual review (ops overhead).",
     "Phase 13: multi-account detection test; velocity test; KYC mismatch test; flag+freeze test.",
     "PROPOSED", "Security Lead + Compliance Lead + CTO"),

    (81, "DEC-0081", "RGPort + JurisdictionPort Stub Interfaces (Phase 14 implements)",
     "Compliance Lead", "Phase12+",
     "Phase 13 depends on Phase 14 (Protection & Jurisdiction) for RG gates and jurisdiction restrictions. Forward-dependency via port stubs (hexagonal pattern from Phase 8/12).",
     "RGPort interface: check_self_exclusion(player_id) → bool; check_deposit_limit(player_id, amount) → bool; check_loss_limit(player_id) → bool. JurisdictionPort interface: check_bonus_eligibility(player, offer) → bool; check_jurisdiction_rule(jurisdiction, rule_name) → bool. StubRGAdapter + StubJurisdictionAdapter return permissive (true) in Phase 13. Phase 14 implements real adapters with actual RG + jurisdiction rules.",
     "Alternatives: wait for Phase 14 (rejected — blocks Phase 13); inline checks (rejected — couples phases).",
     "Stubs are permissive (no actual RG/jurisdiction enforcement in Phase 13). Phase 14 must implement real adapters before production.",
     "Phase 13: port interface tests (stub returns permissive). Phase 14: real adapter tests (actual restrictions).",
     "PROPOSED", "Compliance Lead + Legal Counsel + Architecture Lead"),

    (82, "DEC-0082", "RealtimePort Stub Interface (Phase 22 implements)",
     "Infrastructure Lead", "Phase12+",
     "Law 22 (Law of the Edge) requires realtime invalidation (e.g., revoked bonus offer immediately unavailable to connected clients). Phase 22 implements the actual WebSocket fan-out. Phase 13 uses a stub.",
     "RealtimePort interface: invalidate(tenant_id, channel, event_type, payload) → void. StubRealtimeAdapter logs the event + no-ops (Phase 13). Phase 22 implements RealRealtimeAdapter with WebSocket fan-out to connected clients.",
     "Alternatives: no realtime (rejected — Law 22 mandate); polling (rejected — latency).",
     "Stub means revoked offers are not immediately unavailable to connected clients in Phase 13 (they'll see it on next API call). Phase 22 closes this gap.",
     "Phase 13: stub emits log on invalidate(). Phase 22: real WebSocket fan-out test.",
     "PROPOSED", "Infrastructure Lead + Architecture Lead + CTO"),

    (83, "DEC-0083", "Bonus→Ledger Posting Contract",
     "CFO", "Phase12+",
     "Bonus awards, conversions, and forfeitures must post to Phase 11 ledger exactly once. Same DB transaction as the FSM transition.",
     "Posting triggers (same DB transaction as FSM transition): Award=credit player-bonus-balance; Conversion=debit bonus-balance/credit real-balance; Forfeiture=debit bonus-balance/credit house. Idempotency via Phase 8 pattern. Reconciliation extends Phase 11 pattern.",
     "Alternatives: async posting (rejected — financial integrity requires synchronous).",
     "Bonus service must use transaction.atomic() spanning FSM + ledger posting. Two ledger accounts per player (bonus + real).",
     "Phase 13: award posting test; conversion posting test; forfeiture posting test; exactly-once test.",
     "PROPOSED", "CFO + External Auditor + Architecture Lead"),
]


def render(n, d, t, o, s, c, dec, a, cons, v, st, ap):
    aid = f"ADR-{n:04d}"
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
Stage A design only — Stage B merge stop active (Phase 11+12 GREEN required).
Approver: {ap}.

## DEC link

This ADR cites {d} per the ADR-DEC mapping law (DEC-0023, errata E7).
1:1: {d} ↔ {aid}.
"""


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for (n, d, t, o, s, c, dec, a, cons, v, st, ap) in ADRS:
        p = OUT_DIR / f"ADR-{n:04d}.md"
        p.write_text(render(n, d, t, o, s, c, dec, a, cons, v, st, ap))
        print(f"wrote {p} (status={st})")
    print(f"\n{len(ADRS)} new ADRs.")


if __name__ == "__main__":
    main()
