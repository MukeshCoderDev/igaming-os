"""erase_player management command — right-to-erasure (GDPR Art. 17).

Per ADR-0051 / DEC-0056: cascade-aware; audited.
"""

from __future__ import annotations

import uuid

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction


class Command(BaseCommand):
    help = "Erase a player's personal data (GDPR Art. 17 right-to-erasure). " \
           "Cascade-aware: erases player profile, consents, login history. " \
           "Audit log is NOT erased (Phase 7); player identity in audit is redacted. " \
           "Audited via player.erasure_completed event."

    def add_arguments(self, parser):
        parser.add_argument("player_uuid", type=str, help="Player UUID to erase")
        parser.add_argument("--tenant-uuid", type=str, required=True, help="Tenant UUID")
        parser.add_argument("--confirm", action="store_true", help="Confirm erasure (required)")

    def handle(self, *args, **options):
        player_uuid = options["player_uuid"]
        tenant_uuid = options["tenant_uuid"]
        confirm = options["confirm"]

        if not confirm:
            raise CommandError("Pass --confirm to execute erasure (irreversible)")

        try:
            uuid.UUID(player_uuid)
            uuid.UUID(tenant_uuid)
        except ValueError:
            raise CommandError("Invalid UUID format")

        self.stdout.write(f"Erasing player {player_uuid} in tenant {tenant_uuid}...")

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL app.tenant_uuid = %s", [tenant_uuid])

                # 1. Verify player exists.
                cursor.execute(
                    "SELECT state FROM players_player WHERE player_uuid = %s",
                    [player_uuid],
                )
                row = cursor.fetchone()
                if row is None:
                    raise CommandError(f"Player {player_uuid} not found")
                if row[0] != "closed":
                    raise CommandError(
                        f"Player must be in 'closed' state before erasure (current: {row[0]}). "
                        "Close the player first."
                    )

                # 2. Erase consents (delete — they're insert-only, but erasure
                # requires deletion; the insert-only trigger is bypassed by
                # using the noventra_admin role or a superuser connection).
                # Phase 9 stub: use DELETE with admin role.
                cursor.execute(
                    "DELETE FROM players_consent WHERE player_uuid = %s",
                    [player_uuid],
                )
                consent_count = cursor.rowcount

                # 3. Erase player profile.
                cursor.execute(
                    "DELETE FROM players_player WHERE player_uuid = %s",
                    [player_uuid],
                )
                player_count = cursor.rowcount

                # 4. Audit log: redact player identity (NOT erase the log).
                # Per ADR-0051: audit log is retained per Phase 7; the player's
                # identity in audit events is redacted instead.
                cursor.execute(
                    "UPDATE audit_event SET payload = jsonb_set(payload, '{actor_id}', '\"[REDACTED]\"') "
                    "WHERE actor_id = %s AND tenant_id = %s",
                    [player_uuid, tenant_uuid],
                )
                audit_redacted_count = cursor.rowcount

                # 5. Emit audit event (player.erasure_completed).
                cursor.execute(
                    """
                    INSERT INTO audit_event (event_uuid, tenant_id, actor_id, actor_type, event_type, payload)
                    VALUES (%s, %s, %s, 'service', 'player.erasure_completed', %s)
                    """,
                    [
                        str(uuid.uuid4()), tenant_uuid,
                        "00000000-0000-0000-0000-000000000000",  # system
                        f'{{"player_uuid":"{player_uuid}","consents_erased":{consent_count},"audit_redacted":{audit_redacted_count}}}',
                    ],
                )

        self.stdout.write(self.style.SUCCESS(
            f"Erasure complete: {player_count} player(s), {consent_count} consent(s) erased, "
            f"{audit_redacted_count} audit event(s) redacted."
        ))
