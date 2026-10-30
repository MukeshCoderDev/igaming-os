"""Sampling for high-volume endpoints.

Per ADR-0025 / DEC-0030: 1-in-100 sampling on /health/ and /metrics/.
"""

from __future__ import annotations

import random

# Endpoints sampled at 1-in-100. Path prefixes; matches startswith.
SAMPLED_PATHS = ("/health/", "/metrics/")

# Sampling rate: 1-in-100 = 0.01.
SAMPLE_RATE = 0.01


def should_sample(path: str) -> bool:
    """Return True if a log line for this path should be sampled.

    For sampled paths (/health/, /metrics/), returns True with probability
    SAMPLE_RATE (default 0.01 = 1-in-100). For all other paths, returns
    True (always sample — non-sampled endpoints aren't noisy).
    """
    if not any(path.startswith(p) for p in SAMPLED_PATHS):
        return True
    return random.random() < SAMPLE_RATE
