"""Error catalog — RFC 7807 codes for the Noventra platform.

Per ADR-0026 / DEC-0031:
- Each code has: code, http_status, i18n_key, title, detail_template.
- One HTTP status per code (no multi-status codes).
- i18n_key resolves via Django's i18n system (default en).
- Generated docs at docs/architecture/error-catalog.md.

To add a new error code:
1. Add a tuple to ERROR_CATALOG below.
2. Add the i18n key to the locale files (Phase 5+ i18n work).
3. Run `python manage.py generate_error_catalog` to regenerate the
   markdown docs (Phase 4 stub: manual; Phase 5+ command).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ErrorCode:
    code: str
    http_status: int
    i18n_key: str
    title: str
    detail_template: str  # {}-style format placeholders


# ─── Catalog ─────────────────────────────────────────────────────────────
# Convention: code is "noventra.<category>.<specific>" all lowercase with
# dots. i18n_key mirrors the code. One HTTP status per code.

ERROR_CATALOG: tuple[ErrorCode, ...] = (
    # ── 4xx — Client errors ────────────────────────────────────────────
    ErrorCode(
        code="noventra.auth.invalid_credentials",
        http_status=401,
        i18n_key="errors.noventra.auth.invalid_credentials",
        title="Invalid credentials",
        detail_template="The credentials provided are invalid.",
    ),
    ErrorCode(
        code="noventra.auth.token_expired",
        http_status=401,
        i18n_key="errors.noventra.auth.token_expired",
        title="Token expired",
        detail_template="The authentication token has expired.",
    ),
    ErrorCode(
        code="noventra.auth.token_invalid",
        http_status=401,
        i18n_key="errors.noventra.auth.token_invalid",
        title="Invalid token",
        detail_template="The authentication token is invalid.",
    ),
    ErrorCode(
        code="noventra.auth.forbidden",
        http_status=403,
        i18n_key="errors.noventra.auth.forbidden",
        title="Forbidden",
        detail_template="You do not have permission to perform this action.",
    ),
    ErrorCode(
        code="noventra.tenant.not_found",
        http_status=404,
        i18n_key="errors.noventra.tenant.not_found",
        title="Tenant not found",
        detail_template="No tenant with id {tenant_id} was found.",
    ),
    ErrorCode(
        code="noventra.tenant.missing",
        http_status=400,
        i18n_key="errors.noventra.tenant.missing",
        title="Tenant missing",
        detail_template="No tenant identity was provided. Set X-Tenant-ID header or include a tenant_id JWT claim.",
    ),
    ErrorCode(
        code="noventra.tenant.invalid",
        http_status=400,
        i18n_key="errors.noventra.tenant.invalid",
        title="Tenant invalid",
        detail_template="The tenant identity '{value}' is not a valid UUID.",
    ),
    ErrorCode(
        code="noventra.tenant.forbidden",
        http_status=403,
        i18n_key="errors.noventra.tenant.forbidden",
        title="Tenant forbidden",
        detail_template="You do not have permission to perform this action on tenant {tenant_id}.",
    ),
    ErrorCode(
        code="noventra.tenant.already_exists",
        http_status=409,
        i18n_key="errors.noventra.tenant.already_exists",
        title="Tenant already exists",
        detail_template="A tenant with the given identifier already exists.",
    ),
    ErrorCode(
        code="noventra.tenant.provisioning_failed",
        http_status=422,
        i18n_key="errors.noventra.tenant.provisioning_failed",
        title="Tenant provisioning failed",
        detail_template="Tenant provisioning failed during step: {step}.",
    ),
    ErrorCode(
        code="noventra.validation.invalid",
        http_status=422,
        i18n_key="errors.noventra.validation.invalid",
        title="Validation failed",
        detail_template="The request failed validation: {details}.",
    ),
    ErrorCode(
        code="noventra.idempotency.conflict",
        http_status=409,
        i18n_key="errors.noventra.idempotency.conflict",
        title="Idempotency conflict",
        detail_template="The idempotency key {key} was used with a different request body.",
    ),
    ErrorCode(
        code="noventra.rate_limit.exceeded",
        http_status=429,
        i18n_key="errors.noventra.rate_limit.exceeded",
        title="Rate limit exceeded",
        detail_template="Rate limit of {limit} requests per {window} exceeded.",
    ),
    # ── 5xx — Server errors ────────────────────────────────────────────
    ErrorCode(
        code="noventra.server.internal",
        http_status=500,
        i18n_key="errors.noventra.server.internal",
        title="Internal server error",
        detail_template="An internal server error occurred. Correlation ID: {correlation_id}.",
    ),
    ErrorCode(
        code="noventra.server.database_unavailable",
        http_status=503,
        i18n_key="errors.noventra.server.database_unavailable",
        title="Database unavailable",
        detail_template="The database is temporarily unavailable.",
    ),
    ErrorCode(
        code="noventra.server.redis_unavailable",
        http_status=503,
        i18n_key="errors.noventra.server.redis_unavailable",
        title="Cache unavailable",
        detail_template="The cache layer is temporarily unavailable.",
    ),
    ErrorCode(
        code="noventra.server.upstream_timeout",
        http_status=504,
        i18n_key="errors.noventra.server.upstream_timeout",
        title="Upstream timeout",
        detail_template="An upstream service did not respond in time: {upstream}.",
    ),
)

# Index for O(1) lookup by code.
_CATALOG_BY_CODE = {e.code: e for e in ERROR_CATALOG}


def get_error(code: str) -> Optional[ErrorCode]:
    """Look up an ErrorCode by code. Returns None if not found."""
    return _CATALOG_BY_CODE.get(code)


def all_codes() -> tuple[ErrorCode, ...]:
    """Return the full catalog (for docs generation and linter rule 19)."""
    return ERROR_CATALOG
