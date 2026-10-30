"""Tests for the error response handler (ADR-0026 / DEC-0031).

Covers:
- problem_response produces RFC 7807 problem+json.
- Stack-trace suppression in production (DEBUG=False).
- Stack-trace present in dev (DEBUG=True).
- correlation_id always present.
"""

from __future__ import annotations

import json

import pytest
from django.test import override_settings

from noventra.errors.handlers import problem_response


@pytest.mark.django_db
def test_problem_response_basic():
    """problem_response returns an RFC 7807 problem+json response."""
    response = problem_response("noventra.auth.invalid_credentials")
    assert response.status_code == 401
    assert response["Content-Type"] == "application/problem+json"
    body = json.loads(response.content)
    assert body["code"] == "noventra.auth.invalid_credentials"
    assert body["status"] == 401
    assert body["i18n_key"] == "errors.noventra.auth.invalid_credentials"
    assert "title" in body
    assert "detail" in body
    assert "correlation_id" in body


@pytest.mark.django_db
def test_problem_response_detail_params():
    """detail_params are formatted into the detail template."""
    response = problem_response(
        "noventra.tenant.not_found",
        detail_params={"tenant_id": "123e4567-e89b-12d3-a456-426614174000"},
    )
    body = json.loads(response.content)
    assert "123e4567-e89b-12d3-a456-426614174000" in body["detail"]


@override_settings(DEBUG=False)
@pytest.mark.django_db
def test_stack_trace_suppressed_in_production():
    """Stack-trace suppression: DEBUG=False → no 'traces' field in response.

    Per Phase 4 hard acceptance: "Stack-trace suppression asserted by test
    against prod settings."
    """
    response = problem_response("noventra.server.internal")
    body = json.loads(response.content)
    assert "traces" not in body, (
        "Stack trace leaked into production response: " + str(body.get("traces", ""))[:100]
    )


@override_settings(DEBUG=True)
@pytest.mark.django_db
def test_stack_trace_present_in_dev():
    """DEBUG=True → 'traces' field present in response (dev-only)."""
    response = problem_response("noventra.server.internal")
    body = json.loads(response.content)
    assert "traces" in body


@pytest.mark.django_db
def test_unknown_code_falls_back_to_internal_error():
    """An unknown code falls back to noventra.server.internal (500)."""
    response = problem_response("noventra.does.not.exist")
    assert response.status_code == 500
    body = json.loads(response.content)
    assert body["code"] == "noventra.server.internal"
