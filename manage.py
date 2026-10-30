#!/usr/bin/env python
"""Django management entrypoint.

Per ADR-0022, the default settings module is noventra.settings.local for
dev. Production overrides via DJANGO_SETTINGS_MODULE env var.
"""

import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "noventra.settings.local")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you in the right venv? "
            "Run 'pip install -e .[dev]' first."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
