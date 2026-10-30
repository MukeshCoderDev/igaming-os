#!/usr/bin/env python3
"""Generate 21 ADR stubs in Nygard format (Phase 2 upgrade of Phase 1 stubs).

Per DEC-0026, every ADR file under docs/adr/ must carry:
  - Nygard front-matter: ADR, Title, Status, DEC, Owner, Created, Supersedes, Last-Reviewed
  - Body sections: Context / Decision / Alternatives / Consequences / Validation Plan

Per the Phase 2 hard acceptance, all 21 stubs transition from
Phase 1 status `Accepted` to Phase 2 status `PROPOSED` pending formal
review. The stubs are now "owned + decided + DEC-linked" (per the gate
criterion) but not yet formally ratified.

Run:  python3 /home/z/my-project/scripts/generate_adr_stubs_v2.py
"""

from pathlib import Path

OUT_DIR = Path("/home/z/my-project/docs/adr")
CREATED = "2025-10-27"     # Phase 1 seed date
LAST_REVIEWED = "2025-10-28"  # Phase 2 review date

# Each tuple: (adr_num, dec_id, title, owner, scope, context, decision,
#              alternatives, consequences, validation_plan)
ADRS = [
    (1, "DEC-0001", "Adopt event-sourced domain model",
     "Architecture Lead", "Foundational",
     "The platform must support a complete audit trail of every state "
     "change, rebuildable read models, and deterministic replay for "
     "compliance and recovery. Traditional CRUD persistence loses history "
     "and complicates regulatory evidence collection. FATF Rec.11 and "
     "GDPR Art.5(2) accountability both favor an immutable event record "
     "as the source of truth.",
     "Adopt event sourcing as the primary persistence model for domain "
     "aggregates. State changes are recorded as immutable domain events; "
     "aggregates are rebuilt by replaying events. Read models are "
     "projections from the event log and may be rebuilt at any time "
     "(DEC-0018).",
     "Alternatives considered: (a) CRUD with audit triggers — simpler "
     "to implement but loses history and complicates rebuilds; (b) "
     "Change Data Capture (CDC) on top of CRUD — adds operational "
     "complexity without simplifying the model; (c) Temporal tables "
     "(PostgreSQL pg_temporal / SQL:2011) — limited to row-level history, "
     "no domain-event semantics. (a) and (b) rejected for insufficient "
     "auditability; (c) rejected for loss of domain semantics.",
     "Event store becomes a critical SPOF; operational discipline "
     "required for schema evolution of events (versioning, upcasters). "
     "Read-model lag must be monitored. Developer ergonomics: aggregates "
     "cannot be inspected via simple SQL queries; tooling required. "
     "Storage cost grows monotonically; snapshotting mitigates but does "
     "not eliminate.",
     "Phase 3 spike: implement a single aggregate (Tenant) end-to-end "
     "with event sourcing; verify rebuild from empty event log produces "
     "identical state. Phase 4: load-test the event store at 10k events/s "
     "sustained. Phase 11: validate that ledger postings (DEC-0011) "
     "compose naturally with event-sourced aggregates."),

    (2, "DEC-0002", "Adopt hexagonal architecture (ports and adapters)",
     "Architecture Lead", "Foundational",
     "Domain logic must be testable in isolation, free of framework and "
     "infrastructure coupling. Direct dependencies on ORMs, HTTP "
     "frameworks, or message buses in domain code make tests slow and "
     "refactors risky. NFR §7.1 (testability) requires 100% of domain "
     "modules unit-testable without external dependencies.",
     "Adopt hexagonal architecture: domain logic interacts with the "
     "outside world only through ports (interfaces) defined in the domain "
     "layer. Adapters (database, HTTP, message bus) implement those ports "
     "and live outside the domain. No domain code imports infrastructure. "
     "Enforced structurally by MB-REQ-0005, MB-REQ-0008, MB-REQ-0009, "
     "MB-REQ-0011, MB-REQ-0026.",
     "Alternatives considered: (a) layered architecture (controller / "
     "service / repository) — permits domain logic in services that "
     "import ORM models; (b) clean architecture (Uncle Bob) — "
     "conceptually equivalent to hexagonal but with more layers; "
     "(c) naked objects — UI directly reflects domain models, too "
     "inflexible for a multi-tenant B2B platform. (a) rejected for "
     "insufficient isolation; (b) rejected for layer proliferation; "
     "(c) rejected for UX rigidity.",
     "More interfaces and indirection than a layered design; learning "
     "curve for new engineers. Adapter boilerplate can be reduced but "
     "not eliminated. Risk of 'port explosion' if not disciplined.",
     "Phase 3: static analysis rule that rejects any import of "
     "`django.db`, `rest_framework`, or `pika` from `domain/` packages. "
     "Phase 4: coverage gate — domain modules must achieve 100% boundary "
     "coverage with stub adapters. Phase 2 risk-register entry tracks "
     "the 'port explosion' risk."),

    (3, "DEC-0003", "Tenant isolation via row-level security",
     "Architecture Lead", "Phase1",
     "Multi-tenancy must enforce isolation at the data layer so that a "
     "bug in application code cannot leak one tenant's data to another. "
     "Schema-per-tenant and database-per-tenant models raise operational "
     "cost (N× migrations, N× backup complexity) and complicate "
     "cross-tenant analytics. MB-REQ-0001 and MB-REQ-0002 mandate "
     "isolation at both data and compute layers.",
     "Use a single PostgreSQL database with row-level security (RLS) "
     "policies keyed on a `tenant_id` column. The tenant context is set "
     "per request via `SET LOCAL app.tenant_id = ...` and cannot be "
     "overridden by application code. Cross-tenant synchronous operations "
     "are forbidden (MB-REQ-0023). Enforced structurally: every table "
     "that holds tenant data has a `tenant_id` column with NOT NULL + "
     "FK to the tenant aggregate.",
     "Alternatives considered: (a) schema-per-tenant — operational "
     "explosion (N× migrations); (b) database-per-tenant — cost "
     "explosion at scale; (c) application-level filtering (no RLS) — "
     "relies on developer discipline; one missed WHERE clause leaks "
     "data. (a) and (b) rejected for operational cost; (c) rejected "
     "for unacceptable leak risk.",
     "RLS adds query overhead (~5–10% in benchmarks) and complicates "
     "cross-tenant analytics (must use a separate analytics replica "
     "with RLS disabled). Migration of legacy data requires backfill "
     "of `tenant_id`. Debugging is harder: RLS hides rows from "
     "interactive sessions.",
     "Phase 3: red-team test that attempts to read another tenant's "
     "rows via SQL injection, ORM misuse, and direct connection. "
     "Phase 4: performance benchmark comparing RLS-on vs RLS-off at "
     "1k req/s. Phase 11: validate that ledger postings (DEC-0011) "
     "compose with RLS without cross-tenant leakage."),

    (4, "DEC-0004", "OIDC for identity federation",
     "Identity Lead", "Phase4-7",
     "Default tenants require standards-based federation that supports "
     "modern auth flows (authorization code, PKCE, refresh tokens). "
     "SAML is heavy for greenfield tenants and lacks first-class "
     "support for mobile and SPA clients. MB-REQ-0003 mandates that "
     "the identity service is the sole issuer of auth tokens.",
     "Adopt OpenID Connect (OIDC) as the default federation protocol. "
     "The identity service is the sole issuer of auth tokens "
     "(MB-REQ-0003) and supports OIDC authorization-code flow with "
     "PKCE for all clients. Token lifetimes are short (≤ 1h access, "
     "≤ 30d refresh) per NFR §1.3.",
     "Alternatives considered: (a) SAML-only — excludes mobile/SPA "
     "clients and modern IdPs; (b) OAuth 2.0 without OIDC — no "
     "standardized user info; (c) custom token format — locks out "
     "third-party IdPs. (a) rejected for client coverage; (b) rejected "
     "for missing identity layer; (c) rejected for vendor lock-in.",
     "Requires running an OIDC provider (or integrating with one). "
     "Discovery and JWKS rotation add operational complexity. Token "
     "revocation is harder than session-based auth.",
     "Phase 4: integrate with two reference IdPs (Auth0, Keycloak) "
     "and verify interop. Phase 5: penetration test of the OIDC "
     "flow including token replay, code injection, and PKCE downgrade. "
     "Phase 7: load-test token issuance at 1k req/s."),

    (5, "DEC-0005", "SAML for enterprise tenancy SSO",
     "Identity Lead", "Phase4-7",
     "Enterprise tenants often mandate SAML 2.0 for SSO due to existing "
     "IdP investments (Azure AD, Okta, Ping). Supporting only OIDC "
     "excludes this segment. DEC-0004 covers default tenants; this "
     "decision covers the enterprise tier.",
     "Support SAML 2.0 as a second-tier federation protocol for "
     "enterprise tenants. SAML assertions are exchanged for the "
     "platform's internal auth tokens at the identity service boundary; "
     "downstream code is unaware of the original protocol.",
     "Alternatives considered: (a) OIDC-only with brokered SAML — "
     "requires a broker (e.g., Keycloak) in front of enterprise IdPs, "
     "adding a SPOF; (b) SAML-only — excludes modern clients; "
     "(c) SCIM-only — SCIM is provisioning, not SSO. (a) rejected for "
     "SPOF; (b) rejected for client coverage; (c) rejected for scope "
     "mismatch.",
     "SAML XML signatures are a frequent source of vulnerabilities "
     "(XML signature wrapping). Metadata exchange is operationally "
     "heavy. Just-in-time provisioning may conflict with enterprise "
     "offboarding procedures.",
     "Phase 5: integrate with one enterprise IdP (Azure AD) end-to-end "
     "including metadata exchange and signed assertions. Phase 5 "
     "penetration test: XML signature wrapping, certificate "
     "substitution, audience restriction bypass."),

    (6, "DEC-0006", "Append-only audit log (no update/delete API)",
     "Architecture Lead", "Phase1",
     "Regulatory regimes (FATF, GDPR, SOC 2) require audit logs to be "
     "tamper-evident and retained for years. An audit log that allows "
     "updates or deletes cannot satisfy tamper-evidence requirements. "
     "Law-REQ-0010 mandates immutability; MB-REQ-0004 enforces it "
     "structurally.",
     "The audit service exposes only an append API. There is no update "
     "and no delete API, and no operational procedure that performs "
     "deletion. Retention enforcement (NFR §4.1) is a forward-only "
     "archival operation to write-once storage (e.g., S3 Object Lock), "
     "not a deletion. See MB-REQ-0004 and Law-REQ-0010.",
     "Alternatives considered: (a) CRUD with soft-delete — deleted "
     "rows are recoverable in principle but the API surface invites "
     "misuse; (b) append + administrative delete with two-person "
     "approval — operationally heavy and still permits tampering if "
     "approvers are compromised; (c) blockchain-style distributed log "
     "— over-engineered for a single-platform audit log. (a) and (b) "
     "rejected for tamper risk; (c) rejected for complexity.",
     "Storage cost grows monotonically. Retention enforcement requires "
     "a separate archival pipeline. Query performance degrades as the "
     "log grows; partitioning and projection read models (DEC-0018) "
     "mitigate.",
     "Phase 1: implemented as a stub contract. Phase 8: red-team test "
     "that attempts deletion via SQL, ORM, and admin shell. Phase 9: "
     "verify that retention archival to S3 Object Lock is irreversible. "
     "Phase 10: load-test append at 5k events/s sustained."),

    (7, "DEC-0007", "Hash-chain audit log entries",
     "Architecture Lead", "Phase1",
     "Append-only is necessary but not sufficient for tamper-evidence: "
     "an attacker with database access could append a fraudulent entry "
     "or modify past entries directly in storage. A hash chain makes "
     "any modification of past entries detectable on read.",
     "Each audit entry stores its content hash and the hash of the "
     "previous entry: `hash_n = SHA256(hash_n-1 || event_n)`. A daily "
     "verifier scans the chain and alerts on any mismatch. The chain "
     "head is published externally (e.g., to a write-once store or a "
     "transparency log) for additional assurance.",
     "Alternatives considered: (a) signed entries only (no chain) — "
     "detects modification of individual entries but not insertion or "
     "deletion; (b) Merkle tree — efficient batch verification but "
     "complex to maintain incrementally; (c) blockchain — over-"
     "engineered. (a) rejected for insertion/deletion blindness; "
     "(b) rejected for incremental complexity; (c) rejected for "
     "operational cost.",
     "Append is now sequential: entry N cannot be written until entry "
     "N-1's hash is known. This bounds append throughput to the "
     "single-threaded hash computation rate (~50k/s on modern hardware, "
     "well above the 5k/s NFR target). Verification is O(N); daily "
     "verifier scans must be partitioned for very large logs.",
     "Phase 1: implemented as a stub contract. Phase 8: red-team test "
     "that modifies a past entry's payload and verifies the daily "
     "verifier detects it. Phase 9: publish chain head to S3 Object "
     "Lock and verify external detection. Phase 10: load-test "
     "concurrent appends; verify hash chain integrity under contention."),

    (8, "DEC-0008", "Idempotency keys on all mutations",
     "Architecture Lead", "Phase1",
     "Distributed systems retry. Without idempotency, a retried request "
     "can double-charge a customer or double-post a ledger entry. "
     "Customer pain (Pain-REQ-0011) confirms this is a top concern for "
     "integrators. NFR §2.4 mandates 100% of mutating endpoints "
     "idempotent.",
     "Every mutating API endpoint accepts an idempotency key (header "
     "`Idempotency-Key`). The reliability context (see "
     "domain-boundaries.md §6) deduplicates requests within the key's "
     "lifetime (default 24h) and returns the original response on "
     "replay. See MB-REQ-0013.",
     "Alternatives considered: (a) client-side deduplication — clients "
     "are unreliable; (b) server-side request-hash deduplication — "
     "fails when clients legitimately send similar but distinct "
     "requests; (c) database unique constraints — protects against "
     "duplicate writes but does not return the original response. "
     "(a) rejected for unreliability; (b) rejected for false positives; "
     "(c) rejected for incomplete semantics.",
     "Idempotency key store must be highly available; loss of the "
     "store causes deduplication failure. Key lifetime (24h) bounds "
     "the replay window; clients with longer retry intervals must "
     "handle 425 Too Early. Storage cost: one row per mutating "
     "request.",
     "Phase 1: implemented as a stub contract. Phase 3: integration "
     "test that submits every mutating endpoint twice with the same "
     "key and asserts identical responses. Phase 8: load-test the "
     "idempotency store at 10k req/s. Phase 11: verify ledger "
     "postings are idempotent end-to-end."),

    (9, "DEC-0009", "Declarative workflow engine",
     "Architecture Lead", "Phase8-10",
     "Customer pain (Pain-REQ-0005) demands configurable approval "
     "workflows without code. Imperative workflow code in services "
     "creates a tight coupling between workflow definition and "
     "deployment cadence. MB-REQ-0007 mandates declarative workflows.",
     "Adopt a declarative workflow engine: workflows are defined as "
     "versioned, immutable documents (DEC-0010) and executed by a "
     "generic engine. Workflow definitions live in a dedicated context "
     "and are independently deployable from the services that host "
     "them.",
     "Alternatives considered: (a) imperative workflow code in "
     "services — couples deployment cadence; (b) embedded BPMN engine "
     "(Camunda, Flowable) — heavyweight, Java-centric; (c) AWS Step "
     "Functions — cloud lock-in. (a) rejected for coupling; (b) "
     "rejected for stack mismatch; (c) rejected for lock-in (risk-"
     "register entry).",
     "Workflow definitions become a new artifact type with its own "
     "versioning, review, and deployment pipeline. The engine is a "
     "SPOF; if it stops, no workflow progresses. Debugging declarative "
     "workflows is harder than imperative code.",
     "Phase 8: prototype the engine with 3 reference workflows "
     "(approval, escalation, parallel branches). Phase 9: load-test "
     "the engine at 1k concurrent workflow instances. Phase 10: "
     "verify rollback semantics when a workflow version is "
     "superseded."),

    (10, "DEC-0010", "Workflow versioning (immutable definitions)",
     "Architecture Lead", "Phase8-10",
     "In-flight workflow instances must complete against the definition "
     "they started under; otherwise, audit and compliance evidence is "
     "ambiguous. Mutating a workflow definition while instances are "
     "running breaks this invariant.",
     "Workflow definitions are immutable and versioned. A new version "
     "is a new document; the old version is retained. In-flight "
     "instances bind to the version they started under. New instances "
     "bind to the latest version by default but may pin to a specific "
     "version explicitly.",
     "Alternatives considered: (a) mutable definitions with "
     "in-flight migration — complex and risky; (b) mutable definitions "
     "with restart-on-change — disrupts in-flight instances; "
     "(c) versioned definitions with mandatory migration — same "
     "complexity as (a). (a) and (c) rejected for complexity; (b) "
     "rejected for disruption.",
     "Storage cost: every workflow definition version is retained "
     "indefinitely. Long-running workflows (days, weeks) pin old "
     "definitions, complicating cleanup. UI must surface which version "
     "an instance is running.",
     "Phase 8: implement versioning; verify that an in-flight "
     "instance completes against its original definition after a new "
     "version is published. Phase 9: penetration test — attempt to "
     "mutate a definition via the admin API. Phase 10: load-test "
     "definition lookup at 5k req/s."),

    (11, "DEC-0011", "Immutable ledger entries (no update, no delete)",
     "Architecture Lead", "Phase11",
     "A financial ledger that allows updates or deletes cannot be "
     "audited. Corrections must be visible as corrections, not as "
     "silent overwrites. This is foundational to the platform's "
     "regulatory posture (FATF, BSA).",
     "Ledger entries are immutable. Corrections are made by posting "
     "compensating entries that reference the original. The net "
     "balance is the sum of all entries, including corrections. There "
     "is no update and no delete API on the ledger.",
     "Alternatives considered: (a) updatable ledger with audit "
     "trigger — corrections invisible in the balance; (b) updatable "
     "ledger with correction markers — fragile; (c) append-only "
     "with hard deletes by admin — invites abuse. (a) and (b) "
     "rejected for auditability; (c) rejected for tamper risk.",
     "Storage cost grows monotonically. Balance computation is O(N) "
     "in entries; materialized balances (DEC-0018 read models) "
     "mitigate. Reversal of an erroneous entry requires a "
     "compensating entry, which inflates gross volume metrics.",
     "Phase 11: implement; verify that compensating entries produce "
     "the same net balance as a deletion would. Phase 11: load-test "
     "balance computation at 10k entries. Phase 12+: verify that "
     "customer deposits compose with immutable entries."),

    (12, "DEC-0012", "Decimal arithmetic for all money",
     "Architecture Lead", "Phase11",
     "Floating-point arithmetic introduces rounding errors that "
     "compound across ledger postings. Financial systems must use "
     "exact decimal arithmetic to avoid these errors. IEEE 754 "
     "decimal types or scaled integers are the standard approaches.",
     "All money values are represented as decimals with explicit "
     "precision (typically 4 decimal places for internal computation, "
     "2 for display). Floating-point is forbidden for money. Rounding "
     "rules are explicit per operation and recorded in audit entries. "
     "In Python: `decimal.Decimal`; in Postgres: `NUMERIC(18, 4)`.",
     "Alternatives considered: (a) integer cents — loses precision "
     "for FX and fractional-cent operations; (b) floating-point with "
     "tolerance — invites bugs; (c) custom Money class with arbitrary "
     "precision — over-engineered. (a) rejected for FX precision; "
     "(b) rejected for bugs; (c) rejected for complexity.",
     "Decimal arithmetic is slower than integer or float; "
     "performance impact is small (~10%) but measurable. "
     "Interoperability with external systems that use float (e.g., "
     "some payment APIs) requires explicit conversion at the "
     "boundary.",
     "Phase 11: implement; verify that a 1-cent rounding test "
     "(repeated 1M times) produces no drift. Phase 11: integration "
     "test with a payment API that uses float; verify boundary "
     "conversion. Phase 11: audit log records the rounding rule "
     "applied per operation."),

    (13, "DEC-0013", "Multi-currency via ISO 4217",
     "Architecture Lead", "Phase11",
     "Currency codes must be standardized for interoperability with "
     "external systems (banks, payment networks, reporting). Ad-hoc "
     "codes invite ambiguity and integration bugs.",
     "All currencies are identified by ISO 4217 three-letter codes. "
     "The platform maintains a currency registry with metadata "
     "(precision, symbol, rounding convention). Custom currencies "
     "are forbidden. The registry is versioned; updates follow ISO "
     "4217 amendments.",
     "Alternatives considered: (a) ad-hoc codes — ambiguity; (b) "
     "ISO 4217 numeric codes — less readable; (c) custom registry "
     "with ISO aliases — complexity. (a) rejected for ambiguity; "
     "(b) rejected for readability; (c) rejected for complexity.",
     "ISO 4217 updates require registry versioning and migration. "
     "Historical transactions must retain the currency metadata "
     "that was in effect at transaction time (e.g., precision "
     "changes for currency redenominations).",
     "Phase 11: implement the registry; verify that all ISO 4217 "
     "currencies are present. Phase 11: integration test with a "
     "payment API; verify currency code interop. Phase 11: "
     "redenomination test (simulate a currency precision change)."),

    (14, "DEC-0014", "Tenant as first-class aggregate root",
     "Architecture Lead", "Phase1",
     "Every operation in the platform is scoped to a tenant. Without "
     "a first-class tenant aggregate, scoping leaks into every "
     "service and every model, creating isolation risks (DEC-0003).",
     "Tenant is a first-class aggregate root. Every other aggregate "
     "carries a `tenant_id` reference. The tenant is the root of the "
     "authorization graph and the unit of metering, billing, and "
     "audit.",
     "Alternatives considered: (a) tenant as a tag on resources — "
     "no enforcement; (b) tenant as a configuration value — easily "
     "spoofed; (c) tenant implicit in user identity — breaks for "
     "service-to-service calls. (a) rejected for no enforcement; "
     "(b) rejected for spoofing risk; (c) rejected for service auth "
     "gap.",
     "Every aggregate must carry `tenant_id`; this is enforced by "
     "RLS (DEC-0003) but is also a code-level invariant. Tenant "
     "deletion is a multi-step process: disable, archive, purge "
     "(after retention period).",
     "Phase 3: implement the Tenant aggregate; verify that every "
     "subsequent aggregate (User, AuditEntry, etc.) carries "
     "`tenant_id`. Phase 4: red-team test that attempts to create "
     "a resource without a tenant. Phase 8: verify audit log "
     "queries are scoped to the requesting user's tenant."),

    (15, "DEC-0015", "RBAC with delegation chains",
     "Identity Lead", "Phase4-7",
     "Customer pain (Pain-REQ-0012) demands role-based access control "
     "with delegation, so that a senior user can temporarily delegate "
     "a subset of their permissions to another user. Simple role "
     "assignment is insufficient.",
     "Adopt RBAC with delegation chains: a user may delegate a "
     "subset of their permissions to another user, with a chain-depth "
     "limit (default 3). Delegations are revocable. The authorization "
     "check walks the delegation chain at request time.",
     "Alternatives considered: (a) flat RBAC without delegation — "
     "doesn't meet Pain-REQ-0012; (b) ABAC (attribute-based) — more "
     "flexible but harder to audit; (c) delegated OAuth scopes — "
     "OAuth scopes are coarse. (a) rejected for insufficient "
     "capability; (b) rejected for auditability; (c) rejected for "
     "coarseness.",
     "Delegation chain walks are O(depth); performance impact is "
     "small at the default depth limit but grows with depth. "
     "Revocation must propagate; a revoked delegation must immediately "
     "invalidate downstream delegations.",
     "Phase 5: implement; verify that a delegation of depth 4 is "
     "rejected. Phase 5: verify revocation propagates within 1s. "
     "Phase 7: load-test authorization checks at 5k req/s."),

    (16, "DEC-0016", "Feature flags at boundary",
     "Architecture Lead", "Phase1",
     "Feature flags evaluated inside domain logic create testability "
     "and determinism problems (the same input can produce different "
     "outputs depending on flag state). Domain logic must be "
     "deterministic (MB-REQ-0025, NFR §7.2).",
     "Feature flags are evaluated at the boundary (API gateway or "
     "service entry point) and injected into the request context. "
     "Domain logic reads the flag value from the context, never "
     "from a flag client. This preserves determinism (NFR §7.2).",
     "Alternatives considered: (a) flag client in domain — breaks "
     "determinism; (b) compile-time flags — no runtime toggling; "
     "(c) per-tenant configuration instead of flags — too coarse "
     "for gradual rollouts. (a) rejected for determinism; (b) "
     "rejected for inflexibility; (c) rejected for granularity.",
     "Flag evaluation at the boundary adds latency (~1ms typical). "
     "Flag state must be propagated to async contexts (Celery, "
     "webhooks) explicitly. Flag misconfiguration can disable "
     "critical paths.",
     "Phase 1: stub contract. Phase 4: implement; verify that a "
     "domain test passes regardless of flag state (determinism "
     "test). Phase 8: load-test flag evaluation at 10k req/s."),

    (17, "DEC-0017", "Blue/green deployments per tenant",
     "Infrastructure Lead", "Phase2-3",
     "Deploying a new version to all tenants simultaneously creates "
     "blast radius risk: a regression affects everyone at once. "
     "Per-tenant rollouts reduce this risk and align with the "
     "tenant-as-aggregate-root model (DEC-0014).",
     "Deployments are blue/green per tenant. A new version is "
     "deployed alongside the old; tenants are migrated one at a "
     "time (canary first, then full population). Rollback is "
     "per-tenant. The deployment framework records migration state "
     "per tenant.",
     "Alternatives considered: (a) big-bang deployments — maximum "
     "blast radius; (b) canary deployments by percentage of traffic "
     "— not tenant-aligned; (c) feature-flag-gated rollouts — "
     "useful within a version but not a deployment strategy. (a) "
     "rejected for blast radius; (b) rejected for tenant alignment; "
     "(c) rejected for scope.",
     "Two versions of the platform run simultaneously during "
     "rollout; database schema must be backward-compatible across "
     "one version (forward-only migrations, DEC-0019). Operational "
     "complexity: monitoring two versions, debugging cross-version "
     "issues.",
     "Phase 3: implement; verify a single-tenant rollout end-to-end "
     "including rollback. Phase 4: load-test simultaneous two-version "
     "operation. Phase 8: verify that a schema migration is "
     "compatible with both versions."),

    (18, "DEC-0018", "Read models rebuildable from events",
     "Architecture Lead", "Phase8-10",
     "Read models (projections) drift over time as bugs are found "
     "and fixed. Without a rebuild path, drift becomes permanent "
     "and read models diverge from the source of truth (DEC-0001).",
     "All read models are projections from the event log. A rebuild "
     "command exists for each read model that re-derives it from "
     "the event log. Rebuilds are idempotent and may be run at any "
     "time without downtime.",
     "Alternatives considered: (a) read models with manual sync — "
     "drifts; (b) read models with periodic reconciliation — "
     "detects drift but doesn't fix it; (c) read models from a "
     "CDC stream — couples to database internals. (a) rejected for "
     "drift; (b) rejected for no fix; (c) rejected for coupling.",
     "Rebuild is O(N) in event log size; for very large logs, "
     "rebuild takes hours. Rebuilds consume compute and I/O; must "
     "be scheduled. Read models may lag the event log by seconds "
     "during normal operation.",
     "Phase 8: implement; verify that a rebuild produces identical "
     "state to the live read model. Phase 9: load-test rebuild at "
     "10M events. Phase 10: verify zero-downtime rebuild."),

    (19, "DEC-0019", "Schema migrations forward-only",
     "Architecture Lead", "CrossCutting",
     "Down-migrations (rolling back a schema change) are risky in "
     "production: they can destroy data that the new schema "
     "captured. Most teams avoid them, which makes the 'rollback' "
     "path untested and therefore non-existent in practice. "
     "Blue/green deployments (DEC-0017) require forward-only "
     "migrations to maintain two-version compatibility.",
     "Database migrations are forward-only. A migration that needs "
     "to be reversed is reversed by a forward migration that "
     "restores the prior state. Down-migrations are forbidden in "
     "production. This forces schema changes to be additive where "
     "possible. MB-REQ-0021, MB-REQ-0022.",
     "Alternatives considered: (a) bidirectional migrations — "
     "encourages risky down-migrations; (b) no migrations (manual "
     "schema changes) — error-prone; (c) expand-contract pattern "
     "without forward-only constraint — works but easy to violate. "
     "(a) rejected for risk; (b) rejected for error-proneness; "
     "(c) rejected for enforcement gap.",
     "Schema changes are slower: each change requires a forward "
     "migration, deploy, verify, then potentially a cleanup "
     "migration. Storage cost from obsolete columns/tables until "
     "cleanup migration. Developers must learn the expand-contract "
     "pattern.",
     "Phase 3: linter rule that rejects down-migrations. Phase 3: "
     "verify a sample expand-contract migration (add column, "
     "deploy, backfill, drop old column). Phase 8: verify two-"
     "version compatibility (DEC-0017) holds across a migration."),

    (20, "DEC-0020", "Telemetry via OpenTelemetry",
     "Infrastructure Lead", "Phase1",
     "Vendor-locked telemetry (Datadog, New Relic, etc.) creates "
     "switching costs and complicates multi-vendor observability "
     "stacks. A standard instrumentation layer preserves "
     "optionality. MB-REQ-0020 mandates boundary telemetry.",
     "Adopt OpenTelemetry as the sole telemetry library. Spans, "
     "metrics, and logs are emitted via OTel. The exporter is "
     "configurable per environment (Jaeger locally, vendor in "
     "production). All boundary operations emit spans (MB-REQ-0020).",
     "Alternatives considered: (a) Datadog-only — vendor lock-in; "
     "(b) Prometheus + Jaeger separately — works but no unified "
     "instrumentation; (c) custom telemetry library — maintenance "
     "burden. (a) rejected for lock-in; (b) rejected for "
     "fragmentation; (c) rejected for burden.",
     "OTel SDK is still maturing; some language ecosystems have "
     "gaps. Performance overhead (~1–3% CPU) is measurable. "
     "Sampling strategy must be tuned to balance cost and "
     "observability.",
     "Phase 2: stub contract. Phase 3: implement; verify spans "
     "appear in Jaeger. Phase 4: load-test OTel overhead at 10k "
     "req/s. Phase 8: verify 100% boundary coverage (NFR §5.1)."),

    (21, "DEC-0021", "Execution-layer phase grouping (27 stages → 25 phases)",
     "Engineering Lead", "Foundational",
     "The original 27-stage plan had two pairs of stages that the "
     "execution layer regrouped into single phases: (a) MFA + "
     "session management and (b) recon rules + recon runs. Treating "
     "them as separate stages created artificial dependencies and "
     "inflated the phase count. Errata E3 corrected the count from "
     "26 to 25.",
     "Regroup the 27 stages into 25 phases by merging the two pairs "
     "above. The merge is recorded in BLUEPRINT §5 and in errata "
     "E3. The phase table is the single authority for phase "
     "numbering. Phase 2 review (DEC-0021 narrative in "
     "traceability.md §C.3) confirms the regrouping remains valid.",
     "Alternatives considered: (a) keep 27 stages — artificial "
     "dependencies; (b) merge to 24 phases — over-merging, loses "
     "audit trail of the original stages; (c) re-number freely — "
     "breaks external references. (a) rejected for dependencies; "
     "(b) rejected for over-merging; (c) rejected for reference "
     "breakage.",
     "Future stage additions or removals require a new erratum "
     "and a new phase-table version. Phase numbering is now stable; "
     "external documents may cite phase numbers without ambiguity.",
     "Phase 2: errata E3 verified (see docs/errata/v5.2.1-"
     "verification.md). Phase 2: DEC-0021 narrative reviewed and "
     "recorded in traceability.md §C.3. Future phases: monitor "
     "for re-merge or re-split triggers."),
]


def render(adr_num, dec_id, title, owner, scope, ctx, dec, alts, cons, val):
    adr_id = f"ADR-{adr_num:04d}"
    return f"""---
ADR: {adr_id}
Title: {title}
Status: PROPOSED
DEC: {dec_id}
Owner: {owner}
Scope: {scope}
Created: {CREATED}
Last-Reviewed: {LAST_REVIEWED}
Supersedes: ""
Superseded-By: ""
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

{dec_id} → {title}. Owner: {owner}. Status: PROPOSED (Phase 2 review).
Supersede history: none (initial seed). Last reviewed: {LAST_REVIEWED}.

## DEC link

This ADR cites {dec_id} per the ADR-DEC mapping law (DEC-0023, errata E7).
The DEC row is in `docs/requirements/traceability.md` §C. The mapping is
1:1: {dec_id} ↔ {adr_id}.
"""


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for (n, dec, title, owner, scope, ctx, dec_text, alts, cons, val) in ADRS:
        path = OUT_DIR / f"ADR-{n:04d}.md"
        path.write_text(render(n, dec, title, owner, scope, ctx, dec_text, alts, cons, val))
        print(f"wrote {path}")
    print(f"\n{len(ADRS)} ADR stubs regenerated in Nygard format (status PROPOSED).")


if __name__ == "__main__":
    main()
