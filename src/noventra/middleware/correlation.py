"""Correlation-ID middleware.

Per ADR-0025 / DEC-0030:
- X-Correlation-ID header read from request; ULID generated if absent.
- contextvar propagation to logging, outbound HTTP, Celery, async.
- Response header X-Correlation-ID always set.
- src/noventra/middleware/correlation.py.

The correlation_id is stored in a contextvar (structlog.contextvars) so
that all log lines emitted during the request carry the same ID. The
contextvar also propagates to async tasks (Celery, asyncio) when the
task is spawned from a request context.
"""

from __future__ import annotations

import contextvars
import secrets
from typing import Callable

# Contextvar: propagates to async tasks spawned from the request.
correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default=""
)

# Header name (case-insensitive per HTTP/1.1, but Django normalizes).
CORRELATION_ID_HEADER = "X-Correlation-ID"


def generate_ulid() -> str:
    """Generate a ULID-like identifier (26 chars, Crockford base32).

    Phase 4 stub: uses secrets.token_hex(13) = 26 hex chars. Real ULID
    (per https://github.com/ulid/spec) is 26 Crockford base32 chars
    encoding a 48-bit timestamp + 80-bit randomness. Phase 5 may swap
    in the `python-ulid` package if added to deps.
    """
    return secrets.token_hex(13)


def get_correlation_id() -> str:
    """Return the current correlation_id from the contextvar."""
    return correlation_id_var.get()


class CorrelationIdMiddleware:
    """Read or generate X-Correlation-ID; store in contextvar; set response header.

    Also pushes the correlation_id into structlog's contextvars so that
    all log lines emitted during the request carry it.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request):
        # Read incoming header (case-insensitive).
        correlation_id = request.headers.get(CORRELATION_ID_HEADER, "") or generate_ulid()

        # Store in contextvar (propagates to async children).
        token = correlation_id_var.set(correlation_id)

        # Push into structlog contextvars for log correlation.
        try:
            import structlog
            structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
        except ImportError:
            pass

        try:
            response = self.get_response(request)
        finally:
            # Reset contextvar (don't leak across requests).
            correlation_id_var.reset(token)

        # Always set the response header.
        response[CORRELATION_ID_HEADER] = correlation_id
        return response
