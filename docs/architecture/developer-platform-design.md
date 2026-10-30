# Developer Platform & Player SDK Design Document (Phase 24)

| Field | Value |
|---|---|
| Authority | DEC-0148..0152 | ADR-0147..0151 |
| Status | Stage A Design (Stage B merge stop #14 active) |
| Coverage floor | 95% (per ADR-0027 v2) |
| Owner | Product Owner + Security Owner + API Owner |
| Law mandate | Law 7 (Event — partner webhooks via outbox + DLQ), Law 17 (Receipt — every partner API call produces receipt ID), Law 21 (PCI Boundary — hosted fields in Player SDK); blueprint §21 (B2B wedge); blueprint §12 (sandbox↔prod key confusion); ADR-0020 (Player SDK Conformance Gate — Phase 2 → Phase 24 closure) |

## 1. Architecture Overview

### 1.1 B2B Developer Platform

1. **Partner Key Model** (Prefixed, Scoped, Rotatable; Hash Storage)
2. **Partner Webhooks** (Signed, DLQ, Retry — Phase 12 pattern extended)
3. **Sandbox Tenant** (Isolation; Stub Adapters; Self-Provisioning)
4. **Docs Portal** (API Reference; Integration Guides; SDK Docs; Versioned)
5. **Player SDK + Reference Lobby + Conformance Suite** (Production-Key Gate)

### 1.2 Laws Enforced

- **Law 7 (Event):** partner webhooks via outbox + DLQ.
- **Law 17 (Receipt):** every partner API call produces citable receipt ID.
- **Law 21 (PCI Boundary):** hosted fields in Player SDK (no PAN).

### 1.3 Blueprint References

- §21: "Build second: Engagement & Developer Platform (The B2B Wedge)"
- ADR-0020: Player SDK Conformance Gate (Phase 2 seed → Phase 24 implementation)
- §12: sandbox↔prod key confusion threat (mitigated by prefixed keys)

## 2. Schema Topology

### 2.1 Tables (with RLS — Phase 5 continuity)

**partner_key**: `key_uuid` UUID PK, `tenant_uuid` UUID (RLS), `partner_id` UUID FK, `key_prefix` ENUM (sk_test_/sk_live_), `key_hash` CHAR(64) (SHA-256), `scope` JSONB, `status` ENUM (active/revoked/rotated), `created_at`/`revoked_at`/`last_used_at` TIMESTAMPTZ, `rotated_from` UUID (nullable), `created_by` VARCHAR.

**partner_webhook_endpoint**: `endpoint_uuid` UUID PK, `tenant_uuid` UUID (RLS), `partner_id` UUID, `url` TEXT, `secret_key_hash` CHAR(64), `event_types` TEXT[], `status` ENUM (active/paused), `created_at`/`updated_at`.

**partner_webhook**: `webhook_uuid` UUID PK, `tenant_uuid` UUID (RLS), `partner_id` UUID, `event_type` VARCHAR, `payload` JSONB, `signature` VARCHAR, `status` ENUM (pending/delivered/failed/dlq), `delivery_attempts` INT, `last_attempt_at`/`next_retry_at` TIMESTAMPTZ, `created_at`. Insert-only (Phase 7).

**conformance_result**: `result_uuid` UUID PK, `tenant_uuid` UUID (RLS), `partner_id` UUID, `suite_version` VARCHAR, `test_results` JSONB, `overall_pass` BOOLEAN, `run_at`/`created_at` TIMESTAMPTZ, `run_by` VARCHAR. Insert-only.

### 2.2 DB Constraints

- RLS policies on all tables per Phase 5 pattern.
- Sandbox tenant isolation (linter rule 217).
- Insert-only triggers on partner_webhook, conformance_result (Phase 7 pattern).

## 3. Partner Key Validation Flow

1. Partner API call: `Authorization: Bearer sk_live_...`
2. Extract key; hash it (SHA-256).
3. Lookup PartnerKey by `key_hash`.
4. Verify `status=active`.
5. Verify `key_prefix` matches endpoint environment (linter rule 219).
6. Verify `scope` includes requested action (linter rule 220).
7. Verify rate limit (per partner; per key).
8. Update `last_used_at`.
9. Generate receipt ID (Law 17; linter rule 225).
10. Proceed or deny (401/403).

## 4. Partner Webhook Delivery Flow

1. Event occurs (e.g., `player.deposit_completed`).
2. Outbox event published (Phase 8).
3. PartnerWebhookConsumer:
   - Lookup PartnerWebhookEndpoint for partner.
   - Filter by `event_type`.
   - For each matching endpoint:
     - Sign payload (HMAC-SHA256 with partner's secret key).
     - POST to endpoint URL.
     - On 2xx: `status=delivered`.
     - On 4xx/5xx/timeout: retry with exponential backoff (1min, 5min, 30min, 2hr, 6hr).
     - After 5 failures: `status=dlq`; alert; `PartnerWebhookDeliveryFailure` event.

## 5. Sandbox Tenant Architecture

### 5.1 Isolation
- `tenant.status = 'sandbox'`.
- RLS: sandbox tenants see only sandbox data; production tenants see only production data.
- Linter rule 217: no cross-environment data access.

### 5.2 Stub Adapters (Already Built)
- Phase 12 `SandboxPspAdapter`.
- Phase 19 `StubLLMAdapter`.
- Phase 14 `StubRGAdapter` (replaced by real in Phase 14, but sandbox uses stub).
- Phase 15 `StubGameProviderAdapter`.

### 5.3 Self-Provisioning
- Partner self-provisions via developer portal.
- Automated; no Noventra staff intervention.
- Time-limited (30 days; re-provisionable).
- Rate-limited (per-partner sandbox limits).

### 5.4 Regulatory Exclusion
- Phase 17 GGR/NGR: sandbox excluded.
- Phase 21 compliance/DSAR: sandbox excluded (test data; not real PII).
- Phase 23 billing: sandbox excluded (no real contract).

## 6. Conformance Suite (Production-Key Gate)

### 6.1 Test Categories (9)
1. Auth flow (login; token refresh; logout)
2. Game launch (session; provider callback; round result)
3. Wallet display (balance; authorization-read; real-time)
4. Bonus display (award; wagering; conversion)
5. RG controls (reality check; self-exclusion; limits)
6. Payment flows (deposit; withdrawal; status)
7. Error handling (format; retry; idempotency)
8. Rate limit handling (429; backoff)
9. WebSocket integration (connection; message; kill-switch)

### 6.2 Production-Key Gate
- Partner must pass all categories to obtain `sk_live_` key.
- Conformance run: automated; triggered by partner via developer portal.
- Result stored (ConformanceResult); audited (Phase 7).
- Linter rule 218: no production PartnerKey without conformance pass.
- Non-conforming: production keys denied; partner must fix and re-test.

### 6.3 ADR-0020 Closure
Blueprint ADR-0020 (Player SDK Conformance Gate) seeded in Phase 2. Phase 24 implements it.
Long-arc governance: Phase 2 ADR stub → Phase 24 implementation.

## 7. Linter Rules 216-225 (Phase 24)

| Rule | Description |
|---|---|
| 216 | Phase 24 ADRs 0147-0151 all exist |
| 217 | ADR-0147 documents partner keys (prefix + scope + hash + rotation) |
| 218 | ADR-0148 documents partner webhooks (HMAC + signature + DLQ + retry) |
| 219 | ADR-0149 documents sandbox tenant (isolation + stub + self-provisioning) |
| 220 | ADR-0150 documents docs portal (OpenAPI + versioning + partner auth) |
| 221 | ADR-0151 documents Player SDK (reference lobby + conformance + gate + ADR-0020) |
| 222 | Phase 24 design doc exists |
| 223 | Phase 24 stage handoff exists |
| 224 | Phase 24 audit exists |
| 225 | OQ-DEV-001..006 + design doc contracts (partner + webhook + sandbox + conformance + SDK + sk_test_ + sk_live_ + ADR-0020 + blueprint + receipt + DLQ) |

## 8. Cross-Phase Continuity

### Phase 4 contracts
- Error format: `E_PARTNER_KEY_INVALID`, `E_PARTNER_KEY_REVOKED`, `E_PARTNER_KEY_SCOPE_INSUFFICIENT`, `E_SANDBOX_KEY_ON_PROD`, `E_PROD_KEY_ON_SANDBOX`, `E_CONFORMANCE_NOT_PASSED`, `E_WEBHOOK_SIGNATURE_INVALID`
- Structured logging with `correlation_id`, `tenant_id`, `partner_id`, `key_id`, `receipt_id`
- mypy strict on developer_platform module; coverage ≥95%

### Phase 5 RLS extension
- All developer platform tables tenant-scoped; sandbox tenant isolation (rule 217).

### Phase 6 service identity continuity
- Partner keys are service identities (`typ=service`).
- Scoped permissions (RBAC per Phase 6).

### Phase 7 audit extension
- Event type taxonomy: `partner.key_created`, `partner.key_revoked`, `partner.key_rotated`, `partner.webhook_delivered`, `partner.webhook_failed`, `partner.webhook_dlq`, `partner.conformance_run`, `partner.conformance_passed`, `partner.conformance_failed`, `partner.sandbox_provisioned`.

### Phase 8 outbox + DLQ continuity
- Partner webhooks via outbox.
- DLQ per Phase 8 pattern.

### Phase 12 webhook pattern continuity
- HMAC-SHA256 signatures (ADR-0075 pattern).
- Key separation (`sk_test_` vs `sk_live_` — ADR-0074 pattern).

### Phase 13/14 sandbox stub continuity
- Sandbox tenant uses stub RGPort/JurisdictionPort.
- Real adapters available for testing real flows.

### Phase 15 game platform continuity
- Player SDK launches games (Phase 15 game session).
- Provider callback handling.

### Phase 19 AI platform continuity
- Docs portal may use Phase 19 RAG for search.
- LLM Gateway for AI-powered docs (Q5-blocked; stub for dev).

### Phase 23 contract continuity
- Partner key scoped per contract (Phase 23 Contract.scope).
- Sandbox tenant excluded from billing (Phase 23).

## 9. Threat Model Mitigation

| Threat | Mitigation |
|---|---|
| Sandbox/prod key confusion (blueprint §12) | Prefixed keys (sk_test_ vs sk_live_); linter rule 219 |
| Partner key compromise | Rotation; revocation; hash storage (no plaintext) |
| Partner key scope escalation | Scope check on every call (rule 220) |
| Webhook forgery | HMAC-SHA256 signatures (rule 222) |
| Webhook delivery failure | Retry + DLQ (rule 223) |
| Broken partner integration in production | Conformance suite gate (rule 218) |
| Sandbox data leak to production | Tenant isolation (rule 217) |
| Cross-tenant partner data leak | RLS on all developer platform tables (Phase 5) |
| Unaudited partner actions | Audit events (rule 224) |
| No receipt for partner API calls | Receipt ID generation (rule 225; Law 17) |

## 10. Concurrency Test Designs (Stage B)

1. Concurrent partner key validation (idempotent; per-key).
2. Concurrent partner webhook delivery (per-endpoint; idempotent via event ID).
3. Concurrent conformance runs (per-partner; only one at a time).
4. Concurrent sandbox provisioning (per-partner; idempotent).
5. Concurrent partner API calls (rate limit enforced; per-key).
6. Concurrent key rotation (old key revoked; new key active; no overlap).

## 11. Acceptance Criteria Tests

### 11.1 Sandbox Keys Rejected on Prod Endpoints
- Test: `sk_test_` key on prod endpoint → 401 (`E_SANDBOX_KEY_ON_PROD`).
- Test: `sk_live_` key on sandbox endpoint → 401 (`E_PROD_KEY_ON_SANDBOX`).
- Linter rule 219.

### 11.2 Webhooks Signed + DLQ'd
- Test: webhook delivery + signature verification (partner verifies HMAC-SHA256).
- Test: webhook delivery failure → retry (5 attempts) → DLQ.
- Test: DLQ alert fires.
- Test: DLQ replay (idempotent).
- Linter rules 222, 223.

### 11.3 Non-Conforming Frontend Cannot Obtain Prod Keys
- Test: non-conforming frontend → conformance suite fails → production keys denied (`E_CONFORMANCE_NOT_PASSED`).
- Test: conforming frontend → conformance suite passes → production keys issued (`sk_live_`).
- Linter rule 218.

## 12. Performance Targets

- Partner API call latency: <200ms p99 (auth + scope check + processing).
- Partner webhook delivery: <5s p99 (sign + POST + verify).
- Conformance suite run: <30 minutes (all 9 categories).
- Sandbox provisioning: <60 seconds (automated).
- Docs portal load: <2s p99 (static + dynamic).

## 13. Open Questions (OQ-DEV-001..006)

| ID | Question | Owner | Due | Status |
|---|---|---|---|---|
| OQ-DEV-001 | Partner key scope catalog (closed?) | API Owner + Product Owner | Phase 24 Stage A | OPEN |
| OQ-DEV-002 | Sandbox tenant TTL (30 days recommended) | Product Owner | Phase 24 Stage A | OPEN |
| OQ-DEV-003 | Reference lobby license (MIT or Apache 2.0) | Legal Counsel | Phase 24 Stage A | OPEN |
| OQ-DEV-004 | Conformance suite hosting (Noventra vs partner) | Product Owner + Reliability Owner | Phase 24 Stage A | OPEN |
| OQ-DEV-005 | Docs portal AI search (Phase 19 RAG; Q5-blocked) | Product Owner | Phase 25 | Q5-BLOCKED |
| OQ-DEV-006 | Partner webhook retry schedule (1min/5min/30min/2hr/6hr) | Reliability Owner | Phase 24 Stage A | OPEN |
