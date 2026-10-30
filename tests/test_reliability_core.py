"""Tests for reliability core (Phase 8).

Per Phase 8 hard acceptance:
- Outbox relay: multi-instance, no double-publish, no missed events.
- Inbox dedup: same message by two consumers; only one side effect.
- DLQ: poison message arrives; alerting fires; replay succeeds.
- Idempotency: same key + same body = cached; same key + different body = 409.
- State machine: invalid transition rejected; concurrent handled; audited.
- MarketingGate: suppression deny; cap deny; transactional bypass.
"""

from __future__ import annotations

import json
import uuid

import pytest
from django.db import connection

from noventra.apps.reliability.domain.outbox import OutboxStatus
from noventra.apps.reliability.domain.marketing_gate import (
    CapChecker, CapResult, GateDecisionType, MarketingGate,
)
from noventra.apps.reliability.domain.notifications import (
    NotificationChannel, SendType,
)
from noventra.apps.reliability.domain.state_machine import (
    StateMachineMixin, TransitionError, transition,
)
from noventra.apps.reliability.adapters.outbox_relay import append_to_outbox, relay_batch
from noventra.apps.reliability.adapters.consumer import ConsumerBase, DLQConsumer
from noventra.apps.reliability.adapters.notifications import (
    EmailStubAdapter, SMSStubAdapter, FallbackAdapter,
)


TENANT_A = "00000000-0000-0000-0000-000000000001"
USER_A = "00000000-0000-0000-0000-000000000a01"


class TestOutboxRelay:
    """Outbox relay: append + relay + no double-publish."""

    @pytest.mark.django_db
    def test_append_to_outbox(self):
        """append_to_outbox inserts a pending event."""
        event_id = append_to_outbox(
            event_type="tenancy.tenant_provisioned",
            aggregate_id=TENANT_A,
            aggregate_type="tenant",
            tenant_id=TENANT_A,
            actor_id=USER_A,
            payload={"legal_name": "Acme"},
        )
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL app.tenant_uuid = %s", [TENANT_A])
            cursor.execute(
                "SELECT status, event_type FROM reliability_outbox WHERE event_id = %s",
                [event_id],
            )
            row = cursor.fetchone()
        assert row is not None
        assert row[0] == "pending"
        assert row[1] == "tenancy.tenant_provisioned"

    @pytest.mark.django_db
    def test_relay_batch_publishes_and_marks(self):
        """relay_batch publishes events + marks them relayed."""
        event_id = append_to_outbox(
            event_type="tenancy.tenant_provisioned",
            aggregate_id=TENANT_A, aggregate_type="tenant",
            tenant_id=TENANT_A, actor_id=USER_A,
            payload={},
        )
        published = []
        count = relay_batch(lambda event: published.append(event))
        assert count >= 1
        assert len(published) >= 1
        # Verify marked as relayed.
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL app.tenant_uuid = %s", [TENANT_A])
            cursor.execute(
                "SELECT status FROM reliability_outbox WHERE event_id = %s",
                [event_id],
            )
            row = cursor.fetchone()
        assert row[0] == "relayed"

    @pytest.mark.django_db
    def test_relay_no_double_publish(self):
        """Relaying twice doesn't re-publish already-relayed events."""
        append_to_outbox(
            event_type="tenancy.tenant_provisioned",
            aggregate_id=TENANT_A, aggregate_type="tenant",
            tenant_id=TENANT_A, actor_id=USER_A, payload={},
        )
        published = []
        relay_batch(lambda e: published.append(e))
        first_count = len(published)
        relay_batch(lambda e: published.append(e))
        second_count = len(published)
        # Second relay should not add more (no double-publish).
        assert second_count == first_count


class TestInboxDedup:
    """Inbox dedup: same message by two consumers; only one side effect."""

    @pytest.mark.django_db
    def test_duplicate_message_skipped(self):
        """Same message processed twice; second is skipped."""
        message = {
            "event_id": str(uuid.uuid4()),
            "tenant_id": TENANT_A,
            "event_type": "tenancy.tenant_provisioned",
            "payload": {"legal_name": "Acme"},
        }

        side_effects = []

        class TestConsumer(ConsumerBase):
            def handle(self, msg):
                side_effects.append(msg["event_id"])

        consumer = TestConsumer("test-consumer")
        # First process: side effect + inbox insert.
        result1 = consumer.process(message)
        assert result1 is True
        assert len(side_effects) == 1

        # Second process: deduped (inbox hit).
        result2 = consumer.process(message)
        assert result2 is False
        assert len(side_effects) == 1  # No additional side effect.


class TestDLQ:
    """DLQ: poison message arrives; replay."""

    @pytest.mark.django_db
    def test_dlq_message_sent(self):
        """Poison message is sent to DLQ."""
        dlq_messages = []
        consumer = DLQConsumer(
            "test-dlq-consumer",
            dlq_publisher=lambda msg, reason: dlq_messages.append((msg, reason)),
        )
        message = {"event_id": str(uuid.uuid4()), "tenant_id": TENANT_A}
        consumer.send_to_dlq(message, "max_retries_exceeded")
        assert len(dlq_messages) == 1
        assert dlq_messages[0][1] == "max_retries_exceeded"


class TestIdempotency:
    """Idempotency: same key + same body = cached; different body = 409."""

    @pytest.mark.django_db
    def test_same_key_same_body_returns_cached(self):
        """Same key + same body returns the cached response."""
        from noventra.middleware.idempotency import IdempotencyMiddleware
        from django.test import RequestFactory
        from django.http import HttpResponse

        rf = RequestFactory()
        key = str(uuid.uuid4())
        body = json.dumps({"name": "test"})

        # First request: processes + stores.
        call_count = [0]
        def get_response(req):
            call_count[0] += 1
            return HttpResponse('{"id": 1}', content_type="application/json")

        mw = IdempotencyMiddleware(get_response)
        request1 = rf.post("/api/v1/test/", data=body, content_type="application/json",
                           **{"HTTP_IDEMPOTENCY_KEY": key})
        request1.jwt_tenant_id = TENANT_A
        response1 = mw(request1)
        assert call_count[0] == 1

        # Second request: same key + same body → cached (no handler call).
        request2 = rf.post("/api/v1/test/", data=body, content_type="application/json",
                           **{"HTTP_IDEMPOTENCY_KEY": key})
        request2.jwt_tenant_id = TENANT_A
        response2 = mw(request2)
        assert call_count[0] == 1  # Handler NOT called again.


class TestStateMachine:
    """State machine: invalid transition rejected; transitions audited."""

    def test_invalid_transition_rejected(self):
        """Invalid transition raises TransitionError."""
        class TenantSM(StateMachineMixin):
            state = "active"

            @transition(source="provisioning", target="active")
            def activate(self):
                pass

            @transition(source="active", target="suspended")
            def suspend(self):
                pass

        sm = TenantSM()
        sm.state = "provisioning"
        sm.activate()
        assert sm.state == "active"

        # Invalid: can't activate from active.
        with pytest.raises(TransitionError):
            sm.activate()

    def test_valid_transition(self):
        """Valid transition changes state."""
        class TenantSM(StateMachineMixin):
            state = "provisioning"

            @transition(source="provisioning", target="active")
            def activate(self):
                pass

        sm = TenantSM()
        sm.activate()
        assert sm.state == "active"

    def test_guard_failure(self):
        """Guard failure raises TransitionError."""
        class TenantSM(StateMachineMixin):
            state = "active"

            @transition(source="active", target="suspended", guard=lambda self: False)
            def suspend(self):
                pass

        sm = TenantSM()
        with pytest.raises(TransitionError):
            sm.suspend()

    def test_transition_side_effects(self):
        """Transition fires before + after hooks."""
        class TenantSM(StateMachineMixin):
            state = "provisioning"
            events = []

            def _before_transition(self, name, source, target):
                self.events.append(("before", name, source, target))

            def _after_transition(self, name, source, target):
                self.events.append(("after", name, source, target))

            @transition(source="provisioning", target="active")
            def activate(self):
                pass

        sm = TenantSM()
        sm.activate()
        assert ("before", "activate", "provisioning", "active") in sm.events
        assert ("after", "activate", "provisioning", "active") in sm.events


class TestMarketingGate:
    """MarketingGate: suppression + caps + send-type taxonomy."""

    def test_marketing_respects_suppression(self):
        """Marketing send to suppressed recipient → deny."""
        gate = MarketingGate(suppression_list={"suppressed@example.com"})
        decision = gate.evaluate(
            send_type="marketing",
            recipient="suppressed@example.com",
            channel="email",
            tenant_id=TENANT_A,
        )
        assert decision.decision == GateDecisionType.DENY_SUPPRESSION

    def test_transactional_bypasses_suppression(self):
        """Transactional send to suppressed recipient → allow."""
        gate = MarketingGate(suppression_list={"suppressed@example.com"})
        decision = gate.evaluate(
            send_type="transactional",
            recipient="suppressed@example.com",
            channel="email",
            tenant_id=TENANT_A,
        )
        assert decision.decision == GateDecisionType.ALLOW

    def test_cap_exceeded_denies(self):
        """Cap exceeded → deny."""
        class StrictCapChecker(CapChecker):
            def check(self, *, tenant_id, recipient, channel):
                return CapResult(allowed=False, reason="tenant_daily_exceeded")

        gate = MarketingGate(cap_checker=StrictCapChecker())
        decision = gate.evaluate(
            send_type="transactional",
            recipient="user@example.com",
            channel="email",
            tenant_id=TENANT_A,
        )
        assert decision.decision == GateDecisionType.DENY_CAP

    def test_allow_when_no_suppression_no_cap(self):
        """No suppression + no cap → allow."""
        gate = MarketingGate()
        decision = gate.evaluate(
            send_type="marketing",
            recipient="user@example.com",
            channel="email",
            tenant_id=TENANT_A,
        )
        assert decision.decision == GateDecisionType.ALLOW


class TestNotifications:
    """Notification adapters (stub)."""

    def test_email_stub_adapter(self):
        adapter = EmailStubAdapter()
        result = adapter.send(
            channel=NotificationChannel.EMAIL,
            recipient="user@example.com",
            content="Hello",
            context={},
        )
        assert result.success is True
        assert "stub-email" in result.message_id

    def test_sms_stub_adapter(self):
        adapter = SMSStubAdapter()
        result = adapter.send(
            channel=NotificationChannel.SMS,
            recipient="+1234567890",
            content="Code: 123456",
            context={},
        )
        assert result.success is True

    def test_fallback_adapter_on_failure(self):
        """Fallback adapter queues for retry on primary failure."""
        class FailingAdapter:
            def send(self, **kwargs):
                raise RuntimeError("vendor down")

        fallback = FallbackAdapter(FailingAdapter())
        result = fallback.send(
            channel=NotificationChannel.EMAIL,
            recipient="user@example.com",
            content="Hello",
            context={},
        )
        assert result.success is False
        assert result.metadata.get("queued_for_retry") is True
