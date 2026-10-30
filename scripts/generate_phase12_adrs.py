#!/usr/bin/env python3
"""Generate Phase 12 ADR stubs: ADR-0072..0077 (6 ADRs, PROPOSED Stage A)."""

from pathlib import Path

OUT_DIR = Path("/home/z/my-project/docs/adr")
LR = "2026-10-28"
CR = "2026-10-28"

ADRS = [
    (72, "DEC-0072", "PCI Boundary (SAQ-A / Hosted Fields)",
     "PCI Owner", "Phase12",
     "PCI scope creep is the highest-severity threat in Phase 12. A single accidental PAN storage converts Noventra from SAQ-A to SAQ-D.",
     "SAQ-A scope enforced via PSP-hosted fields (Stripe Elements / Adyen Drop-in). Card data never touches Noventra DOM, servers, or logs. Linter rules 81 (no card field names) + 88 (DLP redaction). PSP token handling only.",
     "Alternatives: iframe-only (rejected — PSP SDK cleaner); redirect-based (rejected — worse UX).",
     "PCI scope = SAQ-A only. Quarterly ASV scan required. PCI Owner role required for payment PRs.",
     "Phase 12: linter rules 81, 82, 88 green. SAQ-A self-assessment signed.",
     "PROPOSED", "PCI Owner + CTO + Security Lead"),

    (73, "DEC-0073", "Payment Order Model & Status FSM",
     "Product Owner", "Phase12",
     "Payment orders require explicit FSM with regulatory constraints (withdrawal requires KYC pass per Phase 10).",
     "PaymentOrder model with two FSMs: Deposit (PENDING→AUTHORIZED→CAPTURED→SETTLED/FAILED/REFUNDED) and Withdrawal (PENDING→KYC_CHECK→AUTHORIZED→PAYOUT_INITIATED→SETTLED/KYC_FAILED/REJECTED/FAILED). CAPTURED triggers Phase 11 ledger posting. Uses Phase 8 state machine base.",
     "Alternatives: single FSM (rejected — flows are distinct).",
     "Two FSMs to maintain. KYC integration required for withdrawals.",
     "Phase 12: FSM transition tests; KYC gate test.",
     "PROPOSED", "Product Owner + CFO + Compliance Lead"),

    (74, "DEC-0074", "PSP Port Interface & Sandbox Strategy",
     "API Owner", "Phase12",
     "PSP vendor selection is Q5-blocked. Hexagonal architecture allows port interface + stub adapter.",
     "PspPort interface: authorize/capture/refund/get_status/handle_webhook. SandboxPspAdapter (dev/test). Real adapters (Stripe/Adyen/Square) Q5-blocked. Key separation: sk_test_ in dev only, sk_live_ in prod only (linter rule 82).",
     "Alternatives: direct PSP API calls (rejected — vendor lock-in).",
     "Stub adapter for dev; real adapter deferred. Vendor selection = config change, not code change.",
     "Phase 12: linter rule 82 (key separation); rule 87 (no direct PSP calls).",
     "PROPOSED", "API Owner + CTO + Architecture Lead"),

    (75, "DEC-0075", "Webhook Signatures & Replay Protection",
     "Security Lead", "Phase12",
     "PSPs retry webhooks on non-2xx. Forgery + replay attacks must be prevented.",
     "HMAC-SHA256 signature verified BEFORE any DB write. Timestamp tolerance (5-min). Nonce cache (Redis). Idempotency via Phase 8 inbox by psp_event_id. Per-PSP endpoints.",
     "Alternatives: RSA signatures (rejected — HMAC-SHA256 is standard).",
     "Redis dependency for nonce cache. 5-min tolerance configurable.",
     "Phase 12: signature forgery test; replay test; idempotency test.",
     "PROPOSED", "Security Lead + API Owner + CTO"),

    (76, "DEC-0076", "Chargeback Dispute Workflow & Evidence Pack",
     "Legal Lead", "Phase12",
     "PSPs give 7-14 days to respond to disputes. Logs rotate; PII purges. Evidence must be compiled immediately.",
     "DisputeCase model with FSM (open→evidence_submitted→won/lost/expired/arbitration). Evidence pack auto-generated on dispute.opened via async Celery task. Stored immutably via Phase 10 storage port. 7y retention. Deadline enforcement (missed = auto loss).",
     "Alternatives: on-demand evidence (rejected — risk of missing deadline).",
     "Async task required. Storage port integration. 7y retention.",
     "Phase 12: evidence pack generation test; deadline enforcement test.",
     "PROPOSED", "Legal Lead + CFO + Compliance Lead"),

    (77, "DEC-0077", "Payment-to-Ledger Posting Contract",
     "CFO", "Phase12",
     "Payment order state changes must post to Phase 11 ledger exactly once. PSP retries must not cause duplicate postings.",
     "Posting triggers in same DB transaction as order FSM transition: CAPTURED→debit PSP-clearing/credit player-wallet; REFUNDED→reversal entry; FAILED→no entry. Exactly-once via idempotency key + transaction.atomic(). Daily reconciliation matches PSP statements vs ledger.",
     "Alternatives: async posting via outbox only (rejected — financial integrity requires synchronous).",
     "Payment service must use transaction.atomic() spanning FSM + ledger.",
     "Phase 12: exactly-once tests; reconciliation mismatch test; FX lock test.",
     "PROPOSED", "CFO + External Auditor + Architecture Lead"),
]


def render(n, d, t, o, s, c, dec, a, cons, v, st, ap):
    aid = f"ADR-{n:04d}"
    return f"""---
ADR: {aid}
Title: {t}
Status: {st}
DEC: {d}
Owner: {o}
Scope: {s}
Created: {CR}
Last-Reviewed: {LR}
Supersedes: ""
Superseded-By: ""
Approver: {ap}
---

# {aid} — {t}

## Context

{c}

## Decision

{dec}

## Alternatives

{a}

## Consequences

{cons}

## Validation Plan

{v}

## Decision statement (one line)

{d} → {t}. Owner: {o}. Status: {st}.
Stage A design only — Stage B merge stop active.
Approver: {ap}.

## DEC link

This ADR cites {d} per the ADR-DEC mapping law (DEC-0023, errata E7).
1:1: {d} ↔ {aid}.
"""


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for (n, d, t, o, s, c, dec, a, cons, v, st, ap) in ADRS:
        p = OUT_DIR / f"ADR-{n:04d}.md"
        p.write_text(render(n, d, t, o, s, c, dec, a, cons, v, st, ap))
        print(f"wrote {p} (status={st})")
    print(f"\n{len(ADRS)} new ADRs.")


if __name__ == "__main__":
    main()
