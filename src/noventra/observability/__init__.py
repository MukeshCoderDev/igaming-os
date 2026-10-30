"""Observability package — structured logging, metrics, tracing.

Per ADR-0025 / DEC-0030:
- structlog with JSON Lines output.
- Redaction at the logger boundary (PII + secrets).
- 1-in-100 sampling on /health/ and /metrics/.

Per ADR-0017 / DEC-0017 (observability scaffolding):
- Prometheus client + internal /metrics.
- OTel SDK with no-op exporter (vendor Q5-blocked, OPEN-DEPENDENT backend).
"""

from .logging import configure_logging, get_logger  # noqa: F401
from .redaction import RedactingProcessor  # noqa: F401
from .sampling import should_sample  # noqa: F401
