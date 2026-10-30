# Stage 12 Handoff — Phase 13 Entry Criteria

| Field | Value |
|---|---|
| Document | `docs/stage-handoffs/stage-12-handoff.md` |
| Version | 6.3 (Phase 12 — Payments & Chargebacks) |
| Status | Stage A Design (Stage B merge stop active) |
| Owner | Engineering Lead |

## 1. Phase 12 Stage A deliverables

### 1.1 ADRs (6 PROPOSED — Stage A)
ADR-0072 (PCI Boundary), ADR-0073 (Payment Order FSM),
ADR-0074 (PSP Port), ADR-0075 (Webhook Signatures),
ADR-0076 (Chargeback Disputes), ADR-0077 (Payment-to-Ledger Contract).

### 1.2 DECs (6 HUMAN-APPROVED)
DEC-0072..0077.

### 1.3 Design doc
`docs/architecture/payments-design.md` — PCI boundary map, payment order
FSMs, webhook verification, linter rules 81-90, threat model, cross-phase
continuity, concurrency tests, currency-mismatch tests.

## 2. Contracts Phase 13 must honor

### 2.1 Payment contract
- All payments go through PSP port (rule 87).
- No PAN storage (rules 81, 88).
- Payment→ledger posting is exactly-once (ADR-0077).

### 2.2 Webhook contract
- HMAC-SHA256 verified before any DB write (rule 83).
- Replay protection via timestamp + nonce (rule 84).

### 2.3 Dispute contract
- Evidence packs auto-generated on dispute.opened.
- 7-year retention per Phase 9 schedule.
- Deadline enforcement (missed = auto loss).

## 3. Phase 13 entry criteria
- Phase 12 Stage B GREEN (CI, coverage ≥95%, ADRs ACCEPTED, linter 1-90).
- PCI Owner named.
- PSP vendor selected (Q5) or stub-adapter acceptance.

## 4. Phase 13 scope (preview)
- Wallet aggregation (multi-currency wallet views).
- Transaction history API.
- Balance snapshot service.
- Reporting read models (GGR/NGR).
