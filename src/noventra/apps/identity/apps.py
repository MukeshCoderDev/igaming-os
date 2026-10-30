"""identity app configuration."""

from django.apps import AppConfig


class IdentityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "noventra.apps.identity"
    label = "identity"
    verbose_name = "Identity"
