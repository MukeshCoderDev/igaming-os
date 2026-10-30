---
audit_id: AUD-014-005
date: 2026-10-28
auditor: GLM Code AI Agent (Deep Audit — Phases 11-14)
scope: Phase 11 FX Rate Snapshots
verdict: UNVERIFIED
---

# Phase 11 FX Rate Snapshots

## FX Rate Snapshots

| Check | Code Exists | Test | State |
|---|---|---|---|
| FxRateSnapshot table (immutable) | ✅ fx/models.py + migration | MISSING | UNVERIFIED |
| Insert-only trigger | ✅ migration trigger | MISSING | UNVERIFIED |
| Locked at posting (fx_pair_id) | ✅ ledger models has fx_pair_id | MISSING | UNVERIFIED |
| Source-attributed | ✅ model has source field | MISSING | UNVERIFIED |
| Volatility monitoring | MISSING (design only) | MISSING | MISSING |
| Cross-currency without fx_pair_id rejected | MISSING | MISSING | MISSING |

**Verdict: UNVERIFIED.** Model + migration exist. Volatility monitoring
and cross-currency rejection are MISSING.

