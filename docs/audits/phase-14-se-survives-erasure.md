---
audit_id: AUD-014-018
date: 2026-10-28
auditor: GLM Code AI Agent (Deep Audit — Phases 11-14)
scope: Phase 14 SE-survives-erasure
verdict: UNVERIFIED
---

# Phase 14 SE-survives-erasure

## SE-survives-erasure

| Check | Code Exists | Test | State |
|---|---|---|---|
| HMAC pseudonymization | ✅ compute_pseudonymized_identity() | MISSING | UNVERIFIED |
| pseudonymized_identity field | ✅ SelfExclusion model | MISSING | UNVERIFIED |
| check_pseudonymized_identity() | ✅ | MISSING | UNVERIFIED |
| Erasure retains SE record | MISSING (no integration) | MISSING | MISSING |
| Re-registration blocked | MISSING (no integration) | MISSING | MISSING |
| HMAC key rotation strategy | MISSING | MISSING | MISSING |

**Verdict: UNVERIFIED.** HMAC code exists. No erasure + re-registration
integration test. Key rotation strategy MISSING.

