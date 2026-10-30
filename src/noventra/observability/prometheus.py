"""Prometheus metrics + /metrics/ endpoint scaffolding.

Per ADR-0017 / DEC-0017 (observability scaffolding): Prometheus client
+ internal /metrics/. Vendor Q5-blocked (ASSUMED scaffolding; OPEN-
DEPENDENT backend).

Phase 4 stub: exposes a Counter and a Histogram for the health
endpoint, plus process metrics. Phase 5+ adds per-endpoint metrics
via middleware.
"""

from __future__ import annotations

try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
    _PROMETHEUS_AVAILABLE = True
except ImportError:
    _PROMETHEUS_AVAILABLE = False
    Counter = Histogram = None  # type: ignore[assignment]

if _PROMETHEUS_AVAILABLE:
    # Health endpoint metrics.
    HEALTH_REQUESTS = Counter(
        "noventra_health_requests_total",
        "Total health endpoint requests",
        ["status"],
    )
    HEALTH_LATENCY = Histogram(
        "noventra_health_request_duration_seconds",
        "Health endpoint request duration",
    )


def metrics_response():
    """Return an HTTP response with the latest Prometheus metrics.

    Returns None if prometheus_client is not installed.
    """
    if not _PROMETHEUS_AVAILABLE:
        return None
    from django.http import HttpResponse
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)
