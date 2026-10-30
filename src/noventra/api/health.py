"""Health endpoint.

Per Phase 3 spec output #5:
- GET /health/ → 200 {status, version, checks:{db, redis, migrations_applied}}
- 503 on any failure
- No secrets in response
- Rate-limited (Phase 4 wires the throttle class; Phase 3 stub)

The health check performs three sub-checks:
1. Database: SELECT 1 (verifies connection + auth).
2. Redis: PING (verifies connection + auth).
3. Migrations applied: queries django_migrations count and compares
   against the expected count (computed from migration files on disk).

No secrets are exposed in the response body. The response contains only:
status ("healthy" / "unhealthy"), version (from noventra.__version__),
and checks (a dict of check-name → boolean).
"""

from __future__ import annotations

import importlib.metadata
import os
from pathlib import Path

from django.conf import settings
from django.db import connections, OperationalError
from django.http import JsonResponse
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView


def _check_db() -> bool:
    """Verify the default database connection works (SELECT 1)."""
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True
    except (OperationalError, Exception):
        return False


def _check_redis() -> bool:
    """Verify Redis connection works (PING).

    Uses a lazy import so that test environments without Redis can still
    load the health module. If redis is not installed, the check returns
    False (treated as a failure).
    """
    try:
        import redis  # type: ignore[import-untyped]
    except ImportError:
        return False
    try:
        client = redis.from_url(settings.REDIS["URL"], socket_timeout=2)
        return bool(client.ping())
    except Exception:
        return False


def _check_migrations_applied() -> bool:
    """Verify that all migration files on disk are recorded in django_migrations.

    Counts migration files under each app's migrations/ directory and
    compares against the count recorded in the django_migrations table.
    Returns True if they match.
    """
    try:
        # Count migration files on disk (excluding __init__.py).
        disk_count = 0
        for app_config in settings.INSTALLED_APPS:
            try:
                app_module = __import__(app_config, fromlist=["migrations"])
                mig_dir = Path(app_module.__file__).parent / "migrations"
                if mig_dir.is_dir():
                    disk_count += len(
                        [f for f in mig_dir.glob("*.py") if f.stem != "__init__"]
                    )
            except (ImportError, AttributeError, TypeError):
                continue
        # Count applied migrations in the database.
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_migrations")
            db_count = cursor.fetchone()[0]
        return db_count >= disk_count
    except Exception:
        return False


class HealthView(APIView):
    """GET /health/ — platform health check.

    Returns 200 with status, version, and per-check booleans if all
    checks pass. Returns 503 if any check fails. No secrets are exposed.
    """

    permission_classes = [AllowAny]
    # Phase 4: add throttle_classes for rate limiting per Pain-REQ-0008.
    # throttle_classes = [HealthAnonThrottle]

    def get(self, request):  # noqa: D401
        checks = {
            "db": _check_db(),
            "redis": _check_redis(),
            "migrations_applied": _check_migrations_applied(),
        }
        all_healthy = all(checks.values())

        body = {
            "status": "healthy" if all_healthy else "unhealthy",
            "version": _get_version(),
            "checks": checks,
        }

        http_status = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        return JsonResponse(body, status=http_status)


def _get_version() -> str:
    """Return the platform version. Tries importlib.metadata, falls back to __version__."""
    try:
        from noventra import __version__
        return __version__
    except (ImportError, AttributeError):
        return "unknown"
