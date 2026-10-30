"""Tenant resolution middleware.

Per ADR-0029 / DEC-0034:
- JWT claim (primary) + X-Tenant-ID header (fallback).
- Validates format (UUID) + existence before DB call.
- Missing/malformed → 400 E_TENANT_MISSING / E_TENANT_INVALID.
- On valid: SET LOCAL app.tenant_uuid on the DB connection + contextvar.

Runs AFTER CorrelationIdMiddleware so log lines carry both IDs.
"""

from __future__ import annotations

import contextvars
import logging
import uuid
from typing import Callable, Optional

from django.db import connection
from django.http import HttpRequest, HttpResponse

from noventra.errors.handlers import problem_response

log = logging.getLogger("noventra.middleware.tenant")

# Contextvar: the resolved tenant UUID for the current request.
tenant_uuid_var: contextvars.ContextVar[Optional[uuid.UUID]] = contextvars.ContextVar(
    "tenant_uuid", default=None
)

# Header name for the fallback path.
TENANT_ID_HEADER = "X-Tenant-ID"

# Paths exempt from tenant resolution (no tenant context needed).
EXEMPT_PATHS = frozenset({
    "/health/",
    "/metrics/",
    "/admin/",  # Django admin uses superuser, not tenant context.
})


def get_tenant_uuid() -> Optional[uuid.UUID]:
    """Return the current tenant UUID from the contextvar."""
    return tenant_uuid_var.get()


def _extract_tenant_id(request: HttpRequest) -> Optional[str]:
    """Extract tenant ID from JWT claim (primary) or X-Tenant-ID header (fallback).

    Phase 5 stub: JWT parsing lands in Phase 6 (identity service). For
    now, we read from the X-Tenant-ID header. The JWT path is stubbed
    but the interface is stable.
    """
    # Primary: JWT claim (Phase 6+). For now, check if request.user
    # has a tenant_id attribute (set by a future JWT middleware).
    jwt_tenant_id = getattr(request, "jwt_tenant_id", None)
    if jwt_tenant_id:
        return str(jwt_tenant_id)

    # Fallback: X-Tenant-ID header.
    header_value = request.headers.get(TENANT_ID_HEADER, "")
    if header_value:
        return header_value

    return None


def _validate_uuid(value: str) -> Optional[uuid.UUID]:
    """Validate that the value is a proper UUID. Returns UUID or None."""
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError, TypeError):
        return None


def _tenant_exists(tenant_uuid: uuid.UUID) -> bool:
    """Check if a tenant exists. Uses a raw query with app.tenant_uuid set.

    IMPORTANT: This query must run with a superuser/break-glass
    connection OR with app.tenant_uuid set to the queried UUID. We
    set app.tenant_uuid first, then query. This is safe because
    we're checking existence, not exposing data.
    """
    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL app.tenant_uuid = %s", [str(tenant_uuid)])
        cursor.execute(
            "SELECT 1 FROM tenancy_tenant WHERE tenant_uuid = %s AND status = 'active' LIMIT 1",
            [str(tenant_uuid)],
        )
        return cursor.fetchone() is not None


class TenantResolutionMiddleware:
    """Resolve the active tenant for every non-exempt request.

    Per ADR-0029: JWT claim primary, X-Tenant-ID header fallback.
    Missing/malformed → 400 before DB call. Valid → SET LOCAL +
    contextvar.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Exempt paths: health, metrics, admin.
        if any(request.path.startswith(p) for p in EXEMPT_PATHS):
            return self.get_response(request)

        # Extract tenant ID (JWT primary, header fallback).
        raw_tenant_id = _extract_tenant_id(request)

        # Missing → 400 E_TENANT_MISSING.
        if not raw_tenant_id:
            log.warning(
                "tenant_missing",
                extra={"path": request.path, "correlation_id": _get_corr_id()},
            )
            return problem_response(
                "noventra.tenant.missing",
                detail_params={},
            )

        # Malformed → 400 E_TENANT_INVALID.
        tenant_uuid = _validate_uuid(raw_tenant_id)
        if tenant_uuid is None:
            log.warning(
                "tenant_invalid_format",
                extra={"raw": raw_tenant_id, "path": request.path},
            )
            return problem_response(
                "noventra.tenant.invalid",
                detail_params={"value": raw_tenant_id},
            )

        # Existence check (sets SET LOCAL app.tenant_uuid for the check).
        if not _tenant_exists(tenant_uuid):
            log.warning(
                "tenant_not_found",
                extra={"tenant_uuid": str(tenant_uuid), "path": request.path},
            )
            return problem_response(
                "noventra.tenant.not_found",
                detail_params={"tenant_id": str(tenant_uuid)},
            )

        # Valid: set contextvar + SET LOCAL for downstream queries.
        token = tenant_uuid_var.set(tenant_uuid)
        # SET LOCAL was already set by _tenant_exists; it persists for
        # the current transaction (ATOMIC_REQUESTS). If not in a
        # transaction, set it again.
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL app.tenant_uuid = %s", [str(tenant_uuid)])

        # Bind to structlog contextvars for log correlation.
        try:
            import structlog
            structlog.contextvars.bind_contextvars(tenant_id=str(tenant_uuid))
        except ImportError:
            pass

        try:
            response = self.get_response(request)
        finally:
            tenant_uuid_var.reset(token)

        return response


def _get_corr_id() -> str:
    """Get correlation ID from the correlation middleware's contextvar."""
    try:
        from noventra.middleware.correlation import get_correlation_id
        return get_correlation_id()
    except ImportError:
        return ""
