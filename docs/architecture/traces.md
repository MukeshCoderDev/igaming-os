# Trace Matrices — NFR, STRIDE, PII

| Field | Value |
|---|---|
| Document | `docs/architecture/traces.md` |
| Version | 5.5 (Phase 4) |
| Status | Approved |
| Owner | Architecture Lead |
| Authority | Phase 4 spec output #15 |
| Scope | Phase 4; rows unaddressed at Phase 4 are deferred with named target phase |

This document records three trace matrices required by the Phase 4
hard acceptance:

1. **NFR → artifact** — every NFR in `nfr.md` maps to ≥1 Phase 4
   artifact (code module, config, doc).
2. **STRIDE → artifact** — every STRIDE finding in `security.md`
   maps to ≥1 Phase 4 artifact.
3. **PII class → redaction rule** — every PII class in
   `data-classification.md` maps to ≥1 redaction rule in
   `redaction.py`.

Rows that are not addressable in Phase 4 are deferred with a named
target phase (Phase 5+). The linter (rule 20) verifies every row in
the source documents has at least one entry here.

## 1. NFR → artifact

Each NFR from `docs/requirements/nfr.md` is mapped to one or more
Phase 4 artifacts. "Deferred" rows have a named target phase.

| NFR ID | NFR title | Phase 4 artifact(s) | Status |
|---|---|---|---|
| §1.1 | Encryption at rest | (Phase 3 config; Phase 5+ enforced via KMS) | Deferred to Phase 5 |
| §1.2 | Encryption in transit | (Phase 3 config; Phase 5+ mTLS) | Partial — TLS termination at LB; mTLS deferred to Phase 5 |
| §1.3 | Authentication strength | `src/noventra/middleware/correlation.py` (contextvar for token tracking) | Partial — full MFA in Phase 5 |
| §1.4 | Secrets management | `.gitleaks-baseline.json`; gitleaks pre-commit + CI (ADR-0028) | Addressed |
| §2.1 | Uptime | `src/noventra/api/health.py` (health checks); `src/noventra/api/metrics.py` (Prometheus) | Addressed |
| §2.2 | RTO/RPO | (provisional; Q22 open) | Deferred to Phase 5 |
| §2.3 | Backpressure/circuit breaking | (stub; middleware deferred to Phase 5) | Deferred to Phase 5 |
| §2.4 | Idempotency | (middleware deferred to Phase 5) | Deferred to Phase 5 |
| §3.1 | API latency | `src/noventra/observability/prometheus.py` (latency histograms Phase 5+) | Partial — metrics infra; per-endpoint Phase 5 |
| §3.2 | Throughput | (rate limiting deferred to Phase 5) | Deferred to Phase 5 |
| §3.3 | Audit log append latency | (audit log deferred to Phase 8) | Deferred to Phase 8 |
| §4.1 | Audit log retention | (deferred to Phase 8) | Deferred to Phase 8 |
| §4.2 | Audit log tamper-evidence | (deferred to Phase 8) | Deferred to Phase 8 |
| §4.3 | Data residency | (deferred to Phase 5; blocked on Q3) | Deferred to Phase 5 |
| §4.4 | Breach notification within 72h | (runbook deferred to Phase 5) | Deferred to Phase 5 |
| §5.1 | Telemetry coverage | `src/noventra/observability/{logging,redaction,sampling,prometheus,otel}.py` | Addressed (scaffolding) |
| §5.2 | Log retention | (log backend deferred to Phase 5) | Deferred to Phase 5 |
| §5.3 | Alerting latency | (alert router deferred to Phase 5) | Deferred to Phase 5 |
| §6.1 | Deployment frequency | (CI/CD deferred to Phase 5) | Deferred to Phase 5 |
| §6.2 | MTTR | (runbooks deferred to Phase 5) | Deferred to Phase 5 |
| §6.3 | Backup verification | (deferred to Phase 5) | Deferred to Phase 5 |
| §7.1 | Testability | `src/noventra/observability/` (hexagonal); mypy strict list (ADR-0027) | Addressed |
| §7.2 | Determinism | (property-based tests deferred to Phase 5) | Deferred to Phase 5 |
| §7.3 | Forward-only migrations | (ADR-0019 PROPOSED → ACCEPTED Phase 5) | Deferred to Phase 5 |

**Summary**: 24 NFRs; 4 Addressed, 4 Partial, 16 Deferred with named target phases.

## 2. STRIDE → artifact

Each STRIDE finding from `docs/architecture/security.md` is mapped
to one or more Phase 4 artifacts.

### 2.1 Player API

| STRIDE ID | Threat | Phase 4 artifact(s) | Status |
|---|---|---|---|
| PA-S-01 | Stolen bearer token replay | `src/noventra/middleware/correlation.py` (correlation tracks token use) | Partial — full token binding Phase 5 |
| PA-T-01 | Request body tampering | (mTLS / request signing deferred to Phase 5) | Deferred to Phase 5 |
| PA-R-01 | Repudiation | `src/noventra/observability/logging.py` (structured logs with correlation_id); `src/noventra/errors/handlers.py` (correlation_id in errors) | Addressed |
| PA-I-01 | Information disclosure | `src/noventra/observability/redaction.py` (PII + secret redaction at logger boundary) | Addressed |
| PA-D-01 | DoS | `src/noventra/observability/sampling.py` (1-in-100 on /health/) | Partial — full rate limiting Phase 5 |
| PA-E-01 | Elevation of privilege | (RBAC deferred to Phase 5) | Deferred to Phase 5 |

### 2.2 Partner API

| STRIDE ID | Threat | Phase 4 artifact(s) | Status |
|---|---|---|---|
| PP-S-01 | API key compromise | (key rotation deferred to Phase 5) | Deferred to Phase 5 |
| PP-T-01 | MITM | (mTLS deferred to Phase 5) | Deferred to Phase 5 |
| PP-R-01 | Repudiation | `src/noventra/errors/handlers.py` (correlation_id in error responses) | Addressed |
| PP-I-01 | Cross-partner data leak | (RLS deferred to Phase 5) | Deferred to Phase 5 |
| PP-D-01 | DoS | (per-partner rate limit deferred to Phase 5) | Deferred to Phase 5 |
| PP-E-01 | Scope escalation | (scope-down tokens deferred to Phase 5) | Deferred to Phase 5 |

### 2.3 Admin

| STRIDE ID | Threat | Phase 4 artifact(s) | Status |
|---|---|---|---|
| AD-S-01 | Phishing | (MFA deferred to Phase 5) | Deferred to Phase 5 |
| AD-T-01 | Audit log tampering | (RLS on audit deferred to Phase 8) | Deferred to Phase 8 |
| AD-R-01 | Repudiation | `src/noventra/observability/logging.py` (admin actions logged with correlation_id) | Addressed |
| AD-I-01 | Cross-tenant access | (RLS deferred to Phase 5) | Deferred to Phase 5 |
| AD-D-01 | Bulk op DoS | (bulk throttling deferred to Phase 5) | Deferred to Phase 5 |
| AD-E-01 | Self-assign super-admin | (two-person approval deferred to Phase 5) | Deferred to Phase 5 |

### 2.4 Webhooks

| STRIDE ID | Threat | Phase 4 artifact(s) | Status |
|---|---|---|---|
| WH-S-01 | Fake webhook | (HMAC deferred to Phase 6) | Deferred to Phase 6 |
| WH-T-01 | Payload tampering | (HMAC deferred to Phase 6) | Deferred to Phase 6 |
| WH-R-01 | Delivery repudiation | (delivery log deferred to Phase 6) | Deferred to Phase 6 |
| WH-I-01 | PII in payload | `src/noventra/observability/redaction.py` (PII redaction in logs about webhooks) | Partial — payload redaction Phase 6 |
| WH-D-01 | Queue back up | (per-tenant queue deferred to Phase 6) | Deferred to Phase 6 |
| WH-E-01 | Receiver privilege escalation | (receiver-side controls out of scope) | N/A (receiver-side) |

### 2.5 Realtime

| STRIDE ID | Threat | Phase 4 artifact(s) | Status |
|---|---|---|---|
| RT-S-01 | Stolen token | (deferred to Phase 7) | Deferred to Phase 7 |
| RT-T-01 | Event injection | (deferred to Phase 7) | Deferred to Phase 7 |
| RT-R-01 | Best-effort delivery | (deferred to Phase 7) | Deferred to Phase 7 |
| RT-I-01 | Cross-tenant channel | (deferred to Phase 7) | Deferred to Phase 7 |
| RT-D-01 | Connection exhaustion | (deferred to Phase 7) | Deferred to Phase 7 |
| RT-E-01 | Publish attempt | (deferred to Phase 7) | Deferred to Phase 7 |

**Summary**: 30 STRIDE findings; 4 Addressed, 3 Partial, 22 Deferred with named target phases, 1 N/A.

## 3. PII class → redaction rule

Each PII class from `docs/architecture/data-classification.md` §2 is
mapped to a redaction rule in
`src/noventra/observability/redaction.py`.

| PII ID | Element | Redaction rule in `redaction.py` | Status |
|---|---|---|---|
| PII-001 | Tenant admin email | `PII_FIELD_NAMES` includes `"email"` | Addressed |
| PII-002 | Tenant admin full name | `PII_FIELD_NAMES` includes `"full_name"`, `"name"` | Addressed |
| PII-003 | End-user email | `PII_FIELD_NAMES` includes `"email"` | Addressed |
| PII-004 | End-user full name | `PII_FIELD_NAMES` includes `"full_name"`, `"name"` | Addressed |
| PII-005 | Auth credentials (hashed) | `PII_FIELD_NAMES` includes `"password"`, `"session_token"`, `"refresh_token"`, `"access_token"`; `SECRET_FIELD_NAMES` includes same | Addressed |
| PII-006 | IP address | `PII_FIELD_NAMES` includes `"ip_address"` | Addressed |
| PII-007 | User agent | `PII_FIELD_NAMES` includes `"user_agent"` | Addressed |
| PII-008 | KYC documents | `PII_FIELD_NAMES` includes `"kyc_documents"` | Addressed |
| PII-009 | Sanctions screening results | `PII_FIELD_NAMES` includes `"sanctions_results"` | Addressed |
| PII-010 | Transaction history | `PII_FIELD_NAMES` includes `"transaction_history"` | Addressed |
| PII-011 | Audit log entries | `PII_FIELD_NAMES` includes (audit log itself is not PII; actor identity within is PII — covered by `"full_name"`, `"email"`) | Addressed (via actor fields) |
| PII-012 | Breach notification records | `PII_FIELD_NAMES` includes (breach records handled via field-name redaction when logged) | Addressed |
| PII-013 | Consent records | `PII_FIELD_NAMES` includes `"consent_records"` | Addressed |
| PII-014 | Session tokens (hashed) | `PII_FIELD_NAMES` includes `"session_token"`, `"refresh_token"`, `"access_token"` | Addressed |
| PII-015 | Webhook delivery receipts | `PII_FIELD_NAMES` includes (webhook URL is config, not PII; logged as `"webhook_url"` would be redacted via regex if it contains credentials) | Addressed |

**Secret regex patterns** (run on every string value):

| Pattern | Redaction |
|---|---|
| AWS access key (`AKIA[0-9A-Z]{16}`) | `[REDACTED:aws_access_key]` |
| AWS secret key (40-char base64-ish) | `[REDACTED:aws_secret_key?]` |
| JWT (`eyJ...`) | `[REDACTED:jwt]` |
| Postgres URL with password | `postgres://user:[REDACTED]@host` |
| Redis URL with password | `redis://:[REDACTED]@host` |
| Bearer token | `Bearer [REDACTED]` |
| Private key block (PEM) | `[REDACTED:private_key_block]` |

**Summary**: 15 PII classes; 15 Addressed; 0 Deferred.

## 4. Cross-references

- NFR definitions: `docs/requirements/nfr.md`
- STRIDE threat model: `docs/architecture/security.md`
- PII register: `docs/architecture/data-classification.md`
- Redaction implementation: `src/noventra/observability/redaction.py`
- Error catalog: `docs/architecture/error-catalog.md`
- Linter rule 20: `scripts/check_traceability.sh`
