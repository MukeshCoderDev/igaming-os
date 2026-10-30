"""Ledger models — account, journal_entry, journal_line, account_balance,
financial_audit_event, reconciliation_log.

Per ADR-0059 (ledger architecture), ADR-0060 (balance derivation),
ADR-0061 (overdraft), ADR-0062 (reversals), ADR-0063 (financial audit chain).
All tables tenant-scoped (RLS per Phase 5). All financial tables insert-only
(trigger per Phase 7 pattern). Integer minor units only (no floats, rule 78).
"""

from __future__ import annotations

import uuid

from django.db import models


class Account(models.Model):
    """Chart of accounts entry. Per ADR-0059.

    account_class determines overdraft policy (ADR-0061):
    - player: CHECK (balance_minor >= 0) — no overdraft
    - house/settlement/fee/fx_gain/fx_loss/suspense/revenue: overdraft allowed
    """

    ACCOUNT_CLASSES = [
        ("player", "Player"),
        ("house", "House"),
        ("settlement", "Settlement"),
        ("fee", "Fee"),
        ("fx_gain", "FX Gain"),
        ("fx_loss", "FX Loss"),
        ("suspense", "Suspense"),
        ("revenue", "Revenue"),
    ]

    account_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_uuid = models.UUIDField()
    account_class = models.CharField(max_length=16, choices=ACCOUNT_CLASSES)
    currency_code = models.CharField(max_length=3)  # ISO 4217
    status = models.CharField(max_length=16, default="active")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ledger_account"
        app_label = "ledger"


class JournalEntry(models.Model):
    """Journal entry (parent, append-only). Per ADR-0059.

    Insert-only (trigger-enforced per Phase 7 pattern).
    Hash-chained into financial_audit_event (ADR-0063).
    """

    JOURNAL_TYPES = [
        ("POSTING", "Posting"),
        ("REVERSAL", "Reversal"),
        ("RESTATEMENT", "Restatement"),
        ("FX_REVALUATION", "FX Revaluation"),
        ("SETTLEMENT", "Settlement"),
    ]

    entry_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_uuid = models.UUIDField()
    posted_at = models.DateTimeField(auto_now_add=True)
    journal_type = models.CharField(max_length=16, choices=JOURNAL_TYPES)
    source_ref = models.UUIDField(null=True, blank=True)  # FK for reversals
    correlation_id = models.UUIDField()
    idempotency_key = models.UUIDField()
    fx_pair_id = models.UUIDField(null=True, blank=True)  # FK to fx_rate_snapshot
    status = models.CharField(max_length=8, default="POSTED")
    prev_hash = models.CharField(max_length=64, null=True, blank=True)
    hash = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ledger_journal_entry"
        app_label = "ledger"
        unique_together = (("tenant_uuid", "idempotency_key"),)


class JournalLine(models.Model):
    """Journal line (child, append-only). Per ADR-0059.

    Each line is a debit OR credit (not both).
    Integer minor units (no floats, rule 78).
    exponent_at_time records ISO 4217 exponent at posting (ADR-0061b).
    """

    line_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.PROTECT, db_column="entry_uuid", to_field="entry_uuid")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, db_column="account_uuid", to_field="account_uuid")
    tenant_uuid = models.UUIDField()  # Denormalized for RLS
    currency_code = models.CharField(max_length=3)
    exponent_at_time = models.SmallIntegerField()  # ISO 4217 exponent
    debit_minor = models.BigIntegerField(default=0)
    credit_minor = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ledger_journal_line"
        app_label = "ledger"


class AccountBalance(models.Model):
    """Cached balance projection. NOT truth (Law 4). Per ADR-0060.

    Display reads from here (fast). Authorization reads from journal_line
    under row lock (authoritative). Reconciliation verifies projection vs.
    journal truth every 5 minutes; HALT on mismatch.
    """

    account = models.OneToOneField(Account, primary_key=True, on_delete=models.PROTECT, db_column="account_uuid", to_field="account_uuid")
    tenant_uuid = models.UUIDField()
    balance_minor = models.BigIntegerField(default=0)
    as_of_journal_entry = models.ForeignKey(JournalEntry, on_delete=models.PROTECT, db_column="as_of_entry_uuid", to_field="entry_uuid")
    last_reconciled_at = models.DateTimeField(null=True, blank=True)
    last_reconciled_status = models.CharField(max_length=16, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ledger_account_balance"
        app_label = "ledger"


class FinancialAuditEvent(models.Model):
    """Financial audit event (separate WORM chain). Per ADR-0063.

    Separate from Phase 7 operational audit_event.
    Separate chain ID: audit.financial. Separate retention: 7y.
    Separate access: noventra_auditor role.
    """

    event_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_uuid = models.UUIDField(null=True, blank=True)
    actor_id = models.UUIDField()
    actor_type = models.CharField(max_length=16)
    event_type = models.CharField(max_length=64)
    target_type = models.CharField(max_length=64, null=True, blank=True)
    target_id = models.CharField(max_length=128, null=True, blank=True)
    payload = models.JSONField(default=dict)
    prev_hash = models.CharField(max_length=64, null=True, blank=True)
    hash = models.CharField(max_length=64, null=True, blank=True)
    correlation_id = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ledger_financial_audit_event"
        app_label = "ledger"
        managed = False  # Partitioned + trigger-managed


class ReconciliationLog(models.Model):
    """Reconciliation job audit trail. Per ADR-0060."""

    RECONCILIATION_STATUS = [
        ("running", "Running"),
        ("matched", "Matched"),
        ("mismatched", "Mismatched"),
        ("halted", "Halted"),
    ]

    log_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_uuid = models.UUIDField()
    account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.SET_NULL, db_column="account_uuid", to_field="account_uuid")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=RECONCILIATION_STATUS, default="running")
    mismatched_accounts = models.JSONField(null=True, blank=True)
    correlation_id = models.UUIDField()

    class Meta:
        db_table = "ledger_reconciliation_log"
        app_label = "ledger"
