"""telemetry app configuration."""

from django.apps import AppConfig


class TelemetryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "noventra.apps.telemetry"
    label = "telemetry"
    verbose_name = "Telemetry"
