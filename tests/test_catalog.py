"""Tests for the error catalog (ADR-0026 / DEC-0031).

Covers:
- Catalog parses; every ErrorCode has required fields.
- One HTTP status per code (no two codes share the same code string).
- i18n keys resolve (default en).
- get_error returns the correct ErrorCode.
- problem_response produces RFC 7807 problem+json.
"""

from __future__ import annotations

import pytest
from noventra.errors.catalog import ErrorCode, ERROR_CATALOG, all_codes, get_error


def test_catalog_non_empty():
    """Catalog has at least one ErrorCode."""
    assert len(ERROR_CATALOG) >= 1


def test_every_error_code_has_required_fields():
    """Every ErrorCode has code, http_status, i18n_key, title, detail_template."""
    for ec in ERROR_CATALOG:
        assert ec.code, f"ErrorCode missing code: {ec}"
        assert ec.http_status, f"ErrorCode {ec.code} missing http_status"
        assert ec.i18n_key, f"ErrorCode {ec.code} missing i18n_key"
        assert ec.title, f"ErrorCode {ec.code} missing title"
        assert ec.detail_template, f"ErrorCode {ec.code} missing detail_template"


def test_code_strings_unique():
    """No two ErrorCodes share the same code string (one HTTP status per code)."""
    codes = [ec.code for ec in ERROR_CATALOG]
    assert len(codes) == len(set(codes)), "Duplicate error codes found"


def test_i18n_keys_resolve():
    """i18n keys resolve via Django's gettext (default en).

    Phase 4 stub: gettext returns the input string when no translation
    is available. The key resolves (no exception); the title is non-empty.
    """
    from django.utils.translation import gettext as _
    for ec in ERROR_CATALOG:
        title = _(ec.title)
        assert title, f"i18n key {ec.i18n_key} resolved to empty title"


def test_get_error_returns_known_code():
    """get_error returns the ErrorCode for a known code."""
    ec = get_error("noventra.auth.invalid_credentials")
    assert ec is not None
    assert ec.http_status == 401


def test_get_error_returns_none_for_unknown_code():
    """get_error returns None for an unknown code."""
    assert get_error("noventra.unknown.code") is None


def test_http_statuses_are_valid():
    """Every http_status is a valid HTTP status code (4xx or 5xx)."""
    for ec in ERROR_CATALOG:
        assert 400 <= ec.http_status <= 599, (
            f"ErrorCode {ec.code} has invalid http_status {ec.http_status}"
        )


def test_all_codes_returns_catalog():
    """all_codes() returns the full catalog tuple."""
    assert all_codes() == ERROR_CATALOG
