# Audit Redaction Policy

| Field | Value |
|---|---|
| Document | `docs/architecture/audit-redaction-policy.md` |
| Version | 5.8 (Phase 7) |
| Status | Approved |
| Owner | Privacy Owner |
| Authority | ADR-0037 / DEC-0042; GDPR Art.5(1)(c) data minimization |

This document defines the redaction policy for audit events. Per
ADR-0037, Merkle-style payload hashing enables redaction without
breaking the hash chain.

## 1. Redaction triggers

Per ADR-0037: redaction triggers per policy. Phase 7 adopts **at-read**
redaction as the default:

| Trigger | When | Phase |
|---|---|---|
| at-read | Redact on read based on reader's clearance | Phase 7 (default) |
| at-insert | Redact on insert (irreversible; for high-PII events) | Phase 8+ (per event type) |
| scheduled | Redact aged events (post-retention, pre-archive) | Phase 8+ |

**at-read** is the Phase 7 default because it preserves the original
event for compliance officers while redacting for external auditors.
**at-insert** is irreversible and reserved for events where the PII
has no evidentiary value (e.g., passwords — never logged anyway).
**scheduled** redacts PII after a policy period (e.g., 90 days) while
preserving the event metadata.

## 2. Field-class-to-rule mapping

Sourced from the PII register (`data-classification.md` §2). See
`src/noventra/apps/audit/adapters/redaction.py` for the implementation.

| Rule | Effect | Example fields |
|---|---|---|
| `redact` | Replace value with [REDACTED] | email, full_name, password, ip_address, user_agent |
| `hash` | Replace with SHA-256 hash (for correlation) | ip_address (when correlation needed) |
| `keep` | No redaction | event_type, created_at, hash |

## 3. Clearance levels

Per ADR-0039 / DEC-0044:

| Clearance | Redaction | Who |
|---|---|---|
| tenant_admin | PII redacted (own tenant only) | Tenant admins |
| compliance_officer | No redaction (full access) | Compliance Lead |
| external_auditor | PII redacted (all tenants) | External auditors, service accounts |

## 4. Irreversibility

SHA-256 is one-way. Redacted values cannot be recovered. This is
intentional: redaction is a one-way operation per GDPR Art.5(1)(c)
data minimization. If a value must be recoverable (e.g., for legal
hold), it must NOT be redacted — use the retention policy's legal
hold mechanism instead.

## 5. Redaction is audited

Per ADR-0037: redaction itself is audited via `audit.redaction_applied`
event. The event records: which event was redacted, which fields, by
whom (the reader's clearance), and when. This provides a complete
audit trail of redaction actions.

## 6. Q1-adjacent

Q1 (jurisdictions) affects redaction: some jurisdictions may require
stronger redaction (e.g., full payload redaction for certain event
types) or weaker (e.g., IP address retention for fraud detection).
Until Q1 resolves, the default at-read policy applies.

## 7. Cross-references

- ADR-0037: `docs/adr/ADR-0037.md`
- PII register: `docs/architecture/data-classification.md`
- Redaction implementation: `src/noventra/apps/audit/adapters/redaction.py`
- Clearance model: `docs/adr/ADR-0039.md`
- Q1 (jurisdictions): `docs/requirements/unresolved-decisions.md`
