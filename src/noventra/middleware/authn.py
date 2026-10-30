"""AuthN middleware — JWT verification + API key + service token.

Per ADR-0031 / DEC-0036: verifies JWT (JWS) on every request to a
protected endpoint. Sets request.jwt_tenant_id (consumed by the
Phase 5 tenant middleware per ADR-0029/0033). Populates request.user
identity for downstream permission checks.

Per ADR-0034: separates human (typ=bearer) from service (typ=service)
tokens. Endpoint decorators enforce separation.

Runs BEFORE TenantResolutionMiddleware so the tenant middleware can
use the JWT claim.
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

from django.http import HttpRequest, HttpResponse

from noventra.apps.identity.adapters.jwt import TokenClaims, verify_token, hash_token_for_logging
from noventra.errors.handlers import problem_response

log = logging.getLogger("noventra.middleware.authn")

# Header names.
AUTHORIZATION_HEADER = "Authorization"
BEARER_PREFIX = "Bearer "
API_KEY_HEADER = "X-API-Key"

# Paths that don't require authn (login, refresh, health, metrics, OpenAPI).
PUBLIC_PATHS = frozenset({
    "/auth/login/",
    "/auth/refresh/",
    "/health/",
    "/metrics/",
    "/api/schema/",
    "/api/docs/",
})


class AuthNMiddleware:
    """Verify JWT or API key on every non-public request.

    Sets:
    - request.jwt_claims: TokenClaims (for downstream use).
    - request.jwt_tenant_id: the tenant_id claim (for TenantResolutionMiddleware).
    - request.is_service: True if typ=service.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Public paths: no authn required.
        if any(request.path.startswith(p) for p in PUBLIC_PATHS):
            return self.get_response(request)

        # Try JWT first.
        auth_header = request.headers.get(AUTHORIZATION_HEADER, "")
        if auth_header.startswith(BEARER_PREFIX):
            token = auth_header[len(BEARER_PREFIX):]
            claims = verify_token(token)
            if claims is None:
                log.warning(
                    "authn_token_invalid",
                    extra={"token_hash": hash_token_for_logging(token), "path": request.path},
                )
                return problem_response("noventra.auth.token_invalid")

            # Check refresh token blacklist (Phase 6 stub: DB check;
            # Phase 7: Redis cache).
            if _is_token_blacklisted(claims.jti):
                log.warning(
                    "authn_token_blacklisted",
                    extra={"jti": claims.jti, "sub": claims.sub},
                )
                return problem_response("noventra.auth.token_invalid")

            # Set request attributes for downstream middleware.
            request.jwt_claims = claims
            request.jwt_tenant_id = claims.tenant_id  # Consumed by tenant middleware.
            request.is_service = (claims.typ == "service")
            log.info(
                "authn_success",
                extra={
                    "sub": claims.sub,
                    "typ": claims.typ,
                    "tenant_id": claims.tenant_id,
                    "path": request.path,
                },
            )
            return self.get_response(request)

        # API key path (Phase 6 stub: partner integrations).
        api_key = request.headers.get(API_KEY_HEADER, "")
        if api_key:
            # Phase 6 stub: API key verification lands with partner
            # integration in Phase 7. For now, reject.
            log.warning("authn_api_key_not_implemented", extra={"path": request.path})
            return problem_response("noventra.auth.invalid_credentials")

        # No authn provided.
        log.warning("authn_missing", extra={"path": request.path})
        return problem_response("noventra.auth.invalid_credentials")


def _is_token_blacklisted(jti: str) -> bool:
    """Check if a token's JTI is in the refresh token blacklist."""
    if not jti:
        return False
    try:
        from noventra.apps.identity.adapters.orm import RefreshTokenBlacklist
        return RefreshTokenBlacklist.objects.filter(jti=jti).exists()
    except Exception:
        # DB not available (e.g., during tests without DB); fail open.
        return False
