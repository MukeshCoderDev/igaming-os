# Settings Split — Required Variables & Default Allow-list

| Field | Value |
|---|---|
| Document | `docs/architecture/settings-split.md` |
| Version | 5.4 (Phase 3) |
| Status | Approved |
| Owner | Architecture Lead |
| Authority | DEC-0028 / ADR-0023 |
| Linter | `scripts/check_traceability.sh` rule 13 enforces env coverage |

This document defines the settings-split scheme, the required
environment variables, the default allow-list, and the named-var loud
failure semantics. Per DEC-0028 / ADR-0023, every required variable
must be present at settings import time; if any is missing, a named
message is printed and `sys.exit(1)` is called BEFORE any database
or network call.

## 1. Settings split

The settings module is split across four files per ADR-0023:

| File | Purpose | DEBUG | Used by |
|---|---|---|---|
| `src/noventra/settings/base.py` | Shared base. Defines required vars, validates them, sets safe defaults. | env-controlled | All environments. |
| `src/noventra/settings/local.py` | Local dev. Permits DEBUG=True, broadens ALLOWED_HOSTS. | True (default) | Developers. |
| `src/noventra/settings/test.py` | Test runner. DEBUG=False, MD5 hasher, throttling disabled. | False | CI + local pytest. |
| `src/noventra/settings/production.py` | Production. Enforces HSTS, secure cookies, SSL redirect. | False | Production deploys. |

The active settings module is selected via `DJANGO_SETTINGS_MODULE`
env var. Defaults: `noventra.settings.local` for dev (manage.py),
`noventra.settings.production` for WSGI/ASGI entrypoints.

## 2. Required environment variables

These variables are **required**. Per DEC-0028, they are validated at
import time in `base.py` via the `_require_env()` helper. Missing any
→ named message + `sys.exit(1)` before any DB/network call.

The linter (rule 13) verifies that every variable in this table
appears in `.env.example`.

| Variable | Purpose | Example | Validated by |
|---|---|---|---|
| `SECRET_KEY` | Django secret key (session signing, CSRF). Generate with `django.core.management.utils.get_random_secret_key()`. | `django-insecure-...` | `base.py` `_require_env("SECRET_KEY")` |
| `DATABASE_URL` | PostgreSQL connection URL. Format: `postgres://user:pass@host:port/dbname`. | `postgres://noventra_dev:...@localhost:5432/noventra` | `base.py` `_require_env("DATABASE_URL")` |
| `REDIS_URL` | Redis connection URL. Used for idempotency store, cache, Celery broker. | `redis://localhost:6379/0` | `base.py` `_require_env("REDIS_URL")` |

## 3. Optional environment variables (with safe defaults)

These variables are optional. They are read via `_opt_env()` or
`_bool_env()` with safe defaults. Production deploys should set them
explicitly; `manage.py check --deploy` will flag unsafe defaults.

| Variable | Default | Purpose |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | `noventra.settings.local` (manage.py) / `noventra.settings.production` (wsgi/asgi) | Selects the active settings module. |
| `DEBUG` | `False` | Django debug mode. NEVER set to true in production. |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,0.0.0.0` | Comma-separated list of allowed host headers. |
| `SECURE_SSL_REDIRECT` | `False` | Redirect HTTP to HTTPS. Production: `True`. |
| `SESSION_COOKIE_SECURE` | `False` | Mark session cookies as secure (HTTPS only). Production: `True`. |
| `CSRF_COOKIE_SECURE` | `False` | Mark CSRF cookies as secure. Production: `True`. |
| `SECURE_HSTS_SECONDS` | `0` | HSTS max-age in seconds. Production: `31536000` (1 year). |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | `False` | HSTS includes subdomains. Production: `True`. |
| `SECURE_HSTS_PRELOAD` | `False` | HSTS preload list. Production: `True`. |
| `SECURE_CONTENT_TYPE_NOSNIFF` | `False` | X-Content-Type-Options: nosniff. Production: `True`. |
| `SECURE_BROWSER_XSS_FILTER` | `False` | X-XSS-Protection. Production: `True`. |
| `X_FRAME_OPTIONS` | `DENY` | X-Frame-Options header. Prevents clickjacking. |

## 4. Named-var loud failure semantics

Per DEC-0028 / ADR-0023, when a required env var is missing:

1. The `_require_env()` function in `base.py` is called at import time.
2. It checks `os.environ.get(name)`.
3. If the value is falsy (empty string or None), it writes to stderr:
   ```
   NOVENTRA FATAL: required environment variable 'SECRET_KEY' is not set.
   Set it in your environment or .env file. See .env.example and
   docs/architecture/settings-split.md for the full list.
   ```
4. It calls `sys.exit(1)`.
5. This happens BEFORE any database connection or network call.

The named message ensures the operator knows exactly which variable is
missing. The non-zero exit ensures the process does not continue with
insecure defaults.

### 4.1 Verification

The loud-failure behavior is verified by:

1. **Manual test**: `unset SECRET_KEY && python manage.py check` →
   exits 1 with the named message.
2. **CI test** (Phase 4+): a dedicated test case that unsets each
   required var and asserts the named message + exit code.
3. **Production deploy check**: the orchestrator (k8s, ECS) must
   inject all required vars; if any is missing, the pod fails to
   start with the named message in its logs.

## 5. Default allow-list

The "default allow-list" is the set of variables that have safe
defaults in `base.py` and therefore do not need to be set explicitly.
Variables NOT in the allow-list (i.e., required) MUST be set.

### 5.1 Required (no default; missing → exit 1)

- `SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`

### 5.2 Allow-listed (optional; safe defaults)

- `DJANGO_SETTINGS_MODULE`
- `DEBUG`
- `ALLOWED_HOSTS`
- `SECURE_SSL_REDIRECT`
- `SESSION_COOKIE_SECURE`
- `CSRF_COOKIE_SECURE`
- `SECURE_HSTS_SECONDS`
- `SECURE_HSTS_INCLUDE_SUBDOMAINS`
- `SECURE_HSTS_PRELOAD`
- `SECURE_CONTENT_TYPE_NOSNIFF`
- `SECURE_BROWSER_XSS_FILTER`
- `X_FRAME_OPTIONS`

### 5.3 Docker-compose vars (used by docker-compose.yml)

These are used by `docker-compose.yml` to configure the Postgres and
Redis containers. They are NOT required by Django settings directly
(Django reads `DATABASE_URL` and `REDIS_URL`, which are constructed
from these in the compose file).

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_PORT`
- `REDIS_PORT`
- `APP_PORT`

## 6. Secrets strategy

Per DEC-0028, secrets are read from environment variables ONLY. They
are NEVER:

- Committed to the repository (`.env` is in `.gitignore`).
- Baked into Docker images (passed via env at runtime).
- Stored in Django settings defaults.
- Logged (the health endpoint explicitly excludes secrets from its
  response body; see `src/noventra/api/health.py`).

The secret management strategy per environment:

| Environment | Secret source |
|---|---|
| Local dev | `.env` file (gitignored); copied from `.env.example`. |
| CI | GitHub Actions secrets; injected as env vars in `ci.yml`. |
| Production | Orchestrator secrets (k8s secrets, AWS Secrets Manager, etc.); injected as env vars at pod startup. |

## 7. Cross-references

- ADR-0023: `docs/adr/ADR-0023.md`
- DEC-0028: `docs/requirements/traceability.md` §C
- Settings code: `src/noventra/settings/base.py`
- `.env.example`: repository root
- Health endpoint (no-secrets guarantee): `src/noventra/api/health.py`
- Linter rule 13: `scripts/check_traceability.sh`
