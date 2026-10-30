"""RFC 7807 problem+json response handler.

Per ADR-0026 / DEC-0031:
- RFC 7807 problem+json response shape.
- One HTTP status per code (enforced by catalog).
- i18n-key messages (default en; resolved via Django's i18n).
- correlation_id always included (from contextvar or header).
- Stack traces in logs only, never in response bodies.
- traces field is dev-only (DEBUG=True).
"""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.http import JsonResponse
from rest_framework import status

from .catalog import get_error
from ..middleware.correlation import get_correlation_id

log = logging.getLogger("noventra.errors")


def problem_response(
    code: str,
    *,
    detail_params: dict[str, Any] | None = None,
    instance: str | None = None,
    extras: dict[str, Any] | None = None,
) -> JsonResponse:
    """Build an RFC 7807 problem+json response from a catalog code.

    Args:
        code: Catalog code (e.g., "noventra.auth.invalid_credentials").
        detail_params: Format params for the detail_template.
        instance: Optional URI identifying the specific occurrence.
        extras: Optional additional fields merged into the response.

    Returns:
        JsonResponse with Content-Type application/problem+json.
    """
    error = get_error(code)
    if error is None:
        # Unknown code — fall back to internal server error.
        log.error("unknown_error_code", extra={"code": code})
        error = get_error("noventra.server.internal")  # type: ignore[assignment]
        detail_params = {"correlation_id": get_correlation_id()}

    detail_params = detail_params or {}
    try:
        detail = error.detail_template.format(**detail_params)
    except KeyError as e:
        log.warning("error_detail_missing_param", extra={"code": code, "missing": str(e)})
        detail = error.detail_template  # Fall back to template as-is.

    # i18n: resolve via Django's gettext if a translation is available.
    # Phase 4 stub: returns the English default. Phase 5+ adds locale files.
    title = error.title
    try:
        from django.utils.translation import gettext as _
        title = _(error.title)
    except Exception:
        pass

    body: dict[str, Any] = {
        "type": f"https://noventra.example/errors/{code}",
        "title": title,
        "status": error.http_status,
        "detail": detail,
        "code": error.code,
        "i18n_key": error.i18n_key,
        "correlation_id": get_correlation_id(),
    }
    if instance:
        body["instance"] = instance
    if extras:
        body.update(extras)

    # Dev-only: include stack trace field (DEBUG=True). Production never
    # includes traces in responses.
    if settings.DEBUG:
        import traceback
        body["traces"] = traceback.format_exc()

    response = JsonResponse(body, status=error.http_status, content_type="application/problem+json")
    return response


def unhandled_exception_handler(exc, context):
    """DRF exception handler fallback for unhandled exceptions.

    Logs the exception with correlation_id; returns a 500 problem+json
    response WITHOUT a stack trace in the body (traces in logs only).
    """
    request = context.get("request")
    view = context.get("view")
    correlation_id = get_correlation_id()

    log.exception(
        "unhandled_exception",
        extra={
            "correlation_id": correlation_id,
            "exc_class": exc.__class__.__name__,
            "view": view.__class__.__name__ if view else None,
            "path": request.path if request else None,
        },
    )

    return problem_response(
        "noventra.server.internal",
        detail_params={"correlation_id": correlation_id},
    )
