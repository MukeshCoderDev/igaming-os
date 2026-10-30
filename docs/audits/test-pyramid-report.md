---
audit_id: AUD-010-TEST
date: 2026-10-28
auditor: GLM Code AI Agent (Deep Audit)
scope: Counts; ratios; coverage per module; property/fuzz tests
verdict: RED
---

# Test Pyramid Report

## Test Counts

| Category | Count | Target % | Actual % |
|---|---|---|---|
| Unit tests | ~150 | 70% | ~76% |
| Integration tests | ~40 | 20% | ~20% |
| E2e tests | 0 | 10% | 0% |
| Property-based tests (Hypothesis) | 0 | (recommended) | 0% |
| Fuzz tests (Atheris) | 0 | (recommended) | 0% |
| **Total** | **~197** | | |

## Test Files

| File | Tests | Type |
|---|---|---|
| test_health.py | 3 | Unit |
| test_redaction.py | 10 | Unit |
| test_correlation.py | 6 | Unit |
| test_catalog.py | 8 | Unit |
| test_errors.py | 5 | Unit |
| test_sampling.py | 4 | Unit |
| test_tenancy_rls.py | 8 | Integration (requires DB) |
| test_pgbouncer.py | 4 | Integration (requires DB) |
| test_identity_rbac.py | 19 | Unit + Integration |
| test_audit_chain.py | 20 | Integration (requires DB) |
| test_reliability_core.py | 20 | Unit + Integration |
| test_players_consents.py | 15 | Unit + Integration |
| test_kyc_documents.py | 30 | Unit |

## Coverage Per Module

| Module | Target | Actual | Status |
|---|---|---|---|
| Phase 3 (settings, health, middleware) | ≥80% | ⚠️ Not measured | RED |
| Phase 5 (tenancy, RLS) | ≥80% | ⚠️ Not measured | RED |
| Phase 6 (identity, RBAC) | ≥80% | ⚠️ Not measured | RED |
| Phase 7 (audit, hash chain) | ≥85% | ⚠️ Not measured | RED |
| Phase 8 (reliability) | ≥85% | ⚠️ Not measured | RED |
| Phase 9 (players, consents) | ≥90% | ⚠️ Not measured | RED |
| Phase 10 (KYC, documents) | ≥90% | ⚠️ Not measured | RED |
| Diff coverage | ≥80% | ⚠️ Not measured | RED |
| Branch coverage (Phase 8+) | Mandatory | ⚠️ Not measured | RED |

**Finding (Critical)**: No coverage measurement has been executed.
Coverage thresholds are specified in ADR-0027 but never verified
against actual code. The `--cov` flag is in CI configuration but CI
has not been run.

## Findings

| # | Severity | Finding |
|---|---|---|
| 1 | Critical | No coverage measurement executed; all thresholds unverified |
| 2 | High | Zero property-based tests (Hypothesis recommended for RLS + hash chain) |
| 3 | High | Zero fuzz tests (Atheris recommended for input surfaces) |
| 4 | High | Zero e2e tests (target 10% of pyramid) |
| 5 | Medium | No branch coverage measurement (mandatory from Phase 8) |
| 6 | Medium | ADR-0027 v2 coverage curve amendment not recorded |
