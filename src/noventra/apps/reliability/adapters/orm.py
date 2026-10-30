"""Reliability ORM adapter — Django models.

Per ADR-0040 (outbox), ADR-0041 (inbox), ADR-0043 (idempotency).
All tenant-scoped tables have RLS per DEC-0003.
"""

from __future__ import annotations

import uuid

from django.db import models


class OutboxEvent(models.Model):
    """Outbox event (tenant-scoped). Per ADR-0040."""

    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField()
    event_type = models.CharField(max_length=64)
    event_version = models.IntegerField(default=1)
    aggregate_id = models.CharField(max_length=128)
    aggregate_type = models.CharField(max_length=64)
    actor_id = models.UUIDField()
    correlation_id = models.CharField(max_length=64, null=True, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=16, default="pending")
    relayed_at = models.DateTimeField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)

    class Meta:
        db_table = "reliability_outbox"
        app_label = "reliability"


class InboxEntry(models.Model):
    """Inbox dedup entry (tenant-scoped). Per ADR-0041."""

    message_id = models.UUIDField()
    consumer_id = models.CharField(max_length=64)
    processed_at = models.DateTimeField(auto_now_add=True)
    payload_hash = models.CharField(max_length=64, null=True, blank=True)
    tenant_id = models.UUIDField()

    class Meta:
        db_table = "reliability_inbox"
        app_label = "reliability"
        unique_together = (("message_id", "consumer_id"),)


class IdempotencyKey(models.Model):
    """Idempotency key record (tenant-scoped). Per ADR-0043."""

    key = models.CharField(max_length=64)  # UUIDv4
    tenant_id = models.UUIDField()
    endpoint = models.CharField(max_length=128)
    request_hash = models.CharField(max_length=64)
    response_status = models.IntegerField()
    response_body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "reliability_idempotency_key"
        app_label = "reliability"
        unique_together = (("key", "tenant_id", "endpoint"),)
