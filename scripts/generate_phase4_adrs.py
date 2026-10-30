#!/usr/bin/env python3
"""Generate Phase 4 ADRs: 4 new (0025-0028) ACCEPTED + update ADR-0017 → ACCEPTED.

Per amended DEC-0026, approvers for Phase 4 ADRs include reliability/API/QA/
security owners in addition to Architecture Lead.

Run:  python3 /home/z/my-project/scripts/generate_phase4_adrs.py
"""

from pathlib import Path
import re

OUT_DIR = Path("/home/z/my-project/docs/adr")
LAST_REVIEWED = "2025-10-28"
CREATED = "2025-10-28"

# (adr_num, dec_id, title, owner, scope, context, decision, alternatives,
#  consequences, validation_plan, approver)
NEW_ADRS = [
    (25, "DEC-0030", "Structured logging (structlog, JSON Lines, redaction, sampling)",
     "Architecture Lead", "Phase1",
     "Phase 4 requires structured logging that survives machine parsing at scale, "
     "redacts PII and secrets at the logger boundary, and samples noisy endpoints "
     "(health, metrics). Python's stdlib logging is unstructured; ad-hoc formatters "
     "drift between services. NFR §5 (observability) and audit §1.4 require JSON "
     "Lines with required fields.",
     "Adopt structlog with JSON Lines output. Required fields per audit §1.4: "
     "timestamp (ISO 8601 UTC), level, event, logger, correlation_id, tenant_id "
     "(when in request context), request_id, module, line. Redaction at the logger "
     "boundary: PII register (docs/architecture/data-classification.md) is the "
     "source of truth for PII fields; secret redaction by name + regex "
     "(SECRET_KEY, passwords, tokens). 1-in-100 sampling on /health/ and "
     "/metrics/. Package: src/noventra/observability/.",
     "Alternatives: (a) stdlib logging + custom JSON formatter — reinvents "
     "structlog; (b) loguru — nice DX but non-standard; (c) vendor-locked "
     "(Datadog, NewRelic) — conflicts with ADR-0020 OTel decision. (a) and (b) "
     "rejected for non-standardization; (c) rejected for lock-in.",
     "structlog adds ~1ms per log call. Redaction regex must be maintained "
     "as new PII fields are added. Sampling config must be tuned per "
     "environment. Dev ergonomics: pretty-print in local dev, JSON in "
     "production.",
     "Phase 4: unit tests for redaction (PII + secret by name and regex); "
     "regression test with injected secret. Phase 4: sampling assertion "
     "on /health/. Phase 5: load-test logger overhead at 5k req/s.",
     "ACCEPTED", "Architecture Lead + Reliability Lead + Security Lead"),

    (26, "DEC-0031", "Error format (RFC 7807 + catalog + i18n-key messages)",
     "Architecture Lead", "Phase1",
     "API errors must be machine-readable, consistent across endpoints, and "
     "i18n-capable. Ad-hoc error JSON shapes break client integrations. RFC 7807 "
     "(Problem Details for HTTP APIs) is the standard. A central catalog prevents "
     "code drift. Stack traces must never leak in production (NFR §1 security).",
     "Adopt RFC 7807 problem+json. Catalog of error codes in "
     "src/noventra/errors/catalog.py. Each code has: code, http_status (one "
     "per code), i18n_key (default en), title, detail_template. Generated "
     "docs at docs/architecture/error-catalog.md. correlation_id always "
     "included. Stack traces emitted in logs only, never in response bodies; "
     "traces field is dev-only (DEBUG=True).",
     "Alternatives: (a) ad-hoc JSON errors — inconsistent; (b) DRF default "
     "error responses — not RFC 7807; (c) JSON:API errors — heavier schema. "
     "(a) rejected for inconsistency; (b) rejected for non-conformance; "
     "(c) rejected for weight.",
     "Catalog must be regenerated when codes are added. i18n keys must "
     "resolve for every supported locale (Q19). One-HTTP-status-per-code "
     "constraint requires careful code design (no multi-status codes).",
     "Phase 4: catalog parses (test asserts every code has required fields); "
     "one HTTP status per code (test); i18n keys resolve (test against "
     "en locale). Phase 4: stack-trace suppression test against production "
     "settings.",
     "ACCEPTED", "Architecture Lead + API Lead + QA Lead"),

    (27, "DEC-0032", "Testing & coverage (mypy gradual + coverage baseline + diff ≥80%)",
     "Engineering Lead", "CrossCutting",
     "Phase 4 introduces type checking and coverage enforcement. mypy from "
     "scratch on a large codebase is noisy; gradual typing with a strict "
     "module list is the practical path. Coverage baseline must be locked at "
     "Phase 4 achieved level; diff enforcement prevents regression. Branch "
     "coverage is mandatory from Phase 8.",
     "Adopt mypy gradual baseline. strict_modules = Phase 3+4 packages "
     "(noventra.settings, noventra.api, noventra.apps.core, "
     "noventra.observability, noventra.middleware, noventra.errors). List "
     "grows per phase. Linter rule 18 enforces the strict list is clean. "
     "Coverage baseline locked at Phase 4 achieved level "
     "(.coverage-baseline-phase4.txt). Diff ≥80% from Phase 4 onward. "
     "+5%/phase from Phase 5 (80%@10, 85%@15, 90%@20). Branch mandatory @8. "
     "Exclusions in pyproject [tool.coverage].",
     "Alternatives: (a) mypy strict from day 1 — too noisy; (b) pyright — "
     "different ecosystem; (c) no type checking — conflicts with NFR §7.1 "
     "testability; (d) 100% coverage always — unrealistic and gaming-prone. "
     "(a) rejected for noise; (b) rejected for ecosystem; (c) rejected for "
     "testability; (d) rejected for gaming.",
     "Strict module list must be maintained (added per phase). Coverage "
     "baseline file must be committed; if it drifts, CI fails. Diff "
     "enforcement requires diff-cover or equivalent. Branch coverage at "
     "Phase 8 may surface legacy uncovered branches.",
     "Phase 4: mypy strict list clean (rule 18). Phase 4: baseline locked; "
     "diff ≥80% on every PR. Phase 5: coverage 80%@10. Phase 8: branch "
     "coverage mandatory.",
     "ACCEPTED", "Engineering Lead + QA Lead + Architecture Lead"),

    (28, "DEC-0033", "Scanning stack (gitleaks secret scan + pip-audit dep scan)",
     "Security Lead", "CrossCutting",
     "Phase 4 hardens CI with secret and dependency scanning. Secret leaks "
     "via committed credentials are a top industry incident cause. Known-"
     "vulnerable dependencies (CVEs) are exploitable. Both must be scanned "
     "automatically.",
     "Adopt gitleaks for secret scanning: pre-commit hook + CI push-diff + "
     "weekly full scan. .gitleaks-baseline.json records known findings "
     "(scan-forward, no history rewrite; rotation = open question Q40). "
     "Adopt pip-audit for dependency scanning: on-push + daily. CVSS ≥7.0 "
     "blocks the build. .pip-audit-allowlist.txt records false positives "
     "with owner + due date. Both run in CI and nightly.",
     "Alternatives: (a) trufflehog — alternative secret scanner; (b) Snyk — "
     "commercial dep scanning; (c) GitHub native secret scanning — requires "
     "GitHub Advanced Security (paid). (a) rejected for overlapping "
     "coverage (gitleaks is FOSS standard); (b) rejected for cost (Q5-"
     "blocked); (c) rejected for paid tier.",
     "gitleaks baseline must be maintained as new secrets are found. "
     "pip-audit allowlist must be reviewed monthly (stale allowlists are "
     "a common audit finding). CVSS threshold (7.0) is a judgment call; "
     "may need tuning. Scan runtime adds to CI minutes (Q37 ASSUMED).",
     "Phase 4: scans clean or baseline/allowlist-justified. Phase 4: weekly "
     "full gitleaks scan scheduled. Phase 4: daily pip-audit scheduled. "
     "Phase 5: review allowlists monthly.",
     "ACCEPTED", "Security Lead + Engineering Lead + Architecture Lead"),
]

UPDATE_ADRS = [
    (17, "Infrastructure Lead + Engineering Lead"),
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
