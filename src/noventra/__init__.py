"""Noventra platform — root package.

Phase 3 skeleton. Per DEC-0027 / ADR-0022, this is a src-layout Django
project. Per DEC-0028 / ADR-0023, settings are split across
``noventra.settings.{base,local,test,production}`` and required env vars
are validated at import time with named-var loud failure.
"""

__version__ = "0.3.0"
