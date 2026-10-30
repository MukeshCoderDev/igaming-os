"""fx app configuration."""

from django.apps import AppConfig


class FxConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "noventra.modules.fx"
    label = "fx"
    verbose_name = "FX (foreign exchange rates)"
