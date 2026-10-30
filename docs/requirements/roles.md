# Roles — Phase 1

| Field | Value |
|---|---|
| Document | `docs/requirements/roles.md` |
| Version | 5.2 |
| Status | Approved |
| Owner | Engineering Lead |
| Authority | BLUEPRINT §6 (agents); DEC-0022 |

This document defines the Phase 1 role roster, the RACI for Phase 1
deliverables, and the small-team blocker rule that escalates Q1, Q2,
Q4, and Q5 to BLOCKED status when the team falls below three named
members.

## 1. Role roster

The following named roles are required for Phase 1. Each role may be
held by one or more humans, but each role must have at least one
named human owner recorded in the project's people directory (held
outside this document, by the Engineering Lead).

| Role | Responsibilities | Default owner title |
|---|---|---|
| Architecture Lead | Owns BLUEPRINT, traceability, ADRs, domain boundaries. | Head of Architecture |
| Engineering Lead | Owns delivery schedule, agent roster, Phase 2 entry criteria. | VP Engineering |
| Identity Lead | Owns OIDC/SAML integration, RBAC, delegation chains. | Head of Identity |
| Compliance Lead | Owns AML/KYC/sanctions/retention REQs, vendor selection for compliance tooling. | Chief Compliance Officer |
| Security Lead | Owns encryption, incident response, penetration testing, SOC 2. | Chief Information Security Officer |
| Infrastructure Lead | Owns cloud provider, deployment, observability, DR. | Head of Platform Engineering |
| Product Lead | Owns pain-ledger REQs, customer discovery, sandbox. | Head of Product |
| Commercial Lead | Owns business model, pricing, pilot contracts. | Chief Commercial Officer |
| Legal Lead | Owns jurisdictions, licensing, contracts. | General Counsel |
| Operations Lead | Owns runbooks, BCP, agent schedules. | Head of Operations |
| Data Protection Officer | Owns GDPR, data residency, breach notification. | DPO |

Roles may be combined on small teams (e.g., the Compliance Lead and
the Operations Lead may be the same human). The combination is
recorded in the people directory and flagged in §3 below.

## 2. RACI for Phase 1 deliverables

R = Responsible (does the work). A = Accountable (signs off, only
one per row). C = Consulted (input). I = Informed (kept aware).

| Deliverable | Architecture Lead | Engineering Lead | Identity Lead | Compliance Lead | Security Lead | Infrastructure Lead | Product Lead | Commercial Lead | Legal Lead | Operations Lead | DPO |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BLUEPRINT v5.2 | R | A | C | C | C | C | C | C | C | I | I |
| Errata v5.2.1 | R | A | I | I | I | I | I | I | I | I | I |
| traceability.md | R | A | C | C | C | C | C | C | C | I | C |
| scope.md | R | A | C | I | I | I | C | I | I | I | I |
| roles.md | C | R/A | C | C | C | C | C | C | C | C | C |
| workflows.md | R | A | C | C | I | C | C | I | I | C | I |
| nfr.md | R | A | C | C | C | C | C | I | I | C | C |
| domain-boundaries.md | R | A | C | I | I | C | I | I | I | I | I |
| unresolved-decisions.md | C | R | C | C | C | C | C | C | C | C | C |
| stage-1-handoff.md | R | A | C | C | C | C | C | C | C | C | C |
| triage-table.md | R | A | C | I | I | I | C | I | I | I | I |
| phase-0-evidence.md | C | C | I | R (Legal gate) | C | C | C | R (Commercial gate) | C | C | C |
| 21 ADR stubs | R | A | C | I | I | I | I | I | I | I | I |
| check_traceability.sh | R | A | I | I | I | I | I | I | I | I | I |

The Phase 0 evidence pack has three gates, each with a different
Accountable owner: Compliance Lead owns the Legal gate; Commercial
Lead owns the Commercial gate; the Financial gate's Accountable owner
is the CFO (a role outside this roster; add per Q5 owner). The
Engineering Lead is Accountable for the overall Phase 0 evidence
pack assembly but not for any single gate's sign-off.

## 3. Small-team blocker rule

Per the user's hard acceptance: if the named team has fewer than
three humans across the role roster, the following four open
questions escalate to BLOCKED status and require external validation
before the Phase 0 gate can pass:

- **Q1 — jurisdictions.** External validation: counsel qualified in
  each target jurisdiction. If team < 3, this is BLOCKED because the
  internal Legal Lead role is unfilled or overloaded.
- **Q2 — licensing regime per jurisdiction.** External validation:
  counsel. Same condition.
- **Q4 — pilot partner identification.** External validation: at
  least one signed letter of intent from a regulated institution in
  a target jurisdiction. If team < 3, this is BLOCKED because the
  Commercial Lead role is unfilled.
- **Q5 — budget allocation for Phases 1–3.** External validation:
  funder (investor or board) commitment letter. If team < 3, this
  is BLOCKED because the Commercial Lead and Operations Lead roles
  cannot both be staffed.

The team-size check is performed at the Phase 0 gate review by the
Engineering Lead, who counts named humans in the people directory
mapped to the role roster. If the count is less than three, the four
questions above are auto-marked BLOCKED in `unresolved-decisions.md`
and the gate fails.

## 4. Agent roster (DEC-0022)

Nine delivery agents operate on a fixed schedule per DEC-0022. The
roster is governed in the operations runbook; this document records
only the existence of the roster and the rule that agent outputs
which touch the governed baseline (REQs, DECs, ADRs, the linter)
must come from a **live** agent, not a shadow one. Phase 1 outputs
are human-authored; agents are first eligible to contribute from
Phase 2 onward.

The nine agent roles are:

1. **Requirements agent** — drafts REQs in shadow; never mutates
   traceability.md in live mode without human review.
2. **Decision agent** — drafts DEC rows and ADR stubs.
3. **Triage agent** — proposes workflow triage changes.
4. **Linter agent** — proposes linter rule changes; never executes
   the linter in live mode (the linter is human-executed).
5. **Documentation agent** — drafts prose for governance documents.
6. **Compliance evidence agent** — collects evidence for the Phase 0
   Legal gate.
7. **Commercial evidence agent** — collects evidence for the Phase 0
   Commercial gate.
8. **Financial evidence agent** — collects evidence for the Phase 0
   Financial gate.
9. **Handoff agent** — drafts stage-handoff documents.

Each agent's promotion gate (shadow → live) requires: a documented
runbook; three consecutive shadow runs with zero P0 findings; a
human approver sign-off; a tested rollback procedure. The promotion
log is held by the Engineering Lead.

## 5. Conflicts of interest

The following role combinations are prohibited regardless of team
size, to preserve separation of duties:

- The Architecture Lead may not also be the Engineering Lead. (The
  architect decides; the engineer delivers. Combining them removes
  the natural review tension.)
- The Compliance Lead may not also be the Commercial Lead. (Compliance
  must be able to veto commercial decisions without conflict.)
- The Security Lead may not also be the Infrastructure Lead. (Security
  must be able to veto infrastructure decisions without conflict.)
- The Data Protection Officer may not hold any other role on the
  roster. (The DPO must be independent per GDPR Art.38.)

Other combinations are permitted. Combinations in use on the current
team are recorded in the people directory and flagged in §1.
