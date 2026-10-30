# Event Schema — Outbox + Domain Events

| Field | Value |
|---|---|
| Document | `docs/architecture/event-schema.md` |
| Version | 5.9 (Phase 8) |
| Status | Approved |
| Owner | Architecture Lead |
| Authority | ADR-0040 / DEC-0045; Phase 8 spec output #9 |

This document defines the canonical event schema for outbox + domain
events. All events follow this schema; per-event-type payload schemas
are versioned.

## 1. Canonical event envelope

Every event (outbox + domain) carries these fields:

| Field | Type | Description |
|---|---|---|
| `event_id` | UUID | Unique event identifier (UUIDv4). |
| `event_type` | string | Closed catalog code (e.g., `tenancy.tenant_provisioned`). |
| `event_version` | int | Schema version of the payload (starts at 1; incremented on breaking change). |
| `aggregate_id` | string | The aggregate that emitted the event (e.g., tenant UUID). |
| `aggregate_type` | string | Aggregate type (e.g., `tenant`, `user`, `brand`). |
| `tenant_id` | UUID \| null | Tenant scope (null for global events). |
| `actor_id` | UUID | Who triggered the event (user_uuid or service_uuid). |
| `correlation_id` | string \| null | Phase 4 correlation ID (propagated across services). |
| `occurred_at` | ISO 8601 | When the event occurred (DB now() on outbox insert). |
| `payload` | JSONB | Event-type-specific payload (schema-versioned). |

## 2. Per-event-type payload schemas

### 2.1 tenancy.tenant_provisioned (v1)

```json
{
  "legal_name": "Acme Bank",
  "jurisdiction": "US-NY",
  "contract_id": "CTR-001"
}
```

### 2.2 auth.login_success (v1)

```json
{
  "method": "password",
  "mfa_used": false
}
```

### 2.3 reliability.outbox_appended (v1)

```json
{
  "event_type": "tenancy.tenant_provisioned",
  "aggregate_id": "00000000-0000-0000-0000-000000000001",
  "aggregate_type": "tenant"
}
```

### 2.4 reliability.gate_decision (v1)

```json
{
  "send_type": "marketing",
  "recipient": "user@example.com",
  "channel": "email",
  "decision": "deny_suppression",
  "reason": "recipient user@example.com is suppressed"
}
```

## 3. Schema versioning

- `event_version` starts at 1 for every event type.
- Breaking changes (field removed/renamed, type changed) increment `event_version`.
- Additive changes (new optional field) do NOT increment the version.
- Consumers MUST handle unknown versions gracefully (log + DLQ).
- Schema-versioned payloads enable replay (old events retain old schema).

## 4. Cross-references

- ADR-0040: `docs/adr/ADR-0040.md`
- Outbox relay: `src/noventra/apps/reliability/adapters/outbox_relay.py`
- Event type catalog: `src/noventra/apps/audit/domain/event_types.py`
- Audit event schema: `docs/architecture/audit-retention-policy.md`
