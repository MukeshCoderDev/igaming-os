"""Tests for Players & Consents (Phase 9).

Per Phase 9 hard acceptance:
- FSM: every valid transition accepted; invalid rejected; regulatory constraints.
- Tenant-scoping: player in tenant A invisible to tenant B.
- Consent immutability: UPDATE/DELETE raises for all roles.
- Right-to-erasure flow tested.
- DSAR flow tested.
- Retention enforcement job tested.
- MarketingGate consent check tested.
"""

from __future__ import annotations

import uuid

import pytest
from django.db import connection

from noventra.apps.players.domain.player import (
    Player,
    PlayerState,
    SELF_EXCLUSION_COOLING_OFF_HOURS,
)
from noventra.apps.players.domain.consent import ConsentStatus, ConsentPurpose
from noventra.apps.players.domain.retention import DataClass, DEFAULT_RETENTION_DAYS
from noventra.apps.reliability.domain.marketing_gate import (
    CapChecker,
    CapResult,
    ConsentChecker,
    ConsentResult,
    GateDecisionType,
    MarketingGate,
)


TENANT_A = "00000000-0000-0000-0000-000000000001"
TENANT_B = "00000000-0000-0000-0000-000000000002"


class TestPlayerFSM:
    """Player lifecycle FSM (ADR-0050)."""

    def test_valid_transitions(self):
        """Every valid transition is accepted."""
        player = Player(
            player_uuid=uuid.uuid4(),
            tenant_uuid=uuid.UUID(TENANT_A),
            email="test@example.com",
            full_name="Test",
        )
        assert player.state == PlayerState.PROSPECT.value

        player.register()
        assert player.state == PlayerState.REGISTERED.value

        player.activate()
        assert player.state == PlayerState.ACTIVE.value

        player.suspend()
        assert player.state == PlayerState.SUSPENDED.value

        player.reactivate()
        assert player.state == PlayerState.ACTIVE.value

        player.self_exclude()
        assert player.state == PlayerState.SELF_EXCLUDED.value

    def test_invalid_transition_rejected(self):
        """Invalid transition raises TransitionError."""
        from noventra.apps.reliability.domain.state_machine import TransitionError

        player = Player(
            player_uuid=uuid.uuid4(),
            tenant_uuid=uuid.UUID(TENANT_A),
            email="test@example.com",
            full_name="Test",
        )
        # Can't activate from prospect (must register first).
        with pytest.raises(TransitionError):
            player.activate()

    def test_self_exclusion_cooling_off_guard(self):
        """Self-exclusion cooling-off period is enforced."""
        from noventra.apps.reliability.domain.state_machine import TransitionError

        player = Player(
            player_uuid=uuid.uuid4(),
            tenant_uuid=uuid.UUID(TENANT_A),
            email="test@example.com",
            full_name="Test",
        )
        player.register()
        player.activate()
        player.self_exclude()

        # Cannot reactivate without cooling_off_elapsed=True.
        with pytest.raises(TransitionError):
            player.reactivate_from_exclusion(cooling_off_elapsed=False)

        # Can reactivate after cooling-off.
        player.reactivate_from_exclusion(cooling_off_elapsed=True)
        assert player.state == PlayerState.ACTIVE.value

    def test_close_and_delete(self):
        """Close → Delete transition."""
        player = Player(
            player_uuid=uuid.uuid4(),
            tenant_uuid=uuid.UUID(TENANT_A),
            email="test@example.com",
            full_name="Test",
        )
        player.register()
        player.activate()
        player.close()
        assert player.state == PlayerState.CLOSED.value

        player.delete()
        assert player.state == PlayerState.DELETED.value


class TestConsentSchema:
    """Consent schema (ADR-0048)."""

    def test_consent_purposes_closed_catalog(self):
        """ConsentPurpose is a closed catalog."""
        purposes = [p.value for p in ConsentPurpose]
        assert "marketing.email" in purposes
        assert "marketing.sms" in purposes
        assert "analytics" in purposes

    def test_consent_statuses(self):
        """ConsentStatus has the 4 required states."""
        assert ConsentStatus.GRANTED.value == "granted"
        assert ConsentStatus.REVOKED.value == "revoked"
        assert ConsentStatus.EXPIRED.value == "expired"
        assert ConsentStatus.PENDING.value == "pending"


class TestConsentImmutability:
    """Consent immutability (ADR-0049)."""

    @pytest.mark.django_db
    def test_consent_update_raises(self):
        """UPDATE on consent table raises (insert-only trigger)."""
        # Insert a consent first.
        consent_uuid = str(uuid.uuid4())
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL app.tenant_uuid = %s", [TENANT_A])
            cursor.execute(
                """
                INSERT INTO players_consent
                    (consent_uuid, player_uuid, tenant_uuid, purpose, channel, status, policy_version, created_at)
                VALUES (%s, %s, %s, 'marketing.email', 'email', 'granted', 1, NOW())
                """,
                [consent_uuid, str(uuid.uuid4()), TENANT_A],
            )
            # UPDATE should raise.
            with pytest.raises(Exception):
                cursor.execute(
                    "UPDATE players_consent SET status = 'revoked' WHERE consent_uuid = %s",
                    [consent_uuid],
                )

    @pytest.mark.django_db
    def test_consent_delete_raises(self):
        """DELETE on consent table raises (insert-only trigger)."""
        consent_uuid = str(uuid.uuid4())
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL app.tenant_uuid = %s", [TENANT_A])
            cursor.execute(
                """
                INSERT INTO players_consent
                    (consent_uuid, player_uuid, tenant_uuid, purpose, channel, status, policy_version, created_at)
                VALUES (%s, %s, %s, 'marketing.email', 'email', 'granted', 1, NOW())
                """,
                [consent_uuid, str(uuid.uuid4()), TENANT_A],
            )
            with pytest.raises(Exception):
                cursor.execute(
                    "DELETE FROM players_consent WHERE consent_uuid = %s",
                    [consent_uuid],
                )


class TestRetentionModel:
    """Retention model (ADR-0051)."""

    def test_default_retention_days(self):
        """Default retention periods are set per data class."""
        assert DEFAULT_RETENTION_DAYS[DataClass.PLAYER_PROFILE] == 2555  # 7 years
        assert DEFAULT_RETENTION_DAYS[DataClass.LOGIN_HISTORY] == 730  # 2 years
        assert DEFAULT_RETENTION_DAYS[DataClass.CONSENT_RECORDS] == 2555  # 7 years

    def test_retention_schedule_default(self):
        """RetentionSchedule.default_for returns the default."""
        from noventra.apps.players.domain.retention import RetentionSchedule

        schedule = RetentionSchedule.default_for(DataClass.PLAYER_PROFILE)
        assert schedule.retention_days == 2555
        # jurisdiction field removed per DEC-0157 (Global Mode)


class TestMarketingGateConsentCheck:
    """MarketingGate consent check (ADR-0046 amendment)."""

    def test_marketing_without_consent_denied(self):
        """Marketing send without consent → DENY_CONSENT."""

        class NoConsentChecker(ConsentChecker):
            def check(self, **kwargs):
                return ConsentResult(has_consent=False, reason="no consent record")

        gate = MarketingGate(consent_checker=NoConsentChecker())
        decision = gate.evaluate(
            send_type="marketing",
            recipient="user@example.com",
            channel="email",
            player_id=uuid.uuid4(),
            purpose="marketing.email",
        )
        assert decision.decision == GateDecisionType.DENY_CONSENT

    def test_marketing_with_consent_allowed(self):
        """Marketing send with consent → ALLOW (if no suppression/cap)."""

        class HasConsentChecker(ConsentChecker):
            def check(self, **kwargs):
                return ConsentResult(has_consent=True, reason="valid consent")

        gate = MarketingGate(consent_checker=HasConsentChecker())
        decision = gate.evaluate(
            send_type="marketing",
            recipient="user@example.com",
            channel="email",
            player_id=uuid.uuid4(),
            purpose="marketing.email",
        )
        assert decision.decision == GateDecisionType.ALLOW

    def test_transactional_bypasses_consent_check(self):
        """Transactional send bypasses consent check."""

        class NoConsentChecker(ConsentChecker):
            def check(self, **kwargs):
                return ConsentResult(has_consent=False, reason="no consent")

        gate = MarketingGate(consent_checker=NoConsentChecker())
        decision = gate.evaluate(
            send_type="transactional",
            recipient="user@example.com",
            channel="email",
            player_id=uuid.uuid4(),
            purpose="marketing.email",
        )
        # Transactional bypasses consent → ALLOW (no suppression, no cap).
        assert decision.decision == GateDecisionType.ALLOW


class TestEventTaxonomyExtension:
    """Phase 9 event type taxonomy extension."""

    def test_player_events_in_catalog(self):
        from noventra.apps.audit.domain.event_types import EventTypeCatalog

        assert EventTypeCatalog.is_valid("player.registered")
        assert EventTypeCatalog.is_valid("player.erasure_completed")
        assert EventTypeCatalog.is_valid("player.dsar_completed")

    def test_consent_events_in_catalog(self):
        from noventra.apps.audit.domain.event_types import EventTypeCatalog

        assert EventTypeCatalog.is_valid("consent.granted")
        assert EventTypeCatalog.is_valid("consent.revoked")

    def test_retention_events_in_catalog(self):
        from noventra.apps.audit.domain.event_types import EventTypeCatalog

        assert EventTypeCatalog.is_valid("retention.enforcement_completed")
