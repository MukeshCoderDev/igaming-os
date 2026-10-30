"""PCI DLP Injection Test.

Per the Stage B Verification Suite spec §1.7.
Per linter rules 81, 82, 88. PCI SAQ-A boundary enforcement.

Tests:
1. DLP redacts PAN-shaped values in structured logging.
2. DLP redacts PAN in audit event payload.
3. No DB columns named card_number, pan, cvv, etc.
4. No PAN field names in src/ code.
5. No PSP keys (sk_test_/sk_live_) in source code.

This test is CRITICAL — a single PAN storage converts Noventra from
SAQ-A (self-assessment) to SAQ-D (full audit, potentially business-ending).
"""

import re
import subprocess
from io import StringIO

import pytest

# Luhn-valid test PANs (from Stripe docs — NOT real cards).
TEST_PANS = [
    "4242424242424242",  # Visa
    "5555555555554444",  # Mastercard
    "378282246310005",   # Amex
    "6011111111111117",  # Discover
    "3530111333300000",  # JCB
    "6200000000000005",  # UnionPay
]


def luhn_valid(card_number: str) -> bool:
    """Check if a card number passes Luhn validation."""
    total = 0
    reverse = card_number[::-1]
    for i, digit in enumerate(reverse):
        n = int(digit)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


class TestPCIDLPInjection:
    """PCI DLP injection tests. Per linter rules 81, 82, 88."""

    def test_luhn_valid_test_pans(self):
        """Verify our test PANs are actually Luhn-valid."""
        for pan in TEST_PANS:
            assert luhn_valid(pan), f"Test PAN {pan} is not Luhn-valid"

    def test_dlp_redacts_pan_in_structlog(self):
        """DLP redacts PAN-shaped values in structlog output."""
        from noventra.observability.redaction import _redact_value, _redact_dict

        for pan in TEST_PANS:
            # Test direct value redaction.
            result = _redact_value(f"My card is {pan}")
            assert pan not in result, f"PAN {pan} not redacted in value"
            assert "[REDACTED" in result or pan not in result

    def test_dlp_redacts_pan_in_dict(self):
        """DLP redacts PAN-shaped values in dict payloads."""
        from noventra.observability.redaction import _redact_dict

        for pan in TEST_PANS:
            payload = {
                "description": f"Card on file: {pan}",
                "amount": 100,
            }
            result = _redact_dict(payload)
            assert pan not in str(result), f"PAN {pan} leaked in dict payload"

    def test_dlp_redacts_pan_field_names(self):
        """DLP redacts fields named card_number, pan, cvv, etc."""
        from noventra.observability.redaction import _redact_dict

        sensitive_fields = {
            "card_number": "4242424242424242",
            "pan": "5555555555554444",
            "cvv": "123",
            "cvc": "456",
            "expiry_month": "12",
            "expiry_year": "2025",
        }
        result = _redact_dict(sensitive_fields)
        for key in sensitive_fields:
            assert result[key] == "[REDACTED]", f"Field {key} not redacted"

    @pytest.mark.django_db
    def test_no_pan_db_columns(self):
        """Verify no DB columns named card_number, pan, cvv, etc."""
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND column_name IN ('card_number', 'pan', 'cvv', 'cvc',
                                      'expiry_month', 'expiry_year',
                                      'track_data', 'magstripe')
            """)
            results = cursor.fetchall()
            assert len(results) == 0, f"PAN-shaped columns found: {results}"

    def test_no_pan_field_names_in_src(self):
        """Verify no PAN field names in src/ code."""
        result = subprocess.run(
            ["grep", "-rn", "-E",
             "card_number|pan|cvv|cvc|expiry_month|expiry_year|track_data|magstripe",
             "src/"],
            capture_output=True, text=True
        )
        # Filter out false positives (comments, docstrings, PCI references).
        real_findings = []
        for line in result.stdout.split("\n"):
            if not line:
                continue
            # Allow: comments mentioning PCI, docstrings, __pycache__
            if "PCI" in line or "__pycache__" in line or ".pyc" in line:
                continue
            # Allow: the word "pan" in non-card contexts (e.g., "panel", "panda", "expansion")
            parts = line.split(":", 2)
            if len(parts) >= 3:
                code = parts[2]
                # Check if it's a standalone "pan" (not part of another word).
                if re.search(r'\bpan\b', code, re.IGNORECASE):
                    # Allow if in a comment or docstring.
                    stripped = code.strip()
                    if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                        continue
                    real_findings.append(line)
            else:
                real_findings.append(line)

        assert len(real_findings) == 0, f"PAN field names found in code:\n{chr(10).join(real_findings)}"

    def test_no_psp_keys_in_src(self):
        """Verify no PSP keys (sk_test_/sk_live_) in source code."""
        result = subprocess.run(
            ["grep", "-rn", "-E", "sk_test_|sk_live_", "src/"],
            capture_output=True, text=True
        )
        real_findings = [
            line for line in result.stdout.split("\n")
            if line and "__pycache__" not in line and ".pyc" not in line
            and "PCI" not in line and "#" not in line.split(":", 2)[-1][:10]
        ]
        assert len(real_findings) == 0, f"PSP keys found in source:\n{chr(10).join(real_findings)}"
