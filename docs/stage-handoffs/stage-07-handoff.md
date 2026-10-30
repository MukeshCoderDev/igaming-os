# Stage 07 Handoff — Phase 8 Entry Criteria

| Field | Value |
|---|---|
| Document | `docs/stage-handoffs/stage-07-handoff.md` |
| Version | 5.8 (Phase 7) |
| Status | Approved |
| Owner | Engineering Lead |
| Authority | Phase 7 hard acceptance |

This document defines what Phase 7 hands off to Phase 8, the entry
criteria, and the contracts Phase 8 must honor.

## 1. Phase 7 deliverables handed off

### 1.1 ADRs (5 ACCEPTED in Phase 7)
ADR-0035 (hash-chain), ADR-0036 (AuditEvent schema + taxonomy),
ADR-0037 (redaction + Merkle), ADR-0038 (insert-only enforcement),
ADR-0039 (audit read API + clearance model). All with multi-approvers.

### 1.2 Audit data model + hash chain
- `audit/domain/` — aggregates, event_types (closed catalog: 23 types
  across auth/tenancy/rbac/audit/security), ports.
- `audit/adapters/orm.py` — AuditEvent (partitioned) + AuditChainHead.
- `audit/migrations/0001_initial.py` — partitioned table + BEFORE INSERT
  trigger (SHA-256 + Merkle) + BEFORE UPDATE/DELETE trigger (insert-only)
  + RLS + grants (INSERT+SELECT only).
- `audit/adapters/redaction.py` — Merkle-style payload hashing,
  field-class-to-rule mapping, clearance-based redaction.

### 1.3 Audit middleware + read API
- `middleware/audit.py` — emits audit events on mutations + reads;
  meta-audit cut-off.
- `audit/api/views.py` — AuditLogView with clearance model (tenant_admin
  / compliance_officer / external_auditor) + cursor pagination.

### 1.4 Chain verifier
- `core/management/commands/verify_audit_chain.py` — checks hash
  continuity, Merkle payload integrity, timestamp monotonicity, chain
  head consistency. CI-integrated (rule 39).

### 1.5 Docs
- `audit-retention-policy.md` (7y default, partitioning, legal hold,
  archival Q5-blocked).
- `audit-redaction-policy.md` (at-read default, field-class-to-rule,
  irreversibility, redaction audited).

## 2. Contracts Phase 8 must honor

### 2.1 Audit event contract
- Every mutation MUST emit an audit event via `append_audit_event()`.
- Event types MUST come from the closed catalog (`event_types.py`).
- New event types require ADR amendment (ADR-0036).
- `correlation_id` MUST be propagated from Phase 4.

### 2.2 Hash-chain integrity contract
- NEVER UPDATE or DELETE audit_event rows (trigger-enforced).
- The chain verifier MUST pass in CI (rule 39).
- Chain breaks MUST be detected and alerted (audit.chain_break_detected).

### 2.3 Redaction contract
- PII MUST be redacted based on reader's clearance.
- Redaction MUST preserve the Merkle root (field hashes preserved).
- Redaction itself MUST be audited (audit.redaction_applied).

### 2.4 Clearance model contract
- tenant_admin: own tenant only.
- compliance_officer: all events, unredacted.
- external_auditor: all events, redacted.
- Meta-audit cut-off at depth 1 (no infinite recursion).

### 2.5 Inherited contracts (Phase 4-6)
- Error format (problem_response), logging (structured + redaction),
  correlation-ID, RLS (every tenant-scoped table), pgbouncer compat,
  AuthN (JWT), RBAC (closed permission catalog).

## 3. Phase 8 entry criteria
- Phase 0 gate passed (Q1/Q2/Q4/Q5).
- Phase 7 hard acceptance met (migrations, insert-only, chain verifier,
  redaction, clearance, events audited, 5 ADRs ACCEPTED, privacy owner
  ratified, rules 1-43 green, coverage ≥85%).
- Linter green on rules 1-43.

## 4. Phase 8 scope (preview)
- Ledger primitives (DEC-0011 immutable entries, DEC-0012 decimal money,
  DEC-0013 multi-currency).
- Monthly partition automation (cron job for audit_event).
- Audit log export endpoint (full bundle generation).
- ADR-0011/0012/0013 → ACCEPTED.
- Coverage 90%@20 (per ADR-0027).

## 5. Handoff sign-off
Engineering Lead, Architecture Lead, Security Lead, Privacy Owner,
Compliance Lead.

## 6. Worklog pointer
`/home/z/my-project/worklog.md` — Phase 7 close-out entry.
