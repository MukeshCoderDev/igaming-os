# Data Classification — PII Register

| Field | Value |
|---|---|
| Document | `docs/architecture/data-classification.md` |
| Version | 5.3 (Phase 2) |
| Status | Approved |
| Owner | Data Protection Officer |
| Authority | DEC-0025; GDPR Art.30 (records of processing); Law-REQ-0011..0016 |

This document classifies every data element the platform processes
into one of four tiers, records the controls applied per tier, and
maintains the PII register required by GDPR Art.30 and SOC 2 CC6.1.
The linter (rule 12) verifies that every data element cited in
`security.md` STRIDE findings has a row in this register.

## §1. Classification scheme

| Tier | Label | Definition | Examples | Controls |
|---|---|---|---|---|
| **T0** | Public | Data explicitly approved for public release. | Platform name, marketing copy, public docs | None beyond integrity controls |
| **T1** | Internal | Non-public business data; no PII; not customer-specific. | Internal runbooks, architecture docs, ADRs | Access control; encryption in transit |
| **T2** | Confidential | Customer-specific business data; no direct PII. | Tenant config, aggregate metrics, non-PII audit events | RLS (DEC-0003); encryption at rest + in transit; per-tenant access |
| **T3** | Personal / Sensitive | PII or sensitive personal data. | Name, email, government ID, KYC documents, transaction history | T2 controls + minimized collection + retention limits + DPO approval + jurisdiction-specific controls |

## §2. PII register (T3 elements)

The PII register is the authoritative list of T3 data elements the
platform processes. Each row records: the element, the source (how
it enters the platform), the lawful basis (GDPR Art.6), the
retention period, the jurisdictions where it is stored, and the
controls applied.

| ID | Element | Source | Lawful basis (GDPR Art.6) | Retention | Jurisdictions | Controls | Owner |
|---|---|---|---|---|---|---|---|
| PII-001 | Tenant admin email | Tenant provisioning (WF-01) | 6(b) contract | Tenant lifetime + 90d | Per tenant residency tag (Q3) | T3 + min collection; verification email; DPO approval | Data Protection Officer |
| PII-002 | Tenant admin full name | Tenant provisioning (WF-01) | 6(b) contract | Tenant lifetime + 90d | Per tenant residency tag | T3 + min collection; display only | Data Protection Officer |
| PII-003 | End-user email (player) | User invitation (WF-03) | 6(b) contract (via tenant) | User lifetime + 90d | Per tenant residency tag | T3 + min collection; verification email | Data Protection Officer |
| PII-004 | End-user full name | User invitation (WF-03) | 6(b) contract | User lifetime + 90d | Per tenant residency tag | T3 + min collection; display only | Data Protection Officer |
| PII-005 | End-user authentication credentials (hashed) | SSO (WF-04) | 6(b) contract | Session lifetime | Per tenant residency tag | T3 + hashed (Argon2id); never logged; never exported | Identity Lead |
| PII-006 | IP address (request origin) | All API surfaces | 6(f) legitimate interest (security) | 30d hot; 90d cold | Per tenant residency tag | T3 + min retention; security-only access | Security Lead |
| PII-007 | User agent string | All API surfaces | 6(f) legitimate interest | 30d hot; 90d cold | Per tenant residency tag | T3 + min retention; security-only access | Security Lead |
| PII-008 | KYC documents (government ID, proof of address) | KYC workflow (Phase 12+) | 6(c) legal obligation (FATF Rec.10) | 5y after relationship ends (Law-REQ-0009) | Per tenant residency tag + KYC vendor residency (Q6) | T3 + vendor DPA; encrypted at rest; access logged | Compliance Lead |
| PII-009 | Sanctions screening results | Screening workflow (Phase 12+) | 6(c) legal obligation | 5y (Law-REQ-0009) | Per tenant residency tag + screening vendor residency (Q7) | T3 + vendor DPA; access logged | Compliance Lead |
| PII-010 | Transaction history (account, amount, counterparty) | Ledger postings (Phase 11+) | 6(b) contract + 6(c) legal obligation | 5y–7y (Law-REQ-0009) | Per tenant residency tag | T3 + RLS; audit log; tenant-only access | Architecture Lead |
| PII-011 | Audit log entries (actor identity + operation) | All state changes (WF-06) | 6(c) legal obligation + 6(f) legitimate interest | 5y–7y (Law-REQ-0009) | Per tenant residency tag | T3 + append-only (DEC-0006); hash chain (DEC-0007); no deletion | Architecture Lead |
| PII-012 | Breach notification records | Incident response (NFR §4.4) | 6(c) legal obligation | 5y after notification | Provider jurisdiction | T3 + DPO-only access; legal hold capable | Data Protection Officer |
| PII-013 | Consent records (privacy notice, marketing) | Onboarding (Phase 4–7) | 6(a) consent | Until consent withdrawn + 90d | Per tenant residency tag | T3 + auditable; revocation API | Data Protection Officer |
| PII-014 | Session tokens (hashed) | SSO (WF-04) | 6(b) contract | Token lifetime (≤1h access; ≤30d refresh) | Per tenant residency tag | T3 + hashed; never logged; short-lived | Identity Lead |
| PII-015 | Webhook delivery receipts (tenant endpoint URL, response code) | Webhook delivery (WF-06 outbound) | 6(b) contract | 30d | Per tenant residency tag | T3 + min retention; tenant-only access | Infrastructure Lead |

## §3. Lawful basis summary

Per GDPR Art.6, the platform relies on four lawful bases:

| Basis | Used for | Count of PII elements |
|---|---|---|
| 6(a) Consent | Marketing, optional features | 1 (PII-013) |
| 6(b) Contract | Service delivery | 9 (PII-001..005, PII-010, PII-014, PII-015, PII-005 partial) |
| 6(c) Legal obligation | AML, KYC, retention | 5 (PII-008, PII-009, PII-011, PII-012, PII-010 partial) |
| 6(f) Legitimate interest | Security, fraud prevention | 3 (PII-006, PII-007, PII-011 partial) |

## §4. Retention summary

| Retention period | PII elements |
|---|---|
| ≤ 1 hour | PII-014 (access token) |
| ≤ 30 days | PII-006, PII-007, PII-015 |
| ≤ 30 days (refresh token) | PII-014 (refresh) |
| User / tenant lifetime + 90d | PII-001, PII-002, PII-003, PII-004 |
| Until consent withdrawn + 90d | PII-013 |
| 5 years after relationship ends | PII-008, PII-009, PII-010, PII-011, PII-012 |

Retention enforcement is a forward-only archival operation (DEC-0006)
to write-once storage (S3 Object Lock, Compliance Mode). Deletion
before the minimum is forbidden; deletion after the maximum is
mandated unless a litigation hold is in place.

## §5. Jurisdiction summary

The jurisdiction where each PII element is stored is determined by
the tenant's residency tag, set at provisioning (WF-01). The
residency tag is governed by Law-REQ-0012 (data residency) and
Law-REQ-0013 (cross-border transfer). Both are BLOCKED on Q1
(jurisdictions) and Q3 (data residency per jurisdiction).

| PII element | Jurisdiction authority | Status |
|---|---|---|
| PII-001..007, PII-010..011, PII-013..015 | Per tenant residency tag | Blocked on Q1, Q3 |
| PII-008 (KYC documents) | Tenant residency + KYC vendor residency | Blocked on Q1, Q3, Q6 |
| PII-009 (sanctions screening) | Tenant residency + screening vendor residency | Blocked on Q1, Q3, Q7 |
| PII-012 (breach records) | Provider jurisdiction (single) | Blocked on Q1 |

## §6. Data subject rights

GDPR Arts. 15–22 grant data subjects eight rights. The platform's
implementation status per right:

| Right | GDPR Article | PII elements in scope | Implementation status |
|---|---|---|---|
| Access | Art.15 | All T3 | Phase 4–7: API endpoint returning the data subject's PII |
| Rectification | Art.16 | All T3 except immutable (PII-005, PII-011, PII-014) | Phase 4–7: API endpoint; immutables corrected via compensation |
| Erasure | Art.17 | All T3 except where legal obligation overrides (PII-008, PII-009, PII-010, PII-011, PII-012) | Phase 4–7: API endpoint; legal-override elements retained per Law-REQ-0009 |
| Restriction | Art.18 | All T3 | Phase 4–7: API endpoint; restricts processing, retains data |
| Portability | Art.20 | PII-001..004, PII-010, PII-013 | Phase 4–7: export endpoint in machine-readable format |
| Object | Art.21 | PII-006, PII-007 (legitimate interest) | Phase 4–7: API endpoint; objects to processing |
| Automated decision-making | Art.22 | None (no ADM in scope) | N/A |
| Consent withdrawal | Art.7(3) | PII-013 | Phase 4–7: revocation API; one-click |

## §7. Cross-references

- Law-REQ-0011..0016: `docs/requirements/traceability.md` §B.1
- DEC-0003 (RLS), DEC-0006 (append-only audit), DEC-0007 (hash chain): `docs/requirements/traceability.md` §C
- STRIDE threats citing PII (WH-I-01, RT-I-01, PA-I-01, etc.): `docs/architecture/security.md`
- Phase 0 evidence Gate 1 (Legal): `docs/phase-0-evidence.md`
- Open questions Q1, Q3, Q6, Q7: `docs/requirements/unresolved-decisions.md`
