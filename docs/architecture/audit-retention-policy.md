# Audit Retention Policy

| Field | Value |
|---|---|
| Document | `docs/architecture/audit-retention-policy.md` |
| Version | 5.8 (Phase 7) |
| Status | Approved |
| Owner | Compliance Lead |
| Authority | Law-REQ-0009; ADR-0036 / DEC-0041 |

This document defines the retention policy for audit events. Per
Law-REQ-0009, the floor is 5 years; the default is 7 years. The
maximum is 7 years unless a jurisdiction requires longer (Q1-blocked).

## 1. Retention periods

| Event category | Default retention | Jurisdiction floor | Max |
|---|---|---|---|
| auth.* | 7 years | 5y (FATF Rec.11) | 7y (jurisdiction may extend) |
| tenancy.* | 7 years | 5y | 7y |
| rbac.* | 7 years | 5y | 7y |
| audit.* | 7 years | 5y | 7y |
| security.* | 7 years | 5y | 10y (recommended for breach records) |

**Q1-blocked:** jurisdiction-specific retention periods (e.g., some
jurisdictions require 10 years for financial records). Until Q1 is
resolved, the 7-year default applies.

## 2. Partitioning strategy

Per ADR-0036: audit_event is partitioned by RANGE (created_at) into
monthly partitions. Each partition is a separate table
(`audit_event_YYYY_MM`). Phase 7 creates the baseline partition
(2025-10) + a default partition. Phase 8 automates monthly partition
creation via a scheduled job.

## 3. Partition drop = audit event

Dropping a partition (after retention expiry) generates an
`audit.export_generated` event (the partition is exported to cold
storage before drop) + a `security.contract_violation` event if the
drop happens before retention expiry (safety net).

## 4. Legal hold

A legal hold suspends retention enforcement for affected events.
Implementation (Phase 8+):

1. A `legal_hold` table records: event_uuid or partition_name,
   hold_reason, held_by, hold_until.
2. The partition-drop job checks `legal_hold` before dropping; if a
   hold is active, the partition is skipped.
3. Legal holds are audited (`audit.read_performed` with
   `target_type=legal_hold`).

## 5. Archival to cold storage

Per Q5-blocked: archival vendor (S3 Glacier, GCS Coldline, Azure
Archive) is Q5-blocked ASSUMED-scaffolding. Phase 7 specifies the
interface; Phase 8 implements once Q5 resolves.

Archival process:
1. Partition reaches retention expiry.
2. Export the partition to cold storage (JSONL + manifest).
3. Verify the export (checksums).
4. Emit `audit.export_generated` event.
5. Drop the partition (generates a final audit event in the current
   partition).

## 6. Cross-references

- Law-REQ-0009: `docs/requirements/traceability.md` §B.1
- ADR-0036: `docs/adr/ADR-0036.md`
- Partitioning: `src/noventra/apps/audit/migrations/0001_initial.py`
- Q1 (jurisdictions): `docs/requirements/unresolved-decisions.md`
- Q5 (budget / archival vendor): `docs/requirements/unresolved-decisions.md`
