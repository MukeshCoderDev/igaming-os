---
ADR: ADR-0027-amendment-v2
Title: ADR-0027 v2 — Coverage Curve Amendment + Deferred Linter Rules Disposition
Status: ACCEPTED
DEC: DEC-0032
Owner: QA Owner
Scope: CrossCutting
Created: 2026-10-28
Last-Reviewed: 2026-10-28
Supersedes: ADR-0027 v1 coverage curve + deferral of rules 33/34/36
Superseded-By: ""
Approver: QA Owner + Architecture Lead + Engineering Lead
---

# ADR-0027 v2 — Coverage Curve Amendment + Deferred Linter Rules Disposition

## Context

Phase 10 Deep Audit identified two gaps in ADR-0027 v1:
1. Coverage curve was tightened across Phases 5–10 audits but never
   formally amended into the ADR.
2. Linter rules 33, 34, 36 (deferred from Phase 6 audit "if config
   stability requires") remained in limbo — neither adopted nor
   explicitly dropped.

## Decision

### Coverage Curve (tightened from v1)

| Phase | Module Type | Coverage Floor | Justification |
|---|---|---|---|
| Phase 5 | Tenancy / RLS | ≥ 60% | First domain module; baseline |
| Phase 6 | Identity / RBAC | ≥ 80% | Security-critical |
| Phase 7 | Audit / hash chain | ≥ 85% | Security-critical (evidentiary) |
| Phase 8 | Reliable core | ≥ 85% | Integrity-critical |
| Phase 9 | Players / consents | ≥ 90% | Compliance-critical (regulated PII) |
| Phase 10 | KYC / documents | ≥ 90% | Compliance-critical (AML/CFT) |
| Phase 11+ | Ledger / FX / financial | ≥ 95% | Money layer — bugs are existential |
| Future phases | Per phase audit | Per audit recommendation | Phase audits may amend upward |

Branch coverage: mandatory from Phase 8 onward (per Phase 4 audit).
Diff coverage: ≥ 80% from Phase 4 onward (per Phase 4 audit).

### Deferred Linter Rules Disposition (Phase 6 audit §5)

Phase 6 audit defined rules 33, 34, 36 as follows (NOT redefined here —
this amendment adopts the Phase 6 audit's definitions verbatim):

- **Rule 33** — Token `typ` claim distinguishes human vs service;
  human-only endpoints reject `typ=service`; service-only endpoints
  reject `typ=human`.
  **DISPOSITION: ADOPTED in Phase 11** (Phase 10 close — authN pipeline
  is now stable enough for typ enforcement; Phase 6 deferred to "Phase 7
  if config stability requires" — that threshold is met as of Phase 10
  close).

- **Rule 34** — Shadow→live promotion gate: every agent identity has a
  recorded promotion approver; shadow agents cannot execute mutations.
  **DISPOSITION: ADOPTED in Phase 11** (Phase 8 implemented the gate
  infrastructure per ADR-0044; rule 34 enforces its use).

- **Rule 36** — Agent identity enforcement via ADR citation: no
  `# ADR-0034` citation in a code path that allows human token use; no
  `# ADR-0031` citation in a service-token-only path that accepts human
  tokens.
  **DISPOSITION: DEFERRED to Phase 20** (Bounded Agents phase — rule 36
  is meaningless without agent code to cite; Phase 20 is the natural
  home). Documented as open question OQ-XXX with target Phase 20.

## Consequences

1. CI will enforce 95% coverage on Phase 11+ modules.
2. Rules 33 and 34 are active in `check_traceability.sh` from Phase 11
   onward.
3. Rule 36 is deferred to Phase 20 with documented open question.
4. The Phase 6 audit's deferral of rules 33/34/36 is now formally
   closed: 33 and 34 adopted; 36 deferred with target phase.
5. The chronic "deferred rules in limbo" process defect (Phase 10 mentor
   close audit §2.4) is now resolved.

## Validation Plan

- `pytest --cov=src/noventra/modules/ledger --cov-fail-under=95` in
  Phase 11 CI.
- `pytest --cov=src/noventra/modules/fx --cov-fail-under=95` in Phase
  11 CI.
- Rule 33 enforcement: test that `typ=service` token is rejected on
  `/api/v1/auth/login` (human-only endpoint).
- Rule 34 enforcement: test that shadow agent cannot mutate (attempt to
  POST to a mutating endpoint returns 403).
- Rule 36: documented deferral; open question OQ-XXX references this
  ADR.

## Supersedes

ADR-0027 v1's coverage curve (lines specifying 0%/+5%/phase to
80%@Phase 10).
ADR-0027 v1's deferral of rules 33/34/36.
