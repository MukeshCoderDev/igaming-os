---
audit_id: AUD-014-009
date: 2026-10-28
auditor: GLM Code AI Agent (Deep Audit — Phases 11-14)
scope: Phase 12 Webhook Signatures & Replay Protection
verdict: MISSING
---

# Phase 12 Webhook Signatures & Replay Protection

## Webhook Verification

| Check | Code Exists | State |
|---|---|---|
| HMAC-SHA256 verification | MISSING | MISSING |
| Timestamp tolerance (5-min) | MISSING | MISSING |
| Nonce cache (Redis) | MISSING | MISSING |
| Idempotency (psp_event_id) | MISSING | MISSING |
| Per-PSP endpoints | MISSING | MISSING |
| Forged signature test | MISSING | MISSING |
| Replay test | MISSING | MISSING |

Design spec exists in `docs/architecture/payments-design.md` §3.

**Verdict: MISSING.** No webhook code exists.

