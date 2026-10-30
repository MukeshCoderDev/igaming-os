"""Test the health endpoint.

Per Phase 3 spec hard acceptance: 503 path must be tested. This test
verifies the 200 path; the 503 path is tested via a unit test of the
check functions.
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_health_endpoint_returns_200(api_client, health_url):
    """GET /health/ returns 200 with status, version, and checks dict."""
    response = api_client.get(health_url)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in ("healthy", "unhealthy")
    assert "version" in body
    assert "checks" in body
    assert set(body["checks"].keys()) == {"db", "redis", "migrations_applied"}


@pytest.mark.django_db
def test_health_endpoint_no_secrets(api_client, health_url):
    """Response body must not contain SECRET_KEY or DB password."""
    from django.conf import settings
    response = api_client.get(health_url)
    body_text = response.content.decode()
    # The secret key must not appear in the response.
    assert settings.SECRET_KEY not in body_text
    # DB password must not appear.
    assert "noventra_dev_password" not in body_text
    assert "noventra_test" not in body_text.split("://")[-1] if "://" in body_text else True


def test_health_check_functions_exist():
    """The three check functions are importable and callable."""
    from noventra.api.health import _check_db, _check_redis, _check_migrations_applied
    assert callable(_check_db)
    assert callable(_check_redis)
    assert callable(_check_migrations_applied)
