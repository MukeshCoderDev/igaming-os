"""Audit read API — clearance model + cursor pagination + meta-audit cut-off.

Per ADR-0039 / DEC-0044.
"""

from __future__ import annotations

import base64
import json
import logging
import uuid

from django.db import connection
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from noventra.apps.audit.adapters.redaction import redact_payload
from noventra.errors.handlers import problem_response

log = logging.getLogger("noventra.api.audit")


def _determine_clearance(claims) -> str:
    """Determine the reader's clearance level.

    Returns: "tenant_admin", "compliance_officer", or "external_auditor".

    Phase 7 stub: based on role claim. compliance_officer role = full
    access. service role = redacted. Otherwise = tenant_admin.
    """
    if claims.role == "compliance_officer":
        return "compliance_officer"
    if claims.typ == "service":
        return "external_auditor"
    return "tenant_admin"


class AuditLogView(APIView):
    """GET /api/v1/audit/log/ — read audit events with clearance model.

    Per ADR-0039:
    - tenant_admin: sees only own tenant's events.
    - compliance_officer: sees all events (unredacted).
    - external_auditor: sees all events (redacted).
    - Cursor-based pagination (no offset).
    - Filtering by event_type, actor_id, target_id, correlation_id, time range.
    - Meta-audit cut-off: this read generates audit.read_performed, but
      that event does NOT generate a further event.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        claims = getattr(request, "jwt_claims", None)
        if claims is None:
            return problem_response("noventra.auth.token_invalid")

        clearance = _determine_clearance(claims)

        # Build query.
        filters = []
        params = []

        # Clearance: tenant_admin sees only own tenant.
        if clearance == "tenant_admin":
            filters.append("(tenant_id = %s OR tenant_id IS NULL)")
            params.append(claims.tenant_id)

        # Optional filters.
        if event_type := request.query_params.get("event_type"):
            filters.append("event_type = %s")
            params.append(event_type)

        if actor_id := request.query_params.get("actor_id"):
            filters.append("actor_id = %s")
            params.append(actor_id)

        if target_id := request.query_params.get("target_id"):
            filters.append("target_id = %s")
            params.append(target_id)

        if correlation_id := request.query_params.get("correlation_id"):
            filters.append("correlation_id = %s")
            params.append(correlation_id)

        if start_time := request.query_params.get("start_time"):
            filters.append("created_at >= %s")
            params.append(start_time)

        if end_time := request.query_params.get("end_time"):
            filters.append("created_at <= %s")
            params.append(end_time)

        # Cursor pagination: cursor = base64(created_at + "|" + event_uuid).
        cursor = request.query_params.get("cursor")
        if cursor:
            try:
                decoded = base64.b64decode(cursor).decode()
                cursor_time, cursor_uuid = decoded.rsplit("|", 1)
                filters.append("(created_at, event_uuid) < (%s, %s)")
                params.extend([cursor_time, cursor_uuid])
            except Exception:
                return problem_response("noventra.validation.invalid",
                                        detail_params={"details": "invalid cursor"})

        limit = min(int(request.query_params.get("limit", 100)), 1000)

        where_clause = " AND ".join(filters) if filters else "TRUE"

        # Set tenant context for RLS (tenant_admin case).
        with connection.cursor() as cursor_obj:
            cursor_obj.execute("SET LOCAL app.tenant_uuid = %s", [claims.tenant_id])
            cursor_obj.execute(
                f"""
                SELECT event_uuid, tenant_id, actor_id, actor_type, event_type,
                       target_type, target_id, payload, prev_hash, hash,
                       correlation_id, created_at
                FROM audit_event
                WHERE {where_clause}
                ORDER BY created_at DESC, event_uuid DESC
                LIMIT %s
                """,
                params + [limit + 1],
            )
            rows = cursor_obj.fetchall()

        has_more = len(rows) > limit
        rows = rows[:limit]

        events = []
        for row in rows:
            payload = row[7] if isinstance(row[7], dict) else json.loads(row[7] or "{}")
            # Redact based on clearance.
            if clearance == "external_auditor":
                payload = redact_payload(payload, clearance)

            events.append({
                "event_uuid": str(row[0]),
                "tenant_id": str(row[1]) if row[1] else None,
                "actor_id": str(row[2]),
                "actor_type": row[3],
                "event_type": row[4],
                "target_type": row[5],
                "target_id": row[6],
                "payload": payload,
                "prev_hash": row[8],
                "hash": row[9],
                "correlation_id": row[10],
                "created_at": row[11].isoformat() if row[11] else None,
            })

        next_cursor = None
        if has_more and events:
            last = events[-1]
            next_cursor = base64.b64encode(
                f"{last['created_at']}|{last['event_uuid']}".encode()
            ).decode()

        # Emit audit.read_performed (meta-audit cut-off enforced in middleware).
        # The middleware will emit this; we don't emit here to avoid double-emission.

        return Response({
            "events": events,
            "next_cursor": next_cursor,
            "clearance": clearance,
        })
