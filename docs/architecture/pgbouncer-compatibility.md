# pgbouncer Compatibility — Constraints & Patterns

| Field | Value |
|---|---|
| Document | `docs/architecture/pgbouncer-compatibility.md` |
| Version | 5.6 (Phase 5) |
| Status | Approved |
| Owner | Infrastructure Lead |
| Authority | ADR-0030 / DEC-0035 |

This document records the constraints and patterns required for
pgbouncer compatibility in transaction-mode. Per ADR-0030, the
platform uses pgbouncer in transaction-mode for connection pooling
(R-SCL-02 risk; Q30 selection). Transaction-mode breaks session-
level features; the Django app must use only transaction-safe
patterns.

## 1. pgbouncer configuration

The pgbouncer container is defined in `docker-compose.yml`:

| Setting | Value | Rationale |
|---|---|---|
| `POOL_MODE` | `transaction` | Connections are returned to the pool after each transaction, not each session. Maximizes pooling. |
| `MAX_CLIENT_CONN` | `200` | Max client connections to pgbouncer. |
| `DEFAULT_POOL_SIZE` | `20` | Max backend (Postgres) connections per database/user pair. |
| `ADMIN_USERS` | `noventra_dev` | Admin user for pgbouncer admin console (`SHOW POOLS`, etc.). |

## 2. Application constraints

### 2.1 SET LOCAL only (no bare SET)

pgbouncer in transaction-mode assigns a different backend connection
per transaction. A bare `SET` (without `LOCAL`) persists for the
session and leaks to subsequent transactions on the same backend.

**✅ Allowed:**
```python
cursor.execute("SET LOCAL app.tenant_uuid = %s", [str(tenant_uuid)])
```

**❌ Forbidden:**
```python
cursor.execute("SET app.tenant_uuid = %s", [str(tenant_uuid)])  # leaks!
```

The tenant middleware (`src/noventra/middleware/tenant.py`) uses
`SET LOCAL` exclusively. Per ADR-0030, this is the only pattern.

### 2.2 No session cursors

Session cursors (declared with `DECLARE CURSOR` without `WITH HOLD`)
persist across transactions. pgbouncer breaks this. Use server-side
cursors only within a single transaction, or use client-side
pagination (Django's `Paginator`).

**✅ Allowed:**
```python
# Django ORM: uses client-side pagination by default.
for obj in Model.objects.all().iterator(chunk_size=100):
    ...
```

**❌ Forbidden:**
```python
cursor.execute("DECLARE my_cursor CURSOR FOR SELECT ...")  # session-level
```

### 2.3 ATOMIC_REQUESTS=True or explicit atomic blocks

Per ADR-0030, `ATOMIC_REQUESTS=True` is set in `settings/base.py`.
Every request is a single transaction. This ensures `SET LOCAL`
persists for the entire request and is cleaned up at the end.

For background tasks (Celery), use explicit `with transaction.atomic():`
blocks. Never rely on implicit multi-statement transactions.

**✅ Allowed:**
```python
# ATOMIC_REQUESTS handles the request.
# For background tasks:
from django.db import transaction
with transaction.atomic():
    ...
```

**❌ Forbidden:**
```python
# Implicit multi-statement transaction (no atomic block).
cursor.execute("INSERT ...")
cursor.execute("UPDATE ...")  # may land on different backend
```

### 2.4 prepare_threshold=None

psycopg3 caches prepared statements by default. pgbouncer in
transaction-mode can't track prepared statements across backends.
Set `prepare_threshold=None` to disable.

This is set in `settings/base.py`:
```python
DATABASES["default"]["OPTIONS"]["prepare_threshold"] = None
```

### 2.5 No LISTEN/NOTIFY

LISTEN/NOTIFY is session-level and incompatible with pgbouncer
transaction-mode. Use Redis pub/sub or Celery for inter-process
messaging.

### 2.6 No advisory locks

Session-level advisory locks (`pg_advisory_lock`) persist across
transactions and are incompatible. Transaction-level advisory locks
(`pg_advisory_xact_lock`) are OK within an atomic block.

## 3. Testing pgbouncer compatibility

The test suite includes a pgbouncer compatibility test
(`tests/test_pgbouncer.py`) that verifies:

1. **Read**: a SELECT under pgbouncer returns expected rows.
2. **Write**: an INSERT under pgbouncer persists.
3. **Rollback**: a transaction that rolls back leaves no side effects.
4. **Recycle**: a connection recycled between transactions still has
   the correct RLS context (SET LOCAL doesn't leak).

The test runs against the local docker-compose stack (postgres +
pgbouncer). CI runs the same test against a pgbouncer service.

## 4. Cross-references

- ADR-0030: `docs/adr/ADR-0030.md`
- DEC-0035: `docs/requirements/traceability.md` §C
- Tenant middleware (SET LOCAL): `src/noventra/middleware/tenant.py`
- Settings (ATOMIC_REQUESTS, prepare_threshold): `src/noventra/settings/base.py`
- docker-compose.yml (pgbouncer service): repo root
- Linter rule 24: `scripts/check_traceability.sh`
