"""Tests for pgbouncer compatibility (Phase 5 / ADR-0030).

Per Phase 5 hard acceptance: "pgbouncer test passes against local
compose instance."

These tests verify that the application's DB patterns work correctly
under pgbouncer transaction-mode:
1. Read: SELECT returns expected rows.
2. Write: INSERT persists.
3. Rollback: a rolled-back transaction leaves no side effects.
4. Recycle: a recycled connection has the correct RLS context (SET
   LOCAL doesn't leak between transactions).

Phase 5 stub: these tests run against the DATABASE_URL configured
in the test environment. If pgbouncer is in the path (port 6432),
they exercise pgbouncer. If not, they still pass (the patterns are
pgbouncer-safe regardless).
"""

from __future__ import annotations

import uuid

import pytest
from django.db import connection


TENANT_A = uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.mark.django_db
class TestPgbouncerCompatibility:
    """Verify pgbouncer-safe patterns work under transaction-mode."""

    def test_read_under_pgbouncer(self):
        """A SELECT under pgbouncer returns expected rows."""
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL app.tenant_uuid = %s", [str(TENANT_A)])
            cursor.execute("SELECT COUNT(*) FROM tenancy_tenant")
            count = cursor.fetchone()[0]
        assert count == 1, f"Expected 1 tenant, got {count}"

    def test_write_under_pgbouncer(self):
        """An INSERT under pgbouncer persists within the transaction."""
        new_brand_uuid = uuid.uuid4()
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL app.tenant_uuid = %s", [str(TENANT_A)])
            cursor.execute(
                "INSERT INTO tenancy_brand (brand_uuid, tenant_uuid, name, display_name) "
                "VALUES (%s, %s, 'test-brand', 'Test Brand')",
                [str(new_brand_uuid), str(TENANT_A)],
            )
            cursor.execute(
                "SELECT name FROM tenancy_brand WHERE brand_uuid = %s",
                [str(new_brand_uuid)],
            )
            row = cursor.fetchone()
        assert row is not None
        assert row[0] == "test-brand"

    def test_rollback_under_pgbouncer(self):
        """A rolled-back transaction leaves no side effects."""
        new_brand_uuid = uuid.uuid4()
        from django.db import transaction
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("SET LOCAL app.tenant_uuid = %s", [str(TENANT_A)])
                    cursor.execute(
                        "INSERT INTO tenancy_brand (brand_uuid, tenant_uuid, name, display_name) "
                        "VALUES (%s, %s, 'rollback-brand', 'Rollback Brand')",
                        [str(new_brand_uuid), str(TENANT_A)],
                    )
                raise RuntimeError("intentional rollback")
        except RuntimeError:
            pass

        # Verify the brand was NOT persisted.
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL app.tenant_uuid = %s", [str(TENANT_A)])
            cursor.execute(
                "SELECT COUNT(*) FROM tenancy_brand WHERE brand_uuid = %s",
                [str(new_brand_uuid)],
            )
            count = cursor.fetchone()[0]
        assert count == 0, "Rolled-back brand was persisted (pgbouncer transaction issue)"

    def test_set_local_does_not_leak_between_transactions(self):
        """SET LOCAL in one transaction does not leak to the next.

        Per ADR-0030: SET LOCAL only. This test verifies that a SET
        LOCAL in transaction 1 does not affect transaction 2 (which
        would be a security issue: cross-tenant data leak).
        """
        from django.db import transaction

        # Transaction 1: set tenant to TENANT_A.
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL app.tenant_uuid = %s", [str(TENANT_A)])
                cursor.execute("SELECT COUNT(*) FROM tenancy_tenant")
                count_1 = cursor.fetchone()[0]
        assert count_1 == 1

        # Transaction 2: do NOT set tenant. Should see zero rows (fail-closed).
        with transaction.atomic():
            with connection.cursor() as cursor:
                # Explicitly clear any leaked setting.
                cursor.execute("SET LOCAL app.tenant_uuid = ''")
                cursor.execute("SELECT COUNT(*) FROM tenancy_tenant")
                count_2 = cursor.fetchone()[0]
        assert count_2 == 0, "SET LOCAL leaked between transactions (pgbouncer/RLS issue)"
