#!/usr/bin/env python3
"""Generate Phase 9 ADRs: 5 new (0047-0051) ACCEPTED.

Run:  python3 /home/z/my-project/scripts/generate_phase9_adrs.py
"""

from pathlib import Path

OUT_DIR = Path("/home/z/my-project/docs/adr")
LAST_REVIEWED = "2025-10-28"
CREATED = "2025-10-28"

NEW_ADRS = [
    (47, "DEC-0052", "Player entity model + User relationship",
     "Product Owner", "Phase4-7",
     "Phase 9 introduces the Player entity — the end-user of a tenant's platform (e.g., a bank's customer). "
     "Players are distinct from Users (Phase 6): a User is an authenticated identity; a Player is the "
     "person the data belongs to. A Player may or may not be linked to a User (e.g., a prospect who hasn't "
     "registered yet). Players are tenant-scoped; multi-tenant player support is a design decision.",
     "Adopt a separate Player entity, optionally linked to User (Phase 6) via a nullable user_uuid FK. "
     "Tenant-scoped (RLS per DEC-0003). Multi-tenant player decision: Phase 9 supports single-tenant "
     "players only (a player belongs to one tenant); multi-tenant players are Phase 10+ (Q61). PII fields "
     "per extended PII register (email, full_name, date_of_birth, phone, address, jurisdiction). Lifecycle "
     "FSM via Phase 8 state machine base (ADR-0044). Every state change emits outbox events (ADR-0040) + "
     "audit events (Phase 7).",
     "Alternatives: (a) Player = User (no separate entity) — conflates identity with person; (b) Player "
     "as a role on User — loses prospect state; (c) multi-tenant players from day 1 — complexity before "
     "need. (a) rejected for conflation; (b) rejected for prospect loss; (c) rejected for complexity.",
     "Player + User relationship requires careful sync (player.user_uuid may be NULL for prospects). "
     "Multi-tenant players (Q61) deferred. PII fields must be redacted per Phase 4 + Phase 7 redaction "
     "policies. Player deletion (right-to-erasure) cascades to consents, login history, etc.",
     "Phase 9: Player model + migration + RLS. Phase 9: lifecycle FSM (8 states). Phase 9: tenant-"
     "scoping test (player in tenant A invisible to tenant B). Phase 10: multi-tenant player evaluation "
     "(Q61).",
     "ACCEPTED", "Product Owner + Architecture Lead + Architect"),

    (48, "DEC-0053", "Consent schema + jurisdiction-aware fields",
     "Product Owner", "Phase4-7",
     "GDPR Art.7 requires demonstrable consent. The consent schema must capture: who consented, to what "
     "purpose, via which channel, when, from what IP/user-agent, and the policy version they consented to. "
     "Jurisdiction-aware extensions are needed for jurisdictions with stricter consent requirements (e.g., "
     "some require double opt-in). The schema must be immutable (revocation creates a new record, not a "
 "mutation).",
     "Adopt a consent schema: id (UUID), player_id (FK), tenant_id, purpose (closed catalog), channel "
     "(matches Phase 8 NotificationChannel), status (granted, revoked, expired, pending), granted_at, "
     "revoked_at, policy_version, consent_text_hash (SHA-256 of the consent text presented), ip_address, "
     "user_agent, correlation_id, created_at. Jurisdiction-aware extensions: jurisdiction field (from "
     "player's jurisdiction), double_opt_in_required (bool), double_opt_in_verified_at. Policy versioning: "
     "policy_version field; re-consent trigger on policy change; grace period documented (Q66); refusal → "
     "consents withdrawn. HUMAN-APPROVED per linter rule 5 (Legal/Regulatory category).",
     "Alternatives: (a) single consent flag (boolean) — insufficient for GDPR; (b) consent as a field on "
     "Player — no history; (c) consent as an event in the audit log — no queryable index. (a) rejected "
     "for GDPR; (b) rejected for no history; (c) rejected for queryability.",
     "Consent schema is complex (12+ fields). Policy versioning requires a policy store (Phase 10+). "
     "Jurisdiction-aware extensions are Q1-blocked (can't finalize without jurisdiction list). Double "
     "opt-in adds UX friction. Consent text hash requires the consent text to be versioned + stored.",
     "Phase 9: Consent model + migration + RLS. Phase 9: consent CRUD API. Phase 9: policy versioning "
     "stub. Phase 10: jurisdiction-aware extensions (Q1 unblock). Phase 10: policy store + re-consent "
     "trigger.",
     "ACCEPTED", "Product Owner + Legal Lead + Privacy Owner + DPO"),

    (49, "DEC-0054", "Consent immutability pattern — hash-chained",
     "Architecture Lead", "Phase4-7",
     "Consents are legal evidence. They must be tamper-evident. Phase 7 built a hash-chain infrastructure "
     "for audit events. Consent records should reuse that infrastructure: hash-chained, insert-only, with "
     "chain break detection. Revocation creates a NEW record (status=revoked), not a mutation of the "
     "original granted record.",
     "Adopt hash-chained consent immutability, reusing Phase 7 infrastructure (ADR-0035 algorithm, scope, "
     "payload, concurrency). Chain scope = per-player (each player has their own consent chain). Chain "
     "verifier extended for consent chains (verify_audit_chain --scope=consent:player_uuid). Chain break "
     "detection applies (audit.chain_break_detected). Revocation: INSERT a new consent record with "
     "status=revoked, revoked_at=NOW(), referencing the original consent_id. The original record is "
     "never UPDATEd or DELETEd (insert-only trigger per ADR-0038).",
     "Alternatives: (a) insert-only without hash chain — no tamper-evidence; (b) hash-chained with "
     "separate infra — duplication; (c) mutable consents with audit trail — tamper risk. (a) rejected "
     "for no tamper-evidence; (b) rejected for duplication; (c) rejected for tamper risk.",
     "Per-player chains add chain head management overhead (one head per player). Chain verifier must "
     "handle many small chains (partitioned by player). Revocation creates 2 records (original + revoked), "
     "increasing storage. Querying 'current consent' requires finding the latest record per (player, "
     "purpose, channel).",
     "Phase 9: consent hash-chain (reuse Phase 7 trigger pattern). Phase 9: chain verifier extended. "
     "Phase 9: revocation test (new record, original unchanged). Phase 9: chain break detection test.",
     "ACCEPTED", "Architecture Lead + Privacy Owner + Security Lead"),

    (50, "DEC-0055", "Player lifecycle FSM — states, transitions, regulatory constraints",
     "Product Owner", "Phase4-7",
     "Players have a regulated lifecycle: prospect → registered → active → suspended → self_excluded → "
     "dormant → closed → deleted. Some transitions have regulatory constraints: self-exclusion has a "
     "cooling-off period (jurisdiction-dependent, Q1-blocked); dormancy is defined by inactivity "
     "(jurisdiction-dependent). Every transition must be audited (Phase 7) and emit outbox events "
     "(Phase 8).",
     "Adopt an 8-state FSM using the Phase 8 state machine base (ADR-0044). States: prospect, registered, "
     "active, suspended, self_excluded, dormant, closed, deleted. Transitions: register (prospect→"
     "registered), activate (registered→active), suspend (active→suspended), reactivate (suspended→"
     "active), self_exclude (active→self_excluded), dormancy_trigger (active→dormant), close (any→closed), "
     "delete (closed→deleted). Regulatory constraints: self_exclude has a cooling-off period (Q1-blocked; "
     "Phase 9 uses 24h default); dormancy_trigger requires inactivity > N days (Q1-blocked; Phase 9 uses "
     "365d default). Every transition: audited (Phase 7) + outbox event (Phase 8). HUMAN-APPROVED per "
     "linter rule 5 (Legal/Regulatory category).",
     "Alternatives: (a) free-form status field (no FSM) — invalid transitions; (b) fewer states (no "
     "self_excluded/dormant) — regulatory gap; (c) separate FSM per jurisdiction — complexity. (a) "
     "rejected for invalid transitions; (b) rejected for regulatory gap; (c) rejected for complexity.",
     "8 states + 8 transitions = complex FSM. Regulatory constraints (cooling-off, dormancy) are Q1-"
     "blocked; Phase 9 uses defaults. Self-exclusion is a serious regulatory action (must not be "
     "reversible during cooling-off). Dormancy may trigger data retention enforcement (ADR-0051).",
     "Phase 9: FSM implemented (Phase 8 base). Phase 9: every transition audited + outbox event. Phase 9: "
     "regulatory constraint tests (self-exclusion cooling-off, dormancy). Phase 10: jurisdiction-specific "
     "constraints (Q1 unblock).",
     "ACCEPTED", "Product Owner + Legal Lead + Architect + Compliance Lead"),

    (51, "DEC-0056", "Retention model + jurisdiction-aware schedule + DSAR + right-to-erasure",
     "Product Owner", "Phase4-7",
     "GDPR Art. 5(1)(e) requires storage limitation. GDPR Art. 15 gives data subjects the right to access "
     "(DSAR). GDPR Art. 17 gives the right to erasure. The retention model must: define a default schedule "
     "per data class, allow jurisdiction overrides, enforce retention via a scheduled job, support legal "
     "hold, and handle archival to cold storage (Q5-blocked).",
     "Adopt a retention model with: (1) default schedule per data class (player profile: 7y after "
     "closure; consent records: 7y after revocation; login history: 2y; audit log: per Phase 7 ADR-0036); "
     "(2) jurisdiction overrides per (data_class, jurisdiction) tuple (Q1-blocked; Phase 9 uses defaults); "
     "(3) right-to-erasure flow (request → verify → erase → audit → respond; cascade to related data); "
     "(4) DSAR flow (request → verify → gather → format → deliver within 30 days; response-time tracking); "
     "(5) retention enforcement job (scheduled, audited); (6) legal hold mechanism (suspends retention "
     "for affected records); (7) archival to cold storage (Q5-blocked, ASSUMED-scaffolding). HUMAN-"
     "APPROVED per linter rule 5 (Legal/Regulatory category).",
     "Alternatives: (a) no retention model (keep forever) — GDPR violation; (b) global retention (no "
     "jurisdiction overrides) — non-compliant in stricter jurisdictions; (c) manual retention (no job) — "
     "error-prone. (a) rejected for GDPR; (b) rejected for jurisdiction variance; (c) rejected for "
     "errors.",
     "Retention schedule is complex (many data classes × many jurisdictions). Right-to-erasure cascade "
     "must carefully handle: player profile, consents, login history, audit log (audit log is NOT erased "
     "— it's retained per Phase 7; the player's identity in audit is redacted instead). DSAR delivery "
     "infrastructure (file format, secure transfer) is Q5-blocked. Archival vendor is Q5-blocked.",
     "Phase 9: retention model + schedule. Phase 9: erase_player + export_player_data + enforce_retention "
     "commands. Phase 9: right-to-erasure + DSAR flow tests. Phase 10: jurisdiction overrides (Q1). "
     "Phase 10: archival vendor (Q5).",
     "ACCEPTED", "Product Owner + Legal Lead + DPO + Compliance Lead"),
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
