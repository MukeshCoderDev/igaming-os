#!/usr/bin/env python3
"""Generate Phase 6 ADRs: 4 new (0031-0034) ACCEPTED.

Run:  python3 /home/z/my-project/scripts/generate_phase6_adrs.py
"""

from pathlib import Path

OUT_DIR = Path("/home/z/my-project/docs/adr")
LAST_REVIEWED = "2025-10-28"
CREATED = "2025-10-28"

NEW_ADRS = [
    (31, "DEC-0036", "AuthN strategy (JWT JWS + rotating refresh + Argon2id + MFA TOTP + API keys + service JWTs)",
     "Identity Lead", "Phase4-7",
     "Phase 6 introduces authentication for human users, partner integrations, and service accounts. "
     "The strategy must cover: password hashing (Argon2id), JWT access tokens (JWS), rotating refresh "
     "tokens with Redis blacklist, MFA (TOTP + recovery codes), login throttling + lockout, API key "
     "authN for partners, and service-account JWTs with typ=service claim. The strategy must compose "
     "with the Phase 5 tenant middleware (ADR-0029) and the Phase 4 error format (ADR-0026).",
     "Adopt JWT (JWS, HS256 for Phase 6 stub; RS256 in Phase 7 with key rotation) for access tokens "
     "(15min lifetime). Refresh tokens rotate on every use (30d lifetime); old tokens blacklisted in "
     "Redis (refresh_token_blacklist table for durable record). Passwords hashed with Argon2id (params "
     "from env: time_cost=3, memory_cost=64MB, parallelism=4). MFA: TOTP (RFC 6238) + 10 recovery "
     "codes (hashed). Login throttling: 5 failures → 15min lockout (Redis). API keys: hashed in DB, "
     "constant-time comparison. Service JWTs: typ=service claim, no refresh token, short lifetime (1h).",
     "Alternatives: (a) session-based auth (Django sessions) — CSRF + state burden; (b) opaque tokens "
     "(no JWT) — requires DB lookup per request; (c) Bcrypt instead of Argon2id — less modern; (d) "
     "WebAuthn for MFA — Phase 7+ (Q43 scope). (a) rejected for state; (b) rejected for DB overhead; "
     "(c) rejected for modernity; (d) deferred.",
     "JWT signing key management is critical (rotation, revocation). Refresh token blacklisted in Redis "
     "must be TTL'd to avoid unbounded growth. MFA recovery codes must be hashed (not plaintext). "
     "Login throttling can be abused for DoS (attacker locks out a user); mitigated by lockout keyed on "
     "username+IP, not username alone. SMS-based MFA is out of scope (Q44 blocked).",
     "Phase 6: login + refresh + logout endpoints return Phase 4 error format. Phase 6: MFA flow test "
     "(setup, verify, recovery). Phase 6: refresh rotation test (old token blacklisted). Phase 6: "
     "login throttling test (5 failures → lockout). Phase 7: RS256 + key rotation. Phase 7: load-test "
     "JWT verification.",
     "ACCEPTED", "Identity Lead + Security Lead + Architecture Lead"),

    (32, "DEC-0037", "RBAC model (permission-based, closed catalog, baseline roles)",
     "Identity Lead", "Phase4-7",
     "Phase 6 introduces role-based access control with a permission catalog. The catalog must be a "
     "closed enumeration (no ad-hoc permissions). Baseline roles (admin, manager, viewer, service) are "
     "seeded by migration. The model composes with tenant memberships: a user's effective permissions "
     "are the intersection of their membership role (per-tenant) and the permission catalog.",
     "Adopt permission-based RBAC. Permission catalog is a closed enumeration in "
     "src/noventra/apps/identity/domain/permissions.py (frozen-tree-cited path). Each permission has a "
     "code, description, and category. Roles are collections of permissions. Baseline roles seeded by "
     "migration: admin (all permissions), manager (read + write + invite), viewer (read-only), service "
     "(service-only permissions). Tenant memberships carry a role FK. Effective permissions = role's "
     "permissions intersected with the catalog. Custom roles are Phase 7+.",
     "Alternatives: (a) ABAC (attribute-based) — more flexible but harder to audit; (b) flat roles "
     "(no permission catalog) — inflexible; (c) delegated OAuth scopes — coarse; (d) open permission "
     "catalog (ad-hoc) — audit risk. (a) rejected for auditability; (b) rejected for inflexibility; "
     "(c) rejected for coarseness; (d) rejected for audit risk (must be closed).",
     "Permission catalog must be maintained as new endpoints are added. Custom roles (Phase 7+) add "
     "complexity. The (role × endpoint) test matrix grows quadratically; parametrized tests mitigate. "
     "Service role must be distinct from human roles (no human can have service permissions).",
     "Phase 6: permission catalog closed (linter rule 35). Phase 6: baseline roles seeded. Phase 6: "
     "(role × endpoint) test matrix parametrized. Phase 6: cross-tenant denial at user-membership "
     "level. Phase 7: custom roles + permission management UI.",
     "ACCEPTED", "Identity Lead + Architecture Lead + API Lead"),

    (33, "DEC-0038", "Tenant resolution order (JWT claim + X-Tenant-ID + membership validation + switch)",
     "Architecture Lead", "Phase1",
     "Phase 5 introduced tenant resolution (ADR-0029) with JWT claim primary + X-Tenant-ID header "
     "fallback. Phase 6 adds user-tenant membership validation: the resolved tenant must be one the "
     "user is a member of (active membership). Multi-tenant users can switch tenants via a tenant-"
     "switch endpoint that re-issues a JWT with the new tenant claim. The resolution order must be "
     "explicit and documented.",
     "Adopt Option B (JWT claim primary + membership validation + X-Tenant-ID fallback for service "
     "accounts). Resolution order: (1) JWT `tenant_id` claim — validated against tenant_memberships "
     "(active) for human users; (2) X-Tenant-ID header — for service accounts (typ=service JWT) only; "
     "(3) missing/malformed → 400 E_TENANT_MISSING / E_TENANT_INVALID (Phase 5); (4) membership not "
     "found/inactive → 403 E_TENANT_FORBIDDEN. Tenant-switch endpoint: POST /auth/switch-tenant/ "
     "with tenant_id body; re-issues access + refresh JWT with new tenant claim. First-login default "
     "tenant: the user's first active membership (or explicitly set default_tenant on the user).",
     "Alternatives: (a) Option A (header-only) — spoofable; (b) Option C (URL path) — couples tenancy "
     "to routing; (c) Option D (DB lookup per request) — DB overhead. (a) rejected for spoofing; (b) "
     "rejected for coupling; (c) rejected for overhead. Option B chosen for security + flexibility.",
     "JWT claim must be populated by the login flow. Membership validation adds one DB/cache lookup "
     "per request (mitigated by Redis cache). Tenant-switch invalidates the old JWT's tenant context "
     "(old refresh token blacklisted). Multi-tenant users with many memberships need a membership list "
     "endpoint (Phase 7).",
     "Phase 6: tenant resolution extends Phase 5 middleware with membership validation. Phase 6: "
     "tenant-switch endpoint test. Phase 6: multi-tenant user first-login default tenant test. Phase 6: "
     "membership-inactive → 403 test. Phase 7: membership list endpoint + cache.",
     "ACCEPTED", "Architecture Lead + Identity Lead + Security Lead"),

    (34, "DEC-0039", "Service/agent identity model (shadow→live gate + typ=service JWT + endpoint separation)",
     "Identity Lead", "Phase4-7",
     "Phase 6 introduces service/agent identities for non-human callers (internal services, background "
     "workers, the nine delivery agents per DEC-0022). Service identities must be distinct from human "
     "users: they authenticate with typ=service JWTs, cannot use human endpoints, and are subject to "
     "the shadow→live promotion gate from DEC-0022. Defense-in-depth: claim + endpoint + role.",
     "Adopt a service_identity table (UUID PK, name, tenant FK, status [shadow/live], created_at, "
     "promoted_at). Shadow services cannot mutate state (read-only). Promotion to live requires the "
     "DEC-0022 gate (runbook + 3 shadow runs + human approver + rollback). Service JWTs carry "
     "typ=service claim; human JWTs carry typ=bearer. Endpoints are marked human-only or service-only "
     "via a decorator (@human_only / @service_only). Defense-in-depth: claim check + endpoint check + "
     "role check (service role).",
     "Alternatives: (a) service accounts as regular users — no shadow→live gate; (b) no endpoint "
     "separation — relies on role check only; (c) mutual TLS only (no JWT) — no tenant context; (d) "
     "opaque service tokens (no JWT) — requires DB lookup. (a) rejected for no gate; (b) rejected for "
     "weak defense-in-depth; (c) rejected for no tenant context; (d) rejected for DB overhead.",
     "Service identity lifecycle (shadow→live→deprecated) must be managed. Endpoint decorators must be "
     "maintained as new endpoints are added. The nine delivery agents (DEC-0022) each get a service "
     "identity. Shadow services that attempt mutation must be rejected with a clear error. Promotion "
     "gate is manual in Phase 6 (ops console Phase 7+).",
     "Phase 6: service_identity table + migration. Phase 6: typ=service JWT issuance. Phase 6: "
     "@human_only / @service_only decorators. Phase 6: shadow→live gate test (shadow cannot mutate). "
     "Phase 6: agent-vs-human enforcement test. Phase 7: promotion gate automation + ops console.",
     "ACCEPTED", "Identity Lead + Engineering Lead + Security Lead"),
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
