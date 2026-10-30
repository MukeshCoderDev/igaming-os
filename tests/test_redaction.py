"""Tests for the redaction processor (ADR-0025 / DEC-0030).

Covers:
- PII field redaction by name.
- Secret field redaction by name.
- Secret value redaction by regex (AWS key, JWT, Postgres URL, Redis URL,
  Bearer token, PEM block).
- Injected-secret regression: a dict containing a known secret is
  redacted; the secret value never appears in the output.
"""

from __future__ import annotations

from noventra.observability.redaction import (
    RedactingProcessor,
    _redact_dict,
    _redact_value,
    PII_FIELD_NAMES,
    SECRET_FIELD_NAMES,
    REDACTED_VALUE,
)


def test_pii_field_redacted_by_name():
    """PII field names are redacted regardless of value."""
    out = _redact_dict({"email": "user@example.com", "ok": "keep"})
    assert out["email"] == REDACTED_VALUE
    assert out["ok"] == "keep"


def test_secret_field_redacted_by_name():
    """Secret field names are redacted regardless of value."""
    out = _redact_dict({"SECRET_KEY": "abc123", "password": "hunter2"})
    assert out["SECRET_KEY"] == REDACTED_VALUE
    assert out["password"] == REDACTED_VALUE


def test_aws_access_key_redacted_by_regex():
    """AWS access key pattern is redacted in any string value."""
    val = "token=AKIAIOSFODNN7EXAMPLE"
    out = _redact_value(val)
    assert "AKIAIOSFODNN7EXAMPLE" not in out
    assert "[REDACTED:aws_access_key]" in out


def test_jwt_redacted_by_regex():
    """JWT pattern (eyJ...) is redacted in any string value."""
    jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    out = _redact_value(jwt)
    assert "eyJhbGciOiJIUzI1NiJ9" not in out
    assert "[REDACTED:jwt]" in out


def test_postgres_url_redacted_by_regex():
    """Postgres URL with password is redacted."""
    url = "postgres://user:secretpass@localhost:5432/db"
    out = _redact_value(url)
    assert "secretpass" not in out
    assert "[REDACTED]" in out


def test_redis_url_redacted_by_regex():
    """Redis URL with password is redacted."""
    url = "redis://:secretpass@localhost:6379/0"
    out = _redact_value(url)
    assert "secretpass" not in out
    assert "[REDACTED]" in out


def test_bearer_token_redacted_by_regex():
    """Bearer token in Authorization header is redacted."""
    val = "Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    out = _redact_value(val)
    assert "eyJhbGciOiJIUzI1NiJ9" not in out
    assert "[REDACTED]" in out


def test_pem_private_key_block_redacted_by_regex():
    """PEM private key block is redacted."""
    pem = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA1234567890abcdefghijklmnopqrstuvwxyz
-----END RSA PRIVATE KEY-----"""
    out = _redact_value(pem)
    assert "MIIEpAIBAAKCAQEA" not in out
    assert "[REDACTED:private_key_block]" in out


def test_nested_dict_redaction():
    """Nested dicts are recursively redacted."""
    out = _redact_dict({
        "outer": {
            "email": "nested@example.com",
            "safe": "ok",
        },
        "list_of_dicts": [
            {"password": "secret1"},
            {"password": "secret2"},
        ],
    })
    assert out["outer"]["email"] == REDACTED_VALUE
    assert out["outer"]["safe"] == "ok"
    assert out["list_of_dicts"][0]["password"] == REDACTED_VALUE
    assert out["list_of_dicts"][1]["password"] == REDACTED_VALUE


def test_injected_secret_regression():
    """Regression: a known secret value never appears in redacted output.

    This is the regression test for the secret-redaction guarantee. If
    a new field is added that should be redacted, this test catches it
    when the secret value leaks.
    """
    known_secret = "AKIAIOSFODNN7EXAMPLE"
    event_dict = {
        "event": "test",
        "authorization": f"Bearer somejwt.{known_secret}",
        "metadata": {"aws_key": known_secret},
    }
    out = _redact_dict(event_dict)
    # The known secret must not appear anywhere in the redacted output.
    out_str = str(out)
    assert known_secret not in out_str, (
        f"Secret leaked into redacted output: {out_str}"
    )


def test_processor_callable():
    """RedactingProcessor is callable as a structlog processor."""
    proc = RedactingProcessor()
    event_dict = {"event": "test", "email": "user@example.com"}
    out = proc(None, "info", event_dict)
    assert out["email"] == REDACTED_VALUE
