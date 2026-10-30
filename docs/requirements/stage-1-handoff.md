# Stage 1 Handoff — Phase 2 Entry Criteria

| Field | Value |
|---|---|
| Document | `docs/requirements/stage-1-handoff.md` |
| Version | 5.2 |
| Status | Approved |
| Owner | Engineering Lead |
| Authority | BLUEPRINT §10, §11 |

This document defines what Phase 1 hands off to Phase 2, the entry
criteria Phase 2 must satisfy before it can start, and the open
risks Phase 2 inherits. Phase 2 does not start until (a) all entry
criteria are met and (b) the Phase 0 evidence pack has been signed
off per `phase-0-evidence.md`.

## 1. Phase 1 deliverables handed off

Phase 1 produces documentation and a linter only. Zero application
code is written. The handed-off artefacts are:

### 1.1 Governance documents

| Artefact | Path | Purpose |
|---|---|---|
| Blueprint | `docs/BLUEPRINT.md` | Master authority for Increment 1. |
| Errata | `docs/ERRATA-v5.2.1.md` | Records E1–E7 corrections. |
| Traceability | `docs/requirements/traceability.md` | Sole authority for REQ and DEC IDs. |
| Scope | `docs/requirements/scope.md` | Single authority for capability-level triage. |
| Roles | `docs/requirements/roles.md` | RACI and small-team blocker rule. |
| Workflows | `docs/requirements/workflows.md` | Specs for the 10 in-scope workflows. |
| NFRs | `docs/requirements/nfr.md` | Non-functional requirements. |
| Domain boundaries | `docs/requirements/domain-boundaries.md` | Bounded contexts and contracts. |
| Triage table | `docs/requirements/triage-table.md` | Single authority for workflow-level triage. |
| Open questions | `docs/requirements/unresolved-decisions.md` | 27 questions; Q1/Q2/Q4/Q5 BLOCKED. |
| Stage 1 handoff | `docs/requirements/stage-1-handoff.md` | This document. |
| Phase 0 evidence | `docs/phase-0-evidence.md` | Legal/Commercial/Financial gate template. |

### 1.2 ADR stubs

21 ADR stubs under `docs/adr/` (`ADR-0001.md` through
`ADR-0021.md`). Each stub has YAML front-matter (including the
mandatory `DEC: DEC-00XX` citation per errata E7 and DEC-0023), a
title, a Status field, a brief Context section, and a brief
Decision section. Full Context / Decision / Consequences sections
are a Phase 2 deliverable per ADR.

### 1.3 Linter

`scripts/check_traceability.sh` — enforces linter rules 1–7
against `traceability.md` and the ADR stubs. The linter is
human-executed in Phase 1; CI integration is a Phase 2 deliverable.

### 1.4 Tags

Two git tags are applied to the Phase 1 commit:

- `blueprint-v5.2` — applied to the commit that introduces the
  blueprint and errata.
- `errata-v5.2.1` — annotated tag applied to the same SHA,
  preserving the errata identity for audit.

### 1.5 What is NOT handed off

The following are explicitly NOT produced in Phase 1 and are NOT
handed off:

- Application code (Django models, DRF serializers, services,
  migrations). Phase 3 begins repo scaffold.
- CI pipeline configuration. Phase 2 deliverable.
- Static analysis configuration. Phase 2 deliverable.
- Service mesh configuration. Phase 2 deliverable.
- Test suite. Phase 2 begins test scaffolding.
- Deployment manifests. Phase 2 deliverable.
- Runbooks for the nine agents (DEC-0022). Phase 2 deliverable;
  the agents themselves are first eligible to contribute from
  Phase 2 onward.

## 2. Phase 2 entry criteria

Phase 2 starts only when ALL of the following are true. The
Engineering Lead is Accountable for verifying each criterion.

### 2.1 Phase 0 evidence gate passed

The Phase 0 evidence pack (`phase-0-evidence.md`) is signed off,
with all three gates (Legal, Commercial, Financial) marked PASS.
If any gate is BLOCKED, Phase 2 does not start. There are no
exceptions. See BLUEPRINT §10 and `unresolved-decisions.md` §4.

### 2.2 Phase 1 acceptance criteria met

All Phase 1 hard acceptance criteria (BLUEPRINT §11) are verified
true. The verification is recorded in the Phase 1 close-out
section of the worklog (held by the Engineering Lead).

### 2.3 Linter passes against the seeded baseline

`scripts/check_traceability.sh` exits 0 against the committed
`traceability.md` and the 21 ADR stubs. The linter's exit code is
recorded in the worklog.

### 2.4 Zero application code present

The repository contains no `manage.py`, `pyproject.toml`, `src/`,
`apps/`, or any `models.py` / `serializers.py` / `services.py`
files outside `docs/` and `scripts/`. This is verified by a
filesystem scan recorded in the worklog.

### 2.5 Role roster staffed

The role roster in `roles.md` §1 has at least one named human
owner per role (combinations permitted per `roles.md` §1, but
prohibited combinations per `roles.md` §5 are not in use). The
team-size check passes (≥ 3 humans) or the small-team blocker
rule has been formally accepted by the Engineering Lead and the
blockers (Q1, Q2, Q4, Q5) are resolved with external validation
evidence on file.

### 2.6 Agent promotion gate defined

The nine agent promotion gates (DEC-0022) are defined, even if no
agent has yet been promoted from shadow to live. The definition
includes: the runbook (draft), the three-shadow-run requirement,
the human approver, and the rollback procedure. The actual shadow
runs begin in Phase 2.

### 2.7 Open risks acknowledged

The open risks in §4 below are acknowledged by the Engineering
Lead and the Architecture Lead. Acknowledgement is recorded in
the worklog. Acknowledgement does not mean acceptance; it means
the risks are known and will be tracked.

## 3. Phase 2 scope (preview)

Phase 2 begins repo skeleton, CI, and the dev environment. The
Phase 2 deliverables are previewed here so that the Phase 1
handoff is informed by what Phase 2 will need.

| Deliverable | Owner | Notes |
|---|---|---|
| Repo skeleton (Django project, DRF scaffold, package layout) | Architecture Lead | First application code. Boundary enforcement (§9 of `domain-boundaries.md`) begins here. |
| CI pipeline (build, test, lint, traceability check) | Engineering Lead | `check_traceability.sh` integrated as a CI step. |
| Dev environment (Docker Compose, local seed data) | Infrastructure Lead | Includes a local KMS, a local IdP stub, a local audit log. |
| Test scaffolding (pytest, integration test framework) | Engineering Lead | Property-based tests for determinism (NFR §7.2). |
| Static analysis configuration (context boundary enforcement) | Architecture Lead | Per `domain-boundaries.md` §9. |
| Agent runbooks (9 agents) | Engineering Lead | Draft runbooks; shadow runs begin. |
| ADR full sections (21 ADRs) | Architecture Lead | Context / Decision / Consequences expanded from stubs. |

Phase 2 does NOT deliver: tenant data model (Phase 3), identity
primitives (Phase 4–7), audit log (Phase 8–10), ledger (Phase 11),
or any workflow runtime.

## 4. Open risks inherited by Phase 2

The following risks are open at the Phase 1 / Phase 2 boundary.
Each is owned by a named role and has a mitigation plan.

### 4.1 Risk: jurisdictions unresolved

If Q1 (jurisdictions) is resolved but Q2 (licensing) is not, the
platform may build toward a jurisdiction in which it cannot
legally operate. Mitigation: Phase 2 work is restricted to
jurisdiction-neutral components (tenancy primitives, identity
primitives, audit primitives) until Q2 is resolved. Owner: Legal
Lead.

### 4.2 Risk: pilot partner churn

If Q4 (pilot partner) is resolved with a single partner and that
partner withdraws, the Phase 2 build may be over-fit to one
customer's needs. Mitigation: Phase 2 work is reviewed against
the general B2B OS provider requirements (DEC-0024), not against
any single partner's requests. Owner: Commercial Lead.

### 4.3 Risk: budget shortfall mid-Phase 2

If Q5 (budget) is resolved for Phases 1–3 but a shortfall emerges
mid-Phase 2, the Phase 2 deliverables may be partially built and
then abandoned. Mitigation: Phase 2 deliverables are sequenced so
that the repo skeleton + CI + dev environment are delivered first;
if budget is cut, the partial state is at least a usable scaffold.
Owner: Commercial Lead.

### 4.4 Risk: vendor selection delays Phase 4–7

If Q6 (KYC vendor) or Q7 (sanctions vendor) is unresolved when
Phase 4–7 begins, the identity and compliance primitives cannot
be fully delivered. Mitigation: Phase 2 and Phase 3 work is
vendor-neutral; vendor integration is deferred to Phase 4–7 and
is the gating item for that phase's start. Owner: Compliance
Lead.

### 4.5 Risk: architectural decisions revisited

The 21 ADR stubs commit the architecture to specific choices
(event sourcing, hexagonal, RLS-based tenancy, etc.). If a Phase 2
spike reveals one of these to be unworkable, the cost of
revisiting is high. Mitigation: ADR full sections (Phase 2
deliverable) must include a "Reversibility" paragraph assessing
the cost of reversal. ADRs with high reversal cost are flagged
for Architecture Lead review. Owner: Architecture Lead.

### 4.6 Risk: agent promotion delays Phase 2

If the nine agents are not promoted from shadow to live by
mid-Phase 2, the human team's workload is higher than planned.
Mitigation: agent runbooks (Phase 2 deliverable) are prioritised
ahead of other Phase 2 work; the first three agents to be
promoted are the Documentation agent, the Linter agent, and the
Handoff agent (lowest risk). Owner: Engineering Lead.

### 4.7 Risk: scope creep via "just one more workflow"

The triage anti-scope-creep rule (`triage-table.md` §4) is
enforced in Phase 1 but may come under pressure in Phase 2 when
the first code is written and "obvious" workflows emerge.
Mitigation: any new workflow proposal goes through the triage
change protocol (`triage-table.md` §3); no exception is made for
"obvious" workflows. Owner: Architecture Lead.

## 5. Handoff sign-off

The handoff is signed off by:

- **Engineering Lead** — confirms Phase 1 acceptance criteria met
  and Phase 2 entry criteria satisfied.
- **Architecture Lead** — confirms the governance documents are
  internally consistent and the ADR stubs satisfy the ADR-DEC
  mapping law.
- **Compliance Lead** — confirms the Phase 0 Legal gate status
  (PASS or BLOCKED).
- **Commercial Lead** — confirms the Phase 0 Commercial and
  Financial gate status (PASS or BLOCKED).

Sign-off is recorded in the worklog with the sign-off date, the
signer's role, and the gate status at sign-off. If any sign-off
is BLOCKED, Phase 2 does not start.

## 6. Worklog pointer

The shared worklog is at `/home/z/my-project/worklog.md`. The
Phase 1 close-out entry is the last entry before the Phase 2
kick-off entry. The Phase 2 kick-off entry references this
document and the signed-off gate status.
