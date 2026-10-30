#!/usr/bin/env python3
"""Generate Phase 5 ADRs: 2 new (0029, 0030) ACCEPTED + update ADR-0002 → ACCEPTED.

Run:  python3 /home/z/my-project/scripts/generate_phase5_adrs.py
"""

from pathlib import Path
import re

OUT_DIR = Path("/home/z/my-project/docs/adr")
LAST_REVIEWED = "2025-10-28"
CREATED = "2025-10-28"

NEW_ADRS = [
    (29, "DEC-0034", "Tenant resolution (JWT claim primary + X-Tenant-ID header fallback)",
     "Architecture Lead", "Phase1",
     "Every request to a tenant-scoped endpoint must resolve the active tenant before any DB call. "
     "The tenant identity comes from the authenticated user's JWT (primary) or an X-Tenant-ID header "
     "(fallback for service-to-service or migration scenarios). Missing or malformed tenant identity "
     "must fail fast with 400 before any database query is issued, so RLS never sees a NULL tenant_uuid.",
     "Adopt TenantResolutionMiddleware in src/noventra/middleware/tenant.py. Resolution order: "
     "(1) JWT `tenant_id` claim if present; (2) X-Tenant-ID header if JWT absent or claim missing. "
     "Validate format (UUID v4) and existence (cached tenant lookup). On missing/malformed: 400 "
     "E_TENANT_MISSING / E_TENANT_INVALID via problem_response(). On valid: set contextvar + "
     "SET LOCAL app.tenant_uuid = '<uuid>' on the DB connection. The middleware runs AFTER "
     "CorrelationIdMiddleware so log lines carry both correlation_id and tenant_id.",
     "Alternatives: (a) X-Tenant-ID header only — spoofable; (b) JWT only — breaks service-to-service; "
     "(c) tenant in URL path — couples tenancy to routing; (d) tenant from DB lookup of API key — "
     "extra DB call per request. (a) rejected for spoofing; (b) rejected for service auth; (c) rejected "
     "for coupling; (d) rejected for DB overhead.",
     "Adds one DB round-trip per request for tenant existence check (mitigated by cache). JWT claim "
     "must be populated by the identity service (Phase 6+). X-Tenant-ID header fallback is restricted "
     "to internal service-to-service (mTLS) in production; the middleware trusts the header only when "
     "the request comes from an authenticated internal caller.",
     "Phase 5: middleware 400s before DB on missing/malformed (test). Phase 5: cross-tenant read = "
     "zero rows; write = 403 E_TENANT_FORBIDDEN (test). Phase 6: JWT claim populated by identity "
     "service. Phase 7: load-test tenant lookup cache hit rate.",
     "ACCEPTED", "Architecture Lead + Security Lead + API Lead"),

    (30, "DEC-0035", "pgbouncer compatibility (transaction-mode; SET LOCAL only)",
     "Infrastructure Lead", "Phase1",
     "Phase 5 introduces pgbouncer for connection pooling (R-SCL-02 risk; Q30 selection). pgbouncer "
     "in transaction-mode breaks session-level features: SET (without LOCAL), session cursors, "
     "prepared statements, and advisory locks. The Django app must use only transaction-safe patterns.",
     "Adopt pgbouncer in transaction-mode. Constraints: (1) SET LOCAL only (never bare SET) — the "
     "tenant middleware uses SET LOCAL app.tenant_uuid; (2) no session cursors — use server-side "
     "cursors only within a single transaction; (3) ATOMIC_REQUESTS=True or explicit atomic blocks — "
     "no implicit multi-statement transactions; (4) prepare_threshold=None on psycopg connection — "
     "disables prepared statements; (5) no LISTEN/NOTIFY (session-level). Document all constraints "
     "in docs/architecture/pgbouncer-compatibility.md. pgbouncer added to local docker-compose.yml.",
     "Alternatives: (a) pgbouncer session-mode — loses pooling benefits; (b) Pgcat — less mature; "
     "(c) Odyssey — fewer features; (d) no pooler — R-SCL-02 ceiling unmitigated. (a) rejected for "
     "pooling loss; (b) and (c) rejected for maturity/features; (d) rejected for unmitigated risk.",
     "Developers must learn transaction-safe patterns. Some Django features (e.g., postgresql "
     "FTS with session-level GIN config) are unavailable. Debugging is harder (no session state). "
     "prepare_threshold=None has a small perf cost (~5%).",
     "Phase 5: pgbouncer test passes against local compose instance (read/write/rollback/recycle). "
     "Phase 5: SET LOCAL app.tenant_uuid works under pgbouncer (test). Phase 6: load-test connection "
     "pool hit rate. Phase 8: verify audit log append works under pgbouncer.",
     "ACCEPTED", "Infrastructure Lead + Architecture Lead + Reliability Lead"),
]

UPDATE_ADRS = [
    (2, "Architecture Lead + Engineering Lead"),
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


def update_existing(adr_num, approver):
    adr_id = f"ADR-{adr_num:04d}"
    path = OUT_DIR / f"{adr_id}.md"
    text = path.read_text()
    text = re.sub(r'^Status: PROPOSED$', 'Status: ACCEPTED', text, flags=re.MULTILINE)
    text = re.sub(r'^Last-Reviewed: .*$',
                  f'Last-Reviewed: {LAST_REVIEWED}', text, flags=re.MULTILINE)
    if 'Approver:' not in text:
        text = re.sub(r'^(Superseded-By: ".*")$',
                      f'\\1\nApprover: {approver}', text, flags=re.MULTILINE)
    else:
        text = re.sub(r'^Approver: .*$', f'Approver: {approver}',
                      text, flags=re.MULTILINE)
    path.write_text(text)
    print(f"updated {path} (status → ACCEPTED, approver → {approver})")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for (n, dec, title, owner, scope, ctx, dec_text, alts, cons, val,
         status, approver) in NEW_ADRS:
        path = OUT_DIR / f"ADR-{n:04d}.md"
        path.write_text(render_new(n, dec, title, owner, scope, ctx, dec_text,
                                    alts, cons, val, status, approver))
        print(f"wrote {path} (status={status})")
    for (n, approver) in UPDATE_ADRS:
        update_existing(n, approver)
    print(f"\n{len(NEW_ADRS)} new ADRs + {len(UPDATE_ADRS)} updated ADRs.")


if __name__ == "__main__":
    main()
