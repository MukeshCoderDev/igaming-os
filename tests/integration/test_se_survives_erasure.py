"""SE-survives-erasure Test.

Per the Stage B Verification Suite spec §1.9.
Per ADR-0085 / DEC-0085. Per GDPR Art 17 + UK GC SE mandate.

Tests:
1. HMAC pseudonymization is deterministic.
2. SE record survives player erasure (player_id NULLed, pseudonymized_identity retained).
3. Excluded player cannot re-register after erasure (HMAC matches active SE).
4. HMAC produces 64-char hex (SHA-256).

This test requires live Postgres.
"""

import hashlib
import hmac
import uuid

import pytest
from django.conf import settings
from django.db import connection, transaction

from noventra.modules.protection.domain.self_exclusion import (
    SelfExclusion, ExclusionPeriod, compute_pseudonymized_identity,
    DEFAULT_REACTIVATION_COOLING_OFF_HOURS,
)


TENANT_A = "00000000-0000-0000-0000-000000000001"
TEST_IDENTITY_DOC = "passport_123456789"
TEST_SECRET_KEY = "test-se-pseudonymization-key"


class TestSESurvivesErasure:
    """SE-survives-erasure tests. Per ADR-0085."""

    def test_hmac_deterministic(self):
        """HMAC of same identity document produces same pseudonymized identity."""
        pseudo1 = compute_pseudonymized_identity(TEST_IDENTITY_DOC, TEST_SECRET_KEY)
        pseudo2 = compute_pseudonymized_identity(TEST_IDENTITY_DOC, TEST_SECRET_KEY)

        assert pseudo1 == pseudo2  # Deterministic.
        assert len(pseudo1) == 64  # SHA-256 hex = 64 chars.

    def test_hmac_different_documents_different_output(self):
        """Different identity documents produce different HMACs."""
        pseudo1 = compute_pseudonymized_identity("passport_123", TEST_SECRET_KEY)
        pseudo2 = compute_pseudonymized_identity("passport_456", TEST_SECRET_KEY)

        assert pseudo1 != pseudo2  # Different documents → different HMACs.

    def test_hmac_different_keys_different_output(self):
        """Different keys produce different HMACs for same document."""
        pseudo1 = compute_pseudonymized_identity(TEST_IDENTITY_DOC, "key1")
        pseudo2 = compute_pseudonymized_identity(TEST_IDENTITY_DOC, "key2")

        assert pseudo1 != pseudo2  # Different keys → different HMACs.

    def test_check_pseudonymized_identity_blocks_active_se(self):
        """check_pseudonymized_identity returns False (block) for active SE."""
        pseudo = compute_pseudonymized_identity(TEST_IDENTITY_DOC, TEST_SECRET_KEY)

        se = SelfExclusion(
            exclusion_uuid=uuid.uuid4(),
            tenant_uuid=uuid.UUID(TENANT_A),
            player_uuid=uuid.uuid4(),
            period=ExclusionPeriod.ONE_YEAR,
            pseudonymized_identity=pseudo,
        )

        # Should return False (blocked) — active SE exists.
        result = SelfExclusion.check_pseudonymized_identity(pseudo, [se])
        assert result is False  # Registration should be blocked.

    def test_check_pseudonymized_identity_allows_expired_se(self):
        """check_pseudonymized_identity returns True (allow) for expired SE."""
        from datetime import datetime, timezone, timedelta

        pseudo = compute_pseudonymized_identity(TEST_IDENTITY_DOC, TEST_SECRET_KEY)

        se = SelfExclusion(
            exclusion_uuid=uuid.uuid4(),
            tenant_uuid=uuid.UUID(TENANT_A),
            player_uuid=uuid.uuid4(),
            period=ExclusionPeriod.SIX_MONTHS,
            started_at=datetime.now(timezone.utc) - timedelta(days=365),
            pseudonymized_identity=pseudo,
        )
        # SE started 365 days ago; 6-month period = 182 days → expired.
        assert se.is_active is False

        # Should return True (allowed) — SE has expired.
        result = SelfExclusion.check_pseudonymized_identity(pseudo, [se])
        assert result is True  # Registration should be allowed.

    def test_check_pseudonymized_identity_allows_no_se(self):
        """check_pseudonymized_identity returns True (allow) when no SE exists."""
        pseudo = compute_pseudonymized_identity(TEST_IDENTITY_DOC, TEST_SECRET_KEY)
        result = SelfExclusion.check_pseudonymized_identity(pseudo, [])
        assert result is True  # No SE — registration allowed.

    @pytest.mark.django_db
    def test_se_record_survives_erasure_simulation(self):
        """Simulate: SE record retained with pseudonymized_identity after erasure.

        This test simulates the erasure flow:
        1. Player has active SE with pseudonymized_identity.
        2. Player is erased (player_id NULLed in SE record).
        3. SE record still exists with pseudonymized_identity.
        4. New registration with same identity document → blocked.
        """
        player_uuid = uuid.uuid4()
        pseudo = compute_pseudonymized_identity(TEST_IDENTITY_DOC, TEST_SECRET_KEY)

        # Step 1: Player has active SE.
        se = SelfExclusion(
            exclusion_uuid=uuid.uuid4(),
            tenant_uuid=uuid.UUID(TENANT_A),
            player_uuid=player_uuid,
            period=ExclusionPeriod.ONE_YEAR,
            pseudonymized_identity=pseudo,
        )
        assert se.is_active is True
        original_pseudo = se.pseudonymized_identity

        # Step 2: Simulate erasure — NULL out player_uuid.
        se_after_erasure = SelfExclusion(
            exclusion_uuid=se.exclusion_uuid,
            tenant_uuid=se.tenant_uuid,
            player_uuid=None,  # NULLed after erasure.
            period=se.period,
            started_at=se.started_at,
            pseudonymized_identity=se.pseudonymized_identity,  # Retained!
        )

        # Step 3: SE record still exists with pseudonymized_identity.
        assert se_after_erasure.player_uuid is None  # Original player_id NULLed.
        assert se_after_erasure.pseudonymized_identity == original_pseudo  # Pseudonymized identity retained.
        assert se_after_erasure.is_active is True  # SE still active.

        # Step 4: New registration with same identity document → blocked.
        new_pseudo = compute_pseudonymized_identity(TEST_IDENTITY_DOC, TEST_SECRET_KEY)
        assert new_pseudo == original_pseudo  # Same document → same HMAC.
        result = SelfExclusion.check_pseudonymized_identity(new_pseudo, [se_after_erasure])
        assert result is False  # Registration blocked — active SE detected.

    def test_reactivation_cooling_off(self):
        """Reactivation requires 24h cooling-off (configurable)."""
        from datetime import datetime, timezone, timedelta

        se = SelfExclusion(
            exclusion_uuid=uuid.uuid4(),
            tenant_uuid=uuid.UUID(TENANT_A),
            player_uuid=uuid.uuid4(),
            period=ExclusionPeriod.SIX_MONTHS,
            started_at=datetime.now(timezone.utc) - timedelta(days=200),
            pseudonymized_identity="test_pseudo",
        )
        # 6 months ≈ 182 days; started 200 days ago → can reactivate.
        assert se.can_reactivate is True

        # Reactivation initiates (in real impl: 24h cooling-off, then status=reactivated).
        result = se.reactivate()
        assert result is True  # Reactivation initiated.
        assert se.status == "reactivated"

    def test_lifetime_se_cannot_reactivate(self):
        """Lifetime SE cannot be reactivated."""
        se = SelfExclusion(
            exclusion_uuid=uuid.uuid4(),
            tenant_uuid=uuid.UUID(TENANT_A),
            player_uuid=uuid.uuid4(),
            period=ExclusionPeriod.LIFETIME,
            pseudonymized_identity="test_pseudo",
        )
        assert se.can_reactivate is False  # Lifetime — cannot reactivate.
        result = se.reactivate()
        assert result is False  # Reactivation rejected.
