#!/usr/bin/env python3
"""Generate 21 ADR stubs (ADR-0001 .. ADR-0021) under docs/adr/.

Each stub has:
- YAML front-matter with `DEC: DEC-00XX` citation (mandatory per errata E7
  and DEC-0023).
- Title (matches the DEC title in traceability.md).
- Status (Accepted, matching the DEC status).
- Brief Context section (one paragraph).
- Brief Decision section (one paragraph).
- Reversibility placeholder (filled in Phase 2 per stage-1-handoff.md §4.5).

Run:  python3 /home/z/my-project/scripts/generate_adr_stubs.py
"""

from pathlib import Path

OUT_DIR = Path("/home/z/my-project/docs/adr")

# (adr_num, dec_id, title, status, scope, context_paragraph, decision_paragraph)
ADRS = [
    (1, "DEC-0001", "Adopt event-sourced domain model",
     "Accepted", "Foundational",
     "The platform must support a complete audit trail of every state change, "
     "rebuildable read models, and deterministic replay for compliance and "
     "recovery. Traditional CRUD persistence loses history and complicates "
     "regulatory evidence collection.",
     "Adopt event sourcing as the primary persistence model for domain "
     "aggregates. State changes are recorded as immutable domain events; "
     "aggregates are rebuilt by replaying events. Read models are projections "
     "from the event log and may be rebuilt at any time."),

    (2, "DEC-0002", "Adopt hexagonal architecture (ports and adapters)",
     "Accepted", "Foundational",
     "Domain logic must be testable in isolation, free of framework and "
     "infrastructure coupling. Direct dependencies on ORMs, HTTP frameworks, "
     "or message buses in domain code make tests slow and refactors risky.",
     "Adopt hexagonal architecture: domain logic interacts with the outside "
     "world only through ports (interfaces) defined in the domain layer. "
     "Adapters (database, HTTP, message bus) implement those ports and live "
     "outside the domain. No domain code imports infrastructure."),

    (3, "DEC-0003", "Tenant isolation via row-level security",
     "Accepted", "Phase1",
     "Multi-tenancy must enforce isolation at the data layer so that a bug in "
     "application code cannot leak one tenant's data to another. "
     "Schema-per-tenant and database-per-tenant models raise operational cost "
     "and complicate cross-tenant analytics.",
     "Use a single database with row-level security (RLS) policies keyed on a "
     "tenant_id column. The tenant context is set per request by the identity "
     "service and cannot be overridden by application code. Cross-tenant "
     "synchronous operations are forbidden (MB-REQ-0023)."),

    (4, "DEC-0004", "OIDC for identity federation",
     "Accepted", "Phase4-7",
     "Default tenants require standards-based federation that supports "
     "modern auth flows (authorization code, PKCE, refresh tokens). SAML is "
     "heavy for greenfield tenants and lacks first-class support for mobile "
     "and SPA clients.",
     "Adopt OpenID Connect (OIDC) as the default federation protocol. The "
     "identity service is the sole issuer of auth tokens (MB-REQ-0003) and "
     "supports OIDC authorization-code flow with PKCE for all clients."),

    (5, "DEC-0005", "SAML for enterprise tenancy SSO",
     "Accepted", "Phase4-7",
     "Enterprise tenants often mandate SAML 2.0 for SSO due to existing IdP "
     "investments (Azure AD, Okta, Ping). Supporting only OIDC excludes this "
     "segment.",
     "Support SAML 2.0 as a second-tier federation protocol for enterprise "
     "tenants. SAML assertions are exchanged for the platform's internal "
     "auth tokens at the identity service boundary; downstream code is "
     "unaware of the original protocol."),

    (6, "DEC-0006", "Append-only audit log (no update/delete API)",
     "Accepted", "Phase1",
     "Regulatory regimes (FATF, GDPR, SOC 2) require audit logs to be "
     "tamper-evident and retained for years. An audit log that allows updates "
     "or deletes cannot satisfy tamper-evidence requirements.",
     "The audit service exposes only an append API. There is no update and "
     "no delete API, and no operational procedure that performs deletion. "
     "Retention enforcement is a forward-only archival operation, not a "
     "deletion. See MB-REQ-0004 and Law-REQ-0010."),

    (7, "DEC-0007", "Hash-chain audit log entries",
     "Accepted", "Phase1",
     "Append-only is necessary but not sufficient for tamper-evidence: an "
     "attacker with database access could append a fraudulent entry. A hash "
     "chain makes any modification of past entries detectable on read.",
     "Each audit entry stores its content hash and the hash of the previous "
     "entry: hash_n = SHA256(hash_n-1 || event_n). A daily verifier scans "
     "the chain and alerts on any mismatch. The chain head is published "
     "externally (e.g., to a write-once store) for additional assurance."),

    (8, "DEC-0008", "Idempotency keys on all mutations",
     "Accepted", "Phase1",
     "Distributed systems retry. Without idempotency, a retried request can "
     "double-charge a customer or double-post a ledger entry. Customer pain "
     "(Pain-REQ-0011) confirms this is a top concern for integrators.",
     "Every mutating API endpoint accepts an idempotency key (header "
     "`Idempotency-Key`). The reliability context (see domain-boundaries.md "
     "§6) deduplicates requests within the key's lifetime (default 24h) and "
     "returns the original response on replay. See MB-REQ-0013."),

    (9, "DEC-0009", "Declarative workflow engine",
     "Accepted", "Phase8-10",
     "Customer pain (Pain-REQ-0005) demands configurable approval workflows "
     "without code. Imperative workflow code in services creates a tight "
     "coupling between workflow definition and deployment cadence.",
     "Adopt a declarative workflow engine: workflows are defined as versioned, "
     "immutable documents (DEC-0010) and executed by a generic engine. "
     "Workflow definitions live in a dedicated context and are independently "
     "deployable from the services that host them."),

    (10, "DEC-0010", "Workflow versioning (immutable definitions)",
     "Accepted", "Phase8-10",
     "In-flight workflow instances must complete against the definition they "
     "started under; otherwise, audit and compliance evidence is ambiguous. "
     "Mutating a workflow definition while instances are running breaks "
     "this invariant.",
     "Workflow definitions are immutable and versioned. A new version is a "
     "new document; the old version is retained. In-flight instances bind to "
     "the version they started under. New instances bind to the latest "
     "version by default but may pin to a specific version explicitly."),

    (11, "DEC-0011", "Immutable ledger entries (no update, no delete)",
     "Accepted", "Phase11",
     "A financial ledger that allows updates or deletes cannot be audited. "
     "Corrections must be visible as corrections, not as silent overwrites.",
     "Ledger entries are immutable. Corrections are made by posting "
     "compensating entries that reference the original. The net balance is "
     "the sum of all entries, including corrections. There is no update and "
     "no delete API on the ledger."),

    (12, "DEC-0012", "Decimal arithmetic for all money",
     "Accepted", "Phase11",
     "Floating-point arithmetic introduces rounding errors that compound "
     "across ledger postings. Financial systems must use exact decimal "
     "arithmetic to avoid these errors.",
     "All money values are represented as decimals with explicit precision "
     "(typically 4 decimal places for internal computation, 2 for display). "
     "Floating-point is forbidden for money. Rounding rules are explicit "
     "per operation and recorded in audit entries."),

    (13, "DEC-0013", "Multi-currency via ISO 4217",
     "Accepted", "Phase11",
     "Currency codes must be standardized for interoperability with external "
     "systems (banks, payment networks, reporting). Ad-hoc codes invite "
     "ambiguity and integration bugs.",
     "All currencies are identified by ISO 4217 three-letter codes. The "
     "platform maintains a currency registry with metadata (precision, "
     "symbol, rounding convention). Custom currencies are forbidden."),

    (14, "DEC-0014", "Tenant as first-class aggregate root",
     "Accepted", "Phase1",
     "Every operation in the platform is scoped to a tenant. Without a "
     "first-class tenant aggregate, scoping leaks into every service and "
     "every model, creating isolation risks.",
     "Tenant is a first-class aggregate root. Every other aggregate carries "
     "a tenant_id reference. The tenant is the root of the authorization "
     "graph and the unit of metering, billing, and audit."),

    (15, "DEC-0015", "RBAC with delegation chains",
     "Accepted", "Phase4-7",
     "Customer pain (Pain-REQ-0012) demands role-based access control with "
     "delegation, so that a senior user can temporarily delegate a subset of "
     "their permissions to a junior. Simple role assignment is insufficient.",
     "Adopt RBAC with delegation chains: a user may delegate a subset of "
     "their permissions to another user, with a chain-depth limit. Delegations "
     "are revocable. The authorization check walks the delegation chain at "
     "request time."),

    (16, "DEC-0016", "Feature flags at boundary",
     "Accepted", "Phase1",
     "Feature flags evaluated inside domain logic create testability and "
     "determinism problems (the same input can produce different outputs "
     "depending on flag state). Domain logic must be deterministic "
     "(MB-REQ-0025).",
     "Feature flags are evaluated at the boundary (API gateway or service "
     "entry point) and injected into the request context. Domain logic "
     "reads the flag value from the context, never from a flag client. This "
     "preserves determinism (NFR §7.2)."),

    (17, "DEC-0017", "Blue/green deployments per tenant",
     "Accepted", "Phase2-3",
     "Deploying a new version to all tenants simultaneously creates blast "
     "radius risk: a regression affects everyone at once. Per-tenant "
     "rollouts reduce this risk.",
     "Deployments are blue/green per tenant. A new version is deployed "
     "alongside the old; tenants are migrated one at a time (canary first, "
     "then full population). Rollback is per-tenant. The deployment "
     "framework records migration state per tenant."),

    (18, "DEC-0018", "Read models rebuildable from events",
     "Accepted", "Phase8-10",
     "Read models (projections) drift over time as bugs are found and fixed. "
     "Without a rebuild path, drift becomes permanent and read models "
     "diverge from the source of truth.",
     "All read models are projections from the event log. A rebuild command "
     "exists for each read model that re-derives it from the event log. "
     "Rebuilds are idempotent and may be run at any time without downtime."),

    (19, "DEC-0019", "Schema migrations forward-only",
     "Accepted", "CrossCutting",
     "Down-migrations (rolling back a schema change) are risky in production: "
     "they can destroy data that the new schema captured. Most teams avoid "
     "them, which makes the 'rollback' path untested and therefore "
     "non-existent in practice.",
     "Database migrations are forward-only. A migration that needs to be "
     "reversed is reversed by a forward migration that restores the prior "
     "state. Down-migrations are forbidden in production. This forces "
     "schema changes to be additive where possible."),

    (20, "DEC-0020", "Telemetry via OpenTelemetry",
     "Accepted", "Phase1",
     "Vendor-locked telemetry (Datadog, New Relic, etc.) creates switching "
     "costs and complicates multi-vendor observability stacks. A standard "
     "instrumentation layer preserves optionality.",
     "Adopt OpenTelemetry as the sole telemetry library. Spans, metrics, "
     "and logs are emitted via OTel. The exporter is configurable per "
     "environment (Jaeger locally, vendor in production). All boundary "
     "operations emit spans (MB-REQ-0020)."),

    (21, "DEC-0021", "Execution-layer phase grouping (27 stages → 25 phases)",
     "Accepted", "Foundational",
     "The original 27-stage plan had two pairs of stages that the execution "
     "layer regrouped into single phases: (a) MFA + session management and "
     "(b) recon rules + recon runs. Treating them as separate stages created "
     "artificial dependencies and inflated the phase count.",
     "Regroup the 27 stages into 25 phases by merging the two pairs above. "
     "The merge is recorded in BLUEPRINT §5 and in errata E3. The phase "
     "table is the single authority for phase numbering."),
]


def render(adr_num, dec_id, title, status, scope, context, decision):
    adr_id = f"ADR-{adr_num:04d}"
    return f"""---
ID: {adr_id}
Title: {title}
DEC: {dec_id}
Status: {status}
Scope: {scope}
Date: 2025-10-27
Owner: Architecture Lead
Superseded-By:
---

# {adr_id} — {title}

## Status

{status}. Cites {dec_id} per the ADR-DEC mapping law (DEC-0023, errata E7).

## Context

{context}

## Decision

{decision}

## Consequences

(Phase 2 deliverable. To be expanded in the ADR full-section pass per
`stage-1-handoff.md` §1.2 and §4.5. Must include a Reversibility paragraph
assessing the cost of reversing this decision.)

## Reversibility

(Phase 2 deliverable. Assess the cost of reversal: data migration cost,
code refactor cost, operational risk. Flag high-reversal-cost ADRs for
Architecture Lead review.)
"""


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for (n, dec, title, status, scope, ctx, dec_text) in ADRS:
        path = OUT_DIR / f"ADR-{n:04d}.md"
        path.write_text(render(n, dec, title, status, scope, ctx, dec_text))
        print(f"wrote {path}")
    print(f"\n{len(ADRS)} ADR stubs generated.")


if __name__ == "__main__":
    main()
