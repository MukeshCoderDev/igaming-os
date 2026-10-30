"""payments app configuration."""

from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "noventra.modules.payments"
    label = "payments"
    verbose_name = "Payments (PSP, webhooks, disputes)"
