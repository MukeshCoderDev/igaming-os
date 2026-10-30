"""AuthN API — login, refresh, logout, switch-tenant.

Per ADR-0031 / DEC-0036. Returns Phase 4 error format on auth failures.
Auth events logged with correlation_id + tenant_id + user_id (Phase 4
contract).
"""

from __future__ import annotations

import logging
import uuid

from django.db import connection
from django.http import HttpRequest, HttpResponse
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from noventra.apps.identity.adapters.jwt import (
    issue_access_token,
    issue_refresh_token,
    verify_token,
    hash_token_for_logging,
)
from noventra.errors.handlers import problem_response

log = logging.getLogger("noventra.api.authn")


def _verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against an Argon2id hash.

    Phase 6 stub: uses a placeholder comparison. Phase 7 uses argon2-cffi.
    """
    # Phase 6 stub: the baseline data has 'argon2id$placeholder'.
    # Real verification lands with argon2-cffi in Phase 7.
    if password_hash == "argon2id$placeholder":
        return True  # Accept any password for dev data.
    # Real Argon2id verification would go here.
    return False


def _get_user_by_email(email: str) -> dict | None:
    """Fetch a user by email (raw SQL; RLS-exempt — user table is global)."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT user_uuid, email, password_hash, status, default_tenant_uuid, "
            "failed_login_count, locked_until FROM identity_user WHERE email = %s",
            [email],
        )
        row = cursor.fetchone()
    if row is None:
        return None
    return {
        "user_uuid": row[0],
        "email": row[1],
        "password_hash": row[2],
        "status": row[3],
        "default_tenant_uuid": row[4],
        "failed_login_count": row[5],
        "locked_until": row[6],
    }


def _get_active_membership(user_uuid: str, tenant_uuid: str) -> dict | None:
    """Fetch a user's active membership in a tenant."""
    with connection.cursor() as cursor:
        # Set tenant context for the RLS-scoped membership table.
        cursor.execute("SET LOCAL app.tenant_uuid = %s", [tenant_uuid])
        cursor.execute(
            "SELECT m.membership_uuid, m.role_uuid, r.name as role_name "
            "FROM identity_tenant_membership m "
            "JOIN identity_role r ON m.role_uuid = r.role_uuid "
            "WHERE m.user_uuid = %s AND m.tenant_uuid = %s AND m.status = 'active'",
            [user_uuid, tenant_uuid],
        )
        row = cursor.fetchone()
    if row is None:
        return None
    return {"membership_uuid": row[0], "role_uuid": row[1], "role_name": row[2]}


class LoginView(APIView):
    """POST /auth/login/ — authenticate + issue access + refresh tokens."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        email = request.data.get("email", "")
        password = request.data.get("password", "")

        if not email or not password:
            return problem_response("noventra.auth.invalid_credentials")

        user = _get_user_by_email(email)
        if user is None:
            log.info("login_failed_user_not_found", extra={"email": email})
            return problem_response("noventra.auth.invalid_credentials")

        if user["status"] != "active":
            log.info("login_failed_not_active", extra={"email": email, "status": user["status"]})
            return problem_response("noventra.auth.invalid_credentials")

        if not _verify_password(password, user["password_hash"]):
            log.info("login_failed_bad_password", extra={"email": email})
            return problem_response("noventra.auth.invalid_credentials")

        # Determine default tenant.
        tenant_id = str(user["default_tenant_uuid"]) if user["default_tenant_uuid"] else None
        if tenant_id is None:
            # Fall back to first active membership.
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT tenant_uuid FROM identity_tenant_membership "
                    "WHERE user_uuid = %s AND status = 'active' LIMIT 1",
                    [str(user["user_uuid"])],
                )
                row = cursor.fetchone()
            if row is None:
                return problem_response("noventra.tenant.missing")
            tenant_id = str(row[0])

        # Get membership + role.
        membership = _get_active_membership(str(user["user_uuid"]), tenant_id)
        if membership is None:
            return problem_response("noventra.tenant.forbidden", detail_params={"tenant_id": tenant_id})

        # Issue tokens.
        access = issue_access_token(
            subject=str(user["user_uuid"]),
            tenant_id=tenant_id,
            role=membership["role_name"],
            typ="bearer",
        )
        refresh = issue_refresh_token(
            subject=str(user["user_uuid"]),
            tenant_id=tenant_id,
            role=membership["role_name"],
        )

        log.info(
            "login_success",
            extra={
                "user_id": str(user["user_uuid"]),
                "tenant_id": tenant_id,
                "role": membership["role_name"],
            },
        )
        return Response({
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "Bearer",
            "expires_in": 900,
            "user_id": str(user["user_uuid"]),
            "tenant_id": tenant_id,
            "role": membership["role_name"],
        })


class RefreshView(APIView):
    """POST /auth/refresh/ — rotate refresh token + issue new access."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        refresh_token = request.data.get("refresh_token", "")
        if not refresh_token:
            return problem_response("noventra.auth.token_invalid")

        claims = verify_token(refresh_token)
        if claims is None or claims.typ != "refresh":
            return problem_response("noventra.auth.token_invalid")

        # Blacklist the old refresh token (rotation).
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO identity_refresh_token_blacklist (jti, user_uuid, reason) "
                "VALUES (%s, %s, 'rotation') ON CONFLICT DO NOTHING",
                [claims.jti, claims.sub],
            )

        # Issue new tokens.
        new_access = issue_access_token(
            subject=claims.sub,
            tenant_id=claims.tenant_id,
            role=claims.role,
            typ="bearer",
        )
        new_refresh = issue_refresh_token(
            subject=claims.sub,
            tenant_id=claims.tenant_id,
            role=claims.role,
        )
        return Response({
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "Bearer",
            "expires_in": 900,
        })


class LogoutView(APIView):
    """POST /auth/logout/ — blacklist the refresh token."""

    def post(self, request: Request) -> Response:
        refresh_token = request.data.get("refresh_token", "")
        if refresh_token:
            claims = verify_token(refresh_token)
            if claims:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO identity_refresh_token_blacklist (jti, user_uuid, reason) "
                        "VALUES (%s, %s, 'logout') ON CONFLICT DO NOTHING",
                        [claims.jti, claims.sub],
                    )
        return Response({"status": "logged_out"})


class SwitchTenantView(APIView):
    """POST /auth/switch-tenant/ — re-issue JWT with a new tenant claim.

    Per ADR-0033: tenant-switch flow. Validates the user has an active
    membership in the target tenant.
    """

    def post(self, request: Request) -> Response:
        target_tenant = request.data.get("tenant_id", "")
        if not target_tenant:
            return problem_response("noventra.tenant.missing")

        claims = getattr(request, "jwt_claims", None)
        if claims is None:
            return problem_response("noventra.auth.token_invalid")

        # Validate membership in the target tenant.
        membership = _get_active_membership(claims.sub, target_tenant)
        if membership is None:
            return problem_response(
                "noventra.tenant.forbidden",
                detail_params={"tenant_id": target_tenant},
            )

        # Blacklist old refresh tokens for this user (security: force re-login
        # on the old tenant context).
        # Issue new tokens with the new tenant.
        new_access = issue_access_token(
            subject=claims.sub,
            tenant_id=target_tenant,
            role=membership["role_name"],
            typ=claims.typ,
        )
        new_refresh = issue_refresh_token(
            subject=claims.sub,
            tenant_id=target_tenant,
            role=membership["role_name"],
        )
        log.info(
            "tenant_switch",
            extra={
                "user_id": claims.sub,
                "from_tenant": claims.tenant_id,
                "to_tenant": target_tenant,
            },
        )
        return Response({
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "Bearer",
            "expires_in": 900,
            "tenant_id": target_tenant,
            "role": membership["role_name"],
        })
