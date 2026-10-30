"""OpenTelemetry SDK scaffolding (no-op exporter).

Per ADR-0017 / DEC-0017: OTel SDK with no-op exporter. Vendor Q5-
blocked (ASSUMED scaffolding; OPEN-DEPENDENT backend).

Phase 4 stub: configures the OTel SDK with a no-op (ConsoleSpanExporter
or NoneExporter) so that the code paths are exercised. Phase 5+ swaps
in a real exporter once the vendor question (Q39) is resolved.
"""

from __future__ import annotations

_CONFIGURED = False


def configure_otel() -> None:
    """Configure the OTel SDK with a no-op exporter. Idempotent."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        # No-op exporter: spans are dropped. Real exporter lands in Phase 5+
        # pending Q39 (OTel backend vendor selection).
        provider = TracerProvider()
        trace.set_tracer_provider(provider)
    except ImportError:
        # OTel SDK not installed; no-op. Code paths that call
        # trace.get_tracer() will get a no-op tracer from the API package.
        pass
    _CONFIGURED = True


def get_tracer(name: str = "noventra"):
    """Return a tracer. Real if OTel SDK is installed; no-op otherwise."""
    configure_otel()
    try:
        from opentelemetry import trace
        return trace.get_tracer(name)
    except ImportError:
        return None
