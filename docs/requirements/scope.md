# Scope — Increment 1 (Phase 1)

| Field | Value |
|---|---|
| Document | `docs/requirements/scope.md` |
| Version | 5.2 |
| Status | Approved |
| Owner | Architecture Lead |
| Authority | BLUEPRINT §2, §9 |
| Single pointer | Workflow-level triage lives in `triage-table.md`. |

This document is the **single authority** for Increment 1 capability
scope. Workflow-level triage is delegated to `triage-table.md`, which
is the only document allowed to list workflow-level in/out decisions.
Any capability or workflow not listed in either document is implicitly
out of Increment 1.

## 1. In-scope capabilities (Phase 1)

Increment 1 delivers four capability areas. Each is described below
with its primary REQs and DECs.

### 1.1 Tenancy

The platform is multi-tenant from day one. Each customer institution
is a tenant with isolated data and isolated configuration. Tenancy is
enforced at two layers: the data layer (row-level security per
DEC-0003) and the compute layer (no cross-tenant synchronous calls per
DEC-0003 / MB-REQ-0002). Tenant is a first-class aggregate root per
DEC-0014. The tenant object is the root of all authorization scopes
and is the entity against which all metering, billing, and audit is
attributed.

Primary REQs: MB-REQ-0001, MB-REQ-0002, MB-REQ-0023.
Primary DECs: DEC-0003, DEC-0014.
Pain REQs addressed: Pain-REQ-0002 (self-serve provisioning).

### 1.2 Identity

The identity service is the sole issuer of authentication tokens
(MB-REQ-0003). Federation uses OIDC (DEC-0004) for default tenants and
SAML (DEC-0005) for enterprise tenants requiring SSO. Role-based
access control with delegation chains (DEC-0015) is delivered in
Phase 4–7, but the identity service primitives (token issuance, token
verification, session lifecycle) are part of the Phase 1 reliable
core so that downstream phases can build on a stable foundation.

Primary REQs: MB-REQ-0003, Pain-REQ-0003, Pain-REQ-0012.
Primary DECs: DEC-0004, DEC-0005, DEC-0015.

### 1.3 Audit

The audit service is append-only (DEC-0006, MB-REQ-0004). Audit
entries are hash-chained (DEC-0007) so that any tampering is
detectable. Query and export endpoints exist in Phase 1; the
compliance-team UI for real-time audit visibility (Pain-REQ-0004) is
delivered in Phase 8–10 against the Phase 1 query API.

Primary REQs: MB-REQ-0004, Law-REQ-0010, Pain-REQ-0004.
Primary DECs: DEC-0006, DEC-0007.

### 1.4 Reliable Core

The reliable core is the substrate on which all later phases build. It
comprises: idempotency keys at the API gateway (DEC-0008,
MB-REQ-0013), backpressure signals (MB-REQ-0014), circuit breakers on
outbound calls (MB-REQ-0015), externalized configuration (DEC-0016,
MB-REQ-0018), feature flags evaluated at the boundary (DEC-0016,
MB-REQ-0019), telemetry via OpenTelemetry (DEC-0020, MB-REQ-0020),
and event emission on every state change (DEC-0001, MB-REQ-0012).
Together these form the "reliable core" guarantee: a request that
reaches the system either completes exactly once, fails visibly, or is
rejected with a deterministic error.

Primary REQs: MB-REQ-0012, MB-REQ-0013, MB-REQ-0014, MB-REQ-0015,
MB-REQ-0018, MB-REQ-0019, MB-REQ-0020, Pain-REQ-0008, Pain-REQ-0010,
Pain-REQ-0011.
Primary DECs: DEC-0001, DEC-0008, DEC-0016, DEC-0020.

## 2. Out-of-scope capabilities (Increment 1)

The following capabilities are explicitly out of Increment 1. Each is
assigned a target phase per DEC-0021 and the triage rule
(BLUEPRINT §9).

| Capability | Target phase | Authority |
|---|---|---|
| Ledger primitives (postings, balances, double-entry) | Phase 11 | DEC-0011; errata E4 |
| First customer deposit | Phase 12+ | Errata E4 |
| KYC vendor integration | Increment 2 | Open question Q6 |
| Sanctions/PEP screening runtime | Increment 2 | Open question Q7 |
| Payment instruction execution | Increment 3 | DEC-0021 (phase plan) |
| FX conversion | Increment 3 | DEC-0021 (phase plan) |
| Reconciliation engine | Phase 22 | DEC-0021 (merge of stages 22+23) |
| Reporting and regulatory filings | Phase 23+ | DEC-0021 |

If a Phase 11+ capability is later found to be a prerequisite for a
Phase 1 deliverable, the prerequisite must be split per the triage
rule (BLUEPRINT §9): extract the Phase 1-relevant slice as a new REQ
with a Phase 1 scope, leave the original at its later scope, and
record the split in `traceability.md` §D.

## 3. Single pointer for workflow-level triage

Workflow-level triage is delegated to `triage-table.md`. This document
does not list workflows. The triage table is the only document that
may. Any workflow not present in `triage-table.md` is implicitly out
of Increment 1; no work may begin on such a workflow until it is
added to the table.

## 4. Out-of-scope categories (always)

The following are out of scope for the entire programme, not just
Increment 1, and are listed here for completeness:

- The provider does not take deposits on its own balance sheet
  (DEC-0024). Deposits are customer-tenant operations on customer
  balance sheets, enabled by Phase 12+ workflows.
- The provider does not lend. Lending is a customer-tenant workflow,
  not a provider capability.
- The provider does not issue currency. Stablecoin issuance, token
  minting, or any form of monetary issuance is explicitly excluded.
- The provider does not act as a counterparty to customer trades.
  Matching engines, order books, and market-making are excluded.

These exclusions flow from DEC-0024 (business model Option A) and
are not subject to triage.
