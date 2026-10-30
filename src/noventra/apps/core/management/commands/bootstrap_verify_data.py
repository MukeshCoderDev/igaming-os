"""Bootstrap verification data: tenants, users, players, accounts, etc.

Per the Stage B Verification Suite spec §1.4.
Run: python manage.py bootstrap_verify_data
"""

import uuid

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Bootstrap verification data for Stage B testing"

    def handle(self, *args, **options):
        tenant_uuid = "00000000-0000-0000-0000-000000000001"
        admin_uuid = "00000000-0000-0000-0000-000000000a01"
        player_email = "player@verify.test"

        with connection.cursor() as cursor:
            # Ensure tenant exists (from Phase 5 baseline).
            cursor.execute(
                """
                INSERT INTO tenancy_tenant (tenant_uuid, legal_name, contract_id, status)
                VALUES (%s, 'Verify Tenant', 'VERIFY-001', 'active')
                ON CONFLICT (tenant_uuid) DO NOTHING
                """,
                [tenant_uuid],
            )

            # Ensure admin user exists (from Phase 6 baseline).
            cursor.execute(
                """
                INSERT INTO identity_user (user_uuid, email, password_hash, status, mfa_enabled, default_tenant_uuid)
                VALUES (%s, %s, 'argon2id$verify_placeholder', 'active', false, %s)
                ON CONFLICT (email) DO NOTHING
                """,
                [admin_uuid, "admin@verify.test", tenant_uuid],
            )

            # Ensure admin membership exists.
            cursor.execute(
                """
                INSERT INTO identity_tenant_membership (membership_uuid, user_uuid, tenant_uuid, role_uuid, status, joined_at)
                VALUES ('00000000-0000-0000-0000-000000000v01', %s, %s, '00000000-0000-0000-0000-000000000101', 'active', NOW())
                ON CONFLICT DO NOTHING
                """,
                [admin_uuid, tenant_uuid],
            )

            # Create player wallet account (Phase 11 ledger).
            cursor.execute(
                """
                INSERT INTO ledger_account (account_uuid, tenant_uuid, account_class, currency_code, status)
                VALUES ('00000000-0000-0000-0000-00000000w001', %s, 'player', 'USD', 'active')
                ON CONFLICT DO NOTHING
                """,
                [tenant_uuid],
            )

            # Create house account.
            cursor.execute(
                """
                INSERT INTO ledger_account (account_uuid, tenant_uuid, account_class, currency_code, status)
                VALUES ('00000000-0000-0000-0000-00000000h001', %s, 'house', 'USD', 'active')
                ON CONFLICT DO NOTHING
                """,
                [tenant_uuid],
            )

            # Create account balance for player wallet.
            cursor.execute(
                """
                INSERT INTO ledger_account_balance (account_uuid, tenant_uuid, balance_minor, as_of_entry_uuid)
                VALUES ('00000000-0000-0000-0000-00000000w001', %s, 10000000, '00000000-0000-0000-0000-000000000001')
                ON CONFLICT (account_uuid) DO NOTHING
                """,
                [tenant_uuid],
            )

            # Seed a sample FX rate snapshot (Phase 11 FX).
            cursor.execute(
                """
                INSERT INTO fx_rate_snapshot (snapshot_uuid, tenant_uuid, source, base_currency, quote_currency, rate_minor, rate_exponent, captured_at)
                VALUES ('00000000-0000-0000-0000-00000000fx001', NULL, 'STUB', 'EUR', 'USD', 110000, 5, NOW())
                ON CONFLICT DO NOTHING
                """,
            )

            # Seed reconciliation log defaults (Phase 14).
            cursor.execute(
                """
                INSERT INTO ledger_reconciliation_log (log_uuid, tenant_uuid, status, correlation_id)
                VALUES ('00000000-0000-0000-0000-00000000rc001', %s, 'matched', '00000000-0000-0000-0000-000000000001')
                ON CONFLICT DO NOTHING
                """,
                [tenant_uuid],
            )

        self.stdout.write(self.style.SUCCESS(
            "Verification data bootstrapped:\n"
            "  - Tenant: Verify Tenant\n"
            "  - Admin user: admin@verify.test\n"
            "  - Player wallet account: $100,000.00 (10000000 minor)\n"
            "  - House account: 0\n"
            "  - FX snapshot: EUR/USD = 1.10000 (stub)\n"
            "  - Reconciliation log: matched\n"
        ))
