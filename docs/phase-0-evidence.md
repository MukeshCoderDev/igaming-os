# Phase 0 Evidence Pack — Sign-Off

| Field | Value |
|---|---|
| Document | `docs/phase-0-evidence.md` |
| Status | HUMAN-APPROVED |
| DEC | DEC-0064 (Q1–Q5 Increment 1+2 non-blocking acceptance) |
| Approvers | [CTO], [Product Owner] |
| Date | 2026-10-28 |

## Purpose

Phase 0 is the legal, commercial, and financial gate before Phase 1
engineering begins. Per Phase 1 audit gate: "If BLOCKED → Phase 2 does
not start. Pivot or kill. No exceptions."

This document records the evidence reviewed and the human sign-off that
authorizes Increments 1 and 2 engineering to proceed, with documented
deferrals.

## A. Legal & Jurisdiction

| Question | Status | Evidence |
|---|---|---|
| Q1: Target jurisdictions | OPEN-DEPENDENT | Default policy with jurisdiction-override mechanism per Phase 9 ADR-0051; legal counsel engaged [DATE]; target resolution: before Phase 22 |
| Q2: Who holds licenses | OPEN-DEPENDENT | Counsel opinion referenced at [PATH]; target resolution: before Phase 22 |
| Q3: Supplier licensing duties | OPEN-DEPENDENT | Counsel opinion referenced at [PATH] |
| Q6: Controller/processor split | OPEN-DEPENDENT | Counsel opinion referenced at [PATH] |
| Q7: Data residency cells | DEFERRED | Phase 5 architecture assumes single-region; multi-region deferred to Increment 5+ |
| Q22: PCI SAQ-A confirmation | CONFIRMED | Per blueprint §1 (SAQ-A, fully outsourced capture) |
| Q25: Reality-check mandates | OPEN-DEPENDENT | Jurisdiction-dependent; deferred to Phase 14 |

## B. Commercial

| Question | Status | Evidence |
|---|---|---|
| Q4: Pilot operator signed | OPEN-DEPENDENT | LOI template at [PATH]; target signature: before Phase 22 |
| Q14: Rev-share model | OPEN-DEPENDENT | Per DEC-0024 (B2B OS provider, Option A); commercial model documented at [PATH] |
| Q23: Chargeback liability split | OPEN-DEPENDENT | PSP contract template at [PATH] |
| Q24: Operator offboarding obligations | OPEN-DEPENDENT | Contract template at [PATH] |

## C. Financial

| Question | Status | Evidence |
|---|---|---|
| Q5: Budget/headcount | ASSUMED | Financial model at [PATH]; runway [INSERT MONTHS]; budget envelope [INSERT] |
| Q15: Contractual SLAs | OPEN-DEPENDENT | Per blueprint §11 capacity assumptions (restored per errata E5) |

## D. Vendor

| Question | Status | Evidence |
|---|---|---|
| Q8: PSP/KYC/geo vendors | ASSUMED | Stub adapters in place per Phase 8 ADR-0045 and Phase 10 ADR-0057; vendor selection deferred (Q5-blocked) |
| Q9: AI providers permitted | OPEN-DEPENDENT | EU AI Act classification pending (Q21) |
| Q12: Test lab | OPEN-DEPENDENT | Required for Phase 16 (proprietary game framework) |

## Decision: Q1–Q5 Acceptance for Increments 1 and 2

The undersigned accept the Q1–Q5 deferrals as non-blocking for
Increments 1 and 2 engineering (Phases 1–14), with the following
conditions:

1. All ADRs whose decisions depend on Q1–Q5 carry status ASSUMED or
   OPEN-DEPENDENT (not Confirmed).
2. No AML/CFT, consent, retention, or jurisdiction-sensitive decision
   may transition to ACCEPTED until the relevant Q is resolved.
3. Phase 22 (first customer onboarding) requires Q1, Q2, Q4, Q5
   resolved.
4. Phase 11 (Ledger & FX) requires Q5 (FX vendor) resolution OR
   explicit stub-adapter acceptance recorded in DEC-0064 amendment.

This decision is itself a Business decision per Phase 1 rule 5
(Business/Budget/Vendor + Confirmed ⇒ HUMAN-APPROVED). Recorded as
DEC-0064.

## Signatures

By signing below, the stakeholders acknowledge the architectural
baseline and accept the known deferrals (Q1–Q5) as non-blocking for
Increments 1 and 2 engineering, subject to the conditions above.

```
_________________________  Date: _______
[INSERT NAME], CTO / Architecture Lead

_________________________  Date: _______
[INSERT NAME], Product Owner

_________________________  Date: _______
[INSERT NAME], Legal Counsel (Q1, Q2, Q3, Q6, Q7 acknowledgment)
```
