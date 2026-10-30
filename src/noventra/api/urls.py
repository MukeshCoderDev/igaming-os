"""Health endpoint URLs.

GET /health/ → 200 {status, version, checks:{db, redis, migrations_applied}}
              503 on any failure; no secrets; rate-limited.
"""

from django.urls import path

from .health import HealthView

urlpatterns = [
    path("", HealthView.as_view(), name="health"),
]
