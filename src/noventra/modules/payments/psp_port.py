"""PSP Port interface + sandbox adapter. Per ADR-0074 / DEC-0074.

Hexagonal pattern: PspPort interface + SandboxPspAdapter (dev/test).
Real adapters (Stripe/Adyen/Square) are Q5-blocked.
No card data stored — PSP tokens only (PCI SAQ-A).
"""

from __future__ import annotations

import abc
import logging
import uuid
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger("noventra.payments.psp")


@dataclass(frozen=True)
class PspResult:
    """Result of a PSP operation."""
    success: bool
    charge_id: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class WebhookResult:
    """Result of webhook processing."""
    success: bool
    event_type: Optional[str] = None
    processed: bool = False
    error: Optional[str] = None


class PspPort(abc.ABC):
    """Port: Payment Service Provider interface. Per ADR-0074.

    Every payment-related code path goes through this port (linter rule 87).
    No direct PSP API calls allowed.
    """

    @abc.abstractmethod
    def authorize(self, *, amount_minor: int, currency: str, psp_token: str,
                  idempotency_key: str) -> PspResult:
        """Authorize a payment. Returns PspResult with charge_id."""

    @abc.abstractmethod
    def capture(self, *, charge_id: str, amount_minor: int) -> PspResult:
        """Capture an authorized payment."""

    @abc.abstractmethod
    def refund(self, *, charge_id: str, amount_minor: int) -> PspResult:
        """Refund a captured payment."""

    @abc.abstractmethod
    def get_status(self, *, charge_id: str) -> PspResult:
        """Get payment status from PSP."""

    @abc.abstractmethod
    def verify_webhook(self, *, payload: bytes, signature: str, psp_name: str) -> bool:
        """Verify webhook signature (HMAC-SHA256). Per ADR-0075."""


class SandboxPspAdapter(PspPort):
    """Sandbox PSP adapter for dev/test. Per ADR-0074.

    Returns canned responses. No real PSP calls.
    Configurable per-test via inject_charge_id.
    """

    def __init__(self):
        self._charges: dict[str, dict] = {}

    def authorize(self, *, amount_minor: int, currency: str, psp_token: str,
                  idempotency_key: str) -> PspResult:
        charge_id = f"ch_test_{idempotency_key[:16]}"
        self._charges[charge_id] = {
            "amount": amount_minor,
            "currency": currency,
            "status": "authorized",
        }
        log.info("psp_sandbox_authorize", extra={"charge_id": charge_id, "amount": amount_minor})
        return PspResult(success=True, charge_id=charge_id, status="authorized")

    def capture(self, *, charge_id: str, amount_minor: int) -> PspResult:
        if charge_id not in self._charges:
            return PspResult(success=False, error="charge not found")
        self._charges[charge_id]["status"] = "captured"
        log.info("psp_sandbox_capture", extra={"charge_id": charge_id})
        return PspResult(success=True, charge_id=charge_id, status="captured")

    def refund(self, *, charge_id: str, amount_minor: int) -> PspResult:
        if charge_id not in self._charges:
            return PspResult(success=False, error="charge not found")
        self._charges[charge_id]["status"] = "refunded"
        log.info("psp_sandbox_refund", extra={"charge_id": charge_id})
        return PspResult(success=True, charge_id=charge_id, status="refunded")

    def get_status(self, *, charge_id: str) -> PspResult:
        charge = self._charges.get(charge_id)
        if charge is None:
            return PspResult(success=False, error="charge not found")
        return PspResult(success=True, charge_id=charge_id, status=charge["status"])

    def verify_webhook(self, *, payload: bytes, signature: str, psp_name: str) -> bool:
        """Sandbox: always verify (no real signature)."""
        log.debug("psp_sandbox_verify_webhook", extra={"psp": psp_name})
        return True
