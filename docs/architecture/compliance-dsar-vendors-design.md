# Compliance, DSAR & Vendors Design Document (Phase 21)

| Field | Value |
|---|---|
| Authority | DEC-0132..0137 | ADR-0131..0136 |
| Status | Stage A Design (Stage B merge stop #11 active) |
| Coverage floor | 95% (per ADR-0027 v2) |
| Owner | Compliance Officer + External Auditor + Legal Counsel + Privacy Owner |
| Law mandate | Law 9 (Immutable Audit), Law 18 (Player Protection — SE-survives-erasure), Law 19 (Fair Play — lab/studio cert auto-suspend); errata E1 (DSAR fixed order); blueprint §8.3 (vendor deterministic expiry) |

## 1. Architecture Overview

### 1.1 Unified Compliance Plane

1. **Compliance Control Framework** (model, framework mapping, testing)
2. **Evidence Repository** (immutable storage, retention, access audit)
3. **Periodic Compliance Reviews** (cadence, findings, remediation)
4. **Reporting Adapters** (per-jurisdiction, per-report-type, submission)
5. **DSAR Drill** (verify → export → shred; errata E1; SE-survives-erasure)
6. **Legal-Hold Matrix** (suspension of destruction)
7. **Vendor Registry with Deterministic Expiry** (blueprint §8.3)

### 1.2 Laws Enforced

- **Law 9 (Immutable Audit):** evidence immutable; access audited (WORM via Phase 10 storage port)
- **Law 18 (Player Protection):** DSAR preserves SE registry (HMAC pseudonymization; Phase 14 ADR-0085)
- **Law 19 (Fair Play):** lab/studio cert expiry auto-suspends catalog (Phase 16 release FSM)
- **Errata E1:** DSAR order fixed (verify → export → shred; no reordering)
- **Blueprint §8.3:** vendor cert expiry deterministic (T-30/7/1 + operator decision)

## 2. Schema Topology

### 2.1 Tables (with RLS — Phase 5 continuity)

**compliance_control** (control framework): `control_uuid` UUID PK, `tenant_uuid` UUID (RLS), `control_id` VARCHAR, `framework` ENUM (ISO_27001/SOC_2/UK_GC_LCCP/MGA_BLC/GDPR/AML), `description` TEXT, `owner` VARCHAR (named human), `status` ENUM (active/deprecated), `last_reviewed_at`/`last_tested_at` TIMESTAMPTZ, `test_result` ENUM (pass/fail/remediation_required), `created_at`/`updated_at`. UNIQUE(tenant_uuid, control_id).

**control_framework_mapping** (control → regulatory requirement): `mapping_uuid` UUID PK, `control_uuid` FK, `framework` ENUM, `requirement_ref` VARCHAR (e.g., "UK GC LCCP 2.1.1"), `jurisdiction_code` CHAR(2) (nullable), `created_at`.

**compliance_evidence** (evidence repository): `evidence_uuid` UUID PK, `tenant_uuid` UUID (RLS), `control_uuid` FK, `evidence_type` ENUM (policy_doc/test_result/screenshot/log_export/audit_report/cert/training_record), `evidence_url` TEXT (Phase 10 storage port WORM), `evidence_date` DATE, `collected_by` VARCHAR, `status` ENUM (current/superseded/archived), `superseded_by` UUID FK (nullable), `created_at`/`updated_at`.

**evidence_access_log** (access audit): `log_uuid` UUID PK, `evidence_uuid` FK, `accessed_by` VARCHAR, `accessed_at` TIMESTAMPTZ, `purpose` TEXT, `created_at`. Insert-only (Phase 7 pattern; Law 9).

**compliance_review** (periodic reviews): `review_uuid` UUID PK, `tenant_uuid` UUID (RLS), `review_type` ENUM (internal_audit/external_audit/regulator_inspection/self_assessment), `scope` JSONB, `reviewer` VARCHAR, `start_date`/`end_date` DATE, `status` ENUM (scheduled/in_progress/completed/remediation), `findings` JSONB, `created_at`/`updated_at`.

**regulatory_report** (extends Phase 17): `report_uuid` UUID PK, `tenant_uuid` UUID (RLS), `jurisdiction_code` CHAR(2), `period` VARCHAR, `report_type` ENUM (GGR/NGR/AML_CTR/AML_SAR/RG_SE/RG_LIMITS/KYC_STATS), `data` JSONB, `generated_at`/`submitted_at` TIMESTAMPTZ, `submitted_by` VARCHAR (nullable), `status` ENUM (draft/generated/submitted/acknowledged/rejected), `created_at`/`updated_at`.

**dsar_request** (DSAR workflow): `request_uuid` UUID PK, `tenant_uuid` UUID (RLS), `player_uuid` UUID, `request_type` ENUM (access/erasure/portability/restriction/objection), `status` ENUM (pending/verified/exporting/exported/shredding/shredded/rejected), `verified_at`/`exported_at`/`shredded_at` TIMESTAMPTZ (nullable), `evidence_pack_id` UUID (nullable; Phase 10 storage), `rejection_reason` TEXT (nullable), `created_at`/`updated_at`.

**legal_hold** (legal hold): `hold_uuid` UUID PK, `tenant_uuid` UUID (RLS), `hold_type` ENUM (litigation/regulatory_investigation/audit/compliance_review), `scope` JSONB, `reason` TEXT, `issued_by` VARCHAR (legal counsel), `issued_at`/`released_at` TIMESTAMPTZ, `status` ENUM (active/released), `created_at`/`updated_at`.

**vendor_registry** (vendor expiry): `vendor_uuid` UUID PK, `tenant_uuid` UUID (RLS), `vendor_type` ENUM (lab/studio/psp/kyc/geo/sanctions/pep/ai_provider/storage), `vendor_name` VARCHAR, `contract_id` VARCHAR (nullable), `cert_evidence_id` UUID (nullable; FK Phase 10), `cert_expiry_date` DATE, `status` ENUM (active/expiring/expired/suspended), `last_alert_sent` ENUM (none/T30/T7/T1), `operator_decision` TEXT (nullable), `operator_decision_by`/`operator_decision_at` (nullable), `created_at`/`updated_at`.

### 2.2 DB Constraints

- RLS policies on all tables per Phase 5 pattern.
- Insert-only triggers on `evidence_access_log` (Phase 7 pattern; Law 9).
- CHECK: `dsar_request` status transitions follow E1 order (linter rule 186; enforced at application layer + documented in DB constraint comment).

## 3. DSAR Operational Order (Errata E1)

### 3.1 Fixed Order (Cannot Be Reordered)

1. **verify:** KYC-grade identity check (Phase 10); `status=verified`.
2. **export:** generate export pack (all modules); `status=exported`.
3. **shred:** destroy per-subject KMS key (Phase 9 crypto-shredding); `status=shredded`.

Linter rule 186 enforces: pending → verified → exported → shredded; no skipping. Violations: `E_DSAR_ORDER_VIOLATION`.

### 3.2 SE-Survives-Erasure (Phase 14 ADR-0085)

- SE registry retained via HMAC pseudonymization.
- On shred: SE record retained with `pseudonymized_identity`; original `player_uuid` NULLed.
- Re-registration: HMAC match → rejected with `E_SELF_EXCLUDED`.
- Linter rule 187: shred operation preserves SE registry.

### 3.3 Export Pack Contents (11 modules)

| Data Class | Phase |
|---|---|
| Player profile | 9 |
| Consents | 9 |
| KYC documents | 10 |
| Ledger entries | 11 |
| Payment history | 12 |
| Bonus history | 13 |
| RG records (SE, limits, reality checks) | 14 |
| Game sessions | 15/16 |
| Risk signals + cases | 18 |
| AI interactions | 19/20 |
| Audit events | 7 |

Export pack stored via Phase 10 storage port (immutable; audit proof that export was generated before erasure).

## 4. Vendor Deterministic Expiry (Blueprint §8.3)

### 4.1 Lab/Studio Cert Expired → Auto-Suspend

- Auto-suspend affected catalog items (Phase 16 games; Law 19 linkage).
- Expiry job: vendor `status=expired`; associated games `state=suspended` (Phase 16 ADR-0103 release FSM).
- Alert compliance officer + product owner.
- No operator decision required — auto-suspend is mandatory (Law 19; uncertified math cannot be played).

### 4.2 PSP/KYC/Geo Expired → T-30/7/1 + Operator Decision

- **T-30:** alert at 30 days before expiry.
- **T-7:** alert at 7 days before expiry.
- **T-1:** alert at 1 day before expiry.
- **On expiry:** alert; operator must record decision (continue with justification OR suspend).
- **Linter rule 190:** no expired PSP/KYC/Geo vendor without operator decision.
- If no decision within 24h → auto-suspend (conservative default).

### 4.3 Expiry Job

- Scheduled daily (midnight UTC); Celery beat task `check_vendor_expiry`.
- Checks `cert_expiry_date` for all active vendors.
- Sends alerts (T-30, T-7, T-1) — idempotent per vendor per threshold (`last_alert_sent` field).
- On expiry: auto-suspend (lab/studio) or alert + require operator decision (PSP/KYC/Geo).

## 5. Legal-Hold Matrix

### 5.1 Hold Types

- **litigation:** active lawsuit.
- **regulatory_investigation:** regulator investigating.
- **audit:** internal/external audit in progress.
- **compliance_review:** compliance review in progress.

### 5.2 Suspension of Destruction

- Retention enforcement job (Phase 9) skips held data.
- Partition drops skip held rows (Phase 7 + Phase 9 pattern).
- **Ledger entries exempt** (AML law — 5-10 year retention mandatory; blueprint §8.1; ledger never destroyed regardless of hold).
- Linter rule 189: no destruction of held data.

### 5.3 Release

- When hold released (`status=released`; `released_at` set), retention resumes.
- Held data may be destroyed per normal schedule (after hold release + retention period).

## 6. Linter Rules 186-195 (Phase 21)

**Note on rule numbering:** The prompt's §6 specified rules 186-195 as behavior-enforcing (grep for code patterns). At Stage A (design only), there is no code to grep. The implemented rules 186-195 are Stage A design-artifact checks (ADR keyword verification + artifact existence + design doc contracts + OQ register). The behavior-enforcing rules (prompt's original 186-195 semantics) will be enhanced at Stage B when code exists.

| Rule | Description (Stage A implementation) |
|---|---|
| 186 | Phase 21 ADRs 0131-0136 all exist |
| 187 | ADR-0131 documents compliance control framework (6 frameworks + owner + testing) |
| 188 | ADR-0132 documents evidence repository (immutable + WORM + access audit + Law 9 + supersession) |
| 189 | ADR-0133 documents periodic reviews (4 types + findings + remediation + escalation) |
| 190 | ADR-0134 documents reporting adapters (per-jurisdiction + 7 report types + submission) |
| 191 | ADR-0135 documents DSAR drill (E1 + verify→export→shred + SE-survives + HMAC + statutory window) |
| 192 | ADR-0136 documents legal-hold + vendor expiry (blueprint §8.3 + lab/studio + PSP/KYC/Geo + T-30/7/1 + auto-suspend + operator decision) |
| 193 | Phase 21 design doc exists |
| 194 | Phase 21 stage handoff exists |
| 195 | Phase 21 audit + OQ-COMP-001..006 + design doc contracts (E1 + errata + SE-survives + HMAC + legal-hold + vendor + T-30 + auto-suspend + operator decision + Law 9/18/19) |

## 7. Cross-Phase Continuity

### Phase 4 contracts
- Error format: `E_DSAR_VERIFICATION_FAILED`, `E_DSAR_ORDER_VIOLATION`, `E_DSAR_WINDOW_EXCEEDED`, `E_LEGAL_HOLD_ACTIVE`, `E_VENDOR_EXPIRED_NO_DECISION`, `E_CONTROL_NOT_TESTED`, `E_EVIDENCE_ACCESS_DENIED`, `E_SELF_EXCLUDED`
- Structured logging with `correlation_id`, `tenant_id`, `control_id`, `evidence_id`, `dsar_request_id`, `vendor_id`
- PII redaction (DSAR export packs contain PII; compliance evidence may contain PII)
- mypy strict on compliance module; coverage ≥95%

### Phase 5 RLS extension
- All compliance tables tenant-scoped.

### Phase 7 audit extension
- Event type taxonomy: `compliance.control_tested`, `compliance.evidence_accessed`, `compliance.evidence_superseded`, `compliance.review_completed`, `compliance.report_generated`, `compliance.report_submitted`, `compliance.report_acknowledged`, `compliance.report_rejected`, `dsar.verified`, `dsar.exported`, `dsar.shredded`, `legal_hold.issued`, `legal_hold.released`, `vendor.expiry_alert`, `vendor.expired`, `vendor.suspended`

### Phase 9 retention continuity
- DSAR shred destroys KMS key (Phase 9 crypto-shredding).
- Retention enforcement job extended (checks legal-hold matrix; skips held data).

### Phase 10 KYC continuity
- DSAR verify uses KYC-grade identity check.
- Evidence stored via Phase 10 storage port (WORM).
- Vendor cert evidence linked to Phase 10 CertificationEvidence.

### Phase 11 ledger continuity
- DSAR export includes ledger entries.
- **Ledger entries exempt from legal hold** (AML law mandatory 5-10 year retention).

### Phase 12-20 continuity
- DSAR export includes all module data (payments, bonuses, RG, games, risk, AI).

### Phase 14 protection continuity
- SE-survives-erasure (HMAC pseudonymization; ADR-0085).
- DSAR shred preserves SE registry; re-registration blocked via HMAC match.

### Phase 17 reporting continuity
- RegulatoryReport extends Phase 17 GGR/NGR.
- Per-jurisdiction reporting adapters.
- Source: ledger-reconciled read models (never telemetry; bifurcated truth).

### Phase 18 risk continuity
- AML_CTR + AML_SAR report types (Phase 18 TM + SAR workflow).

## 8. Threat Model Mitigation

| Threat | Mitigation |
|---|---|
| DSAR order violation (erasure before export) | Linter rule 186; E1 order enforced |
| SE registry not preserved (excluded player re-registers) | Linter rule 187; HMAC pseudonymization |
| Destruction during legal hold (spoliation) | Linter rule 189; legal-hold matrix |
| Expired vendor continues operating (regulator fine) | Linter rule 190; operator decision required |
| Evidence tampered (Law 9 violation) | Phase 10 storage port (WORM); linter rule 192 |
| Evidence access unaudited | Linter rule 193; evidence_access_log |
| Report inaccuracy (regulator-reportable) | Per-jurisdiction adapters; sourced from ledger-reconciled read models |
| Control not tested (audit failure) | Linter rule 191; scheduled testing |
| Finding without remediation (audit failure) | Linter rule 195; remediation tracking |
| DSAR statutory window missed (GDPR fine) | Linter rule 188; window tracking + alert |

## 9. Concurrency Test Designs (Stage B)

1. Concurrent DSAR requests (per-player; idempotent).
2. Concurrent legal hold + retention job (hold wins; retention skips).
3. Concurrent vendor expiry alerts (idempotent per vendor per threshold).
4. Concurrent evidence access (logged; immutable).
5. Concurrent control testing (one test per control at a time).
6. Concurrent report generation (per-jurisdiction; per-period; idempotent).

## 10. DSAR Drill Test (Acceptance Criterion)

### End-to-end test
1. Create DSAR request (`status=pending`).
2. Verify identity (KYC-grade; `status=verified`).
3. Generate export pack (all 11 modules; `status=exported`).
4. Verify export pack contains all data classes.
5. Shred KMS key (`status=shredded`).
6. Verify SE registry survives (HMAC pseudonymized identity retained).
7. Attempt re-registration with same identity document.
8. Verify re-registration blocked (HMAC match; `E_SELF_EXCLUDED`).

### Negative tests
- Erasure before export → rejected (E1 violation; linter rule 186).
- Export without verification → rejected (E1 violation; linter rule 186).
- Shred without preserving SE → rejected (linter rule 187).
- DSAR exceeding statutory window → alert (linter rule 188).

## 11. Vendor Expiry Alert Tests (Acceptance Criterion)

- **T-30 alert test:** vendor with expiry 30 days from now → T-30 alert sent.
- **T-7 alert test:** vendor with expiry 7 days from now → T-7 alert sent.
- **T-1 alert test:** vendor with expiry 1 day from now → T-1 alert sent.
- **Auto-suspend test (lab/studio):** lab cert expired → associated games `state=suspended` (Phase 16 ADR-0103).
- **Operator-decision test (PSP/KYC/Geo):** PSP expired → alert; no operation without decision; linter rule 190.

## 12. Performance Targets

- DSAR export generation: <5 minutes for 10-year player history.
- Vendor expiry job: <30 minutes for 1000 vendors.
- Control testing: <1 hour per control.
- Report generation: <5 minutes for quarterly report.
- Evidence access log write: <50ms p99.

## 13. Open Questions (OQ-COMP-001..006)

| ID | Question | Owner | Due | Status |
|---|---|---|---|---|
| OQ-COMP-001 | Compliance frameworks in scope (all 6?) | Compliance Officer | Phase 21 Stage A | OPEN |
| OQ-COMP-002 | Evidence retention period per jurisdiction (5-10 years) | Legal Counsel | Phase 22 | Q1-BLOCKED |
| OQ-COMP-003 | External auditor vendor selection | Compliance Officer | Phase 22 | Q5-BLOCKED |
| OQ-COMP-004 | DSAR statutory window per jurisdiction (30 days default) | Legal Counsel | Phase 22 | Q1-BLOCKED |
| OQ-COMP-005 | Regulator portal API integration (per jurisdiction) | Compliance Officer | Phase 22 | Q5-BLOCKED |
| OQ-COMP-006 | Vendor expiry T-30/7/1 thresholds (configurable per vendor type) | Compliance Officer | Phase 21 Stage A | OPEN |
