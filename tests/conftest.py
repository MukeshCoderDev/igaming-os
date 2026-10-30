"""Pytest conftest — shared fixtures for the Noventra test suite.

Phase 3: minimal harness. Per Phase 3 spec output #8, the test harness
is present (pytest.ini, conftest.py, tests/factories/) but the suite
may be empty. Real fixtures land in Phase 4+.
"""

import os
import sys
from pathlib import Path

import pytest

# Ensure src/ is on the path (src-layout).
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest.fixture(scope="session")
def django_db_setup(django_test_environment, django_db_blocker):
    """Set up the test database with required roles, schema, and functions.

    The Docker init scripts (deploy/docker/init/) create roles, the app
    schema, and the app.tenant_uuid() function on the MAIN database.
    When pytest-django creates a fresh test DB, these don't exist.
    We bootstrap them here before migrations run.
    """
    from django.conf import settings
    from django.test.utils import setup_databases, teardown_databases

    with django_db_blocker.unblock():
        db_cfg = setup_databases(
            verbosity=0,
            interactive=False,
            keepdb=True,
        )
        # Bootstrap: run the init SQL scripts on the test database so
        # that roles, schema `app`, and app.tenant_uuid() exist before
        # any migration references them.
        from django.db import connections
        conn = connections["default"]
        with conn.cursor() as cursor:
            # Read and execute each init script in order.
            init_dir = Path(__file__).resolve().parent.parent / "deploy" / "docker" / "init"
            for sql_file in sorted(init_dir.glob("*.sql")):
                sql = sql_file.read_text()
                try:
                    cursor.execute(sql)
                except Exception:
                    # Some statements may fail if already exist; continue.
                    conn.ensure_connection()
                    pass

            # Also grant noventra_app role to the current test user
            # (so RLS policies referencing noventra_app work).
            try:
                cursor.execute("SELECT current_user")
                current_user = cursor.fetchone()[0]
                cursor.execute(
                    f"GRANT noventra_app TO {current_user}"
                )
            except Exception:
                conn.ensure_connection()

            # Grant noventra_admin to current user (for break-glass tests).
            try:
                cursor.execute(
                    f"GRANT noventra_admin TO {current_user}"
                )
            except Exception:
                conn.ensure_connection()

        # Now run migrations on the test database.
        from django.core.management import call_command
        call_command("migrate", "--run-syncdb", verbosity=0)

    yield

    with django_db_blocker.unblock():
        try:
            teardown_databases(db_cfg, verbosity=0)
        except Exception:
            pass


@pytest.fixture
def api_client():
    """DRF API client for integration tests."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def health_url():
    """URL for the health endpoint."""
    return "/health/"
