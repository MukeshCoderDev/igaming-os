"""flags app configuration."""

from django.apps import AppConfig


class FlagsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "noventra.apps.flags"
    label = "flags"
    verbose_name = "Feature Flags"
