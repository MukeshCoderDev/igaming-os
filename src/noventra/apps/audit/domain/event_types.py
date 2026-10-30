"""Event type taxonomy — closed catalog.

Per ADR-0036 / DEC-0041: closed enumeration. No ad-hoc event types.
New types require ADR amendment.

Linter rule 40 verifies the catalog is closed.

Categories:
- auth.*: authentication events (login, logout, token refresh, MFA).
- tenancy.*: tenant lifecycle (provision, suspend, config update).
- rbac.*: role/permission changes (assign, revoke, delegate).
- audit.*: audit-system events (read, redaction, chain break).
- security.*: security events (lockout, breach, break-glass).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


@dataclass(frozen=True)
class EventTypeDef:
    code: str
    description: str
    category: str
    tenant_scoped: bool  # True = per-tenant chain; False = global chain


class EventType(str, enum.Enum):
    """Closed enumeration of audit event types."""

    # auth.* (global chain — auth events are system-level)
    AUTH_LOGIN_SUCCESS = "auth.login_success"
    AUTH_LOGIN_FAILED = "auth.login_failed"
    AUTH_LOGOUT = "auth.logout"
    AUTH_TOKEN_REFRESHED = "auth.token_refreshed"
    AUTH_TENANT_SWITCHED = "auth.tenant_switched"
    AUTH_MFA_CHALLENGED = "auth.mfa_challenged"
    AUTH_MFA_VERIFIED = "auth.mfa_verified"
    AUTH_LOCKOUT = "auth.lockout"

    # tenancy.* (per-tenant chain)
    TENANCY_TENANT_PROVISIONED = "tenancy.tenant_provisioned"
    TENANCY_TENANT_SUSPENDED = "tenancy.tenant_suspended"
    TENANCY_TENANT_CONFIG_UPDATED = "tenancy.tenant_config_updated"
    TENANCY_BRAND_CREATED = "tenancy.brand_created"

    # rbac.* (per-tenant chain)
    RBAC_ROLE_ASSIGNED = "rbac.role_assigned"
    RBAC_ROLE_REVOKED = "rbac.role_revoked"
    RBAC_DELEGATION_CREATED = "rbac.delegation_created"
    RBAC_PERMISSION_GRANTED = "rbac.permission_granted"

    # audit.* (global chain — audit system events)
    AUDIT_READ_PERFORMED = "audit.read_performed"
    AUDIT_REDACTION_APPLIED = "audit.redaction_applied"
    AUDIT_CHAIN_BREAK_DETECTED = "audit.chain_break_detected"
    AUDIT_EXPORT_GENERATED = "audit.export_generated"

    # security.* (global chain)
    SECURITY_BREAK_GLASS_USED = "security.break_glass_used"
    SECURITY_BREACH_DETECTED = "security.breach_detected"
    SECURITY_CONTRACT_VIOLATION = "security.contract_violation"

    # reliability.* (per-tenant chain for outbox/inbox/idempotency; global for DLQ)
    RELIABILITY_OUTBOX_APPENDED = "reliability.outbox_appended"
    RELIABILITY_OUTBOX_RELAYED = "reliability.outbox_relayed"
    RELIABILITY_OUTBOX_FAILED = "reliability.outbox_failed"
    RELIABILITY_INBOX_DEDUPED = "reliability.inbox_deduped"
    RELIABILITY_DLQ_MESSAGE_SENT = "reliability.dlq_message_sent"
    RELIABILITY_IDEMPOTENCY_CACHE_HIT = "reliability.idempotency_cache_hit"
    RELIABILITY_IDEMPOTENCY_CONFLICT = "reliability.idempotency_conflict"
    RELIABILITY_STATE_TRANSITION = "reliability.state_transition"
    RELIABILITY_GATE_DECISION = "reliability.gate_decision"
    RELIABILITY_NOTIFICATION_SENT = "reliability.notification_sent"

    # player.* (per-tenant chain) — Phase 9
    PLAYER_REGISTERED = "player.registered"
    PLAYER_ACTIVATED = "player.activated"
    PLAYER_SUSPENDED = "player.suspended"
    PLAYER_SELF_EXCLUDED = "player.self_excluded"
    PLAYER_DORMANT = "player.dormant"
    PLAYER_CLOSED = "player.closed"
    PLAYER_DELETED = "player.deleted"
    PLAYER_ERASURE_COMPLETED = "player.erasure_completed"
    PLAYER_DSAR_COMPLETED = "player.dsar_completed"

    # consent.* (per-tenant chain) — Phase 9
    CONSENT_GRANTED = "consent.granted"
    CONSENT_REVOKED = "consent.revoked"
    CONSENT_EXPIRED = "consent.expired"
    CONSENT_RECONSENT_REQUIRED = "consent.reconsent_required"

    # retention.* (per-tenant chain) — Phase 9
    RETENTION_ENFORCEMENT_COMPLETED = "retention.enforcement_completed"
    RETENTION_LEGAL_HOLD_APPLIED = "retention.legal_hold_applied"
    RETENTION_ARCHIVAL_SCHEDULED = "retention.archival_scheduled"

    # kyc.* (per-tenant chain) — Phase 10
    KYC_CASE_SUBMITTED = "kyc.case_submitted"
    KYC_CASE_AUTO_VERIFIED = "kyc.case_auto_verified"
    KYC_CASE_AUTO_REJECTED = "kyc.case_auto_rejected"
    KYC_CASE_IN_REVIEW = "kyc.case_in_review"
    KYC_CASE_EDD_TRIGGERED = "kyc.case_edd_triggered"
    KYC_CASE_PEP_FLAGGED = "kyc.case_pep_flagged"
    KYC_CASE_SANCTIONS_FLAGGED = "kyc.case_sanctions_flagged"
    KYC_CASE_ESCALATED = "kyc.case_escalated"
    KYC_CASE_CLOSED_APPROVED = "kyc.case_closed_approved"
    KYC_CASE_CLOSED_REJECTED = "kyc.case_closed_rejected"
    KYC_CASE_SUSPENDED_PENDING_SAR = "kyc.case_suspended_pending_sar"

    # document.* (per-tenant chain) — Phase 10
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_SUPERSEDED = "document.superseded"
    DOCUMENT_REVOKED = "document.revoked"
    DOCUMENT_VERSION_ACCESSED = "document.version_accessed"

    # aml.* (per-tenant chain) — Phase 10
    AML_SCREENING_PERFORMED = "aml.screening_performed"
    AML_RISK_SCORE_COMPUTED = "aml.risk_score_computed"
    AML_EDD_TRIGGERED = "aml.edd_triggered"

    # review.* (per-tenant chain) — Phase 10
    REVIEW_QUEUE_ENTRY_CREATED = "review.queue_entry_created"
    REVIEW_QUEUE_CASE_CLAIMED = "review.case_claimed"
    REVIEW_DECISION_MADE = "review.decision_made"
    REVIEW_ESCALATED = "review.escalated"
    REVIEW_SLA_BREACHED = "review.sla_breached"

    # sar.* (MLRO-restricted chain) — Phase 10
    SAR_DRAFTED = "sar.drafted"
    SAR_FILED = "sar.filed"  # MLRO-only visibility per ADR-0058
    SAR_WITHDRAWN = "sar.withdrawn"


EVENT_TYPE_CATALOG: tuple[EventTypeDef, ...] = (
    # auth.*
    EventTypeDef("auth.login_success", "User login succeeded", "auth", False),
    EventTypeDef("auth.login_failed", "User login failed", "auth", False),
    EventTypeDef("auth.logout", "User logged out", "auth", False),
    EventTypeDef("auth.token_refreshed", "Refresh token rotated", "auth", False),
    EventTypeDef("auth.tenant_switched", "User switched tenant context", "auth", False),
    EventTypeDef("auth.mfa_challenged", "MFA challenge issued", "auth", False),
    EventTypeDef("auth.mfa_verified", "MFA verification succeeded", "auth", False),
    EventTypeDef("auth.lockout", "Account locked due to failed logins", "auth", False),

    # tenancy.*
    EventTypeDef("tenancy.tenant_provisioned", "Tenant provisioned", "tenancy", True),
    EventTypeDef("tenancy.tenant_suspended", "Tenant suspended", "tenancy", True),
    EventTypeDef("tenancy.tenant_config_updated", "Tenant configuration updated", "tenancy", True),
    EventTypeDef("tenancy.brand_created", "Brand created under tenant", "tenancy", True),

    # rbac.*
    EventTypeDef("rbac.role_assigned", "Role assigned to user", "rbac", True),
    EventTypeDef("rbac.role_revoked", "Role revoked from user", "rbac", True),
    EventTypeDef("rbac.delegation_created", "Permission delegation created", "rbac", True),
    EventTypeDef("rbac.permission_granted", "Permission granted to role", "rbac", True),

    # audit.*
    EventTypeDef("audit.read_performed", "Audit log read performed", "audit", False),
    EventTypeDef("audit.redaction_applied", "PII redacted from audit event", "audit", False),
    EventTypeDef("audit.chain_break_detected", "Hash chain break detected", "audit", False),
    EventTypeDef("audit.export_generated", "Audit log export generated", "audit", False),

    # security.*
    EventTypeDef("security.break_glass_used", "Break-glass admin role used", "security", False),
    EventTypeDef("security.breach_detected", "Security breach detected", "security", False),
    EventTypeDef("security.contract_violation", "Phase 4 contract violation detected", "security", False),

    # reliability.*
    EventTypeDef("reliability.outbox_appended", "Event appended to outbox", "reliability", True),
    EventTypeDef("reliability.outbox_relayed", "Outbox event relayed", "reliability", True),
    EventTypeDef("reliability.outbox_failed", "Outbox relay failed (max retries)", "reliability", True),
    EventTypeDef("reliability.inbox_deduped", "Duplicate message deduped by inbox", "reliability", True),
    EventTypeDef("reliability.dlq_message_sent", "Poison message sent to DLQ", "reliability", False),
    EventTypeDef("reliability.idempotency_cache_hit", "Idempotency key cache hit", "reliability", True),
    EventTypeDef("reliability.idempotency_conflict", "Idempotency key conflict (different body)", "reliability", True),
    EventTypeDef("reliability.state_transition", "State machine transition", "reliability", True),
    EventTypeDef("reliability.gate_decision", "MarketingGate decision (allow/deny)", "reliability", True),
    EventTypeDef("reliability.notification_sent", "Notification sent via adapter", "reliability", True),

    # player.* — Phase 9
    EventTypeDef("player.registered", "Player registered", "player", True),
    EventTypeDef("player.activated", "Player activated", "player", True),
    EventTypeDef("player.suspended", "Player suspended", "player", True),
    EventTypeDef("player.self_excluded", "Player self-excluded", "player", True),
    EventTypeDef("player.dormant", "Player went dormant", "player", True),
    EventTypeDef("player.closed", "Player closed", "player", True),
    EventTypeDef("player.deleted", "Player deleted (erasure)", "player", True),
    EventTypeDef("player.erasure_completed", "Player right-to-erasure completed", "player", True),
    EventTypeDef("player.dsar_completed", "Player DSAR export completed", "player", True),

    # consent.* — Phase 9
    EventTypeDef("consent.granted", "Consent granted", "consent", True),
    EventTypeDef("consent.revoked", "Consent revoked", "consent", True),
    EventTypeDef("consent.expired", "Consent expired", "consent", True),
    EventTypeDef("consent.reconsent_required", "Re-consent required (policy change)", "consent", True),

    # retention.* — Phase 9
    EventTypeDef("retention.enforcement_completed", "Retention enforcement job completed", "retention", True),
    EventTypeDef("retention.legal_hold_applied", "Legal hold applied to data", "retention", True),
    EventTypeDef("retention.archival_scheduled", "Data scheduled for archival", "retention", True),

    # kyc.* — Phase 10
    EventTypeDef("kyc.case_submitted", "KYC case submitted", "kyc", True),
    EventTypeDef("kyc.case_auto_verified", "KYC case auto-verified", "kyc", True),
    EventTypeDef("kyc.case_auto_rejected", "KYC case auto-rejected", "kyc", True),
    EventTypeDef("kyc.case_in_review", "KYC case entered review", "kyc", True),
    EventTypeDef("kyc.case_edd_triggered", "KYC case EDD triggered", "kyc", True),
    EventTypeDef("kyc.case_pep_flagged", "KYC case PEP flagged", "kyc", True),
    EventTypeDef("kyc.case_sanctions_flagged", "KYC case sanctions flagged", "kyc", True),
    EventTypeDef("kyc.case_escalated", "KYC case escalated to MLRO", "kyc", True),
    EventTypeDef("kyc.case_closed_approved", "KYC case closed approved", "kyc", True),
    EventTypeDef("kyc.case_closed_rejected", "KYC case closed rejected", "kyc", True),
    EventTypeDef("kyc.case_suspended_pending_sar", "KYC case suspended pending SAR", "kyc", True),

    # document.* — Phase 10
    EventTypeDef("document.uploaded", "Document uploaded", "document", True),
    EventTypeDef("document.superseded", "Document version superseded", "document", True),
    EventTypeDef("document.revoked", "Document revoked (crypto shredding)", "document", True),
    EventTypeDef("document.version_accessed", "Document version accessed", "document", True),

    # aml.* — Phase 10
    EventTypeDef("aml.screening_performed", "AML screening performed", "aml", True),
    EventTypeDef("aml.risk_score_computed", "AML risk score computed", "aml", True),
    EventTypeDef("aml.edd_triggered", "AML EDD triggered", "aml", True),

    # review.* — Phase 10
    EventTypeDef("review.queue_entry_created", "Review queue entry created", "review", True),
    EventTypeDef("review.case_claimed", "Review case claimed by reviewer", "review", True),
    EventTypeDef("review.decision_made", "Review decision made", "review", True),
    EventTypeDef("review.escalated", "Review escalated (senior/MLRO)", "review", True),
    EventTypeDef("review.sla_breached", "Review SLA breached", "review", True),

    # sar.* — Phase 10 (MLRO-restricted)
    EventTypeDef("sar.drafted", "SAR drafted by MLRO", "sar", True),
    EventTypeDef("sar.filed", "SAR filed by MLRO (MLRO-only visibility)", "sar", True),
    EventTypeDef("sar.withdrawn", "SAR withdrawn", "sar", True),
)


class EventTypeCatalog:
    """Closed catalog lookup."""

    _by_code = {etd.code: etd for etd in EVENT_TYPE_CATALOG}

    @classmethod
    def get(cls, code: str) -> EventTypeDef | None:
        return cls._by_code.get(code)

    @classmethod
    def all_codes(cls) -> tuple[str, ...]:
        return tuple(etd.code for etd in EVENT_TYPE_CATALOG)

    @classmethod
    def is_tenant_scoped(cls, code: str) -> bool:
        etd = cls.get(code)
        return etd.tenant_scoped if etd else False

    @classmethod
    def is_valid(cls, code: str) -> bool:
        return code in cls._by_code
