#!/usr/bin/env python3
"""Generate Phase 7 ADRs: 5 new (0035-0039) ACCEPTED.

Run:  python3 /home/z/my-project/scripts/generate_phase7_adrs.py
"""

from pathlib import Path

OUT_DIR = Path("/home/z/my-project/docs/adr")
LAST_REVIEWED = "2025-10-28"
CREATED = "2025-10-28"

NEW_ADRS = [
    (35, "DEC-0040", "Hash-chain architecture (SHA-256, hybrid scope, Merkle-style payload)",
     "Architecture Lead", "Phase1",
     "The audit log must be tamper-evident: any modification of a past entry must be detectable on "
     "read. Append-only (DEC-0006) prevents API-level modification but not direct DB access. A hash "
     "chain makes any past modification detectable. The chain must work under pgbouncer transaction-mode "
     "(Phase 5 ADR-0030) and support redaction without breaking the chain (Phase 7 ADR-0037).",
     "Adopt SHA-256 hash chaining. Chain scope = hybrid: per-tenant chains for tenant-scoped events + "
     "a global chain for system events (auth.*, security.*). Payload hashing = Merkle-style: each "
     "payload field is hashed individually, and the field hashes are combined into a Merkle root; this "
     "allows redacting individual fields without breaking the chain (only the redacted field's hash is "
     "preserved). Trigger = BEFORE INSERT on audit_event: computes hash = SHA256(prev_hash || "
     "merkle_root || event_meta). Chain head stored in audit_chain_head (singleton per scope). "
     "Concurrency: use INSERT ... RETURNING with a table-level lock on audit_chain_head (pgbouncer-"
     "compatible; short critical section).",
     "Alternatives: (a) single global chain — bottleneck; (b) per-event chains (no chain) — no tamper-"
     "evidence; (c) signed entries only (no chain) — doesn't detect insertion/deletion; (d) external "
     "transparency log — over-engineered; (e) bare SHA-256 (not Merkle) — can't redact without breaking "
     "chain. (a) rejected for bottleneck; (b) rejected for no tamper-evidence; (c) rejected for insertion "
     "blindness; (d) rejected for complexity; (e) rejected for redaction incompatibility.",
     "SHA-256 is current standard; migration plan if compromised: add a new chain with SHA-3 (or whatever "
     "is current) and cross-sign the old chain head into the new chain. Append is serialized per scope "
     "(table-level lock on chain head); throughput bounded by hash computation (~50k/s, well above NFR "
     "§3.3 target of 5k/s). Verification is O(N) per scope; scheduled verifier must partition.",
     "Phase 7: chain verifier passes in CI (rule 39). Phase 7: concurrent insert test (10 parallel "
     "appends; all hashes valid). Phase 7: break detection test (modify a past entry → verifier detects). "
     "Phase 8: load-test at 5k events/s sustained. Phase 24: external chain-head publication (transparency "
     "log).",
     "ACCEPTED", "Architecture Lead + Security Lead + Reliability Lead"),

    (36, "DEC-0041", "AuditEvent schema + partitioning + event type taxonomy",
     "Architecture Lead", "Phase1",
     "The audit log needs a stable schema that supports: tenant-scoped + global events, human vs service "
     "actors (Phase 6 distinction), a closed event type catalog, JSON payload, hash chain fields, and "
     "partitioning for retention (7-year default, jurisdiction-dependent). The schema must compose with "
     "the hash chain (ADR-0035) and redaction (ADR-0037).",
     "AuditEvent schema: UUID PK, tenant_id (NULL for global events), actor_id, actor_type (human|service), "
     "event_type (closed catalog), target_type, target_id, payload (JSONB), prev_hash, hash, "
     "correlation_id (from Phase 4), created_at (DB now()). Partitioning: by month + tenant (PARTITION BY "
     "RANGE (created_at) with sub-partitioning by tenant_id LIST). Event type taxonomy: closed catalog "
     "seed covering auth.*, tenancy.*, rbac.*, audit.*, security.* events. New types require ADR "
     "amendment. Catalog at src/noventra/apps/audit/domain/event_types.py (frozen-tree-cited path).",
     "Alternatives: (a) single table (no partitioning) — unmanageable at 7-year retention; (b) per-tenant "
     "tables — operational explosion; (c) open event type catalog (ad-hoc strings) — audit risk; (d) "
     "protobuf payload (not JSONB) — harder to query. (a) rejected for retention; (b) rejected for "
     "operational cost; (c) rejected for audit risk; (d) rejected for queryability.",
     "Partitioning adds DDL complexity (monthly partition creation must be automated). Closed catalog "
     "requires ADR amendment for new types (intentional friction). JSONB payload is flexible but not "
     "type-safe; the event type catalog mitigates. created_at uses DB now() (not app time) for tamper-"
     "resistance.",
     "Phase 7: migration creates audit_event (partitioned) + audit_chain_head. Phase 7: event type "
     "catalog closed (linter rule 40). Phase 7: baseline partition for current month. Phase 8: monthly "
     "partition automation (cron). Phase 8: load-test insert at 5k/s.",
     "ACCEPTED", "Architecture Lead + Compliance Lead + API Lead"),

    (37, "DEC-0042", "Redaction policy + Merkle-style payload hashing",
     "Privacy Owner", "Phase1",
     "Audit events contain PII (actor identity, target identity, payload details). Per GDPR + the PII "
     "register (data-classification.md), PII must be redactable. But redaction must not break the hash "
     "chain (ADR-0035). Standard hash chaining hashes the full payload; redacting a field would change "
     "the hash and break the chain. Merkle-style hashing solves this: each field is hashed individually, "
     "and only the redacted field's hash is preserved (the value is replaced with [REDACTED]).",
     "Adopt Merkle-style payload hashing. Each payload field is hashed: field_hash = SHA256(field_name || "
     "field_value). The Merkle root = SHA256(concatenation of all field_hashes in canonical order). The "
     "chain hash (ADR-0035) uses the Merkle root. Redaction: replace the field VALUE with [REDACTED] but "
     "PRESERVE the field_hash. Verification: recompute field_hash from the (now redacted) value — it "
     "won't match, but the preserved field_hash proves the original value was consistent at insert time. "
     "Field-class-to-rule mapping from the PII register (data-classification.md). Irreversibility: "
     "SHA-256 is one-way. Redaction itself is audited via audit.redaction_applied event.",
     "Alternatives: (a) no redaction (full payload retained) — GDPR violation; (b) redaction breaks "
     "chain — defeats tamper-evidence; (c) encrypt-then-redact (reversible) — key management burden + "
     "reversible redaction is not true redaction; (d) separate redacted copy — storage cost + sync. "
     "(a) rejected for GDPR; (b) rejected for tamper-evidence; (c) rejected for reversibility; (d) "
     "rejected for sync.",
     "Merkle-style hashing adds CPU cost per insert (~10% vs bare hashing). Field-level hashes increase "
     "storage (~2x payload size). Redaction policy must be maintained as new event types are added. "
     "Irreversibility means redacted data is gone forever (no legal hold recovery — mitigated by "
     "retention policy: redact after retention period, not before).",
     "Phase 7: redaction preserves chain integrity test (redact a field → verifier still passes). "
     "Phase 7: every PII class has a rule (linter rule 41). Phase 7: redaction itself audited "
     "(audit.redaction_applied event). Phase 8: scheduled redaction job for aged events.",
     "ACCEPTED", "Privacy Owner + DPO + Security Lead"),

    (38, "DEC-0043", "Insert-only enforcement (trigger + GRANT + monitoring)",
     "Security Lead", "Phase1",
     "The audit log must be insert-only (DEC-0006). API-level enforcement (no update/delete endpoint) "
     "is insufficient: an attacker with DB access could UPDATE or DELETE directly. Enforcement must be "
     "at the database level, for all roles including the table owner. Superuser bypass is unavoidable "
     "in PostgreSQL but must be monitored.",
     "Adopt three-layer insert-only enforcement: (1) GRANT INSERT, SELECT only to noventra_app — no "
     "UPDATE/DELETE privilege; (2) BEFORE UPDATE OR DELETE trigger raises exception for all roles "
     "including owner (the trigger uses RAISE EXCEPTION; even the owner can't bypass a trigger); (3) "
     "RULE-based denial as defense-in-depth (CREATE RULE ... DO INSTEAD NOTHING — optional, mitigates "
     "ORM-generated UPDATEs). Superuser bypass: PostgreSQL superuser can bypass triggers; this is "
     "unavoidable but monitored via a separate audit trigger that logs any superuser DML on audit_event "
     "to a separate table (audit_superuser_action).",
     "Alternatives: (a) API-level only (no trigger) — bypassable with DB access; (b) REVOKE all from "
     "owner + GRANT to app only — owner can't manage the table; (c) event-sourcing (no update ever) — "
     "over-engineered for audit log; (d) separate append-only database — operational cost. (a) rejected "
     "for bypass; (b) rejected for management; (c) rejected for complexity; (d) rejected for cost.",
     "Trigger adds ~1ms per statement (negligible). RULE-based denial can mask ORM bugs (an UPDATE that "
     "silently does nothing is confusing). Superuser monitoring adds a separate table + trigger; the "
     "monitoring itself must not be bypassable (separate schema, separate grants).",
     "Phase 7: UPDATE/DELETE raises for all roles test (including owner). Phase 7: superuser bypass "
     "monitoring test. Phase 7: RULE-based denial test (optional). Phase 8: load-test trigger overhead "
     "at 5k inserts/s.",
     "ACCEPTED", "Security Lead + Architecture Lead + Compliance Lead"),

    (39, "DEC-0044", "Audit read API + clearance model + meta-audit cut-off",
     "Architecture Lead", "Phase1",
     "The audit log must be readable for compliance, forensics, and tenant self-service. Different "
     "readers have different clearance: tenant admins see only their own tenant's events; compliance "
     "officers see all events; external auditors see redacted events. The read API itself generates "
     "audit events (audit.read_performed) — but this must not recurse infinitely (a meta-meta-audit "
     "event for the read of the read event).",
     "Adopt a clearance model with three levels: (1) tenant_admin — sees events where tenant_id = "
     "requesting user's tenant; (2) compliance_officer — sees all events (unredacted); (3) "
     "external_auditor — sees all events but with PII redacted per ADR-0037. Cursor-based pagination "
     "(no offset; cursor = (created_at, event_uuid)). Filtering by event_type, actor_id, target_id, "
     "time range, correlation_id. Meta-audit cut-off: the audit.read_performed event is itself audited, "
     "but the audit of a read does NOT generate a further audit event (cut-off at depth 1). Implemented "
     "via a context flag (audit._meta_audit_depth) that prevents recursion.",
     "Alternatives: (a) offset-based pagination — slow at high offsets; (b) no clearance model (all "
     "readers see all) — security risk; (c) infinite meta-audit recursion — unbounded growth; (d) no "
     "meta-audit (reads not audited) — repudiation risk. (a) rejected for performance; (b) rejected "
     "for security; (c) rejected for unbounded growth; (d) rejected for repudiation.",
     "Cursor pagination requires stable sort (created_at + event_uuid). Compliance officer role must be "
     "distinct from tenant admin (no tenant admin should see cross-tenant). External auditor redaction "
     "adds CPU per read. Meta-audit cut-off is a deliberate information loss (the audit of a read is "
     "audited, but the audit of that audit is not — acceptable trade-off).",
     "Phase 7: clearance model enforcement test (tenant admin sees only own; compliance sees all; "
     "external auditor sees redacted). Phase 7: meta-audit cut-off test (read generates 1 audit event, "
     "not 2). Phase 7: cursor pagination test. Phase 8: load-test read at 100 concurrent queries.",
     "ACCEPTED", "Architecture Lead + Compliance Lead + Privacy Owner"),
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


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for (n, dec, title, owner, scope, ctx, dec_text, alts, cons, val,
         status, approver) in NEW_ADRS:
        path = OUT_DIR / f"ADR-{n:04d}.md"
        path.write_text(render_new(n, dec, title, owner, scope, ctx, dec_text,
                                    alts, cons, val, status, approver))
        print(f"wrote {path} (status={status})")
    print(f"\n{len(NEW_ADRS)} new ADRs.")


if __name__ == "__main__":
    main()
