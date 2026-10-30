"""Root URL configuration.

Phase 3: health endpoint mounted.
Phase 4: metrics endpoint mounted.
Phase 5: tenancy API (Phase 7+ routes).
Phase 6: authN endpoints (login, refresh, logout, switch-tenant).
"""

from django.urls import include, path

urlpatterns = [
    # Health endpoint (Phase 3 deliverable per spec output #5).
    path("health/", include("noventra.api.urls")),
    # Metrics endpoint (Phase 4 — Prometheus exposition format).
    path("metrics/", include(("noventra.api.metrics_urls", "metrics"), namespace="metrics")),
    # AuthN endpoints (Phase 6 — ADR-0031).
    path("auth/", include("noventra.apps.identity.api.urls")),
    # Audit read API (Phase 7 — ADR-0039).
    path("api/v1/audit/", include("noventra.apps.audit.api.urls")),
    # API routes (Phase 7+).
    # path("api/v1/", include("noventra.api.v1_urls")),
]
