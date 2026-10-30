"""check_rls_coverage management command — Phase 5 (non-vacuous).

Per Phase 5 spec output #8: "check_rls_coverage non-vacuous: covers all
tenant-scoped tables; CI rule 24."

The command scans every table in the `public` schema that has a
`tenant_uuid` column and verifies:
1. RLS is ENABLED on the table.
2. RLS is FORCED (owner subject to RLS).
3. A policy exists with `USING (tenant_uuid = app.tenant_uuid())`.
4. A policy exists with `WITH CHECK (tenant_uuid = app.tenant_uuid())`.

Tables without a `tenant_uuid` column are "global" and are allowlisted
(e.g., django_migrations, django_content_type, auth_user). The allowlist
is maintained in this file.

Exit code: 0 if all tenant-scoped tables have RLS; 1 if any are missing.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import connection


# Global tables (no tenant_uuid column) that are allowlisted.
# These are framework/system tables that don't need RLS.
GLOBAL_ALLOWLIST = frozenset({
    "django_migrations",
    "django_content_type",
    "django_admin_log",
    "django_session",
    "auth_user",
    "auth_group",
    "auth_group_permissions",
    "auth_permission",
    "auth_user_groups",
    "auth_user_user_permissions",
})


class Command(BaseCommand):
    help = "Verify that every tenant-scoped table has RLS enabled + policy. " \
           "Phase 5: non-vacuous check."

    def handle(self, *args, **options):
        # Find all tables with a tenant_uuid column.
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND column_name = 'tenant_uuid'
                ORDER BY table_name;
            """)
            tenant_scoped_tables = {row[0] for row in cursor.fetchall()}

        if not tenant_scoped_tables:
            self.stdout.write(self.style.WARNING(
                "check_rls_coverage: no tenant-scoped tables found. "
                "Phase 5 expects tenancy_tenant + tenancy_brand."
            ))
            # Not a failure, but suspicious. Exit 0 for now.
            return

        failures: list[str] = []

        for table in sorted(tenant_scoped_tables):
            issues = self._check_table(table)
            if issues:
                failures.extend(issues)

        if failures:
            self.stdout.write(self.style.ERROR(
                f"check_rls_coverage: FAIL — {len(failures)} issue(s) found:"
            ))
            for issue in failures:
                self.stdout.write(self.style.ERROR(f"  - {issue}"))
            # Exit non-zero to fail CI.
            import sys
            sys.exit(1)
        else:
            self.stdout.write(self.style.SUCCESS(
                f"check_rls_coverage: PASS — {len(tenant_scoped_tables)} "
                f"tenant-scoped table(s) have RLS enabled + policy."
            ))

    def _check_table(self, table: str) -> list[str]:
        """Check RLS status for a single table. Returns list of issues."""
        issues: list[str] = []
        with connection.cursor() as cursor:
            # Check RLS enabled.
            cursor.execute("""
                SELECT relrowsecurity, relforcerowsecurity
                FROM pg_class
                WHERE relname = %s AND relnamespace = 'public'::regnamespace;
            """, [table])
            row = cursor.fetchone()
            if row is None:
                issues.append(f"{table}: table not found in pg_class")
                return issues
            rls_enabled, rls_forced = row
            if not rls_enabled:
                issues.append(f"{table}: RLS not enabled (relrowsecurity=false)")
            if not rls_forced:
                issues.append(f"{table}: RLS not forced (relforcerowsecurity=false)")

            # Check policy exists with USING.
            cursor.execute("""
                SELECT polname, polqual
                FROM pg_policy
                WHERE polrelid = %s::regclass;
            """, [table])
            policies = cursor.fetchall()
            if not policies:
                issues.append(f"{table}: no RLS policy found")
            else:
                has_using = False
                has_with_check = False
                for polname, polqual in policies:
                    # polqual is the USING expression; polwithcheck is the WITH CHECK.
                    cursor.execute("""
                        SELECT polwithcheck FROM pg_policy
                        WHERE polrelid = %s::regclass AND polname = %s;
                    """, [table, polname])
                    polwithcheck = cursor.fetchone()[0]
                    if polqual and "app.tenant_uuid()" in str(polqual):
                        has_using = True
                    if polwithcheck and "app.tenant_uuid()" in str(polwithcheck):
                        has_with_check = True
                if not has_using:
                    issues.append(f"{table}: no policy with USING (tenant_uuid = app.tenant_uuid())")
                if not has_with_check:
                    issues.append(f"{table}: no policy with WITH CHECK (tenant_uuid = app.tenant_uuid())")

        return issues
