# Payments & Chargebacks Design Document (Phase 12)

| Field | Value |
|---|---|
| Authority | DEC-0072..0077 | ADR-0072..0077 |
| Status | Stage A Design (Stage B merge stop active) |
| Coverage floor | 95% (per ADR-0027 v2) |
| Owner | Architecture Lead |

## 1. PCI SAQ-A Boundary Map

| Layer | Touches PAN? | Mechanism |
|---|---|---|
| Browser (player) | Yes (in PSP iframe) | PSP SDK iframe — Noventra JS cannot read |
| Noventra frontend | No | Loads PSP SDK; never sees PAN |
| Noventra backend | No | Receives PSP token only |
| Noventra DB | No | Stores token + last-4 + brand |
| Noventra logs | No (DLP redacted) | Linter rule 88; regex on all log lines |
| Noventra chat/tickets | No (DLP redacted) | Linter rule 88; regex on inbound text |

## 2. Payment Order FSM

**Deposit:** PENDING → AUTHORIZED → CAPTURED → SETTLED ↘ FAILED ↘ REFUNDED
**Withdrawal:** PENDING → KYC_CHECK → AUTHORIZED → PAYOUT_INITIATED → SETTLED ↘ KYC_FAILED ↘ REJECTED ↘ FAILED

CAPTURED triggers Phase 11 ledger posting in same DB transaction (ADR-0077).
REFUNDED triggers reversal entry (terminal, Phase 11 ADR-0063).

## 3. Webhook Verification Sequence

1. PSP sends webhook to `/api/v1/webhooks/{psp}/`
2. Extract signature header; verify HMAC-SHA256 (constant-time)
3. If signature invalid → 400
4. Extract timestamp; verify within 5-min tolerance
5. If timestamp too old → 400
6. Check nonce cache (Redis) for psp_event_id
7. If nonce seen → 200 (idempotent)
8. Process event (FSM transition + ledger posting in transaction)
9. Store nonce in Redis (TTL = 5 min)
10. Return 200

## 4. Linter Rules 81-90

| Rule | Description |
|---|---|
| 81 | No card field names in code (grep card_number, pan, cvv, cvc, expiry_month, expiry_year, track_data, magstripe). Zero findings. |
| 82 | Key separation: sk_test_ only in dev/test; sk_live_ only in production. |
| 83 | Every webhook endpoint verifies signature before processing; failure → 400. |
| 84 | Every webhook event deduplicated via Phase 8 inbox (idempotency by psp_event_id). |
| 85 | Every payment order status change posts to Phase 11 ledger in same DB transaction. |
| 86 | Every chargeback dispute has FSM transitions audited; deadline alerts configured. |
| 87 | Every payment-related code path goes through PSP port (no direct PSP API calls). |
| 88 | DLP redaction active on all log lines + chat/ticket text; Luhn-validated 13-19 digit numbers redacted. |
| 89 | Every cross-currency payment locks FX rate at order creation (fx_pair_id NOT NULL when currencies differ). |
| 90 | Reconciliation job runs daily; mismatch → alert + HALT. |

## 5. Threat Model Mitigation

| Threat | Mitigation |
|---|---|
| PCI scope creep | SAQ-A boundary + DLP (rules 81, 82, 88); PCI Owner code review |
| Webhook forgery | HMAC-SHA256 signature (rule 83) |
| Webhook replay | Timestamp tolerance + nonce cache (rule 84) |
| Duplicate posting | Idempotency keys + transaction atomicity (rule 85) |
| PSP outage | Outbox queue + retry; alert on queue growth |
| Cross-tenant financial leak | RLS on all payment tables (Phase 5 continuity) |

## 6. Cross-Phase Continuity

- **Phase 4:** Error format (E_PAYMENT_DECLINED, E_PAYMENT_PSP_TIMEOUT, E_PAYMENT_KYC_REQUIRED); structured logging; PII redaction; mypy strict; coverage ≥95%.
- **Phase 5:** RLS on payment_order, payment_method, dispute_case, evidence_pack, webhooks_log.
- **Phase 6:** PSP adapter + reconciliation as service identities (noventra_psp_client, noventra_payments_reconciler).
- **Phase 7:** Event taxonomy: payment.authorized, payment.captured, payment.refunded, payment.failed, dispute.opened, dispute.evidence_submitted, dispute.won, dispute.lost, webhook.received, webhook.replay_rejected.
- **Phase 8:** Payment events via outbox; consumers: risk (Phase 18), compliance (Phase 21).
- **Phase 10:** Evidence packs via storage port (ADR-0054).
- **Phase 11:** Payment→ledger postings (ADR-0077); FX rate locking (ADR-0064); reconciliation extends Phase 11 pattern.

## 7. Concurrency Test Designs

1. Concurrent payment orders with same Idempotency-Key (only one succeeds).
2. Concurrent webhook deliveries of same event (idempotent).
3. Concurrent withdrawal attempts (balance + KYC serialized).
4. Concurrent dispute creation for same order (only one dispute per order).
5. Reconciliation job overlap (only one running; row lock).
6. Payment + ledger posting atomicity (rollback on failure).

## 8. Currency-Mismatch Tests

1. Cross-currency payment without fx_pair_id → rejected.
2. FX rate locked at order creation, not at capture time.
3. Currency mismatch between order and ledger entry → rejected.
