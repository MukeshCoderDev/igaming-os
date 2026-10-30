"""Payment models — PaymentOrder, DisputeCase, EvidencePack, WebhookLog.

Per ADR-0073 (Payment Order FSM), ADR-0076 (Disputes), ADR-0077 (Ledger contract).
PCI SAQ-A: NO card fields anywhere. PSP tokens only.
All tables tenant-scoped (RLS per Phase 5). Integer minor units (no floats).
"""

from __future__ import annotations

import uuid

from django.db import models


class PaymentOrder(models.Model):
    """Payment order with deposit/withdrawal FSM. Per ADR-0073.

    Deposit FSM: PENDING → AUTHORIZED → CAPTURED → SETTLED (or FAILED; or REFUNDED).
    Withdrawal FSM: PENDING → KYC_CHECK → AUTHORIZED → PAYOUT_INITIATED → SETTLED
                     (or KYC_FAILED, FAILED, REJECTED).

    CAPTURED triggers Phase 11 ledger posting (ADR-0077).
    REFUNDED triggers reversal entry (terminal, ADR-0063).
    """

    DIRECTIONS = [("deposit", "Deposit"), ("withdrawal", "Withdrawal")]
    STATUSES = [
        ("PENDING", "Pending"),
        ("KYC_CHECK", "KYC Check"),
        ("AUTHORIZED", "Authorized"),
        ("CAPTURED", "Captured"),
        ("PAYOUT_INITIATED", "Payout Initiated"),
        ("SETTLED", "Settled"),
        ("FAILED", "Failed"),
        ("REFUNDED", "Refunded"),
        ("KYC_FAILED", "KYC Failed"),
        ("REJECTED", "Rejected"),
    ]

    order_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_uuid = models.UUIDField()
    player_uuid = models.UUIDField()
    amount_minor = models.BigIntegerField()  # Integer minor units (no floats)
    currency_code = models.CharField(max_length=3)  # ISO 4217
    exponent_at_time = models.SmallIntegerField()
    direction = models.CharField(max_length=12, choices=DIRECTIONS)
    payment_method = models.CharField(max_length=32, null=True, blank=True)
    psp_token = models.CharField(max_length=255, null=True, blank=True)  # PSP token ONLY — no card data
    psp_charge_id = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUSES, default="PENDING")
    idempotency_key = models.UUIDField()
    correlation_id = models.UUIDField()
    fx_pair_id = models.UUIDField(null=True, blank=True)  # FK to fx_rate_snapshot
    failure_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments_order"
        app_label = "payments"
        unique_together = (("tenant_uuid", "idempotency_key"),)


class DisputeCase(models.Model):
    """Chargeback dispute with FSM + deadline enforcement. Per ADR-0076.

    FSM: open → evidence_submitted → won/lost/expired/arbitration.
    Missed deadline → automatic loss (regulator-mandated).
    Evidence pack auto-generated on dispute.opened.
    """

    DISPUTE_REASONS = [
        ("fraud", "Fraud"),
        ("product_not_received", "Product Not Received"),
        ("credit_not_processed", "Credit Not Processed"),
        ("duplicate", "Duplicate"),
        ("canceled_subscription", "Canceled Subscription"),
        ("unrecognized", "Unrecognized"),
    ]
    DISPUTE_STATUSES = [
        ("open", "Open"),
        ("evidence_submitted", "Evidence Submitted"),
        ("won", "Won"),
        ("lost", "Lost"),
        ("expired", "Expired"),
        ("arbitration", "Arbitration"),
    ]

    dispute_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_uuid = models.UUIDField()
    order = models.ForeignKey(PaymentOrder, on_delete=models.PROTECT, db_column="order_uuid", to_field="order_uuid")
    psp_dispute_id = models.CharField(max_length=255)
    reason = models.CharField(max_length=32, choices=DISPUTE_REASONS)
    status = models.CharField(max_length=20, choices=DISPUTE_STATUSES, default="open")
    amount_minor = models.BigIntegerField()
    currency_code = models.CharField(max_length=3)
    evidence_pack_uuid = models.UUIDField(null=True, blank=True)
    deadline_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments_dispute"
        app_label = "payments"


class WebhookLog(models.Model):
    """Webhook delivery log. Per ADR-0075.

    Records every webhook received for audit + idempotency.
    """

    webhook_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_uuid = models.UUIDField()
    psp_name = models.CharField(max_length=32)  # stripe, adyen, square
    psp_event_id = models.CharField(max_length=255)  # For idempotency
    event_type = models.CharField(max_length=64)
    payload = models.JSONField(default=dict)
    signature_valid = models.BooleanField(default=False)
    processed = models.BooleanField(default=False)
    response_status = models.IntegerField(default=200)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "payments_webhook_log"
        app_label = "payments"
        unique_together = (("tenant_uuid", "psp_name", "psp_event_id"),)
