#!/usr/bin/env python3
"""Generate Phase 14 ADR stubs: ADR-0084..0091 (8 ADRs, PROPOSED Stage A).

Phase 14 — Protection & Jurisdiction. Most safety-critical phase.
Implements real RGPort + JurisdictionPort (replacing Phase 13 stubs).
Pulls Phase 22 real-time infrastructure forward for Kill Switch <200ms SLO.
"""

from pathlib import Path

OUT_DIR = Path("/home/z/my-project/docs/adr")
LR = "2026-10-28"
CR = "2026-10-28"

ADRS = [
    (84, "DEC-0084", "Player Protection Limits Model (Deposit, Loss, Wagering, Session)",
     "Product Owner", "Phase12+",
     "UK GC mandates player-configurable limits (deposit, loss, wagering, session). Limits must be enforced in real-time at every bet/deposit.",
     "PlayerLimit model: limit_type (deposit/loss/wagering/session_time), period (daily/weekly/monthly), amount_minor (or minutes), current_cumulative. Tightening = instant; loosening = cooling-off 24h-7d. Enforcement: deposit checked by Phase 12 payment service; wagering checked by Phase 15 game platform; loss calculated from Phase 11 ledger; session enforced client+server. Jurisdiction mandates via JurisdictionPort.",
     "Alternatives: no limits (rejected — UK GC mandate); server-only (rejected — UX poor).",
     "Every payment + bet checks limits. Cumulative tracking. Limit change cooling-off.",
     "Phase 14: limit enforcement tests; cooling-off test; jurisdiction minimum test.",
     "PROPOSED", "Product Owner + Compliance Lead + Legal Counsel"),

    (85, "DEC-0085", "Self-Exclusion, Cooling-off & SE-survives-erasure",
     "Compliance Lead", "Phase12+",
     "UK GC mandates self-exclusion (6m to lifetime). SE must survive erasure (Phase 9 — excluded player cannot DSAR-erase and re-register). Cross-module enforcement (Law 18).",
     "SelfExclusion model: period (6m/1y/2y/5y/lifetime), pseudonymized_identity (HMAC — survives erasure). SE registry persists across erasure. On new registration: check pseudonymized_identity; reject if active SE. Cross-module enforcement via RGPort: games/bonuses/payments/marketing all blocked. Reactivation: only after ends_at; 24h cooling-off; audit-logged.",
     "Alternatives: plaintext player ID (rejected — DSAR bypass); no reactivation cooling-off (rejected — impulsive risk).",
     "HMAC pseudonymization required. SE registry is regulator-auditable. Cross-module enforcement via RGPort.",
     "Phase 14: SE enforcement test (cross-module); SE-survives-erasure test; reactivation cooling-off test.",
     "PROPOSED", "Compliance Lead + Legal Counsel + Privacy Owner"),

    (86, "DEC-0086", "Reality Checks Model + Enforcement",
     "Product Owner", "Phase12+",
     "UK GC mandates reality checks — periodic reminders of time spent and money lost/gained. Must be displayed to player; player must acknowledge before continuing.",
     "RealityCheck model: interval_minutes (configurable; default 30), last_shown_at, acknowledged_at. Client-side timer triggers display; server enforces on every API call (if overdue, block until acknowledged). Display: session duration, net gain/loss, option to continue or exit.",
     "Alternatives: no reality checks (rejected — UK GC mandate); server-only timer (rejected — UX poor).",
     "Every API call checks reality check status. Client timer required (Phase 15 integration).",
     "Phase 14: reality check display test; enforcement test (block until acknowledged).",
     "PROPOSED", "Product Owner + Compliance Lead + CTO"),

    (87, "DEC-0087", "Jurisdiction Policy Engine",
     "Compliance Lead", "Phase12+",
     "Different jurisdictions have different rules (bonus types, limit mandates, SE cooling-off, age verification). The jurisdiction policy engine centralizes these rules.",
     "JurisdictionPolicy model: jurisdiction_code, rule_name, rule_value, effective_from, effective_until. Rules: bonus_type_allowed (per type), min_deposit_limit, min_loss_limit, se_cooling_off_hours, age_verification_required, reality_check_interval_minutes. JurisdictionPort.check_jurisdiction_rule queries this table. Phase 13 stub replaced with real adapter.",
     "Alternatives: hardcoded rules (rejected — not configurable); per-module rules (rejected — scattered).",
     "Rule changes require compliance approval. Jurisdiction list is Q1-blocked (rules seeded with defaults).",
     "Phase 14: jurisdiction rule test; bonus eligibility test per jurisdiction.",
     "PROPOSED", "Compliance Lead + Legal Counsel + Architecture Lead"),

    (88, "DEC-0088", "Geo Port + VPN/Proxy Detection (Q5-blocked stub)",
     "Security Lead", "Phase12+",
     "Geo-fencing: restrict access by player's geographic location. VPN/proxy detection: block anonymized connections. Vendor (MaxMind/IPQualityScore) is Q5-blocked.",
     "GeoPort interface: get_geo(ip_address) → GeoResult (country_code, is_vpn, is_proxy, is_datacenter). StubGeoAdapter returns permissive (country=unknown, no VPN flag). Real adapter (Q5-blocked) uses MaxMind GeoIP2 + IPQualityScore. Enforcement: JurisdictionPort checks geo before allowing play.",
     "Alternatives: no geo detection (rejected — jurisdiction compliance); IP-only (rejected — VPN bypass).",
     "Vendor Q5-blocked. Stub is permissive (no actual geo enforcement in Phase 14 dev). Real adapter before production.",
     "Phase 14: stub returns permissive. Phase 22: real vendor (Q5).",
     "PROPOSED", "Security Lead + Compliance Lead + CTO"),

    (89, "DEC-0089", "Kill-Switch Architecture + <200ms SLO + Fan-out",
     "Infrastructure Lead", "Phase12+",
     "The Kill Switch is the most safety-critical feature in the platform. Regulator-mandated <200ms SLO (commit → WebSocket disconnect). Must HALT all play across all tenants instantly.",
     "KillSwitch architecture: (1) Admin triggers kill switch (DB flag + outbox event); (2) ASGI WebSocket consumer (Phase 22 pulled forward) receives event via Redis pub/sub; (3) Consumer disconnects all WebSocket connections (<200ms from commit to disconnect); (4) All API endpoints check kill switch flag (cached in Redis; <1ms check); (5) Phase 15 game platform voids all in-progress rounds via RoundVoidingPort. Fan-out: per-tenant kill switch (one tenant) or global (all tenants). Audit: every kill switch trigger + lift is audited per Phase 7.",
     "Alternatives: polling-based (rejected — >200ms latency); per-service kill switch (rejected — not atomic).",
     "Requires ASGI + Redis pub/sub + WebSocket infrastructure (Phase 22 pulled forward). <200ms SLO is regulator-mandated — failure is regulator-reportable.",
     "Phase 14: kill switch latency test (<200ms commit→disconnect); fan-out test; lift test; audit test.",
     "PROPOSED", "Infrastructure Lead + Compliance Lead + Reliability Lead + CTO"),

    (90, "DEC-0090", "Round-Voiding Hooks Port Interface (Phase 15 implements)",
     "Architecture Lead", "Phase12+",
     "When a kill switch triggers or self-exclusion activates mid-round, the in-progress game round must be voided (bets returned). Phase 15 (Game Platform) implements the actual voiding.",
     "RoundVoidingPort interface: void_round(tenant_id, round_id, reason) → VoidResult. StubRoundVoidingAdapter logs the void request (Phase 14). Phase 15 implements RealRoundVoidingAdapter (actual bet returns via Phase 11 ledger reversal). Called by: kill switch trigger, SE activation, reality check failure.",
     "Alternatives: no voiding (rejected — players lose money unfairly); synchronous void (rejected — blocks kill switch <200ms SLO).",
     "Voiding is async (via outbox). Stub in Phase 14; Phase 15 implements real voiding.",
     "Phase 14: stub logs void request. Phase 15: real voiding + ledger reversal test.",
     "PROPOSED", "Architecture Lead + Reliability Lead + CTO"),

    (91, "DEC-0091", "Real-Time Infrastructure (Phase 22 pulled forward)",
     "Infrastructure Lead", "Phase12+",
     "The Kill Switch <200ms SLO requires real-time infrastructure (ASGI WebSocket server). Phase 22 (Realtime) is pulled forward to Phase 14 to meet this SLO. Documented deviation per DEC-0092.",
     "Minimal real-time infrastructure: (1) Django ASGI + channels (WebSocket support); (2) Redis pub/sub for event fan-out; (3) KillSwitchConsumer (WebSocket consumer that listens for kill switch events and disconnects clients); (4) RealtimePort real adapter (replaces Phase 13 stub — sends events via Redis pub/sub to connected consumers). Phase 22 extends this for general real-time features (game state, chat, notifications).",
     "Alternatives: polling (rejected — >200ms); external real-time service (rejected — operational overhead).",
     "ASGI + channels + Redis required. Phase 22 scope reduced (core already built in Phase 14).",
     "Phase 14: ASGI setup + KillSwitchConsumer + RealtimePort real adapter + <200ms latency test.",
     "PROPOSED", "Infrastructure Lead + Architecture Lead + Reliability Lead + CTO"),
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
Stage A design only — Stage B merge stop active (Phase 11+12+13 GREEN required).
**Most safety-critical phase in the plan. Kill Switch <200ms SLO is regulator-mandated.**
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
