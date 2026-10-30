"""Production settings.

Inherits from base. Enforces production hardening. Per ADR-0023, all
required env vars are validated in base.py before this module even loads.
"""

from .base import *  # noqa: F401,F403
from .base import _bool_env, _opt_env

# Production: DEBUG must be False.
DEBUG = False

# Production: SECURE_SSL_REDIRECT must be True (enforced by check --deploy).
SECURE_SSL_REDIRECT = _bool_env("SECURE_SSL_REDIRECT", default=True)

# Production: cookies must be secure.
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Production: HSTS.
SECURE_HSTS_SECONDS = int(_opt_env("SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# Production: ALLOWED_HOSTS must be set explicitly (no wildcards).
# base.py already requires this; check --deploy will flag wildcards.
