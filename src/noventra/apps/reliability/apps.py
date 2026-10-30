"""reliability app configuration."""

from django.apps import AppConfig


class ReliabilityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "noventra.apps.reliability"
    label = "reliability"
    verbose_name = "Reliability"
