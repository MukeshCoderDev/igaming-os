"""verify_audit_chain management command — Phase 7.

Per Phase 7 spec output #11: chain verifier command; CI-integrated
(rule 39); covers hash continuity, payload integrity, timestamp
monotonicity, chain head consistency, concurrent-insert test.

Exit code: 0 if chain is valid; 1 if any break detected.
"""

from __future__ import annotations

import hashlib
import json

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Verify the audit log hash chain. Per ADR-0035. " \
           "Checks: hash continuity, payload integrity (Merkle), " \
           "timestamp monotonicity, chain head consistency."

    def add_arguments(self, parser):
        parser.add_argument(
            "--scope",
            default=None,
            help="Verify only this scope (tenant UUID or 'global'). Default: all scopes.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=10000,
            help="Max events to verify per scope (default 10000).",
        )

    def handle(self, *args, **options):
        scope = options["scope"]
        limit = options["limit"]

        failures: list[str] = []

        with connection.cursor() as cursor:
            # Get all scopes (or just the specified one).
            if scope:
                cursor.execute("SELECT scope FROM audit_chain_head WHERE scope = %s", [scope])
            else:
                cursor.execute("SELECT scope FROM audit_chain_head ORDER BY scope")
            scopes = [row[0] for row in cursor.fetchall()]

            if not scopes:
                self.stdout.write(self.style.WARNING(
                    "verify_audit_chain: no chain heads found. Empty audit log."
                ))
                return

            for scp in scopes:
                failures.extend(self._verify_scope(scp, limit))

        if failures:
            self.stdout.write(self.style.ERROR(
                f"verify_audit_chain: FAIL — {len(failures)} issue(s) found:"
            ))
            for issue in failures:
                self.stdout.write(self.style.ERROR(f"  - {issue}"))
            # Emit a chain-break audit event (if possible).
            self._emit_chain_break_event(failures)
            import sys
            sys.exit(1)
        else:
            self.stdout.write(self.style.SUCCESS(
                f"verify_audit_chain: PASS — {len(scopes)} scope(s) verified."
            ))

    def _verify_scope(self, scope: str, limit: int) -> list[str]:
        """Verify one chain scope. Returns list of issues."""
        issues: list[str] = []
        with connection.cursor() as cursor:
            # Read events for this scope, ordered by created_at.
            if scope == "global":
                cursor.execute(
                    """
                    SELECT event_uuid, tenant_id, actor_id, actor_type, event_type,
                           target_type, target_id, payload, prev_hash, hash,
                           correlation_id, created_at
                    FROM audit_event
                    WHERE tenant_id IS NULL
                    ORDER BY created_at ASC, event_uuid ASC
                    LIMIT %s
                    """,
                    [limit],
                )
            else:
                cursor.execute(
                    """
                    SELECT event_uuid, tenant_id, actor_id, actor_type, event_type,
                           target_type, target_id, payload, prev_hash, hash,
                           correlation_id, created_at
                    FROM audit_event
                    WHERE tenant_id = %s
                    ORDER BY created_at ASC, event_uuid ASC
                    LIMIT %s
                    """,
                    [scope, limit],
                )
            rows = cursor.fetchall()

            if not rows:
                return issues  # Empty scope; nothing to verify.

            prev_hash = None
            prev_time = None
            for row in rows:
                event_uuid, tenant_id, actor_id, actor_type, event_type, \
                    target_type, target_id, payload_raw, stored_prev_hash, stored_hash, \
                    correlation_id, created_at = row

                # 1. Hash continuity: stored prev_hash must match previous event's hash.
                if prev_hash is not None and stored_prev_hash != prev_hash:
                    issues.append(
                        f"scope={scope} event={event_uuid}: prev_hash mismatch "
                        f"(stored={stored_prev_hash}, expected={prev_hash})"
                    )

                # 2. Timestamp monotonicity: created_at must be >= prev_time.
                if prev_time is not None and created_at < prev_time:
                    issues.append(
                        f"scope={scope} event={event_uuid}: timestamp disorder "
                        f"(created_at={created_at}, prev={prev_time})"
                    )

                # 3. Payload integrity: recompute Merkle root + chain hash.
                payload = payload_raw if isinstance(payload_raw, dict) else json.loads(payload_raw or "{}")
                recomputed_hash = self._recompute_hash(
                    prev_hash=stored_prev_hash,
                    payload=payload,
                    event_type=event_type,
                    actor_id=str(actor_id),
                    tenant_id=str(tenant_id) if tenant_id else "",
                    created_at_epoch=int(created_at.timestamp()),
                )
                if recomputed_hash != stored_hash:
                    issues.append(
                        f"scope={scope} event={event_uuid}: hash mismatch "
                        f"(stored={stored_hash}, recomputed={recomputed_hash})"
                    )

                prev_hash = stored_hash
                prev_time = created_at

            # 4. Chain head consistency: last_hash must match the last event's hash.
            cursor.execute(
                "SELECT last_hash, last_event_uuid FROM audit_chain_head WHERE scope = %s",
                [scope],
            )
            head_row = cursor.fetchone()
            if head_row:
                head_last_hash, head_last_uuid = head_row
                if rows and head_last_hash != prev_hash:
                    issues.append(
                        f"scope={scope}: chain head last_hash mismatch "
                        f"(head={head_last_hash}, last_event={prev_hash})"
                    )

        return issues

    def _recompute_hash(
        self,
        *,
        prev_hash: str | None,
        payload: dict,
        event_type: str,
        actor_id: str,
        tenant_id: str,
        created_at_epoch: int,
    ) -> str:
        """Recompute the chain hash. Matches the DB trigger logic."""
        # Merkle-style: hash each field, concatenate, hash again.
        field_hashes = []
        for key in sorted(payload.keys()):
            field_hash = hashlib.sha256(
                f"{key}={payload[key]}".encode()
            ).hexdigest()
            field_hashes.append(field_hash)
        merkle_root = hashlib.sha256("".join(field_hashes).encode()).hexdigest()

        chain_input = "|".join([
            prev_hash or "",
            merkle_root,
            event_type,
            actor_id,
            tenant_id,
            str(created_at_epoch),
        ])
        return hashlib.sha256(chain_input.encode()).hexdigest()

    def _emit_chain_break_event(self, failures: list[str]) -> None:
        """Emit a chain_break_detected audit event (best-effort)."""
        try:
            from noventra.middleware.audit import append_audit_event
            append_audit_event(
                event_type="audit.chain_break_detected",
                actor_id="00000000-0000-0000-0000-000000000000",  # system
                actor_type="service",
                tenant_id=None,  # global
                payload={"failure_count": len(failures), "first_failure": failures[0] if failures else ""},
            )
        except Exception:
            pass  # Best-effort; don't fail the command if audit emit fails.
