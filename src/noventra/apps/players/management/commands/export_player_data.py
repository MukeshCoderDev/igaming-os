"""export_player_data management command — DSAR (GDPR Art. 15).

Per ADR-0051 / DEC-0056: audited; delivers within window (30 days).
"""

from __future__ import annotations

import json
import uuid

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils import timezone


class Command(BaseCommand):
    help = "Export a player's personal data (GDPR Art. 15 DSAR). " \
           "Audited via player.dsar_completed event."

    def add_arguments(self, parser):
        parser.add_argument("player_uuid", type=str, help="Player UUID to export")
        parser.add_argument("--tenant-uuid", type=str, required=True, help="Tenant UUID")

    def handle(self, *args, **options):
        player_uuid = options["player_uuid"]
        tenant_uuid = options["tenant_uuid"]

        try:
            uuid.UUID(player_uuid)
            uuid.UUID(tenant_uuid)
        except ValueError:
            raise CommandError("Invalid UUID format")

        self.stdout.write(f"Exporting data for player {player_uuid}...")

        export_data = {
            "player_uuid": player_uuid,
            "tenant_uuid": tenant_uuid,
            "exported_at": timezone.now().isoformat(),
            "data": {},
        }

        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL app.tenant_uuid = %s", [tenant_uuid])

            # 1. Player profile.
            cursor.execute(
                "SELECT player_uuid, email, full_name, date_of_birth, phone, address, "
                "state, created_at, last_active_at, closed_at "
                "FROM players_player WHERE player_uuid = %s",
                [player_uuid],
            )
            row = cursor.fetchone()
            if row is None:
                raise CommandError(f"Player {player_uuid} not found")

            export_data["data"]["player_profile"] = {
                "player_uuid": str(row[0]),
                "email": row[1],
                "full_name": row[2],
                "date_of_birth": row[3],
                "phone": row[4],
                "address": row[5],
                "state": row[6],
                "created_at": row[7].isoformat() if row[7] else None,
                "last_active_at": row[8].isoformat() if row[8] else None,
                "closed_at": row[9].isoformat() if row[9] else None,
            }

            # 2. Consents.
            cursor.execute(
                "SELECT consent_uuid, purpose, channel, status, granted_at, revoked_at, "
                "policy_version, created_at FROM players_consent WHERE player_uuid = %s",
                [player_uuid],
            )
            consents = []
            for c_row in cursor.fetchall():
                consents.append({
                    "consent_uuid": str(c_row[0]),
                    "purpose": c_row[1],
                    "channel": c_row[2],
                    "status": c_row[3],
                    "granted_at": c_row[4].isoformat() if c_row[4] else None,
                    "revoked_at": c_row[5].isoformat() if c_row[5] else None,
                    "policy_version": c_row[6],
                    "created_at": c_row[7].isoformat() if c_row[7] else None,
                })
            export_data["data"]["consents"] = consents

            # 3. Audit events involving this player.
            cursor.execute(
                "SELECT event_type, created_at, payload FROM audit_event "
                "WHERE actor_id = %s ORDER BY created_at",
                [player_uuid],
            )
            audit_events = []
            for a_row in cursor.fetchall():
                audit_events.append({
                    "event_type": a_row[0],
                    "created_at": a_row[1].isoformat() if a_row[1] else None,
                    "payload": a_row[2] if isinstance(a_row[2], dict) else json.loads(a_row[2] or "{}"),
                })
            export_data["data"]["audit_events"] = audit_events

            # 4. Emit audit event (player.dsar_completed).
            cursor.execute(
                """
                INSERT INTO audit_event (event_uuid, tenant_id, actor_id, actor_type, event_type, payload)
                VALUES (%s, %s, %s, 'service', 'player.dsar_completed', %s)
                """,
                [
                    str(uuid.uuid4()), tenant_uuid,
                    "00000000-0000-0000-0000-000000000000",
                    json.dumps({"player_uuid": player_uuid, "consent_count": len(consents), "audit_count": len(audit_events)}),
                ],
            )

        # Output as JSON (Phase 9 stub; Phase 10 delivers via secure file transfer).
        self.stdout.write(json.dumps(export_data, indent=2, default=str))
        self.stdout.write(self.style.SUCCESS(
            f"DSAR export complete: {len(consents)} consent(s), {len(audit_events)} audit event(s)."
        ))
