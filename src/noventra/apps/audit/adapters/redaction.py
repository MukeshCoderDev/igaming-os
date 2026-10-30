"""Redaction service — Merkle-style payload hashing.

Per ADR-0037 / DEC-0042: Merkle-style payload hashing enables redaction
without breaking the hash chain. Each payload field is hashed
individually; redaction replaces the VALUE with [REDACTED] but preserves
the field_hash. The chain hash (computed by the DB trigger) uses the
Merkle root, which is unchanged because the field_hash is preserved.

Field-class-to-rule mapping from the PII register
(docs/architecture/data-classification.md).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

# ─── PII field → redaction rule mapping ─────────────────────────────────
# Sourced from data-classification.md §2 PII register.
# Rule: "redact" = replace value with [REDACTED]; "hash" = replace with
# SHA-256 hash (for correlation); "keep" = no redaction.

REDACTION_RULES: dict[str, str] = {
    # PII-001..004: names + emails
    "email": "redact",
    "full_name": "redact",
    "name": "redact",
    "first_name": "redact",
    "last_name": "redact",
    # PII-005: credentials
    "password": "redact",
    "password_hash": "redact",
    "session_token": "redact",
    "refresh_token": "redact",
    "access_token": "redact",
    # PII-006..007: network
    "ip_address": "hash",  # hash for correlation
    "user_agent": "redact",
    # PII-008..009: KYC / sanctions
    "kyc_documents": "redact",
    "sanctions_results": "redact",
    # PII-010: transactions
    "transaction_history": "redact",
    # PII-011: audit log (the payload itself; actor identity is PII)
    "actor_email": "redact",
    "actor_name": "redact",
    # PII-013: consent
    "consent_records": "redact",
    # PII-014: tokens (already covered above)
    # PII-015: webhook receipts
    "webhook_url": "redact",
}

REDACTED_VALUE = "[REDACTED]"


def redact_payload(payload: dict[str, Any], clearance: str = "external_auditor") -> dict[str, Any]:
    """Redact a payload based on clearance level.

    Args:
        payload: The audit event payload dict.
        clearance: One of "tenant_admin", "compliance_officer", "external_auditor".

    Returns:
        Redacted payload dict. For compliance_officer, no redaction.
        For tenant_admin + external_auditor, PII fields are redacted/hashed.
    """
    if clearance == "compliance_officer":
        return payload  # No redaction for compliance.

    redacted: dict[str, Any] = {}
    for key, value in payload.items():
        rule = REDACTION_RULES.get(key, "keep")
        if rule == "redact":
            redacted[key] = REDACTED_VALUE
        elif rule == "hash":
            redacted[key] = _hash_value(value)
        else:
            redacted[key] = value
    return redacted


def _hash_value(value: Any) -> str:
    """Hash a value for correlation (irreversible)."""
    return "sha256:" + hashlib.sha256(str(value).encode()).hexdigest()[:16]


def compute_field_hash(field_name: str, field_value: Any) -> str:
    """Compute the Merkle-style field hash (matches DB trigger logic).

    Per ADR-0035: field_hash = SHA256(field_name || '=' || field_value).
    """
    return hashlib.sha256(
        f"{field_name}={field_value}".encode()
    ).hexdigest()


def compute_merkle_root(payload: dict[str, Any]) -> str:
    """Compute the Merkle root = SHA256(concatenation of all field hashes in canonical order).

    Matches the DB trigger logic in audit_compute_hash().
    """
    field_hashes = []
    for key in sorted(payload.keys()):
        field_hashes.append(compute_field_hash(key, payload[key]))
    concatenated = "".join(field_hashes)
    return hashlib.sha256(concatenated.encode()).hexdigest()
