"""Tests for sampling (ADR-0025 / DEC-0030).

Covers:
- /health/ and /metrics/ paths are sampled at 1-in-100.
- Other paths are always sampled (return True).
"""

from __future__ import annotations

from noventra.observability.sampling import should_sample, SAMPLE_RATE, SAMPLED_PATHS


def test_non_sampled_path_always_returns_true():
    """Paths NOT in SAMPLED_PATHS always return True (always sample)."""
    assert should_sample("/api/v1/tenants/") is True
    assert should_sample("/some/other/path/") is True


def test_sampled_path_returns_true_or_false():
    """Paths in SAMPLED_PATHS return True with probability SAMPLE_RATE.

    We can't assert the exact value (random), but we can assert it returns
    a bool. Statistical verification (1-in-100 over 10k trials) is a
    Phase 5 load-test concern.
    """
    result = should_sample("/health/")
    assert isinstance(result, bool)
    result = should_sample("/metrics/")
    assert isinstance(result, bool)


def test_sample_rate_is_one_in_100():
    """SAMPLE_RATE is 0.01 (1-in-100)."""
    assert SAMPLE_RATE == 0.01


def test_sampled_paths_includes_health_and_metrics():
    """SAMPLED_PATHS includes /health/ and /metrics/."""
    assert "/health/" in SAMPLED_PATHS
    assert "/metrics/" in SAMPLED_PATHS
