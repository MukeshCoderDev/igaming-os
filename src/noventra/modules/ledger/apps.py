"""ledger app configuration."""

from django.apps import AppConfig


class LedgerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "noventra.modules.ledger"
    label = "ledger"
    verbose_name = "Ledger (financial core)"
