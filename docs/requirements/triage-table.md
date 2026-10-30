# Triage Table — 10 Workflows

| Field | Value |
|---|---|
| Document | `docs/requirements/triage-table.md` |
| Version | 5.2 |
| Status | Approved |
| Owner | Architecture Lead |
| Authority | BLUEPRINT §9 (triage rule); `scope.md` §3 |

This document is the **single authority** for workflow-level triage
in Increment 1. Exactly 10 workflows are triaged here. Any workflow
not listed here is implicitly out of Increment 1; no work may begin
on such a workflow until it is added to this table.

The triage rule (BLUEPRINT §9) is enforced at three levels:
capability (`scope.md`), workflow (this document), and REQ
(`traceability.md` Scope column). This document is the workflow
level.

## 1. Triage decisions

| WF ID | Workflow | Capability area | Decision | Target phase | Rationale | Primary REQs |
|---|---|---|---|---|---|---|
| WF-01 | Tenant provisioning | Tenancy | IN SCOPE | Phase 1 | Foundation of multi-tenancy; required by every subsequent workflow. | MB-REQ-0001, MB-REQ-0002, MB-REQ-0023, Pain-REQ-0002 |
| WF-02 | Tenant configuration update | Tenancy | IN SCOPE | Phase 1 | Tenants must self-serve configuration; cannot defer to operations team. | DEC-0014, MB-REQ-0018 |
| WF-03 | User invitation and acceptance | Identity | IN SCOPE | Phase 1 | Identity primitives required for any authenticated operation downstream. | DEC-0004, MB-REQ-0003, Pain-REQ-0012 |
| WF-04 | Single sign-on authentication | Identity | IN SCOPE | Phase 1 | Token issuance is the identity service's primary output; required by all authenticated workflows. | DEC-0004, DEC-0005, MB-REQ-0003, Pain-REQ-0003 |
| WF-05 | Role assignment and delegation | Identity | IN SCOPE | Phase 1 (primitives); full UI Phase 4–7 | RBAC primitives required so that Phase 4–7 can build on a stable authorization model. | DEC-0015, MB-REQ-0003, Pain-REQ-0012 |
| WF-06 | Audit event emission | Audit | IN SCOPE | Phase 1 | Append-only audit log is a foundational reliable-core primitive; state changes are conditional on audit write success. | DEC-0006, DEC-0007, MB-0004, Law-REQ-0010 |
| WF-07 | Audit log query and export | Audit | IN SCOPE | Phase 1 | Compliance team requires read access from day one; Pain-REQ-0004. | DEC-0006, MB-REQ-0004, Pain-REQ-0004 |
| WF-08 | Heartbeat and health monitoring | Reliable Core | IN SCOPE | Phase 1 | Observability substrate required for every other workflow's reliability guarantees. | DEC-0020, MB-REQ-0020, MB-REQ-0014 |
| WF-09 | Backup execution | Reliable Core | IN SCOPE | Phase 1 | BCP/DR compliance requires backups from day one; Law-REQ-0021. | DEC-0020, Law-REQ-0021, MB-REQ-0004 |
| WF-10 | Restore (DR drill) | Reliable Core | IN SCOPE | Phase 1 | DR drill must be runnable from day one; RTO/RPO targets (provisional, Q22) must be testable. | DEC-0020, Law-REQ-0021, Law-REQ-0022 |

## 2. Workflows deferred or out of scope

The following workflows are NOT in Increment 1. They are listed
here so that their absence is documented as a decision, not as an
oversight. Each has a target phase and a rationale.

| Workflow | Capability area | Decision | Target phase | Rationale |
|---|---|---|---|---|
| Customer deposit | Ledger | DEFERRED | Phase 12+ | Per errata E4; requires Ledger context (Phase 11) to be in place first. |
| Ledger posting | Ledger | DEFERRED | Phase 11 | Per errata E4; ledger primitives delivered in Phase 11. |
| KYC verification | Compliance | DEFERRED | Increment 2 | Blocked on Q6 (KYC vendor selection). |
| Sanctions/PEP screening | Compliance | DEFERRED | Increment 2 | Blocked on Q7 (screening vendor selection). |
| Payment instruction execution | Payments | OUT OF SCOPE | Increment 3 | Per DEC-0021 phase plan; not part of the platform's foundation. |
| FX conversion | Treasury | OUT OF SCOPE | Increment 3 | Per DEC-0021 phase plan; not part of the platform's foundation. |
| Reconciliation engine | Operations | DEFERRED | Phase 22 | Per DEC-0021 (merge of stages 22+23 into Phase 22). |
| Regulatory reporting | Compliance | DEFERRED | Phase 23+ | Per DEC-0021 phase plan. |
| SAR/STR submission | Compliance | DEFERRED | Phase 23+ | Blocked on Q1 (jurisdictions) and Q15 (submission channel). |
| CTR filing | Compliance | DEFERRED | Phase 23+ | Blocked on Q1 (jurisdictions). |

## 3. Triage change protocol

A triage change (adding a workflow, moving a workflow between
phases, or moving a workflow between decisions) requires:

1. An ADR. The ADR cites the DEC that the change affects (or
   proposes a new DEC).
2. An update to this document.
3. An update to `scope.md` if the change crosses a capability
   boundary.
4. An update to `traceability.md` §B if the change introduces or
   retires REQs.
5. A supersession row in `traceability.md` §D for any REQ that the
   change retires.

Triage changes are not made unilaterally. The Architecture Lead is
Accountable; the Engineering Lead, the Product Lead, and the
Compliance Lead (for compliance-affecting changes) are Consulted.

## 4. Anti-scope-creep rule

If a workflow not listed in §1 or §2 is proposed for Increment 1,
the proposal must be rejected at the triage layer. The proposal may
be reconsidered only after:

1. The proposal is documented as a new open question in
   `unresolved-decisions.md`.
2. The question is assigned an owner and a due date.
3. The Architecture Lead, Engineering Lead, and Product Lead
   jointly approve adding the question to the queue.

This rule exists to prevent scope creep via "just one more
workflow" arguments. Increment 1 is closed at ten workflows. Any
expansion is a Phase 2+ concern.
