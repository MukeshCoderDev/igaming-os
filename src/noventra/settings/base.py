"""Base Django settings — shared across all environments.

Per ADR-0023 / DEC-0028:
- Required env vars are validated at import time via ``_require_env``.
- If any required var is missing, a named message is printed and
  ``sys.exit(1)`` is called BEFORE any database or network call.
- Secrets are read from environment variables only — never from files,
  never from defaults baked into code.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


# ─── Path setup ───────────────────────────────────────────────────────────
# src-layout: BASE_DIR is the repo root (parent of src/).
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


# ─── Named-var loud failure (DEC-0028 / ADR-0023) ────────────────────────
def _require_env(name: str) -> str:
    """Read a required env var. If missing, print named message and exit(1).

    This function MUST be called at settings import time, before any DB
    or network call. The loud failure ensures that misconfigured deploys
    fail fast rather than silently falling back to insecure defaults.
    """
    value = os.environ.get(name)
    if not value:
        # Named-var message: prints the exact missing var name.
        sys.stderr.write(
            f"NOVENTRA FATAL: required environment variable '{name}' is not set.\n"
            f"Set it in your environment or .env file. See .env.example and "
            f"docs/architecture/settings-split.md for the full list.\n"
        )
        sys.exit(1)
    return value


def _opt_env(name: str, default: str = "") -> str:
    """Read an optional env var with a default. Never exits."""
    return os.environ.get(name, default)


def _bool_env(name: str, default: bool = False) -> bool:
    """Read a boolean env var. Accepts true/false/1/0/yes/no (case-insensitive)."""
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw in ("true", "1", "yes", "on")


# ─── Required env vars (validated at import time) ────────────────────────
# Per DEC-0028, these MUST be present. The validation happens here, before
# any DB or network call. Missing any → named message + sys.exit(1).
SECRET_KEY = _require_env("SECRET_KEY")
DATABASE_URL = _require_env("DATABASE_URL")
REDIS_URL = _require_env("REDIS_URL")


# ─── Optional env vars with safe defaults ────────────────────────────────
DEBUG = _bool_env("DEBUG", default=False)
ALLOWED_HOSTS = [
    h.strip() for h in _opt_env("ALLOWED_HOSTS", "").split(",") if h.strip()
]
# If no ALLOWED_HOSTS, default to localhost for local dev; production must
# set this explicitly (check --deploy will flag it).
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]


# ─── Application definition ──────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "drf_spectacular",
    # Phase 3 app skeletons (per stage-02-handoff.md §3.1)
    "noventra.apps.core",
    "noventra.apps.tenancy",
    "noventra.apps.identity",
    "noventra.apps.audit",
    "noventra.apps.config",
    "noventra.apps.flags",
    "noventra.apps.telemetry",
    "noventra.apps.reliability",
    "noventra.apps.backups",
    "noventra.apps.webhooks",
    "noventra.apps.players",
    "noventra.apps.kyc",
    # Phase 11-16 modules (ledger, payments, fx have Django models)
    "noventra.modules.ledger",
    "noventra.modules.payments",
    "noventra.modules.fx",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    # Phase 4: correlation-ID middleware (ADR-0025). Always on; sets
    # X-Correlation-ID response header and propagates via contextvar.
    "noventra.middleware.correlation.CorrelationIdMiddleware",
    # Phase 6: AuthN middleware (ADR-0031). Verifies JWT; sets
    # request.jwt_claims + request.jwt_tenant_id. Runs BEFORE tenant
    # middleware so the tenant middleware can use the JWT claim.
    "noventra.middleware.authn.AuthNMiddleware",
    # Phase 5: tenant resolution middleware (ADR-0029/0033). JWT claim
    # primary, X-Tenant-ID header fallback. 400 on missing/malformed.
    "noventra.middleware.tenant.TenantResolutionMiddleware",
    # Phase 7: audit middleware (ADR-0035..0039). Emits audit events on
    # mutations + reads. Runs AFTER auth + tenant so it has full context.
    "noventra.middleware.audit.AuditMiddleware",
    # Phase 3: reliability middleware (idempotency, backpressure) wired in
    # later phases; the classes exist as stubs.
    # "noventra.apps.reliability.middleware.IdempotencyMiddleware",
    # Phase 3: telemetry middleware (OTel spans) wired in later phases.
    # "noventra.apps.telemetry.middleware.SpanMiddleware",
]

ROOT_URLCONF = "noventra.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
            ],
        },
    },
]

WSGI_APPLICATION = "noventra.wsgi.application"
ASGI_APPLICATION = "noventra.asgi.application"


# ─── Database ────────────────────────────────────────────────────────────
# DATABASE_URL is parsed here (not in db_url parsing lib, to keep deps
# minimal for Phase 3). Format: postgres://user:pass@host:port/dbname
def _parse_database_url(url: str) -> dict:
    """Parse a postgres:// URL into Django DATABASES dict."""
    from urllib.parse import urlparse

    parsed = urlparse(url)
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": parsed.path.lstrip("/"),
        "USER": parsed.username or "",
        "PASSWORD": parsed.password or "",
        "HOST": parsed.hostname or "localhost",
        "PORT": str(parsed.port or 5432),
        # Conn health: pgbouncer-friendly defaults (Phase 3 sets the stage
        # for PgBouncer per stage-02-handoff.md §3.2 / Q30).
        "CONN_HEALTH_CHECKS": True,
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            # Connect as noventra_app by default; the role is set in
            # deploy/docker/init/01-roles.sql. RLS policies use
            # app.tenant_uuid() (set per-request via SET LOCAL).
            "options": "-c search_path=public,app",
        },
    }


DATABASES = {
    "default": _parse_database_url(DATABASE_URL),
}

# Phase 5 (ADR-0030 / DEC-0035): pgbouncer compatibility.
# ATOMIC_REQUESTS=True: every request is a single transaction (no implicit
# multi-statement). Required for pgbouncer transaction-mode.
# prepare_threshold=None: disables prepared statements (pgbouncer incompat).
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASES["default"]["OPTIONS"]["prepare_threshold"] = None


# ─── Redis (for idempotency store, cache, etc.) ──────────────────────────
# REDIS_URL is required (validated above). The actual Redis client is
# instantiated lazily by the reliability and cache subsystems.
REDIS = {
    "URL": REDIS_URL,
}


# ─── Internationalization ────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# ─── Static files ────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"


# ─── Default primary key field type ──────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ─── REST Framework ──────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        # Phase 3 stub: throttle classes wired in Phase 4.
    ],
    "DEFAULT_THROTTLE_RATES": {
        # Phase 3 stub: rate limits wired in Phase 4 per Pain-REQ-0008.
        "anon": "100/min",
        "user": "1000/min",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Noventra Platform API",
    "DESCRIPTION": "B2B OS provider platform — Phase 3 skeleton. "
                   "See docs/BLUEPRINT.md for the full architecture.",
    "VERSION": "0.3.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}


# ─── Security (production hardening) ─────────────────────────────────────
# These are checked by `manage.py check --deploy`. In production, set:
#   SECURE_SSL_REDIRECT=True
#   SESSION_COOKIE_SECURE=True
#   CSRF_COOKIE_SECURE=True
#   SECURE_HSTS_SECONDS=31536000
#   SECURE_HSTS_INCLUDE_SUBDOMAINS=True
#   SECURE_HSTS_PRELOAD=True
#   SECURE_CONTENT_TYPE_NOSNIFF=True
#   SECURE_BROWSER_XSS_FILTER=True
# Phase 3 leaves these as defaults; production settings override.
SECURE_SSL_REDIRECT = _bool_env("SECURE_SSL_REDIRECT", default=False)
SESSION_COOKIE_SECURE = _bool_env("SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = _bool_env("CSRF_COOKIE_SECURE", default=False)
SECURE_HSTS_SECONDS = int(_opt_env("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = _bool_env("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)
SECURE_HSTS_PRELOAD = _bool_env("SECURE_HSTS_PRELOAD", default=False)
SECURE_CONTENT_TYPE_NOSNIFF = _bool_env("SECURE_CONTENT_TYPE_NOSNIFF", default=False)
SECURE_BROWSER_XSS_FILTER = _bool_env("SECURE_BROWSER_XSS_FILTER", default=False)
X_FRAME_OPTIONS = _opt_env("X_FRAME_OPTIONS", "DENY")


# ─── Logging ─────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "noventra": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
    },
}
