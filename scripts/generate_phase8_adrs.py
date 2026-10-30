#!/usr/bin/env python3
"""Generate Phase 8 ADRs: 7 new (0040-0046) ACCEPTED + update ADR-0014 → ACCEPTED.

Run:  python3 /home/z/my-project/scripts/generate_phase8_adrs.py
"""

from pathlib import Path
import re

OUT_DIR = Path("/home/z/my-project/docs/adr")
LAST_REVIEWED = "2025-10-28"
CREATED = "2025-10-28"

NEW_ADRS = [
    (40, "DEC-0045", "Outbox pattern + relay strategy",
     "Architecture Lead", "Phase1",
     "Distributed systems need reliable event publishing. Writing to a message broker within a DB transaction is not atomic (the broker might be down). The outbox pattern: write events to an outbox table in the same transaction as the aggregate change, then relay them asynchronously. This guarantees at-least-once delivery without distributed transactions.",
     "Adopt the outbox pattern. outbox table schema: id, aggregate_id, aggregate_type, event_type, event_version, tenant_id, payload (JSONB), occurred_at, relayed_at. Relay via polling (50ms interval; pgbouncer-compatible per ADR-0030). Multi-instance via SELECT FOR UPDATE SKIP LOCKED. At-least-once semantics: publish-then-mark (relay publishes to Redis/bus, then marks relayed_at). Per-aggregate ordering (ORDER BY id). Backpressure on Redis error (relay pauses + alerts). Schema-versioned payloads (event_version field). Replay command (manage.py replay_outbox).",
     "Alternatives: (a) CDC (debezium) — heavy infra; (b) direct publish in transaction — not atomic; (c) change data capture via triggers — fragile; (d) event sourcing (full) — over-engineered for Phase 8. (a) rejected for infra; (b) rejected for atomicity; (c) rejected for fragility; (d) rejected for scope.",
     "Relay adds latency (~50ms polling interval). At-least-once means consumers must be idempotent (ADR-0041 inbox dedup). Multi-instance requires SKIP LOCKED (Postgres 9.5+; available). Replay command must be carefully scoped (avoid double-publish).",
     "Phase 8: multi-instance relay test (no double-publish, no missed events). Phase 8: pgbouncer transaction-mode relay test. Phase 8: replay command test. Phase 9: load-test at 1k events/s.",
     "ACCEPTED", "Architecture Lead + Architect + Reliability Lead"),

    (41, "DEC-0046", "Inbox dedup + consumer semantics",
     "Architecture Lead", "Phase1",
     "At-least-once delivery (from outbox relay) means consumers may receive duplicate messages. Consumers must be idempotent. The inbox pattern: record (message_id, consumer_id) in an inbox table within the same transaction as the side effect. Duplicates are detected by ON CONFLICT DO NOTHING.",
     "Adopt inbox dedup. inbox table schema: (message_id, consumer_id) composite PK, processed_at, payload_hash. ON CONFLICT DO NOTHING on insert. Insert after processing in the SAME transaction as the side effect (atomicity guarantee). Cleanup of rows older than N days (default 7; configurable). Consumer base class: ConsumerBase.process(message) wraps the handler in a transaction + inbox insert.",
     "Alternatives: (a) idempotent side effects only (no inbox) — hard to guarantee; (b) Redis dedup — not durable; (c) application-level dedup — race-prone. (a) rejected for difficulty; (b) rejected for durability; (c) rejected for races.",
     "Inbox table grows; cleanup is essential (cron job). Same-transaction insertion requires ATOMIC_REQUESTS or explicit atomic blocks (already set per ADR-0030). Consumer must handle the ON CONFLICT case (message already processed; skip).",
     "Phase 8: two-consumer same-message test (only one side effect). Phase 8: cleanup test (old rows removed). Phase 9: load-test inbox insert at 5k/s.",
     "ACCEPTED", "Architecture Lead + Architect + Engineering Lead"),

    (42, "DEC-0047", "DLQ + poison criteria + monitoring",
     "Architecture Lead", "Phase1",
     "Messages that fail repeatedly (poison messages) must be moved to a dead-letter queue (DLQ) to prevent infinite retry. Poison criteria must be explicit. DLQ must be monitored + replayable.",
     "Adopt DLQ with explicit poison criteria: (1) N=3 retries exceeded; (2) deserialization failure (non-retryable); (3) terminal error code (non-retryable); (4) TTL exceeded (message older than 24h). DLQ storage: Redis Stream (fast; Phase 8) with Postgres fallback for durability (Phase 9). Enriched payload (original message + error + stack trace + retry count). Alerting on DLQ arrival (structured log + dedicated channel). Replay command (manage.py replay_dlq).",
     "Alternatives: (a) no DLQ (infinite retry) — blocks consumer; (b) Postgres-only DLQ — slower; (c) RabbitMQ DLX — vendor lock-in. (a) rejected for blocking; (b) rejected for speed; (c) rejected for lock-in.",
     "Redis Stream DLQ is not durable (Redis crash = data loss); Phase 9 adds Postgres fallback. Poison criteria must be tuned (N=3 may be too low for transient failures). Replay command must handle the case where the original message is still in the inbox (skip).",
     "Phase 8: poison message arrives in DLQ test. Phase 8: alerting fires on DLQ arrival. Phase 8: replay succeeds after fix test. Phase 9: Postgres DLQ fallback.",
     "ACCEPTED", "Architecture Lead + Architect + Reliability Lead"),

    (43, "DEC-0048", "Idempotency keys + cross-service propagation",
     "Architecture Lead", "Phase1",
     "Clients retry. Without idempotency, a retried POST creates duplicate resources. The Idempotency-Key header (RFC draft) is the standard. The key + request hash must be stored; on replay, the cached response is returned. Cross-service propagation: the key is forwarded to downstream services.",
     "Adopt idempotency keys. Client-supplied Idempotency-Key header (UUIDv4). idempotency_key table: (key, tenant_id, endpoint) PK, request_hash, response_status, response_body, created_at, expires_at. 24-hour TTL. Conflict handling: same key + same body (matching request_hash) = cached response returned; same key + different body = 409 noventra.idempotency.conflict. Same-transaction insertion (atomic with the request). Cross-service propagation: the Idempotency-Key header is forwarded to downstream service calls.",
     "Alternatives: (a) client-side dedup — unreliable; (b) server-side request-hash only — false positives; (c) DB unique constraints — incomplete. (a) rejected for unreliability; (b) rejected for false positives; (c) rejected for incompleteness.",
     "Idempotency key store must be highly available (Redis recommended; Phase 8 uses Postgres for correctness). 24h TTL bounds the replay window. Cross-service propagation requires the key to be forwarded by all HTTP clients (documented contract).",
     "Phase 8: same key + same body = cached response test. Phase 8: same key + different body = 409 test. Phase 8: cross-service propagation test (mocked downstream). Phase 9: Redis idempotency store.",
     "ACCEPTED", "Architecture Lead + Architect + API Lead"),

    (44, "DEC-0049", "State machine library + transition pattern",
     "Architecture Lead", "CrossCutting",
     "Aggregates have lifecycle states (e.g., Tenant: provisioning → active → suspended → deprovisioned). Ad-hoc state transitions are error-prone. A declarative state machine with guards + side-effects makes transitions explicit, validated, and audited.",
     "Adopt django-fsm (or justified alternative). Declarative transitions via @transition decorator. Guard pattern (conditions that must be true for the transition). Transition side-effect hooks: emit outbox event + audit event. Optimistic locking for concurrent transitions (version field + SELECT ... FOR UPDATE). Every transition audited per Phase 7 (audit event with from_state, to_state, transition_name).",
     "Alternatives: (a) ad-hoc state field + if/else — error-prone; (b) transitions table (data-driven) — over-engineered for Phase 8; (c) xstate (JS) — wrong ecosystem. (a) rejected for errors; (b) rejected for complexity; (c) rejected for ecosystem.",
     "django-fsm adds a dependency (lightweight). Transition guards must be maintained. Optimistic locking may cause user-facing conflicts (mitigated by retry). Every transition generates an audit event (high audit volume; mitigated by partitioning per Phase 7).",
     "Phase 8: invalid transition rejected test. Phase 8: concurrent transition handled (optimistic lock) test. Phase 8: transitions audited test. Phase 9: custom transition UI.",
     "ACCEPTED", "Architecture Lead + Architect + Engineering Lead"),

    (45, "DEC-0050", "Notifications port + adapter vendors",
     "Architecture Lead", "Phase1",
     "The platform sends notifications (email, SMS) for auth events, tenant lifecycle, compliance alerts. Vendors (SendGrid, Twilio) are Q5-blocked. The port pattern decouples the domain from the vendor; adapters are swappable.",
     "Adopt a notifications port. Interface: send(channel, recipient, content, context) -> SendResult. Channels in scope: email + SMS. Push + webhook deferred (Phase 9+). Adapters per channel: vendor per Q5 (stub if blocked). Fallback strategy: if primary vendor fails, log + queue for retry (no silent drop). Port interface in src/noventra/apps/reliability/domain/notifications.py.",
     "Alternatives: (a) direct vendor call (no port) — vendor lock-in; (b) Celery email backend — Django-specific; (c) no notifications — UX gap. (a) rejected for lock-in; (b) rejected for coupling; (c) rejected for UX.",
     "Vendor selection is Q5-blocked (ASSUMED stubs). Fallback strategy may delay notifications (acceptable for non-critical). SMS is Q5-blocked (Q44). Push/webhook deferred.",
     "Phase 8: port interface documented. Phase 8: stub adapters (log + queue). Phase 9: real vendor adapters (Q5 unblock). Phase 9: load-test at 100 notifications/s.",
     "ACCEPTED", "Architecture Lead + Architect + Product Lead"),

    (46, "DEC-0051", "MarketingGate + suppression + caps + send-type taxonomy",
     "Architecture Lead", "Phase1",
     "Marketing sends (promotional) must respect suppression lists (unsubscribes, bounces, complaints) and rate caps (tenant monthly, tenant daily, recipient daily, channel). Transactional sends (auth, security) bypass suppression but respect caps. The MarketingGate is the ONLY place sends are gated — every send goes through it.",
     "Adopt MarketingGate. Joins suppression + caps at send time. Suppression sources: unsubscribes, hard bounces, complaints, legal holds. Caps: tenant monthly, tenant daily, recipient daily, channel, jurisdiction (if Q1 unblocked). Send-type taxonomy: transactional (bypasses suppression, respects caps) vs marketing (respects both). The ONLY place sends are gated (unchecked-send lint fails). Every decision audited per Phase 7 (audit event with send_type, recipient, channel, decision, reason).",
     "Alternatives: (a) no gate (free send) — compliance violation; (b) gate at adapter level — scattered; (c) gate at domain level — too late. (a) rejected for compliance; (b) rejected for scattering; (c) rejected for timing.",
     "MarketingGate is a chokepoint (must be highly available). Caps require counters (Redis recommended; Phase 8 uses Postgres). Suppression list must be maintained. Every send generates an audit event (high volume). Jurisdictional caps are Q1-blocked.",
     "Phase 8: suppression match → deny test. Phase 8: cap exceeded → deny test. Phase 8: transactional bypasses suppression, respects caps test. Phase 8: unchecked-send lint fails test. Phase 9: Redis cap counters.",
     "ACCEPTED", "Architecture Lead + Architect + Privacy Owner + Compliance Lead"),
]

UPDATE_ADRS = [
    (14, "Architecture Lead + Engineering Lead"),
]


def render_new(adr_num, dec_id, title, owner, scope, ctx, dec, alts, cons, val,
               status, approver):
    adr_id = f"ADR-{adr_num:04d}"
    return f"""---
ADR: {adr_id}
Title: {title}
Status: {status}
DEC: {dec_id}
Owner: {owner}
Scope: {scope}
Created: {CREATED}
Last-Reviewed: {LAST_REVIEWED}
Supersedes: ""
Superseded-By: ""
Approver: {approver}
---

# {adr_id} — {title}

## Context

{ctx}

## Decision

{dec}

## Alternatives

{alts}

## Consequences

{cons}

## Validation Plan

{val}

## Decision statement (one line)

{dec_id} → {title}. Owner: {owner}. Status: {status}.
Supersede history: none (initial seed). Last reviewed: {LAST_REVIEWED}.
Approver: {approver}.

## DEC link

This ADR cites {dec_id} per the ADR-DEC mapping law (DEC-0023, errata E7).
The DEC row is in `docs/requirements/traceability.md` §C. The mapping is
1:1: {dec_id} ↔ {adr_id}.
"""


def update_existing(adr_num, approver):
    adr_id = f"ADR-{adr_num:04d}"
    path = OUT_DIR / f"{adr_id}.md"
    text = path.read_text()
    text = re.sub(r'^Status: PROPOSED$', 'Status: ACCEPTED', text, flags=re.MULTILINE)
    text = re.sub(r'^Last-Reviewed: .*$',
                  f'Last-Reviewed: {LAST_REVIEWED}', text, flags=re.MULTILINE)
    if 'Approver:' not in text:
        text = re.sub(r'^(Superseded-By: ".*")$',
                      f'\\1\nApprover: {approver}', text, flags=re.MULTILINE)
    else:
        text = re.sub(r'^Approver: .*$', f'Approver: {approver}',
                      text, flags=re.MULTILINE)
    path.write_text(text)
    print(f"updated {path} (status → ACCEPTED, approver → {approver})")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for (n, dec, title, owner, scope, ctx, dec_text, alts, cons, val,
         status, approver) in NEW_ADRS:
        path = OUT_DIR / f"ADR-{n:04d}.md"
        path.write_text(render_new(n, dec, title, owner, scope, ctx, dec_text,
                                    alts, cons, val, status, approver))
        print(f"wrote {path} (status={status})")
    for (n, approver) in UPDATE_ADRS:
        update_existing(n, approver)
    print(f"\n{len(NEW_ADRS)} new ADRs + {len(UPDATE_ADRS)} updated ADRs.")


if __name__ == "__main__":
    main()
