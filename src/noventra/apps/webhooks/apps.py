"""webhooks app configuration."""

from django.apps import AppConfig


class WebhooksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "noventra.apps.webhooks"
    label = "webhooks"
    verbose_name = "Webhooks"
