# Break-Glass Admin — BYPASSRLS Workflow

| Field | Value |
|---|---|
| Document | `docs/architecture/break-glass-admin.md` |
| Version | 5.6 (Phase 5) |
| Status | Approved |
| Owner | Security Lead |
| Authority | DEC-0003 §3.3; Phase 5 spec output #9 |

This document defines the break-glass admin workflow for operations
that must bypass RLS (e.g., cross-tenant support, migration fixes,
emergency data correction). Per DEC-0003, the `noventra_admin` role
has `BYPASSRLS` and is used ONLY via this workflow.

## 1. The noventra_admin role

| Property | Value |
|---|---|
| Role name | `noventra_admin` |
| LOGIN | NO (no direct login) |
| BYPASSRLS | YES |
| Granted to | No login role by default. Granted temporarily via the break-glass workflow. |

The role is created in the Phase 5 tenancy migration
(`src/noventra/apps/tenancy/migrations/0001_initial.py`).

## 2. Break-glass workflow

### 2.1 Initiation

1. An operator identifies a situation requiring BYPASSRLS (e.g.,
   cross-tenant data correction, migration fix).
2. The operator opens a break-glass request in the ops tooling
   (Phase 5 stub: ticket in the issue tracker).
3. The request specifies: reason, target table(s), time bound
   (max 1 hour), approver.

### 2.2 Dual-control approval

1. A second operator (the approver) reviews the request.
2. The approver must be a different person from the initiator
   (separation of duties).
3. The approver approves or rejects. Approval is recorded in the
   audit log.

### 2.3 Time-bound grant

1. On approval, the `noventra_admin` role is GRANTed to the
   operator's login role for the specified time bound.
2. The grant is recorded in the audit log with: initiator, approver,
   reason, expiry time.
3. A background job (Phase 5 stub: cron) REVOKEs the grant when the
   time bound expires.

### 2.4 Heavy audit logging

Every query executed while the `noventra_admin` role is active is
logged with:

- Operator identity (login role).
- Break-glass request ID.
- SQL text.
- Affected table(s).
- Row count.
- Timestamp.

The audit log is append-only (DEC-0006) and reviewed by the Security
Lead within 24 hours of every break-glass event.

### 2.5 Post-use review

Within 24 hours of the break-glass grant expiring:

1. The Security Lead reviews the audit log.
2. The Security Lead verifies that every query was within the scope
   of the approved request.
3. Any out-of-scope queries are escalated as a security incident
   (Law-REQ-0016 breach notification may apply).

## 3. Application-side enforcement

The application does NOT use `noventra_admin` for normal requests.
The break-glass workflow is for operations only (DBA, ops engineer
with a database client). The Django app always connects as
`noventra_app` (NOBYPASSRLS).

Phase 5 stub: the break-glass workflow is documented but not yet
automated. The GRANT/REVOKE is performed manually by the DBA.
Phase 6+ adds automated tooling (ops console).

## 4. Test coverage

The test suite includes a break-glass audit test
(`tests/test_break_glass.py`) that verifies:

1. The `noventra_admin` role exists with BYPASSRLS.
2. A query using `noventra_admin` can read cross-tenant rows.
3. A query using `noventra_app` (normal) cannot read cross-tenant
   rows (RLS enforced).
4. The audit log records the break-glass event.

## 5. Cross-references

- DEC-0003 (RLS): `docs/requirements/traceability.md` §C
- ADR-0003 (tenant isolation via RLS): `docs/adr/ADR-0003.md`
- Audit log (DEC-0006): `docs/adr/ADR-0006.md`
- RLS role model: `docs/stage-handoffs/stage-02-handoff.md` §3.3
- Linter rule 25: `scripts/check_traceability.sh`
