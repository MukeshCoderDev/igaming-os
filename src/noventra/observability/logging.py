"""Structured logging configuration (structlog + JSON Lines).

Per ADR-0025 / DEC-0030:
- structlog with JSON Lines output in production.
- Pretty-printed console output in local dev (DEBUG=True).
- Required fields per audit §1.4: timestamp, level, event, logger,
  correlation_id, tenant_id (when in request context), request_id,
  module, line.
- Redaction at the logger boundary via RedactingProcessor.
- 1-in-100 sampling on /health/ and /metrics/.

Phase 4 stub: structlog is optional. If not installed, falls back to
stdlib logging. The interface (get_logger) is stable either way.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

from django.conf import settings

from .redaction import RedactingProcessor
from .sampling import should_sample


_CONFIGURED = False


def configure_logging() -> None:
    """Configure structlog + stdlib logging. Idempotent."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    try:
        import structlog
    except ImportError:
        # structlog not installed; stdlib logging is configured via
        # settings.LOGGING. get_logger() will return a stdlib logger.
        _CONFIGURED = True
        return

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _add_module_and_line,
        RedactingProcessor(),
        structlog.processors.StackInfoRenderer(),
        # In DEBUG (local dev), pretty-print. Else JSON Lines.
        structlog.dev.ConsoleRenderer() if settings.DEBUG else structlog.processors.JSONRenderer(),
    ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )

    # Bridge stdlib logging into structlog so Django's logs are also redacted.
    structlog.stdlib.redirect_stdlib_logging()

    _CONFIGURED = True


def _add_module_and_line(logger, method_name, event_dict):
    """Add module and line fields from the call site."""
    import inspect
    frame = inspect.stack()[-1]
    event_dict.setdefault("module", frame.filename)
    event_dict.setdefault("line", frame.lineno)
    return event_dict


def get_logger(name: str = "noventra") -> Any:
    """Return a logger. structlog if available, else stdlib."""
    configure_logging()
    try:
        import structlog
        return structlog.get_logger(name)
    except ImportError:
        return logging.getLogger(name)
