"""Player + Consent ORM models.

Per ADR-0047 (Player), ADR-0048 (Consent). Both tenant-scoped (RLS).
"""

from __future__ import annotations

import uuid

from django.db import models


class Player(models.Model):
    """Player entity. Tenant-scoped (RLS). Per ADR-0047."""

    player_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_uuid = models.UUIDField()
    email = models.EmailField(db_index=True)
    full_name = models.CharField(max_length=255)
    date_of_birth = models.CharField(max_length=32, null=True, blank=True)
    phone = models.CharField(max_length=64, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    user_uuid = models.UUIDField(null=True, blank=True)  # Link to Phase 6 User
    state = models.CharField(max_length=32, default="prospect")
    created_at = models.DateTimeField(auto_now_add=True)
    last_active_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "players_player"
        app_label = "players"


class Consent(models.Model):
    """Consent record. Tenant-scoped (RLS). Per ADR-0048/0049.

    Insert-only (hash-chained per ADR-0049). Revocation creates a NEW
    record (status=revoked), not a mutation.
    """

    consent_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player_uuid = models.UUIDField()
    tenant_uuid = models.UUIDField()
    purpose = models.CharField(max_length=64)  # ConsentPurpose
    channel = models.CharField(max_length=32)  # NotificationChannel
    status = models.CharField(max_length=16, default="pending")
    granted_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    policy_version = models.IntegerField(default=1)
    consent_text_hash = models.CharField(max_length=64, null=True, blank=True)
    ip_address = models.CharField(max_length=64, null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    correlation_id = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Hash-chain fields (per ADR-0049).
    prev_hash = models.CharField(max_length=64, null=True, blank=True)
    hash = models.CharField(max_length=64, null=True, blank=True)

    class Meta:
        db_table = "players_consent"
        app_label = "players"
