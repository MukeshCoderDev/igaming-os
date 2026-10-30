"""Tests for the correlation-ID middleware (ADR-0025 / DEC-0030).

Covers:
- X-Correlation-ID header read from request.
- ULID generated if header absent.
- X-Correlation-ID response header always set.
- contextvar propagation (get_correlation_id returns the value).
"""

from __future__ import annotations

import pytest
from django.test import RequestFactory

from noventra.middleware.correlation import (
    CorrelationIdMiddleware,
    CORRELATION_ID_HEADER,
    correlation_id_var,
    generate_ulid,
    get_correlation_id,
)


@pytest.fixture
def rf():
    return RequestFactory()


def _dummy_get_response(request):
    """A dummy view that records the correlation_id at call time."""
    from django.http import HttpResponse
    response = HttpResponse("ok")
    response._captured_correlation_id = get_correlation_id()
    return response


def test_ulid_generated_is_26_chars(rf):
    """generate_ulid returns a 26-char hex string."""
    ulid = generate_ulid()
    assert len(ulid) == 26
    assert all(c in "0123456789abcdef" for c in ulid)


def test_incoming_correlation_id_header_is_used(rf):
    """If X-Correlation-ID is in the request, it's used and set on the response."""
    request = rf.get("/", **{"HTTP_X_CORRELATION_ID": "incoming-id-123"})
    middleware = CorrelationIdMiddleware(_dummy_get_response)
    response = middleware(request)
    assert response[CORRELATION_ID_HEADER] == "incoming-id-123"


def test_correlation_id_generated_when_absent(rf):
    """If X-Correlation-ID is absent, a ULID is generated and set on the response."""
    request = rf.get("/")
    middleware = CorrelationIdMiddleware(_dummy_get_response)
    response = middleware(request)
    cid = response[CORRELATION_ID_HEADER]
    assert cid
    assert len(cid) == 26  # ULID format


def test_contextvar_set_during_request(rf):
    """The contextvar is set to the correlation_id during the request."""
    request = rf.get("/", **{"HTTP_X_CORRELATION_ID": "ctx-test-id"})
    middleware = CorrelationIdMiddleware(_dummy_get_response)
    response = middleware(request)
    # The dummy view captured the correlation_id at call time.
    assert response._captured_correlation_id == "ctx-test-id"


def test_contextvar_reset_after_request(rf):
    """The contextvar is reset (doesn't leak) after the request."""
    request = rf.get("/", **{"HTTP_X_CORRELATION_ID": "leak-test-id"})
    middleware = CorrelationIdMiddleware(_dummy_get_response)
    middleware(request)
    # After the request, the contextvar should be reset to its default ("").
    assert correlation_id_var.get() == ""


def test_correlation_id_propagates_to_mocked_outbound_call(rf):
    """The correlation_id propagates to a mocked outbound call (contextvar).

    Per Phase 4 hard acceptance: "Correlation-ID on every sampled log line
    + one mocked outbound call." This test simulates an outbound call
    (e.g., to a downstream service) made within the request scope and
    verifies it can access the correlation_id via get_correlation_id().
    """
    captured_in_outbound = []

    def mock_outbound_call():
        """Simulate an outbound HTTP call that should carry the correlation_id."""
        captured_in_outbound.append(get_correlation_id())

    def get_response_with_outbound(request):
        from django.http import HttpResponse
        # Within the request scope, make a mocked outbound call.
        mock_outbound_call()
        return HttpResponse("ok")

    request = rf.get("/", **{"HTTP_X_CORRELATION_ID": "outbound-test-id"})
    middleware = CorrelationIdMiddleware(get_response_with_outbound)
    middleware(request)

    assert captured_in_outbound == ["outbound-test-id"]
