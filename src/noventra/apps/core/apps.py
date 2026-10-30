"""core app configuration."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "noventra.apps.core"
    label = "core"
    verbose_name = "Core (platform baseline)"
