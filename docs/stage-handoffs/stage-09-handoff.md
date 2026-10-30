# Stage 09 Handoff — Phase 10 Entry Criteria

| Field | Value |
|---|---|
| Document | `docs/stage-handoffs/stage-09-handoff.md` |
| Version | 6.0 (Phase 9 — Increment 2 start) |
| Status | Approved |
| Owner | Engineering Lead |
| Authority | Phase 9 hard acceptance |

## 1. Phase 9 deliverables

### 1.1 ADRs (5 ACCEPTED, 3 HUMAN-APPROVED)
ADR-0047 (Player entity), ADR-0048 (Consent schema, HUMAN-APPROVED),
ADR-0049 (Consent immutability), ADR-0050 (Player FSM, HUMAN-APPROVED),
ADR-0051 (Retention model, HUMAN-APPROVED). ADR-0046 amended (consent
check in MarketingGate). Product owner role ratified.

### 1.2 Players app
- `players/domain/` — Player (8-state FSM), Consent (schema +
  immutability), Retention (schedule + data classes).
- `players/adapters/orm.py` — Player + Consent models.
- `players/migrations/0001_initial.py` — tables + RLS + consent
  insert-only trigger.
- `players/management/commands/` — erase_player (right-to-erasure),
  export_player_data (DSAR), enforce_retention.

### 1.3 MarketingGate amended
Consent check added (DENY_CONSENT, DENY_JURISDICTION). Transactional
bypasses consent; marketing respects it.

### 1.4 Audit event taxonomy extended
16 new event types: player.* (9), consent.* (4), retention.* (3).

## 2. Contracts Phase 10 must honor

### 2.1 Player entity contract
- Players are tenant-scoped (RLS).
- Lifecycle transitions use Phase 8 state machine base.
- Every transition audited + outbox event emitted.
- Self-exclusion cooling-off guard enforced.

### 2.2 Consent contract
- Consents are insert-only (trigger-enforced).
- Revocation = new record (status=revoked), not mutation.
- Hash-chained (Phase 7 pattern).
- Marketing sends require valid consent (MarketingGate).

### 2.3 Retention contract
- Retention schedule per data class (DEFAULT_RETENTION_DAYS).
- Jurisdiction overrides Q1-blocked.
- Right-to-erasure: `erase_player` command (cascade-aware, audited).
- DSAR: `export_player_data` command (audited, within 30 days).
- Retention enforcement: `enforce_retention` command (scheduled, audited).
- Audit log NOT erased (Phase 7); player identity redacted instead.

### 2.4 Inherited contracts (Phase 4-8)
All previous contracts remain in force.

## 3. Phase 10 entry criteria
- Phase 9 hard acceptance met (FSM, consent immutability, erasure, DSAR,
  retention, MarketingGate consent check, 5 ADRs ACCEPTED, rules 1-60
  green, coverage ≥90%).
- Q1/Q2/Q4/Q5 carry-over explicit.

## 4. Phase 10 scope (preview)
- Ledger primitives (ADR-0011/0012/0013 → ACCEPTED).
- KYC vendor integration (Q6).
- Sanctions/PEP screening (Q7).
- Jurisdiction-specific retention overrides (Q1).
- Archival vendor (Q5).
- Multi-tenant player evaluation (Q61).

## 5. Handoff sign-off
Engineering Lead, Architecture Lead, Product Owner, Legal Lead,
Privacy Owner, DPO, Compliance Lead, Architect.

## 6. Worklog pointer
`/home/z/my-project/worklog.md` — Phase 9 close-out entry.
