"""Local development settings.

Inherits from base. Permits DEBUG=True, broadens ALLOWED_HOSTS, enables
Django debug toolbar (if installed). Never use in production.
"""

from .base import *  # noqa: F401,F403
from .base import _bool_env, _opt_env

DEBUG = _bool_env("DEBUG", default=True)

# Local dev: allow all hosts. check --deploy will flag this; that's expected.
ALLOWED_HOSTS = ["*"]

# Local dev: disable SSL redirect so HTTP works.
SECURE_SSL_REDIRECT = False

# Local dev: relaxed throttling for development.
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "10000/min",
    "user": "100000/min",
}
