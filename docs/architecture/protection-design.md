# Protection & Jurisdiction Design Document (Phase 14)

| Field | Value |
|---|---|
| Authority | DEC-0084..0092 | ADR-0084..0091 |
| Status | Stage A Design (Stage B merge stop active) |
| Coverage floor | 95% (per ADR-0027 v2) |
| Owner | Architecture Lead |
| **Critical** | **Most safety-critical phase. Kill Switch <200ms SLO is regulator-mandated.** |

## 1. Scope Deviation (DEC-0092)

Phase 22 (Realtime) is pulled forward to Phase 14 to meet the Kill Switch
<200ms SLO. This is a documented deviation from the blueprint Stage 15.
Minimal real-time infrastructure: ASGI + channels + Redis pub/sub +
KillSwitchConsumer (WebSocket consumer). Phase 22 extends this for general
real-time features.

## 2. Player Protection Limits

Per ADR-0084. 4 limit types (deposit, loss, wagering, session_time) × 3
periods (daily, weekly, monthly). Tightening = instant; loosening = cooling-off
(24h-7d). Enforcement: deposit (Phase 12), wagering (Phase 15), loss (Phase 11
ledger), session (client+server).

## 3. Self-Exclusion + SE-survives-erasure

Per ADR-0085. Periods: 6m, 1y, 2y, 5y, lifetime. HMAC pseudonymization survives
erasure. Cross-module enforcement via RGPort (Law 18): games/bonuses/payments/
marketing all blocked. Reactivation: only after ends_at; 24h cooling-off.

## 4. Reality Checks

Per ADR-0086. UK GC mandate. Client timer + server enforcement. Display: session
duration, net gain/loss, continue/exit option. Configurable interval (default 30min).

## 5. Jurisdiction Policy Engine

Per ADR-0087. Centralized per-jurisdiction rules: bonus eligibility, limit mandates,
SE cooling-off, age verification, reality check intervals. Falls back to "ALL" default.
Q1-blocked for jurisdiction-specific values.

## 6. Kill Switch Architecture (<200ms SLO)

Per ADR-0089. **Most safety-critical feature.** Architecture:
1. Admin triggers (DB flag + outbox event).
2. ASGI WebSocket consumer receives via Redis pub/sub.
3. Consumer disconnects all WebSocket connections (<200ms).
4. API endpoints check cached flag (<1ms).
5. Phase 15 voids in-progress rounds via RoundVoidingPort.

Fan-out: per-tenant or global. Audit: every trigger + lift.

## 7. Real-Time Infrastructure (Phase 22 pulled forward)

Per ADR-0091. Django ASGI + channels + Redis pub/sub. KillSwitchConsumer.
RealRealtimeAdapter (replaces Phase 13 stub). Phase 22 extends for game state, chat.

## 8. Port Interfaces (forward-dependencies)

Per ADR-0090 (RoundVoidingPort — Phase 15 implements).
Per ADR-0088 (GeoPort — Q5-blocked stub).

## 9. Real Adapters (replacing Phase 13 stubs)

- RealRGAdapter: actual RG enforcement (limits, SE, reality checks).
- RealJurisdictionAdapter: actual jurisdiction rules (JurisdictionPolicyEngine).
- RealRealtimeAdapter: actual Redis pub/sub (replaces log+no-op stub).

## 10. Cross-Phase Continuity

- Phase 4: Error format; structured logging; PII redaction; mypy strict; 95% coverage.
- Phase 5: RLS on player_limit, self_exclusion, reality_check, kill_switch, jurisdiction_policy tables.
- Phase 7: Audit events: protection.limit_exceeded, protection.se_activated, protection.reality_check_overdue, protection.kill_switch_triggered, protection.kill_switch_lifted.
- Phase 8: Outbox events on every state change; state machine base.
- Phase 9: SE-survives-erasure (HMAC pseudonymization); retention per Phase 9 schedule.
- Phase 11: Loss limits calculated from ledger; kill switch HALTs ledger operations.
- Phase 12: Deposit limits checked by payment service; kill switch HALTs payments.
- Phase 13: RealRGAdapter + RealJurisdictionAdapter replace stubs; MarketingGate checks SE.
- Phase 15: RoundVoidingPort real adapter; game platform checks limits + SE + kill switch.
