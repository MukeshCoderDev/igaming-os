#!/usr/bin/env python3
"""Generate Phase 3 ADR updates: 3 new ADRs (0022, 0023, 0024) in Nygard
format with status ACCEPTED, and update ADR-0001 + ADR-0006 status to ACCEPTED.

Also updates the Last-Reviewed date on the 5 ADRs transitioning to ACCEPTED.

Run:  python3 /home/z/my-project/scripts/generate_phase3_adrs.py
"""

from pathlib import Path
import re

OUT_DIR = Path("/home/z/my-project/docs/adr")
LAST_REVIEWED = "2025-10-28"

# (adr_num, dec_id, title, owner, scope, context, decision, alternatives,
#  consequences, validation_plan, status, approver)
NEW_ADRS = [
    (22, "DEC-0027", "Repository skeleton (pyproject, Docker, compose, Makefile, CI)",
     "Architecture Lead", "Phase2-3",
     "Phase 3 begins the first application code. A reproducible, pinned-dependency "
     "repository skeleton is required so that every developer and CI runner "
     "produces the same environment. The skeleton must encode the constraints "
     "from stage-02-handoff.md §3 (module → Django app map, Postgres 16 major "
     "version lock, RLS role model, idempotent init scripts).",
     "Adopt a src-layout Python project rooted at `src/noventra/`. Pin all "
     "dependencies in `pyproject.toml` with a lock file. Provide "
     "`docker-compose.yml` with Postgres 16 and Redis 7 (pinned majors) with "
     "healthchecks and `depends_on: healthy`. Provide a `Makefile` with "
     "targets: bootstrap, migrate, test, lint, typecheck, runserver. Provide "
     "`deploy/docker/init/` idempotent SQL scripts. Provide `.env.example`, "
     "`.pre-commit-config.yaml`, `CODEOWNERS`, `README.md`.",
     "Alternatives considered: (a) flat layout (no `src/`) — makes accidental "
     "imports easier; (b) pip-tools instead of poetry/uv — more manual; "
     "(c) Docker-only dev (no local venv) — slower inner loop; (d) "
     "k8s-based dev — over-engineered for Phase 3. (a) rejected for import "
     "safety; (b) rejected for manual burden; (c) rejected for inner-loop "
     "speed; (d) rejected for complexity.",
     "Developers must learn src-layout conventions. Lock-file maintenance "
     "is a recurring task. Docker-compose adds resource overhead on dev "
     "machines. Init scripts must be kept idempotent.",
     "Phase 3: `make bootstrap && make migrate && make runserver` works "
     "end-to-end on a clean machine. CI green on trunk. Phase 4: load-test "
     "the dev environment with 10 concurrent developers.",
     "ACCEPTED", "Architecture Lead + Engineering Lead"),

    (23, "DEC-0028", "Settings split + named-var loud failure",
     "Architecture Lead", "Phase2-3",
     "Django settings must be split across environments (base, local, test, "
     "production) so that production never inherits dev defaults. Required "
     "environment variables must fail loudly (named variable, non-zero exit) "
     "before any database or network call. Secrets must never appear in code "
     "or config files — only in the environment.",
     "Split settings into `noventra/settings/{base,local,test,production}.py`. "
     "Define a required-variables list in `base.py`. At import time, validate "
     "every required variable is present; if any is missing, print a message "
     "naming the variable and `sys.exit(1)` before any DB or network call. "
     "Secrets (SECRET_KEY, DATABASE_URL, REDIS_URL, etc.) are read from "
     "environment variables only — never from files, never from Django "
     "settings defaults. Document the full variable list in "
     "`docs/architecture/settings-split.md`.",
     "Alternatives considered: (a) single settings.py with if/else — hard to "
     "audit; (b) django-environ only (no split) — doesn't enforce split; "
     "(c) dynamic settings from DB — chicken-and-egg at startup. (a) rejected "
     "for auditability; (b) rejected for no split; (c) rejected for "
     "chicken-and-egg.",
     "Developers must set environment variables before running any command. "
     "`.env.example` must be kept in sync with the required list. "
     "Production deploys must inject all required variables via the "
     "orchestrator (k8s secrets, ECS, etc.).",
     "Phase 3: missing `SECRET_KEY` in production → `sys.exit(1)` with "
     "named message before DB connection. Phase 3: `.env.example` covers "
     "every required variable (linter rule 13 enforces). Phase 4: "
     "production deploy fails fast on missing variable.",
     "ACCEPTED", "Architecture Lead + Security Lead"),

    (24, "DEC-0029", "CI pipeline (GitHub Actions)",
     "Architecture Lead", "Phase2-3",
     "Phase 3 introduces the first CI pipeline. CI must enforce: traceability "
     "linter rules 1–16, ruff linting (I, F401, E402, F403/F405), Django "
     "`check` and `check --deploy`, migrations on an ephemeral DB, pytest "
     "(harness present, suite may be empty), and OpenAPI drift detection.",
     "Adopt a single GitHub Actions workflow at `.github/workflows/ci.yml` "
     "that runs on every push and PR. The workflow: (1) installs Python + "
     "pinned deps; (2) runs `bash scripts/check_traceability.sh`; (3) runs "
     "`ruff check .`; (4) runs `python manage.py check && python manage.py "
     "check --deploy`; (5) starts Postgres 16 + Redis 7 services; (6) runs "
     "`python manage.py migrate` on the ephemeral DB; (7) runs `pytest`; "
     "(8) runs `python manage.py spectacular --file openapi.yaml` and diffs "
     "against the committed `docs/api/openapi.yaml`.",
     "Alternatives considered: (a) GitLab CI — different runner model; "
     "(b) Jenkins — self-hosted, higher maintenance; (c) no CI until Phase "
     "4 — accumulates debt. (a) rejected for runner model; (b) rejected for "
     "maintenance; (c) rejected for debt accumulation.",
     "CI runner cost is a Q5-blocked ASSUMED (see unresolved-decisions.md). "
     "CI runtime must stay under 10 minutes for developer ergonomics. "
     "Flaky tests block merges; must be fixed immediately.",
     "Phase 3: CI green on trunk. Phase 4: CI runtime ≤ 10min p95. "
     "Phase 5: CI includes integration tests with real IdP stub.",
     "ACCEPTED", "Engineering Lead + Architecture Lead"),
]

# ADRs to update (status → ACCEPTED, add approver, bump Last-Reviewed)
UPDATE_ADRS = [
    (1, "Architecture Lead + Engineering Lead"),
    (6, "Architecture Lead + Compliance Lead"),
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
Created: 2025-10-28
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
    """Update an existing ADR file: status → ACCEPTED, add Approver, bump Last-Reviewed."""
    adr_id = f"ADR-{adr_num:04d}"
    path = OUT_DIR / f"{adr_id}.md"
    text = path.read_text()
    # Update Status
    text = re.sub(r'^Status: PROPOSED$', f'Status: ACCEPTED', text, flags=re.MULTILINE)
    # Update Last-Reviewed
    text = re.sub(r'^Last-Reviewed: .*$',
                  f'Last-Reviewed: {LAST_REVIEWED}', text, flags=re.MULTILINE)
    # Add Approver line after Superseded-By if not present
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

    # Write new ADRs
    for (n, dec, title, owner, scope, ctx, dec_text, alts, cons, val,
         status, approver) in NEW_ADRS:
        path = OUT_DIR / f"ADR-{n:04d}.md"
        path.write_text(render_new(n, dec, title, owner, scope, ctx, dec_text,
                                    alts, cons, val, status, approver))
        print(f"wrote {path} (status={status})")

    # Update existing ADRs
    for (n, approver) in UPDATE_ADRS:
        update_existing(n, approver)

    print(f"\n{len(NEW_ADRS)} new ADRs + {len(UPDATE_ADRS)} updated ADRs.")


if __name__ == "__main__":
    main()
