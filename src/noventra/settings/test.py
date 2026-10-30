"""Test settings.

Inherits from base. Uses an ephemeral Postgres DB (CI provides one via
docker-compose). DEBUG=False. Throttling disabled. In-memory cache.
"""

from .base import *  # noqa: F401,F403

DEBUG = False

# Test: allow all hosts (test client uses whatever).
ALLOWED_HOSTS = ["*"]

# Test: disable throttling so tests aren't rate-limited.
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": None,
    "user": None,
}

# Test: use a faster password hasher.
PASSWORD_HASHERS = [  # noqa: F405
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
