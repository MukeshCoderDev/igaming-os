# Stage 08 Handoff — Phase 9 Entry Criteria (Increment 1 Close)

| Field | Value |
|---|---|
| Document | `docs/stage-handoffs/stage-08-handoff.md` |
| Version | 5.9 (Phase 8 — Increment 1 close) |
| Status | Approved |
| Owner | Engineering Lead |
| Authority | Phase 8 hard acceptance; Increment 1 close |

This document is the **Increment 1 close handoff**. It defines what
Phase 8 (Increment 1 final phase) hands off to Phase 9 (Increment 2
first phase), the contracts Phase 9 must honor, and the Increment 1
completion status.

## 1. Phase 8 deliverables handed off

### 1.1 ADRs (7 ACCEPTED in Phase 8)
ADR-0040 (outbox), ADR-0041 (inbox dedup), ADR-0042 (DLQ),
ADR-0043 (idempotency), ADR-0044 (state machine),
ADR-0045 (notifications port), ADR-0046 (MarketingGate). Plus
ADR-0014 RESOLVED (chronic deferral loop closed → ACCEPTED).

### 1.2 Reliability core
- `reliability/domain/` — outbox, inbox, idempotency, notifications,
  marketing_gate, state_machine.
- `reliability/adapters/` — orm, outbox_relay (SELECT FOR UPDATE
  SKIP LOCKED), consumer (ConsumerBase + DLQConsumer), notifications
  (Email/SMS stub + FallbackAdapter).
- `reliability/migrations/0001_initial.py` — outbox + inbox +
  idempotency_key tables + RLS.
- `middleware/idempotency.py` — IdempotencyMiddleware (same key + same
  body = cached; different body = 409).

### 1.3 Event schema
`docs/architecture/event-schema.md` — canonical envelope (event_id,
event_type, event_version, aggregate_id, aggregate_type, tenant_id,
actor_id, correlation_id, occurred_at, payload) + per-type schemas.

### 1.4 Audit event type taxonomy extended
10 new reliability.* event types added (outbox_appended, outbox_relayed,
outbox_failed, inbox_deduped, dlq_message_sent, idempotency_cache_hit,
idempotency_conflict, state_transition, gate_decision, notification_sent).

## 2. Contracts Phase 9 must honor

### 2.1 Outbox contract
- Every state change that produces an event MUST append to the outbox
  in the same transaction (`append_to_outbox()`).
- The relay polls at 50ms; events are at-least-once.
- Consumers MUST be idempotent (use ConsumerBase).

### 2.2 Inbox dedup contract
- Every consumer MUST extend ConsumerBase (inbox dedup).
- (message_id, consumer_id) is the dedup key.
- ON CONFLICT DO NOTHING; same-transaction insertion.

### 2.3 Idempotency contract
- Every mutating endpoint SHOULD accept Idempotency-Key header.
- Same key + same body = cached response; same key + different body = 409.
- Cross-service: forward the Idempotency-Key header.

### 2.4 State machine contract
- Every aggregate with lifecycle states MUST use @transition decorator.
- Invalid transitions raise TransitionError.
- Every transition fires _before/_after hooks (emit outbox + audit).

### 2.5 MarketingGate contract
- Every notification send MUST go through MarketingGate.
- transactional bypasses suppression, respects caps.
- marketing respects both.
- Every gate decision is audited.

### 2.6 Inherited contracts (Phase 4-7)
Error format, structured logging, correlation-ID, RLS, pgbouncer,
AuthN (JWT), RBAC (closed permission catalog), hash-chained audit,
insert-only audit, redaction, clearance model.

## 3. Phase 9 entry criteria (Increment 2 start)
- Phase 0 gate passed (Q1/Q2/Q4/Q5).
- Phase 8 hard acceptance met (outbox/inbox/DLQ/idempotency/state-
  machine/notifications/MarketingGate implemented; 7 ADRs ACCEPTED;
  ADR-0014 RESOLVED; rules 1-52 green; coverage ≥85%).
- Increment 1 close report signed off (`increment-1-close.md`).

## 4. Increment 2 scope (preview)
Phase 9 begins Increment 2 (Regulated Core continuation):
- Ledger primitives (ADR-0011/0012/0013 → ACCEPTED).
- KYC vendor integration (Q6 unblock required).
- Sanctions/PEP screening (Q7 unblock required).
- Payment instruction execution (Increment 3 scope preview).
- Real vendor adapters for notifications (Q5 unblock).
- Redis for idempotency store + token blacklist + cap counters.

## 5. Increment 1 completion

**Increment 1 (Governed Foundation) is complete.** Four pillars
delivered:
1. **Tenancy** (Phase 5) — Tenant + Brand with RLS.
2. **Identity** (Phase 6) — User + RBAC + AuthN + service identity.
3. **Audit** (Phase 7) — Hash-chained audit log with Merkle redaction.
4. **Reliable Core** (Phase 8) — Outbox + inbox + DLQ + idempotency +
   state machine + notifications + MarketingGate.

**Registry:** 51 DECs, 46 ADRs (30 ACCEPTED, 16 PROPOSED).
**Linter:** rules 1-52, exit 0.
**External blockers:** Q1/Q2/Q4/Q5 remain BLOCKED (block Increment 2).

## 6. Handoff sign-off
Engineering Lead, Architecture Lead, Security Lead, Privacy Owner,
Compliance Lead, Architect (Phase 8 ratified role).

## 7. Worklog pointer
`/home/z/my-project/worklog.md` — Phase 8 close-out entry.
