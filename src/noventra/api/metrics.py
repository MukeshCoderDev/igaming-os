"""Metrics endpoint — Prometheus exposition format.

GET /metrics/ → 200 text/plain (Prometheus exposition format).
No secrets. Rate-limited (Phase 5 wires throttle; Phase 4 stub).
"""

from django.http import HttpResponse
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from noventra.observability.prometheus import metrics_response, _PROMETHEUS_AVAILABLE


class MetricsView(APIView):
    """GET /metrics/ — Prometheus exposition."""

    permission_classes = [AllowAny]
    # Phase 5: throttle_classes = [MetricsAnonThrottle]

    def get(self, request):
        if not _PROMETHEUS_AVAILABLE:
            return HttpResponse(
                "# prometheus_client not installed\n",
                content_type="text/plain",
                status=200,
            )
        response = metrics_response()
        return response or HttpResponse(
            "# metrics unavailable\n",
            content_type="text/plain",
            status=503,
        )
