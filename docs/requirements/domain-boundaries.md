# Domain Boundaries — Increment 1 (Phase 1)

| Field | Value |
|---|---|
| Document | `docs/requirements/domain-boundaries.md` |
| Version | 5.2 |
| Status | Approved |
| Owner | Architecture Lead |
| Authority | BLUEPRINT §2; DEC-0002 (hexagonal); `traceability.md` §B.3 |

This document defines the bounded contexts for Increment 1, the
contracts between them, and the forbidden couplings. The 26
module-boundary REQs (MB-REQ-0001…0026) are the invariants this
document enforces. Any code or design that violates an MB-REQ is a
defect, regardless of the phase that produces it.

## 1. Bounded contexts

The platform is decomposed into the following bounded contexts. Each
context owns its own data model, its own contracts, and its own
deployment cadence. Contexts communicate only via published
contracts (MB-REQ-0006).

| Context | Owner role | In Phase 1? | Primary REQs |
|---|---|---|---|
| Tenancy | Architecture Lead | Yes | MB-REQ-0001, MB-REQ-0002, MB-REQ-0023 |
| Identity | Identity Lead | Primitives yes; full Phase 4–7 | MB-MSG-0003 |
| Audit | Architecture Lead | Yes | MB-REQ-0004 |
| Workflow Engine | Architecture Lead | No (Phase 8–10) | MB-REQ-0007 |
| Ledger | Architecture Lead | No (Phase 11) | — |
| Configuration | Infrastructure Lead | Yes | MB-REQ-0018 |
| Feature Flags | Architecture Lead | Yes | MB-REQ-0019 |
| Telemetry | Infrastructure Lead | Yes | MB-REQ-0020 |
| Reliability (idempotency, backpressure, circuit breakers) | Architecture Lead | Yes | MB-REQ-0013, MB-REQ-0014, MB-REQ-0015 |
| Backups & DR | Operations Lead | Yes (workflow only) | — |
| Sandbox | Product Lead | No (Phase 4–7) | — |
| Webhooks | Infrastructure Lead | Yes | Pain-REQ-0010 |

The boundaries are stable across phases. A context that is "not in
Phase 1" still has a defined boundary; it simply has no
implementation yet. This prevents Phase 1 code from accidentally
reaching into a future context.

## 2. Contracts

Every cross-context call uses a published contract. A contract is a
versioned interface definition (OpenAPI for HTTP, Protobuf or JSON
Schema for events). Contracts live in a dedicated `contracts/`
directory (created in Phase 2) and are versioned independently of
the contexts that implement them.

### 2.1 Contract versioning rules

1. Contracts are additive: a new version may add fields, methods,
   or events, but may not remove or rename them.
2. A contract version is identified by a SemVer triple. Breaking
   changes require a major version bump and a parallel deployment
   of the old and new versions until all consumers migrate.
3. Consumers must declare the contract version they depend on. The
   platform's contract registry rejects undeclared dependencies.
4. A contract change requires an ADR. The ADR cites the DEC that
   governs the affected context.

### 2.2 Forbidden contract patterns

- **DB sharing.** No context may read another context's database
  tables. Cross-context reads go through the owning context's
  query API. (MB-REQ-0005, MB-REQ-0006.)
- **Bypass via ORM.** No context may use an ORM to reach into
  another context's models. The ORM is a private implementation
  detail of each context.
- **Shared mutable state.** No context may hold a reference to
  another context's in-memory state. Inter-context calls are
  always serialized (HTTP, message, or event).
- **Synchronous cross-tenant calls.** No context may make a
  synchronous call that crosses a tenant boundary. Cross-tenant
  operations are asynchronous and go through a workflow.
  (MB-REQ-0023.)

## 3. The Tenancy context

The Tenancy context is the root of the authorization graph. Every
other context's data and operations are scoped to a tenant that the
Tenancy context issued.

### 3.1 Owned data

- Tenant aggregate root (DEC-0014): tenant ID, legal name,
  jurisdiction, contract ID, SSO protocol preference, provisioning
  state, configuration.
- Tenant data partition key (DEC-0003): the row-level security key
  that all other contexts use to isolate tenant data.

### 3.2 Published contracts

- `tenancy.v1.Tenant` — query API for tenant metadata.
- `tenancy.v1.Provisioning` — command API for tenant provisioning
  (WF-01).
- `tenancy.v1.Configuration` — command/query API for tenant
  configuration updates (WF-02).
- `tenancy.v1.events.TenantProvisioned` — domain event.
- `tenancy.v1.events.TenantConfigurationUpdated` — domain event.

### 3.3 Forbidden couplings

- No other context may create a tenant. Only the Tenancy context
  may.
- No other context may modify a tenant's jurisdiction or contract
  ID. These are immutable post-provisioning.
- No other context may read the tenant's data partition key directly.
  The key is injected into requests by the identity service at
  authentication time.

## 4. The Identity context

The Identity context is the sole issuer of authentication tokens
(MB-REQ-0003). It owns user records, role assignments, delegation
chains, and session state.

### 4.1 Owned data

- User records (per tenant): user ID, tenant ID, email, status,
  role assignments, delegation chains.
- Session records: session ID, user ID, tenant ID, issued-at,
  expires-at, token hash.
- Role definitions: per-tenant role catalog (tenant admins may
  extend the catalog within the platform's allowed role schema).

### 4.2 Published contracts

- `identity.v1.Auth` — authentication API (WF-04).
- `identity.v1.Users` — user management API (WF-03).
- `identity.v1.Roles` — role assignment API (WF-05).
- `identity.v1.events.UserCreated` — domain event.
- `identity.v1.events.RoleAssigned` — domain event.
- `identity.v1.events.DelegationCreated` — domain event.

### 4.3 Forbidden couplings

- No other context may issue tokens. Verifying tokens is allowed
  (and required); issuing is forbidden.
- No other context may store passwords, MFA secrets, or session
  state.
- No other context may read user records directly. Cross-context
  user queries go through `identity.v1.Users`.

## 5. The Audit context

The Audit context is append-only (DEC-0006, MB-REQ-0004). It owns
the audit log and the hash chain (DEC-0007).

### 5.1 Owned data

- Audit log entries: sequence number, tenant ID, timestamp, actor
  identity, operation, before-state hash, after-state hash, entry
  hash, previous entry hash.
- Hash chain head pointer: the sequence number and hash of the most
  recent entry.

### 5.2 Published contracts

- `audit.v1.Append` — command API for audit event emission (WF-06).
  This is the only API that mutates the audit log. There is no
  update or delete API.
- `audit.v1.Query` — query API for audit log reads (WF-07).
- `audit.v1.Export` — command API for export bundle generation
  (WF-07).
- `audit.v1.events.AuditAppended` — domain event (used for
  downstream projections, not for re-auditing).

### 5.3 Forbidden couplings

- No other context may write to the audit log directly. All audit
  writes go through `audit.v1.Append`.
- No other context may compute or update the hash chain. The hash
  chain is the Audit context's invariant.
- No other context may delete audit entries. There is no delete
  API and no operational procedure that performs deletion.
  Retention enforcement (§4.1 of `nfr.md`) is a forward-only
  archival operation, not a deletion.

## 6. The Reliability context

The Reliability context bundles the cross-cutting primitives that
every other context uses: idempotency, backpressure, circuit
breakers. It is not a single service; it is a library and a set of
sidecar patterns.

### 6.1 Owned artefacts

- Idempotency key store: records idempotency keys, request hashes,
  and response caches for the key lifetime (default 24h).
- Circuit breaker state store: records per-dependency circuit
  state (closed, open, half-open) and last-trip time.
- Backpressure signal bus: publishes queue depths and reject
  signals that callers honor.

### 6.2 Published contracts

- `reliability.v1.Idempotency` — middleware API used by every
  mutating endpoint.
- `reliability.v1.CircuitBreaker` — library API used by every
  outbound call.
- `reliability.v1.Backpressure` — signal contract that inbound
  queues publish and callers subscribe to.

### 6.3 Forbidden couplings

- No context may implement its own idempotency logic. The
  Reliability context's idempotency middleware is the only
  implementation.
- No context may implement its own circuit breaker. The Reliability
  context's circuit breaker library is the only implementation.
- No context may ignore a backpressure signal. Callers that ignore
  backpressure are defects.

## 7. The Configuration, Feature Flags, and Telemetry contexts

These three contexts are infrastructure-grade and have similar
boundary rules. They are grouped here for brevity.

### 7.1 Configuration

- **Owned data:** per-tenant configuration key-value store.
- **Published contracts:** `config.v1.Get`, `config.v1.Set` (admin
  only), `config.v1.events.ConfigurationUpdated`.
- **Forbidden couplings:** no context may read configuration from
  environment variables directly. All configuration reads go
  through the Configuration context. (MB-REQ-0018.)

### 7.2 Feature Flags

- **Owned data:** per-tenant feature flag state.
- **Published contracts:** `flags.v1.Evaluate`, `flags.v1.Set`
  (admin only), `flags.v1.events.FlagUpdated`.
- **Forbidden couplings:** feature flags are evaluated at the
  boundary (MB-REQ-0019). No domain logic may read a flag directly;
  the boundary injects the flag value into the request context.

### 7.3 Telemetry

- **Owned data:** OpenTelemetry spans and metrics (not audit log
  entries — those are the Audit context's data).
- **Published contracts:** `telemetry.v1.Span` (library API),
  `telemetry.v1.Metric` (library API).
- **Forbidden couplings:** no context may emit telemetry using a
  non-OpenTelemetry library. (DEC-0020, MB-REQ-0020.)

## 8. The Workflow Engine, Ledger, Sandbox, Webhooks, and Backups contexts

These contexts are not implemented in Phase 1 but their boundaries
are defined here to prevent Phase 1 code from reaching into them.

### 8.1 Workflow Engine (Phase 8–10)

- **Boundary:** owns declarative workflow definitions and the
  execution engine (DEC-0009, DEC-0010, MB-REQ-0007).
- **Phase 1 constraint:** no Phase 1 code may execute workflows.
  Phase 1 may define workflow definition schemas for future use,
  but no engine is present.

### 8.2 Ledger (Phase 11)

- **Boundary:** owns ledger entries (DEC-0011), decimal money
  (DEC-0012), and multi-currency (DEC-0013).
- **Phase 1 constraint:** no Phase 1 code may post to a ledger.
  The Ledger context does not exist in Phase 1.

### 8.3 Sandbox (Phase 4–7)

- **Boundary:** owns per-integrator sandbox tenants with synthetic
  data (Pain-REQ-0009).
- **Phase 1 constraint:** the Tenancy context's provisioning API
  may designate a tenant as a sandbox, but no sandbox-specific
  data synthesis exists in Phase 1.

### 8.4 Webhooks (Phase 1)

- **Boundary:** owns outbound webhook delivery with retry
  (Pain-REQ-0010).
- **Phase 1 constraint:** webhook delivery is in Phase 1 scope.
  The Webhooks context subscribes to domain events from other
  contexts and delivers them to tenant-configured endpoints.

### 8.5 Backups & DR (Phase 1, workflow only)

- **Boundary:** owns backup execution (WF-09) and restore
  (WF-10). The actual storage backend is infrastructure.
- **Phase 1 constraint:** backups operate on the Tenancy,
  Identity, and Audit contexts' data only in Phase 1. Later
  contexts are added to the backup set when they are delivered.

## 9. Boundary enforcement

Boundary violations are detected at three layers:

1. **Code review.** Every PR is reviewed against the MB-REQ set.
   The reviewer's checklist includes the forbidden couplings in
   §3.3, §4.3, §5.3, §6.3, and §7.
2. **Static analysis.** A static analyzer (added in Phase 2)
   enforces context boundaries at the import level: a context may
   not import another context's internal modules.
3. **Runtime.** The platform's service mesh (added in Phase 2)
   enforces context boundaries at the network level: a context may
   not call another context's internal endpoints.

The three layers are defense in depth. A violation that escapes one
layer is caught by the next. None of the layers is sufficient
alone.

## 10. Boundary change protocol

A boundary change (adding a context, splitting a context, merging
two contexts, or moving an aggregate between contexts) requires:

1. An ADR. The ADR cites the DEC that the change affects (or
   proposes a new DEC).
2. An update to this document.
3. An update to `traceability.md` §B.3 (the MB-REQ rows that
   encode the boundary).
4. A supersession row in `traceability.md` §D for any MB-REQ that
   the change retires.

Boundary changes are not made unilaterally. The Architecture Lead
is Accountable; the Engineering Lead, the Identity Lead (for
identity-affecting changes), and the Compliance Lead (for
audit-affecting changes) are Consulted.
