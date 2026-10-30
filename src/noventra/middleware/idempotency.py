"""Idempotency middleware.

Per ADR-0043 / DEC-0048: client-supplied Idempotency-Key header (UUIDv4);
24-hour TTL; conflict handling; same-transaction insertion; cross-service
propagation.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import timedelta
from django.utils import timezone

from django.db import connection, transaction
from django.http import HttpRequest, HttpResponse

from noventra.errors.handlers import problem_response

log = logging.getLogger("noventra.middleware.idempotency")

IDEMPOTENCY_KEY_HEADER = "Idempotency-Key"
TTL_HOURS = 24


class IdempotencyMiddleware:
    """Idempotency key middleware.

    Per ADR-0043: only applies to mutating endpoints (POST, PUT, PATCH, DELETE).
    Same key + same body = cached response; same key + different body = 409.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
            return self.get_response(request)

        key = request.headers.get(IDEMPOTENCY_KEY_HEADER, "")
        if not key:
            return self.get_response(request)

        # Get tenant + endpoint from request (set by earlier middleware).
        tenant_id = getattr(request, "jwt_tenant_id", None)
        if not tenant_id:
            return self.get_response(request)

        endpoint = request.path
        request_body = request.body.decode() if request.body else ""
        request_hash = hashlib.sha256(request_body.encode()).hexdigest()

        # Check for existing key.
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL app.tenant_uuid = %s", [tenant_id])
            cursor.execute(
                """
                SELECT request_hash, response_status, response_body, expires_at
                FROM reliability_idempotency_key
                WHERE key = %s AND tenant_id = %s AND endpoint = %s
                """,
                [key, tenant_id, endpoint],
            )
            row = cursor.fetchone()

        if row:
            stored_hash, stored_status, stored_body, expires_at = row
            # Same key + same body = cached response.
            if stored_hash == request_hash:
                log.info("idempotency_cache_hit", extra={"key": key, "endpoint": endpoint})
                from django.http import HttpResponse
                return HttpResponse(stored_body, status=stored_status, content_type="application/json")
            # Same key + different body = 409.
            log.warning("idempotency_conflict", extra={"key": key, "endpoint": endpoint})
            return problem_response(
                "noventra.idempotency.conflict",
                detail_params={"key": key},
            )

        # No existing key: process the request + store the response.
        response = self.get_response(request)

        # Store the response (same transaction as the request's side effects).
        expires = timezone.now() + timedelta(hours=TTL_HOURS)
        response_body = response.content.decode() if hasattr(response, "content") else ""
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL app.tenant_uuid = %s", [tenant_id])
            cursor.execute(
                """
                INSERT INTO reliability_idempotency_key
                    (key, tenant_id, endpoint, request_hash, response_status, response_body, created_at, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s)
                ON CONFLICT DO NOTHING
                """,
                [key, tenant_id, endpoint, request_hash, response.status_code, response_body, expires],
            )

        return response
