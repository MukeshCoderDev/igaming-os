"""Errors package — RFC 7807 problem+json + catalog + handlers.

Per ADR-0026 / DEC-0031:
- RFC 7807 problem+json.
- Catalog in catalog.py.
- One HTTP status per code.
- i18n-key messages (default en).
- correlation_id always included.
- Stack traces in logs only, never in response bodies (traces field dev-only).
"""

from .catalog import ErrorCode, get_error  # noqa: F401
from .handlers import problem_response  # noqa: F401
