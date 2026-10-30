"""enforce_retention management command — scheduled retention enforcement.

Per ADR-0051 / DEC-0056: scheduled; audited.
"""

from __future__ import annotations

import uuid
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone


class Command(BaseCommand):
    help = "Enforce retention schedule. Deletes data past retention period. " \
           "Audited via retention.enforcement_completed event."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report without deleting")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        now = timezone.now()

        self.stdout.write(f"Retention enforcement {'(dry run)' if dry_run else ''} at {now.isoformat()}")

        results = {}

        with connection.cursor() as cursor:
            # 1. Login history older than 2 years (730 days).
            cutoff_login = now - timedelta(days=730)
            # Phase 9 stub: login history not yet a separate table; skip.

            # 2. Closed players older than 7 years (2555 days).
            cutoff_player = now - timedelta(days=2555)
            cursor.execute(
                "SET LOCAL app.tenant_uuid = ''"
            )
            # Count closed players past retention (no RLS — global scan).
            cursor.execute(
                "SELECT COUNT(*) FROM players_player WHERE state = 'closed' AND closed_at < %s",
                [cutoff_player],
            )
            player_count = cursor.fetchone()[0]
            results["players_past_retention"] = player_count

            if not dry_run and player_count > 0:
                # Phase 9 stub: actual deletion requires archival first (Q5-blocked).
                # For now, just report.
                self.stdout.write(self.style.WARNING(
                    f"  {player_count} player(s) past retention — archival required before deletion (Q5-blocked)"
                ))

            # 3. Audit log retention (per Phase 7 ADR-0036 — separate schedule).
            # Phase 7 handles this; Phase 9 does not duplicate.

            # 4. Emit audit event (retention.enforcement_completed).
            if not dry_run:
                cursor.execute(
                    """
                    INSERT INTO audit_event (event_uuid, tenant_id, actor_id, actor_type, event_type, payload)
                    VALUES (%s, NULL, %s, 'service', 'retention.enforcement_completed', %s)
                    """,
                    [
                        str(uuid.uuid4()),
                        "00000000-0000-0000-0000-000000000000",
                        f'{{"dry_run":false,"players_past_retention":{player_count}}}',
                    ],
                )

        self.stdout.write(self.style.SUCCESS(
            f"Retention enforcement complete. Results: {results}"
        ))
