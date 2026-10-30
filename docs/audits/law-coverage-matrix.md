---
audit_id: AUD-010-LAW
date: 2026-10-28
auditor: GLM Code AI Agent (Deep Audit)
scope: 24 Laws × (test exists / negative test / in CI / passing / traceability)
verdict: PARTIAL
---

# Law Coverage Matrix — 24 Laws

## Methodology

For each Law: find in BLUEPRINT, find REQ(s), find ADR(s), find code,
find positive test, find negative test, verify in CI, verify passing.

**Note**: The BLUEPRINT v5.2 references "24 Laws" but the actual
BLUEPRINT.md does not enumerate them as "Law 1" through "Law 24".
The Laws are inferred from the REQ structure (62 REQs across 24
Law-REQ rows). This is itself a finding (Medium): the Laws should be
explicitly enumerated in the BLUEPRINT.

## Matrix

| Law # | Subject (inferred) | REQ(s) | ADR(s) | Code | Positive Test | Negative Test | In CI | Passing | Traceability |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Tenant isolation (RLS fail-closed) | Law-REQ-0010, MB-REQ-0001..0023 | ADR-0003, ADR-0029 | ✅ middleware/tenant.py + RLS policies | ✅ test_tenancy_rls.py | ✅ cross-tenant read=0 rows | ❌ CI not run | ⚠️ unverified | ✅ |
| 2 | Prefiltered isolation (RAG) | (not yet implemented) | — | ❌ Phase 22+ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 3 | Event-sourced domain model | MB-REQ-0012 | ADR-0001 | ✅ domain/aggregates.py | ⚠️ partial | ❌ | ❌ | ⚠️ | ✅ |
| 4 | Ledger (double-entry, append-only) | (not yet implemented) | ADR-0011 (PROPOSED) | ❌ Phase 11 | ❌ | ❌ | ❌ | ❌ | ✅ DEC exists |
| 5 | Hexagonal architecture | MB-REQ-0005..0011 | ADR-0002 | ✅ domain/adapters/api split | ⚠️ structural | ❌ | ❌ | ⚠️ | ✅ |
| 6 | Audit append-only | Law-REQ-0010, MB-REQ-0004 | ADR-0006 | ✅ trigger-enforced | ✅ test_audit_chain.py | ✅ UPDATE/DELETE raises | ❌ CI not run | ⚠️ | ✅ |
| 7 | Event (outbox + at-least-once) | MB-REQ-0012 | ADR-0040 | ✅ outbox_relay.py | ✅ test_reliability_core.py | ⚠️ partial (no state-change-without-outbox lint) | ❌ CI not run | ⚠️ | ✅ |
| 8 | Idempotency keys | MB-REQ-0013 | ADR-0008, ADR-0043 | ✅ middleware/idempotency.py | ✅ test_reliability_core.py | ✅ same key+different body=409 | ❌ CI not run | ⚠️ | ✅ |
| 9 | Immutable audit (hash chain) | Law-REQ-0010 | ADR-0007, ADR-0035 | ✅ trigger + verifier | ✅ test_audit_chain.py | ✅ tamper test | ❌ CI not run | ⚠️ | ✅ |
| 10 | Synchronous revocation | (Phase 10) | ADR-0055 | ✅ document.py is_revoked | ⚠️ domain-only | ❌ no DB trigger test | ❌ | ⚠️ | ✅ |
| 11 | AI boundary (LLM no ledger writes) | (not yet implemented) | — | ❌ Phase 22+ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 12-24 | (Remaining laws not yet implementable; Phase 11+) | Various | Various | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ partial |

## Summary

| Metric | Count |
|---|---|
| Laws with code implemented | 8/24 |
| Laws with positive test | 6/24 |
| Laws with negative test | 4/24 |
| Laws with tests in CI | 0/24 (CI not executed in this audit) |
| Laws with passing tests | ⚠️ unverified (tests not run against live DB) |
| Laws with complete traceability | 10/24 |

**Verdict: PARTIAL.** The 8 implemented Laws have reasonable test
coverage, but:
- No negative tests for Laws 2, 4, 10, 11 (not yet implemented).
- CI pipeline not executed in this audit environment.
- Laws 2, 4, 11, 12-24 are not yet implemented (Phase 11+ scope).

## Critical Findings

1. **Law 2 (Prefiltered Isolation)** — not implemented (Phase 22+).
   No test exists. This is expected but blocks the gate.
2. **Law 4 (Ledger)** — not implemented (Phase 11). This IS the gate
   target; the audit verifies the foundation is ready.
3. **Law 10 (Synchronous Revocation)** — domain model exists but no
   DB trigger test. The is_revoked flag is on the domain model; the
   actual soft-delete + crypto-shredding transaction is not tested
   against a live DB.
4. **Law 11 (AI Boundary)** — not implemented (Phase 22+). No test.
5. **No CI execution** — all tests are written but the CI pipeline
   has not been executed in this audit environment. Tests may pass or
   fail; this is unverified.
