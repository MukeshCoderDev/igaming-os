"""config app configuration."""

from django.apps import AppConfig


class ConfigConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "noventra.apps.config"
    label = "config"
    verbose_name = "Configuration"
