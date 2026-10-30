"""Permission decorators — endpoint-level enforcement.

Per ADR-0032 (RBAC) + ADR-0034 (service/human separation):
- @human_only: rejects typ=service tokens.
- @service_only: rejects typ=bearer (human) tokens.
- @require_permission(code): checks the user's role has the permission.

Defense-in-depth per ADR-0034: claim check + endpoint check + role check.
"""

from __future__ import annotations

import functools
from typing import Callable

from django.http import HttpRequest, HttpResponse

from noventra.errors.handlers import problem_response


def human_only(view: Callable) -> Callable:
    """Reject service tokens. Only human (typ=bearer) tokens allowed."""

    @functools.wraps(view)
    def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        claims = getattr(request, "jwt_claims", None)
        if claims is None:
            return problem_response("noventra.auth.invalid_credentials")
        if claims.typ == "service":
            return problem_response(
                "noventra.auth.forbidden",
                detail_params={},
            )
        return view(request, *args, **kwargs)

    return wrapper


def service_only(view: Callable) -> Callable:
    """Reject human tokens. Only service (typ=service) tokens allowed."""

    @functools.wraps(view)
    def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        claims = getattr(request, "jwt_claims", None)
        if claims is None:
            return problem_response("noventra.auth.invalid_credentials")
        if claims.typ != "service":
            return problem_response(
                "noventra.auth.forbidden",
                detail_params={},
            )
        # Per ADR-0034: shadow services cannot mutate.
        # The @service_only decorator allows read; mutation requires
        # @require_permission("service.mutate") which checks the service
        # is live.
        return view(request, *args, **kwargs)

    return wrapper


def require_permission(code: str) -> Callable:
    """Require the given permission code. Checks role from JWT claims.

    Per ADR-0032: the user's role (from JWT) must have the permission
    in the closed catalog.
    Per ADR-0034: service.mutate requires the service to be LIVE
    (shadow services denied).
    """

    def decorator(view: Callable) -> Callable:
        @functools.wraps(view)
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            claims = getattr(request, "jwt_claims", None)
            if claims is None:
                return problem_response("noventra.auth.invalid_credentials")

            # Check the role has the permission.
            if not _role_has_permission(claims.role, code):
                return problem_response(
                    "noventra.auth.forbidden",
                    detail_params={},
                )

            # Defense-in-depth for service.mutate: check the service is live.
            if code == "service.mutate" and claims.typ == "service":
                if not _service_is_live(claims.sub):
                    return problem_response(
                        "noventra.auth.forbidden",
                        detail_params={},
                    )

            return view(request, *args, **kwargs)

        return wrapper

    return decorator


def _role_has_permission(role_name: str | None, code: str) -> bool:
    """Check if a role has a permission. Phase 6 stub: checks the catalog."""
    if role_name is None:
        return False
    from noventra.apps.identity.domain.permissions import BASELINE_ROLE_PERMISSIONS
    role_perms = BASELINE_ROLE_PERMISSIONS.get(role_name, ())
    return code in role_perms


def _service_is_live(service_uuid: str) -> bool:
    """Check if a service identity is LIVE (not shadow)."""
    try:
        from noventra.apps.identity.adapters.orm import ServiceIdentity
        svc = ServiceIdentity.objects.filter(service_uuid=service_uuid).first()
        return svc is not None and svc.status == "live"
    except Exception:
        return False
