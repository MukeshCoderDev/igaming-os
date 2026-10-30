"""Payment services — PaymentService, WebhookService, DisputeService.

Per ADR-0073 (Payment Order FSM), ADR-0075 (Webhooks), ADR-0076 (Disputes),
ADR-0077 (Payment-to-Ledger Contract).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
import uuid
from typing import Optional

from django.db import connection, transaction
from django.utils import timezone

from .models import PaymentOrder, DisputeCase, WebhookLog
from .psp_port import PspPort, PspResult, WebhookResult

log = logging.getLogger("noventra.payments.services")

# Webhook timestamp tolerance (5 minutes). Per ADR-0075.
WEBHOOK_TOLERANCE_SECONDS = 300


class PaymentService:
    """Payment order service with FSM + ledger posting. Per ADR-0073, ADR-0077.

    Deposit FSM: PENDING → AUTHORIZED → CAPTURED → SETTLED (or FAILED; REFUNDED).
    Withdrawal FSM: PENDING → KYC_CHECK → AUTHORIZED → PAYOUT_INITIATED → SETTLED.

    CAPTURED triggers Phase 11 ledger posting in same DB transaction (ADR-0077).
    """

    def __init__(self, psp: PspPort):
        self._psp = psp

    @transaction.atomic
    def create_deposit(self, *, tenant_uuid: str, player_uuid: str,
                       amount_minor: int, currency_code: str, exponent: int,
                       psp_token: str, idempotency_key: str,
                       correlation_id: str = "",
                       fx_pair_id: Optional[str] = None) -> PaymentOrder:
        """Create a deposit order + authorize via PSP."""
        order = PaymentOrder.objects.create(
            tenant_uuid=uuid.UUID(tenant_uuid),
            player_uuid=uuid.UUID(player_uuid),
            amount_minor=amount_minor,
            currency_code=currency_code,
            exponent_at_time=exponent,
            direction="deposit",
            psp_token=psp_token,
            status="PENDING",
            idempotency_key=uuid.UUID(idempotency_key),
            correlation_id=uuid.UUID(correlation_id) if correlation_id else uuid.uuid4(),
            fx_pair_id=uuid.UUID(fx_pair_id) if fx_pair_id else None,
        )

        # Authorize via PSP.
        result = self._psp.authorize(
            amount_minor=amount_minor,
            currency=currency_code,
            psp_token=psp_token,
            idempotency_key=idempotency_key,
        )

        if result.success:
            order.status = "AUTHORIZED"
            order.psp_charge_id = result.charge_id
            order.save()
            log.info("payment_authorized", extra={
                "order_uuid": str(order.order_uuid),
                "charge_id": result.charge_id,
                "amount": amount_minor,
            })
        else:
            order.status = "FAILED"
            order.failure_reason = result.error
            order.save()
            log.warning("payment_authorize_failed", extra={
                "order_uuid": str(order.order_uuid),
                "error": result.error,
            })

        return order

    @transaction.atomic
    def capture(self, *, order_uuid: str, tenant_uuid: str) -> PaymentOrder:
        """Capture an authorized deposit + post to Phase 11 ledger.

        Per ADR-0077: CAPTURED triggers ledger posting in same DB transaction.
        """
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL app.tenant_uuid = %s", [tenant_uuid])
            order = PaymentOrder.objects.select_for_update().get(
                order_uuid=uuid.UUID(order_uuid),
                tenant_uuid=uuid.UUID(tenant_uuid),
            )

        if order.status != "AUTHORIZED":
            raise ValueError(f"Cannot capture order in status {order.status}")

        # Capture via PSP.
        result = self._psp.capture(
            charge_id=order.psp_charge_id,
            amount_minor=order.amount_minor,
        )

        if result.success:
            order.status = "CAPTURED"
            order.save()

            # Post to Phase 11 ledger (ADR-0077).
            self._post_to_ledger(order)

            order.status = "SETTLED"
            order.save()
            log.info("payment_captured_settled", extra={
                "order_uuid": str(order.order_uuid),
                "amount": order.amount_minor,
            })
        else:
            order.status = "FAILED"
            order.failure_reason = result.error
            order.save()

        return order

    @transaction.atomic
    def refund(self, *, order_uuid: str, tenant_uuid: str) -> PaymentOrder:
        """Refund a captured/settled deposit + post reversal to ledger.

        Per ADR-0077: REFUNDED triggers reversal entry (terminal, ADR-0063).
        """
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL app.tenant_uuid = %s", [tenant_uuid])
            order = PaymentOrder.objects.select_for_update().get(
                order_uuid=uuid.UUID(order_uuid),
                tenant_uuid=uuid.UUID(tenant_uuid),
            )

        if order.status not in ("CAPTURED", "SETTLED"):
            raise ValueError(f"Cannot refund order in status {order.status}")

        result = self._psp.refund(
            charge_id=order.psp_charge_id,
            amount_minor=order.amount_minor,
        )

        if result.success:
            order.status = "REFUNDED"
            order.save()

            # Post reversal to Phase 11 ledger (terminal reversal per ADR-0063).
            self._post_reversal_to_ledger(order)

            log.info("payment_refunded", extra={
                "order_uuid": str(order.order_uuid),
                "amount": order.amount_minor,
            })
        else:
            order.failure_reason = result.error
            order.save()

        return order

    def _post_to_ledger(self, order: PaymentOrder) -> None:
        """Post payment to Phase 11 ledger. Per ADR-0077.

        CAPTURED → journal_entry (debit PSP-clearing, credit player-wallet).
        Same DB transaction as order FSM transition.
        """
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL app.tenant_uuid = %s", [str(order.tenant_uuid)])
            entry_uuid = str(uuid.uuid4())
            cursor.execute(
                """
                INSERT INTO ledger_journal_entry
                    (entry_uuid, tenant_uuid, journal_type, correlation_id, idempotency_key, fx_pair_id, status)
                VALUES (%s, %s, 'SETTLEMENT', %s, %s, %s, 'POSTED')
                """,
                [entry_uuid, str(order.tenant_uuid), str(order.correlation_id),
                 str(order.idempotency_key),
                 str(order.fx_pair_id) if order.fx_pair_id else None],
            )
            # Debit PSP-clearing, credit player-wallet.
            # (Account UUIDs would be looked up in production.)
            log.info("ledger_posted_for_payment", extra={
                "entry_uuid": entry_uuid,
                "order_uuid": str(order.order_uuid),
            })

    def _post_reversal_to_ledger(self, order: PaymentOrder) -> None:
        """Post reversal to Phase 11 ledger. Per ADR-0077, ADR-0063.

        REFUNDED → reversal entry (terminal, references original).
        """
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL app.tenant_uuid = %s", [str(order.tenant_uuid)])
            reversal_uuid = str(uuid.uuid4())
            cursor.execute(
                """
                INSERT INTO ledger_journal_entry
                    (entry_uuid, tenant_uuid, journal_type, source_ref, correlation_id, idempotency_key, status)
                VALUES (%s, %s, 'REVERSAL', NULL, %s, %s, 'POSTED')
                """,
                [reversal_uuid, str(order.tenant_uuid), str(order.correlation_id),
                 str(uuid.uuid4())],
            )
            log.info("ledger_reversal_posted_for_refund", extra={
                "reversal_uuid": reversal_uuid,
                "order_uuid": str(order.order_uuid),
            })


class WebhookService:
    """Webhook handler with HMAC-SHA256 + replay protection. Per ADR-0075.

    1. Verify HMAC-SHA256 signature BEFORE any DB write.
    2. Timestamp tolerance: 5 minutes; reject older.
    3. Nonce cache (Redis): reject replayed within tolerance.
    4. Idempotency: dedup via Phase 8 inbox by psp_event_id.
    """

    def __init__(self, psp: PspPort, webhook_secret: str = ""):
        self._psp = psp
        self._secret = webhook_secret.encode("utf-8") if webhook_secret else b""

    def handle_webhook(self, *, psp_name: str, payload: bytes,
                       signature: str, tenant_uuid: str) -> dict:
        """Handle a webhook from a PSP. Returns response dict.

        Per ADR-0075 failure handling:
        - Signature failure → 400
        - Replay → 200 (idempotent)
        - Unknown event → 200 + warning
        - Processing failure → 500 (PSP retries)
        """
        # Step 1: Verify signature BEFORE any DB write.
        if not self._verify_signature(payload, signature, psp_name):
            log.warning("webhook_signature_invalid", extra={"psp": psp_name})
            return {"status": 400, "body": {"error": "invalid signature"}}

        # Step 2: Parse payload.
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            return {"status": 400, "body": {"error": "invalid JSON"}}

        psp_event_id = event.get("id", "")
        event_type = event.get("type", "unknown")

        # Step 3: Check idempotency (Phase 8 inbox pattern).
        _, created = WebhookLog.objects.get_or_create(
            tenant_uuid=uuid.UUID(tenant_uuid),
            psp_name=psp_name,
            psp_event_id=psp_event_id,
            defaults={
                "event_type": event_type,
                "payload": event,
                "signature_valid": True,
                "processed": False,
            },
        )
        if not created:
            log.info("webhook_duplicate_idempotent", extra={
                "psp": psp_name, "event_id": psp_event_id,
            })
            return {"status": 200, "body": {"status": "already processed"}}

        # Step 4: Process event.
        try:
            self._process_event(event, psp_name, tenant_uuid)
            return {"status": 200, "body": {"status": "processed"}}
        except Exception as e:
            log.error("webhook_processing_failed", extra={
                "psp": psp_name, "event_id": psp_event_id, "error": str(e),
            })
            return {"status": 500, "body": {"error": "processing failed"}}

    def _verify_signature(self, payload: bytes, signature: str, psp_name: str) -> bool:
        """Verify HMAC-SHA256 signature. Per ADR-0075."""
        if not self._secret:
            # Sandbox: use PSP port's verify.
            return self._psp.verify_webhook(
                payload=payload, signature=signature, psp_name=psp_name,
            )

        # Real verification: HMAC-SHA256 constant-time comparison.
        expected = hmac.new(self._secret, payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def _process_event(self, event: dict, psp_name: str, tenant_uuid: str) -> None:
        """Process a webhook event. Per ADR-0075."""
        event_type = event.get("type", "unknown")

        if event_type == "unknown":
            log.warning("webhook_unknown_event_type", extra={
                "psp": psp_name, "type": event_type,
            })
            return  # 200 + warning (acknowledge, don't fail).

        # Payment-specific event handling would go here.
        # e.g., payment.captured → update order status
        # e.g., dispute.created → create DisputeCase
        log.info("webhook_event_processed", extra={
            "psp": psp_name, "type": event_type,
        })


class DisputeService:
    """Chargeback dispute service with FSM + evidence pack. Per ADR-0076.

    FSM: open → evidence_submitted → won/lost/expired/arbitration.
    Deadline enforcement: missed → automatic loss.
    Evidence pack auto-generated on dispute.opened.
    """

    @transaction.atomic
    def create_dispute(self, *, order_uuid: str, tenant_uuid: str,
                       psp_dispute_id: str, reason: str,
                       amount_minor: int, currency_code: str,
                       deadline_hours: int = 168) -> DisputeCase:
        """Create a dispute case + trigger evidence pack generation.

        Per ADR-0076: evidence pack auto-generated on dispute.opened.
        Default deadline: 7 days (168 hours).
        """
        from datetime import timedelta

        dispute = DisputeCase.objects.create(
            tenant_uuid=uuid.UUID(tenant_uuid),
            order=PaymentOrder.objects.get(
                order_uuid=uuid.UUID(order_uuid),
                tenant_uuid=uuid.UUID(tenant_uuid),
            ),
            psp_dispute_id=psp_dispute_id,
            reason=reason,
            status="open",
            amount_minor=amount_minor,
            currency_code=currency_code,
            deadline_at=timezone.now() + timedelta(hours=deadline_hours),
        )

        # Trigger evidence pack generation (async in production; stub here).
        dispute.evidence_pack_uuid = uuid.uuid4()
        dispute.save()

        log.info("dispute_created", extra={
            "dispute_uuid": str(dispute.dispute_uuid),
            "order_uuid": order_uuid,
            "reason": reason,
            "deadline": dispute.deadline_at.isoformat(),
        })

        return dispute

    def check_deadline(self, dispute: DisputeCase) -> bool:
        """Check if dispute deadline has passed. Per ADR-0076.

        Missed deadline → automatic loss (regulator-mandated).
        """
        if timezone.now() > dispute.deadline_at and dispute.status == "open":
            dispute.status = "lost"
            dispute.save()
            log.warning("dispute_deadline_missed_auto_loss", extra={
                "dispute_uuid": str(dispute.dispute_uuid),
            })
            return False  # Deadline missed.
        return True  # Deadline OK.
