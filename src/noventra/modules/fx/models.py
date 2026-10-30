"""FX module — FX rate snapshots.

Per ADR-0062b / DEC-0070. Immutable, insert-only.
"""

from __future__ import annotations

import uuid

from django.db import models


class FxRateSnapshot(models.Model):
    """Immutable FX rate snapshot. Per ADR-0062b.

    Insert-only (trigger-enforced). Locked at posting time.
    Rate stored as integer minor units (e.g., 110000 = 1.10000 USD per EUR
    at exponent 5).
    """

    SNAPSHOT_SOURCES = [
        ("ECB", "European Central Bank"),
        ("REFINITIV", "Refinitiv"),
        ("INTERNAL_TREASURY", "Internal Treasury"),
        ("STUB", "Stub (dev)"),
    ]

    snapshot_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_uuid = models.UUIDField(null=True, blank=True)  # NULL = global
    source = models.CharField(max_length=20, choices=SNAPSHOT_SOURCES)
    base_currency = models.CharField(max_length=3)  # ISO 4217
    quote_currency = models.CharField(max_length=3)  # ISO 4217
    rate_minor = models.BigIntegerField()  # e.g., 110000 = 1.10000
    rate_exponent = models.SmallIntegerField()  # e.g., 5 = 5 decimal places
    bid_minor = models.BigIntegerField(null=True, blank=True)
    ask_minor = models.BigIntegerField(null=True, blank=True)
    captured_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "fx_rate_snapshot"
        app_label = "fx"
