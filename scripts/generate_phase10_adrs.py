#!/usr/bin/env python3
"""Generate Phase 10 ADRs: 7 new (0052-0058) ACCEPTED.

Run:  python3 /home/z/my-project/scripts/generate_phase10_adrs.py
"""

from pathlib import Path

OUT_DIR = Path("/home/z/my-project/docs/adr")
LR = "2025-10-28"
CR = "2025-10-28"

ADRS = [
    (52, "DEC-0057", "KYC case FSM (16 states, regulatory constraints, hash-chained)",
     "Compliance Lead", "Phase4-7",
     "KYC verification is a regulated process with strict state requirements. FATF Rec.10 mandates CDD; PEPs require EDD (Rec.12); sanctions hits require escalation. The FSM must encode these regulatory constraints. KYC decisions are evidentiary — hash-chaining (per Phase 9 consent pattern) is recommended.",
     "Adopt a 16-state KYC case FSM using the Phase 8 state machine base. States: pending_submission, submitted, auto_verified, auto_rejected, in_review, review_passed, review_failed, ed_triggered, ed_in_progress, ed_passed, ed_failed, pep_flagged, sanctions_flagged, escalated, suspended, closed_approved, closed_rejected, suspended_pending_sar. Regulatory constraints: PEP → EDD (ed_triggered); sanctions → escalate; risk > threshold → EDD. Re-verification triggers (scheduled + risk-profile-change). Cooling-off periods Q1-blocked; time-to-decision SLAs Q1-blocked. Hash-chained per Phase 9 consent pattern. Every transition audited (Phase 7) + outbox events (Phase 8). HUMAN-APPROVED per linter rule 5.",
     "Alternatives: (a) free-form status — invalid transitions; (b) fewer states — regulatory gap; (c) per-jurisdiction FSM — complexity. All rejected.",
     "16-state FSM is complex. Regulatory constraints are Q1-blocked (defaults used). Hash-chaining adds chain management overhead. Re-KYC scheduling requires a cron job (Phase 11).",
     "Phase 10: FSM implemented. Phase 10: regulatory constraint tests (PEP→EDD, sanctions→escalate, risk→EDD). Phase 11: re-KYC scheduling. Phase 12: jurisdiction-specific constraints (Q1).",
     "ACCEPTED", "Compliance Lead + Legal Lead + MLRO + Architect"),

    (53, "DEC-0058", "Document model + versioning + retention",
     "Architecture Lead", "Phase4-7",
     "KYC requires documents (passport, utility bill, selfie). Documents have versions (a player may re-upload). Each version is immutable; supersession creates a new version + audit event. One active version per (player, doc_type). Superseded versions retained per Phase 9 schedule.",
     "Adopt per-document versioning. Each version is immutable (insert-only). Supersession: new version inserted; old version marked superseded (audit event emitted). One active version per (player, doc_type) enforced by partial unique index. Superseded versions retained per Phase 9 retention schedule (7y after supersession). Document content stored via the storage port (ADR-0054); metadata in DB.",
     "Alternatives: (a) single version (overwrite) — no audit trail; (b) mutable versions — tamper risk; (c) event-sourced documents — over-engineered. All rejected.",
     "Versioning increases storage (multiple versions per document). Partial unique index requires DB support (Postgres supports). Superseded version cleanup aligned with retention (not immediate).",
     "Phase 10: Document + DocumentVersion models. Phase 10: one-active-version test. Phase 10: supersession audit test.",
     "ACCEPTED", "Architecture Lead + Compliance Lead + Architect"),

    (54, "DEC-0059", "Storage port + backend Q5-blocked",
     "Infrastructure Lead", "Phase4-7",
     "Document content (passport scans, selfies) must be stored securely. The backend (S3, GCS, Azure Blob) is Q5-blocked. The port pattern decouples the domain from the backend. Per-document encryption keys enable cryptographic shredding (ADR-0055). Access control via application-level proxy (no direct backend access).",
     "Adopt a storage port: put(key, data, metadata) -> StorageResult; get(key) -> data; delete(key) -> bool; head(key) -> metadata. Backend Q5-blocked (stub for dev; real adapter deferred). Per-document encryption key (DEK) stored in DB; data encrypted with DEK before put. Access control: application-level proxy (no direct backend access). Object Lock / WORM for legal hold (if backend supports). Retention aligned with Phase 9 schedule.",
     "Alternatives: (a) direct backend call (no port) — vendor lock-in; (b) DB BLOB storage — doesn't scale; (c) no encryption — security gap. All rejected.",
     "Vendor selection is Q5-blocked (stub for dev). DEK management adds complexity (key store, rotation). Application-level proxy adds latency. Object Lock support is backend-dependent.",
     "Phase 10: StoragePort interface + stub adapter. Phase 10: put/get/delete/head tests. Phase 11: real adapter (Q5 unblock). Phase 11: Object Lock integration.",
     "ACCEPTED", "Infrastructure Lead + Security Lead + Architect"),

    (55, "DEC-0060", "Synchronous revocation — soft-delete + cryptographic shredding",
     "Security Lead", "Phase4-7",
     "When a player exercises right-to-erasure (GDPR Art. 17) or a document is revoked, the content must be unretrievable immediately. Soft-delete (DB view hides the row) provides API unretrievability but not byte unretrievability. Cryptographic shredding (DEK deletion) provides byte unretrievability. Both must happen in the same DB transaction (atomicity).",
     "Adopt synchronous revocation: (1) soft-delete via DB view (the document_versions table has a revoked_at column; a view filters revoked rows → immediate API 404); (2) cryptographic shredding (the DEK for the document version is deleted from the document_keys table in the same transaction → bytes unrecoverable even if backend data persists). Both in the same DB transaction. Supersession is NOT revocation (superseded versions are retained per retention; revoked versions are unretrievable). Rollback restores both the view + the DEK.",
     "Alternatives: (a) soft-delete only — bytes recoverable from backend; (b) crypto shredding only — API still returns 200 before propagation; (c) async revocation — window of retrievability. All rejected.",
     "Cryptographic shredding is irreversible (DEK deletion is permanent). If the backend doesn't support immediate deletion (e.g., S3 with versioning), the encrypted blob persists but is unreadable. Legal hold must prevent revocation (checked before revocation).",
     "Phase 10: revocation atomicity test (API 404 + DEK deleted in same transaction). Phase 10: rollback test. Phase 10: supersession ≠ revocation test.",
     "ACCEPTED", "Security Lead + Architecture Lead + Privacy Owner"),

    (56, "DEC-0061", "AML/CFT framework (RBA, PEP/sanctions, SoF/SoW, SAR)",
     "Compliance Lead", "Phase4-7",
     "FATF Recommendations 1, 10, 12, 20, 22 mandate AML/CFT framework: risk-based approach (RBA), PEP screening, sanctions screening, source of funds/wealth (SoF/SoW) evidence, affordability checks, ongoing monitoring, and SAR (Suspicious Activity Report) flow. The MLRO owns SAR filing decisions. Tipping-off (alerting the subject of a SAR) is a criminal offense.",
     "Adopt RBA (rule-based recommended for explainability). PEP screening (vendor Q5-blocked, stub for dev). Sanctions screening (vendor Q5-blocked, stub). SoF/SoW evidence handling (enumerated acceptable evidence types: bank_statement, tax_document, salary_slip, property_sale, inheritance). Affordability checks (triggers Q1-blocked; methods Q5-blocked). Ongoing monitoring (re-KYC scheduled; risk-profile-change triggers). SAR flow: MLRO filing via restricted-audit-visibility event; tipping-off prohibition enforced (no notification to player when SAR filed; no SAR event visible to non-MLRO roles). HUMAN-APPROVED per linter rule 5.",
     "Alternatives: (a) ML-based RBA — explainability gap; (b) no PEP/sanctions screening — regulatory violation; (c) no SAR flow — regulatory violation; (d) no tipping-off prohibition — criminal offense. All rejected.",
     "PEP/sanctions vendor is Q5-blocked (stub). Affordability method is Q5-blocked. SAR filing jurisdiction is Q1-blocked. Re-KYC period is Q1-blocked. Tipping-off prohibition must be enforced at every layer (audit visibility, notification suppression, API response). MLRO appointment is regulator-mandated (documented evidence required).",
     "Phase 10: AML/CFT framework. Phase 10: PEP/sanctions stub. Phase 10: SAR flow + tipping-off test. Phase 11: real PEP/sanctions vendor (Q5). Phase 12: jurisdiction-specific (Q1).",
     "ACCEPTED", "Compliance Lead + Legal Lead + MLRO + Security Lead"),

    (57, "DEC-0062", "KYC vendor integration Q5-blocked",
     "Compliance Lead", "Phase4-7",
     "KYC verification (identity document verification, liveness check) requires a vendor (Onfido, Jumio, Veriff). Vendor choice is Q5-blocked. A stub adapter enables development without the vendor. Liveness check for selfie documents is a security gap if skipped (not recommended).",
     "Adopt a KYC vendor port (verify(document, selfie) -> VerificationResult). Vendor choice Q5-blocked (stub adapter for dev; real adapter deferred). Fallback strategy: if vendor is unavailable, the KYC case enters manual review (no auto-verify). Liveness check: vendor-provided or skip (skip is a security gap; not recommended; documented).",
     "Alternatives: (a) in-house document verification — too expensive; (b) no verification — regulatory violation; (c) no liveness — security gap (deepfake risk). All rejected.",
     "Vendor is Q5-blocked. Stub adapter returns auto_verified (dev only). Liveness skip is documented as a security gap. Fallback to manual review adds review queue load.",
     "Phase 10: KYC vendor port + stub. Phase 11: real vendor (Q5). Phase 11: liveness integration.",
     "ACCEPTED", "Compliance Lead + Architecture Lead + Architect"),

    (58, "DEC-0063", "Review queue + workflow + SLA + escalation",
     "Compliance Lead", "Phase4-7",
     "KYC cases that fail auto-verification enter a review queue. The queue must: assign reviewers (skill-based or round-robin), track SLAs (time-to-decision), support reviewer notes (audited), support escalation (reviewer → senior → MLRO), handle concurrency (prevent double-claim), and restrict MLRO decisions (regulator-reportable, restricted audit visibility).",
     "Adopt a review queue: per-tenant (simpler; Phase 10) or per-risk-tier (Phase 11+). Reviewer assignment: round-robin (Phase 10; skill-based Phase 11+). SLA tracking: created_at + sla_deadline; alerting on breach (structured log + dedicated channel). Reviewer notes: audited (review.note_added event). Reviewer decision: approve/reject/request-more-info/escalate. Escalation: reviewer → senior → MLRO. MLRO decisions: regulator-reportable; restricted audit visibility (SAR events MLRO-only). Concurrency: row-level lock (SELECT FOR UPDATE) or claim-based (UPDATE ... WHERE claimed_by IS NULL). Reviewer PII access logged. HUMAN-APPROVED per linter rule 5.",
     "Alternatives: (a) no queue (auto-only) — regulatory gap; (b) no SLA — compliance risk; (c) no escalation — MLRO bypass; (d) no concurrency control — double-claim. All rejected.",
     "Per-tenant queue is simpler but may not scale (Phase 11+ per-risk-tier). Round-robin is simple but doesn't match reviewer skills (Phase 11+). MLRO restricted visibility requires audit-level filtering (Phase 7 clearance model extension). SLA alerting requires a monitoring job (Phase 11).",
     "Phase 10: review queue + SLA + escalation + concurrency. Phase 10: MLRO restricted visibility test. Phase 11: skill-based assignment. Phase 11: SLA monitoring job.",
     "ACCEPTED", "Compliance Lead + Legal Lead + MLRO + Architect + Engineering Lead"),
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
Supersede history: none. Last reviewed: {LR}.
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
