"""Audit ORM adapter — Django models.

Per ADR-0036 (schema), ADR-0035 (hash-chain), ADR-0038 (insert-only).
Note: the actual hash-chain + insert-only enforcement is in DB triggers
(see migrations/0001_initial.py). The Django models are read/insert
interfaces only.
"""

from __future__ import annotations

import uuid

from django.db import models


class AuditEvent(models.Model):
    """A single audit event. Insert-only (trigger-enforced per ADR-0038).

    Per ADR-0036: partitioned by month + tenant. Phase 7 creates the
    baseline partition; monthly automation is Phase 8.
    """

    event_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True)  # NULL for global events
    actor_id = models.UUIDField()
    actor_type = models.CharField(max_length=16)  # human | service
    event_type = models.CharField(max_length=64)
    target_type = models.CharField(max_length=64, null=True, blank=True)
    target_id = models.CharField(max_length=128, null=True, blank=True)
    payload = models.JSONField(default=dict)
    prev_hash = models.CharField(max_length=64, null=True, blank=True)
    hash = models.CharField(max_length=64, null=True, blank=True)
    correlation_id = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_event"
        app_label = "audit"
        managed = False  # Partitioned table; managed via raw SQL in migration.

    def __str__(self) -> str:
        return f"AuditEvent({self.event_type}, {self.event_uuid})"


class AuditChainHead(models.Model):
    """The head of a hash chain (singleton per scope).

    Per ADR-0035: scope = 'global' or str(tenant_uuid).
    """

    scope = models.CharField(primary_key=True, max_length=64)
    last_event_uuid = models.UUIDField(null=True, blank=True)
    last_hash = models.CharField(max_length=64, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "audit_chain_head"
        app_label = "audit"

    def __str__(self) -> str:
        return f"AuditChainHead({self.scope})"
