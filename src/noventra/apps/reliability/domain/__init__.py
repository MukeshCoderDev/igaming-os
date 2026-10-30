"""Reliability domain — outbox, inbox, idempotency, state machine, notifications, MarketingGate.

Per ADR-0040..0046 / DEC-0045..0051.
"""

from .outbox import OutboxEvent, OutboxStatus  # noqa: F401
from .inbox import InboxEntry  # noqa: F401
from .idempotency import IdempotencyRecord  # noqa: F401
from .notifications import NotificationPort, SendResult, NotificationChannel, SendType  # noqa: F401
from .marketing_gate import MarketingGate, GateDecision, CapChecker, CapResult, ConsentChecker, ConsentResult  # noqa: F401
from .state_machine import transition, StateMachineMixin, TransitionError  # noqa: F401
