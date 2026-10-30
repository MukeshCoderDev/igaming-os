"""PII + secret redaction processor for structlog.

Per ADR-0025 / DEC-0030:
- PII register (docs/architecture/data-classification.md) is the source
  of truth for PII fields.
- Secret redaction by name + regex.

This processor is plugged into the structlog processor chain. It runs
BEFORE any I/O (console, file, network). Redaction is at the boundary;
downstream code never sees the raw PII or secret values.

Phase 4 stub: a minimal but functional implementation. Phase 5+ will
extend the PII field list as new models are introduced.
"""

from __future__ import annotations

import re
from typing import Any

# ─── PII fields (sourced from data-classification.md §2 PII register) ───
# Names of fields/keys that contain PII and must be redacted.
PII_FIELD_NAMES = frozenset({
    "email",
    "full_name",
    "name",
    "first_name",
    "last_name",
    "phone",
    "address",
    "date_of_birth",
    "dob",
    "ssn",
    "national_id",
    "passport_number",
    "driver_license",
    "ip_address",
    "user_agent",
    "kyc_documents",
    "sanctions_results",
    "transaction_history",
    "consent_records",
    "session_token",
    "refresh_token",
    "access_token",
    "password",
    "secret",
    "api_key",
    "private_key",
    # PCI SAQ-A boundary (linter rules 81, 82, 88): card-related fields.
    "card_number",
    "pan",  # noqa: PCI — redaction field name, not storage
    "cvv",
    "cvc",
    "cv2",
    "expiry_month",
    "expiry_year",
    "exp_month",
    "exp_year",
    "track_data",
    "magstripe",
    "track1",
    "track2",
})

# ─── Secret names (env vars + common secret keys) ───────────────────────
SECRET_FIELD_NAMES = frozenset({
    "SECRET_KEY",
    "DATABASE_URL",
    "REDIS_URL",
    "password",
    "passwd",
    "secret",
    "secret_key",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "id_token",
    "bearer_token",
    "authorization",
    "private_key",
    "client_secret",
})

# ─── Secret regexes (catch values that look like secrets) ───────────────
# These run on every string VALUE (not just named fields). If a value
# matches, the value is replaced with "[REDACTED:<pattern>]".
SECRET_PATTERNS = [
    # AWS access key: AKIA followed by 16 uppercase alphanumerics.
    (re.compile(r"AKIA[0-9A-Z]{16}"), "[REDACTED:aws_access_key]"),
    # AWS secret key: 40-char base64-ish.
    (re.compile(r"(?<![A-Za-z0-9/+])[A-Za-z0-9/+]{40}(?![A-Za-z0-9/+])"), "[REDACTED:aws_secret_key?]"),
    # Bearer token in Authorization header (must run BEFORE JWT regex so
    # "Bearer eyJ..." is fully redacted as "Bearer [REDACTED]" rather than
    # partially as "Bearer [REDACTED:jwt]").
    (re.compile(r"(Bearer\s+)[A-Za-z0-9._\-+/=]+"), r"\1[REDACTED]"),
    # Generic JWT: ey... three base64 segments.
    (re.compile(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"), "[REDACTED:jwt]"),
    # Postgres URL with password: postgres://user:pass@host
    (re.compile(r"(postgres(?:s)?://[^:]+:)[^@]+(@)"), r"\1[REDACTED]\2"),
    # Redis URL with password: redis://:pass@host
    (re.compile(r"(redis://:[^@]+@)"), "redis://:[REDACTED]@"),
    # PAN (card number) — 13-19 digit Luhn-shaped sequences (PCI DLP).
    # Matches standalone digit sequences that look like card numbers.
    (re.compile(r"\b(\d{13,19})\b"), "[REDACTED:card_number]"),
    # Private key block.
    (re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----[\s\S]+?-----END [A-Z ]+PRIVATE KEY-----"),
     "[REDACTED:private_key_block]"),
]

REDACTED_VALUE = "[REDACTED]"


def _redact_value(value: Any) -> Any:
    """Apply secret regexes to a string value. Non-strings pass through."""
    if not isinstance(value, str):
        return value
    redacted = value
    for pattern, replacement in SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def _redact_dict(d: dict) -> dict:
    """Recursively redact a dict by field name and value regex."""
    out = {}
    for key, value in d.items():
        key_str = str(key).lower()
        # Name-based redaction: PII or secret field names.
        if key in PII_FIELD_NAMES or key in SECRET_FIELD_NAMES or key_str in PII_FIELD_NAMES or key_str in SECRET_FIELD_NAMES:
            out[key] = REDACTED_VALUE
            continue
        # Recursive dict redaction.
        if isinstance(value, dict):
            out[key] = _redact_dict(value)
        elif isinstance(value, list):
            out[key] = [_redact_dict(v) if isinstance(v, dict) else _redact_value(v) for v in value]
        else:
            out[key] = _redact_value(value)
    return out


class RedactingProcessor:
    """structlog processor: redact PII + secrets from event_dict.

    Usage in structlog config:
        structlog.configure(processors=[..., RedactingProcessor(), ...])
    """

    def __call__(self, logger, method_name, event_dict):  # noqa: D401
        return _redact_dict(event_dict)
