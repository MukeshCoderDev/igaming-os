"""MarketingGate domain — suppression + caps + send-type taxonomy.

Per ADR-0046 / DEC-0051: joins suppression + caps at send time;
the ONLY place sends are gated; every decision audited.
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass
from typing import Optional


class GateDecisionType(str, enum.Enum):
    ALLOW = "allow"
    DENY_SUPPRESSION = "deny_suppression"
    DENY_CAP = "deny_cap"
    DENY_CONSENT = "deny_consent"  # Phase 9 amendment (ADR-0046)


@dataclass(frozen=True)
class GateDecision:
    """The MarketingGate's decision for a send request."""

    decision: GateDecisionType
    reason: str
    send_type: str  # transactional | marketing
    recipient: str
    channel: str
    tenant_id: Optional[uuid.UUID] = None


class MarketingGate:
    """The ONLY place sends are gated.

    Per ADR-0046: joins suppression + caps at send time.
    - transactional: bypasses suppression, respects caps.
    - marketing: respects both.
    """

    def __init__(
        self,
        suppression_list: set[str] | None = None,
        cap_checker: "CapChecker | None" = None,
        consent_checker: "ConsentChecker | None" = None,
    ):
        self._suppression = suppression_list or set()
        self._cap_checker = cap_checker
        self._consent_checker = consent_checker  # Phase 9 amendment

    def evaluate(
        self,
        *,
        send_type: str,
        recipient: str,
        channel: str,
        tenant_id: uuid.UUID | None = None,
        player_id: uuid.UUID | None = None,
        purpose: str | None = None,
    ) -> GateDecision:
        """Evaluate a send request. Returns GateDecision.

        Per ADR-0046 (amended Phase 9):
        - transactional: bypasses suppression + consent, respects caps.
        - marketing: respects suppression + caps + consent.
        """
        # Suppression check: marketing only (transactional bypasses).
        if send_type == "marketing" and recipient in self._suppression:
            return GateDecision(
                decision=GateDecisionType.DENY_SUPPRESSION,
                reason=f"recipient {recipient} is suppressed",
                send_type=send_type,
                recipient=recipient,
                channel=channel,
                tenant_id=tenant_id,
            )

        # Consent check: marketing only (transactional bypasses).
        # Phase 9 amendment (ADR-0046).
        if send_type == "marketing" and self._consent_checker is not None:
            consent_result = self._consent_checker.check(
                player_id=player_id, purpose=purpose, channel=channel
            )
            if not consent_result.has_consent:
                return GateDecision(
                    decision=GateDecisionType.DENY_CONSENT,
                    reason=f"no valid consent: {consent_result.reason}",
                    send_type=send_type,
                    recipient=recipient,
                    channel=channel,
                    tenant_id=tenant_id,
                )

        # Cap check: both transactional + marketing respect caps.
        if self._cap_checker is not None:
            cap_result = self._cap_checker.check(
                tenant_id=tenant_id, recipient=recipient, channel=channel
            )
            if not cap_result.allowed:
                return GateDecision(
                    decision=GateDecisionType.DENY_CAP,
                    reason=f"cap exceeded: {cap_result.reason}",
                    send_type=send_type,
                    recipient=recipient,
                    channel=channel,
                    tenant_id=tenant_id,
                )

        return GateDecision(
            decision=GateDecisionType.ALLOW,
            reason="ok",
            send_type=send_type,
            recipient=recipient,
            channel=channel,
            tenant_id=tenant_id,
        )


@dataclass(frozen=True)
class CapResult:
    allowed: bool
    reason: str


class CapChecker:
    """Cap checker interface (tenant monthly, tenant daily, recipient daily, channel)."""

    def check(
        self,
        *,
        tenant_id: uuid.UUID | None,
        recipient: str,
        channel: str,
    ) -> CapResult:
        """Check if the send is within caps. Returns CapResult."""
        # Phase 8 stub: always allow. Phase 9 implements Redis counters.
        return CapResult(allowed=True, reason="stub: no caps enforced")


@dataclass(frozen=True)
class ConsentResult:
    """Result of a consent check."""
    has_consent: bool
    reason: str


class ConsentChecker:
    """Consent checker interface (Phase 9 amendment to ADR-0046).

    Checks if a valid (granted, not expired, not revoked) consent exists
    for the (player, purpose, channel) tuple.
    """

    def check(
        self,
        *,
        player_id: uuid.UUID | None,
        purpose: str | None,
        channel: str,
    ) -> ConsentResult:
        """Check if consent exists. Returns ConsentResult."""
        # Phase 9 stub: always has consent. Real implementation queries
        # the consent table for the latest (granted) record matching
        # (player, purpose, channel).
        return ConsentResult(has_consent=True, reason="stub: no consent check")
