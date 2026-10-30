"""Audit append service — emits audit events on mutations.

Per Phase 7 spec output #10: audit middleware extends Phase 6 auth
middleware; emits audit events on every mutation; payload per event_type
schema; correlation_id from Phase 4 propagated.

Phase 7 stub: the middleware hooks into response phase to emit audit
events. Full mutation-detection (diff before/after) is Phase 8+.
"""

from __future__ import annotations

import logging
import uuid
from typing import Callable

from django.db import connection
from django.http import HttpRequest, HttpResponse

log = logging.getLogger("noventra.middleware.audit")


def append_audit_event(
    *,
    event_type: str,
    actor_id: str,
    actor_type: str = "human",
    tenant_id: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    payload: dict | None = None,
    correlation_id: str | None = None,
) -> str:
    """Append an audit event. Returns the event_uuid.

    The DB trigger (audit_compute_hash) computes prev_hash + hash.
    Per ADR-0038: insert-only (no update/delete).
    Per ADR-0035: hash chain (hybrid scope).
    """
    event_uuid = str(uuid.uuid4())
    payload = payload or {}

    # Set tenant context for RLS (if tenant_id is set).
    with connection.cursor() as cursor:
        if tenant_id:
            cursor.execute("SET LOCAL app.tenant_uuid = %s", [tenant_id])
        cursor.execute(
            """
            INSERT INTO audit_event
                (event_uuid, tenant_id, actor_id, actor_type, event_type,
                 target_type, target_id, payload, correlation_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                event_uuid,
                tenant_id,
                actor_id,
                actor_type,
                event_type,
                target_type,
                target_id,
                __import__("json").dumps(payload),
                correlation_id,
            ],
        )
    log.info(
        "audit_event_appended",
        extra={
            "event_uuid": event_uuid,
            "event_type": event_type,
            "actor_id": actor_id,
            "tenant_id": tenant_id,
            "correlation_id": correlation_id,
        },
    )
    return event_uuid


class AuditMiddleware:
    """Emit audit events for mutations.

    Phase 7 stub: emits audit.read_performed for GET requests to audit
    endpoints; emits audit events for POST/PUT/PATCH/DELETE. Full
    mutation detection (diff) is Phase 8+.

    Runs AFTER AuthN + Tenant middleware so it has user + tenant context.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        # Emit audit event for mutations.
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            self._emit_mutation_audit(request, response)
        elif request.path.startswith("/api/v1/audit/") and request.method == "GET":
            self._emit_read_audit(request, response)

        return response

    def _emit_mutation_audit(self, request: HttpRequest, response: HttpResponse) -> None:
        """Emit an audit event for a mutation."""
        claims = getattr(request, "jwt_claims", None)
        if claims is None:
            return  # Public endpoint; no audit.

        # Map HTTP method + path to event_type (Phase 7 stub; full mapping Phase 8).
        event_type = self._infer_event_type(request.method, request.path)
        if event_type is None:
            return

        try:
            append_audit_event(
                event_type=event_type,
                actor_id=claims.sub,
                actor_type=claims.typ,
                tenant_id=claims.tenant_id,
                target_type="endpoint",
                target_id=request.path,
                payload={"method": request.method, "status": response.status_code},
                correlation_id=getattr(request, "correlation_id", None),
            )
        except Exception as e:
            log.error("audit_emit_failed", extra={"error": str(e), "event_type": event_type})

    def _emit_read_audit(self, request: HttpRequest, response: HttpResponse) -> None:
        """Emit audit.read_performed for audit endpoint reads.

        Per ADR-0039: meta-audit cut-off. The audit of a read does NOT
        generate a further audit event. This is enforced by the cut-off
        context flag.
        """
        # Meta-audit cut-off: if this request is itself a meta-audit read,
        # don't emit a further event.
        if getattr(request, "_meta_audit_depth", 0) > 0:
            return

        claims = getattr(request, "jwt_claims", None)
        if claims is None:
            return

        try:
            append_audit_event(
                event_type="audit.read_performed",
                actor_id=claims.sub,
                actor_type=claims.typ,
                tenant_id=claims.tenant_id,
                target_type="audit_log",
                target_id=None,
                payload={"path": request.path, "status": response.status_code},
                correlation_id=getattr(request, "correlation_id", None),
            )
        except Exception as e:
            log.error("audit_read_emit_failed", extra={"error": str(e)})

    def _infer_event_type(self, method: str, path: str) -> str | None:
        """Infer event_type from HTTP method + path. Phase 7 stub."""
        if path.startswith("/auth/login"):
            return "auth.login_success"
        if path.startswith("/auth/logout"):
            return "auth.logout"
        if path.startswith("/auth/refresh"):
            return "auth.token_refreshed"
        if path.startswith("/auth/switch-tenant"):
            return "auth.tenant_switched"
        if path.startswith("/api/v1/tenants") and method == "POST":
            return "tenancy.tenant_provisioned"
        if path.startswith("/api/v1/tenants") and method == "DELETE":
            return "tenancy.tenant_suspended"
        return None
