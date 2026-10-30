# Stage 10 Handoff — Phase 11 Entry Criteria

| Field | Value |
|---|---|
| Document | `docs/stage-handoffs/stage-10-handoff.md` |
| Version | 6.1 (Phase 10 — Increment 2 second pillar) |
| Status | Approved |
| Owner | Engineering Lead |

## 1. Phase 10 deliverables

### 1.1 ADRs (7 ACCEPTED, 3 HUMAN-APPROVED)
ADR-0052 (KYC FSM, HUMAN-APPROVED), ADR-0053 (Document versioning),
ADR-0054 (Storage port), ADR-0055 (Synchronous revocation),
ADR-0056 (AML/CFT, HUMAN-APPROVED), ADR-0057 (KYC vendor),
ADR-0058 (Review queue, HUMAN-APPROVED). Compliance officer + MLRO
roles ratified (MLRO is regulator-mandated).

### 1.2 KYC app (12th app)
- `kyc/domain/` — KycCase (16-state FSM), Document + DocumentVersion
  (versioning + types), AML (ScreeningResult, AmlResult, SarRecord),
  ReviewQueue (SLA + escalation), StoragePort.
- `kyc/adapters/storage_stub.py` — StubStorageAdapter (Q5-blocked).

### 1.3 Audit event taxonomy extended
26 new event types: kyc.* (11), document.* (4), aml.* (3),
review.* (5), sar.* (3, MLRO-restricted).

## 2. Contracts Phase 11 must honor

### 2.1 KYC case contract
- Ledger MUST check KYC status before transactions (player must be
  closed_approved).
- KYC data processing requires consent (Phase 9 consent purpose
  `kyc_processing`).

### 2.2 Document model contract
- Ledger references SoF documents (source of funds evidence).
- Documents are versioned + immutable; supersession ≠ revocation.

### 2.3 AML/CFT risk score contract
- Ledger applies risk-based transaction limits (high-risk player =
  lower limits or block).

### 2.4 SAR flow contract
- Ledger freezes account on SAR filing (suspended_pending_sar).
- Tipping-off prohibition: ledger must NOT notify the player.

### 2.5 Inherited contracts (Phase 4-9)
All previous contracts remain in force.

## 3. Phase 11 entry criteria
- Phase 10 hard acceptance met (FSM, document versioning, storage,
  revocation, AML/CFT, review queue, 7 ADRs ACCEPTED, rules 1-70 green,
  coverage ≥90%).
- Q1/Q2/Q4/Q5 carry-over explicit (highest combined blast radius).

## 4. Phase 11 scope (preview)
- Ledger primitives (ADR-0011/0012/0013 → ACCEPTED).
- First deposit workflow.
- Transaction monitoring (AML ongoing).
- Real KYC/PEP/sanctions vendor (Q5).
- Real storage backend (Q5).
- Jurisdiction-specific KYC constraints (Q1).

## 5. Handoff sign-off
Engineering Lead, Architecture Lead, Compliance Lead, MLRO, Legal Lead,
Security Lead, Privacy Owner, Architect.

## 6. Worklog pointer
`/home/z/my-project/worklog.md` — Phase 10 close-out entry.
