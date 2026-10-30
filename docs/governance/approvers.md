# Approvers Registry

This document maps architectural and business roles to named human approvers.
No ADR or DEC may transition to ACCEPTED without a signature from the
designated approver.

**Authority:** DEC-0026 (amended v5 — see §C.3 of traceability.md).

## Approver Roles (ratified across Phases 4–10)

| Role | Ratified In | Named Human | Email / Handle | Signature Date | Scope of Authority |
|---|---|---|---|---|---|
| Architecture Lead | Phase 8 (architect role) | [INSERT NAME] | | | ADRs for repo layout, state machine, modular monolith |
| Product Owner | Phase 9 | [INSERT NAME] | | | ADRs for player lifecycle, FSM, product decisions |
| Privacy / Data Owner | Phase 7 | [INSERT NAME] | | | ADRs for consent, retention, DSAR, redaction |
| Compliance Officer | Phase 10 | [INSERT NAME] | | | ADRs for KYC, AML/CFT, document retention |
| MLRO (Money Laundering Reporting Officer) | Phase 10 | [INSERT NAME] | | | ADRs for SAR flow, AML escalations; regulator-mandated human appointment |
| Reliability Owner | Phase 4 | [INSERT NAME] | | | ADRs for outbox, DLQ, observability, pgbouncer |
| API Owner | Phase 4 | [INSERT NAME] | | | ADRs for error format, OpenAPI, idempotency |
| QA Owner | Phase 4 | [INSERT NAME] | | | ADRs for testing standards, coverage policy |
| Security Owner | Phase 5/6/7 | [INSERT NAME] | | | ADRs for RLS, authN, RBAC, audit chain |
| CFO (Chief Financial Officer) | Phase 11 (anticipated) | [INSERT NAME] | | | ADRs for ledger, FX, posting, reversal (Phase 11+) |
| External Auditor | Phase 11 (anticipated) | [INSERT FIRM/NAME] | | | ADRs for financial audit chain, audit trail |
| Treasury / FX Owner | Phase 11 (anticipated) | [INSERT NAME] | | | ADRs for FX rate snapshots, currency exponents |

## MLRO Appointment Evidence

MLRO is a regulator-mandated human role (UK MLR 2017, EU AMLD, US BSA).

- **Appointment date:** [INSERT — target before Phase 22]
- **Appointment evidence:** [INSERT PATH to appointment letter / board resolution]
- **Regulator notification:** [INSERT PATH to FIU notification, if applicable]
- **Target completion if not yet appointed:** Before Phase 22 (first customer onboarding).

## Phase 11+ Roles (anticipated, not yet ratified)

CFO, External Auditor, Treasury/FX Owner are anticipated for Phase 11.
Until ratified in DEC-0026 amendment v6, Phase 11 ADRs requiring these
approvers cannot transition to ACCEPTED. Ratify before Phase 11
ADR-0059..0063 work begins.

## Signature Block

By signing below, each named human acknowledges their appointment and
accepts the scope of authority listed above.

```
Architecture Lead:        _________________________  Date: _______
Product Owner:            _________________________  Date: _______
Privacy / Data Owner:     _________________________  Date: _______
Compliance Officer:       _________________________  Date: _______
MLRO:                     _________________________  Date: _______
Reliability Owner:        _________________________  Date: _______
API Owner:                _________________________  Date: _______
QA Owner:                 _________________________  Date: _______
Security Owner:           _________________________  Date: _______
```

**Human action required:** Fill in [INSERT NAME] for each role. MLRO
requires documented appointment evidence (regulator-mandated).
