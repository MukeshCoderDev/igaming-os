# ADR Citation Convention

| Field | Value |
|---|---|
| Authority | ADR-0027 v2 (Phase 10 close); enforced by check_traceability.sh Rule 17 |
| Owner | QA Owner |
| Created | 2026-10-28 |
| Last-Reviewed | 2026-10-28 |

## Token Format

Code that implements a specific architectural decision must cite it using
the token `# ADR-00XX` (zero-padded to 4 digits).

**Examples (valid):**
- `# ADR-0001` (modular monolith / stack)
- `# ADR-0002` (tenancy / RLS)
- `# ADR-0035` (hash-chain architecture)

**Examples (invalid):**
- `# ADR-1` (not zero-padded)
- `# adr:0001` (wrong format)
- `# ADR-0001:` (trailing colon — not part of token)

## Multiple ADRs in One File

If a file implements decisions from multiple ADRs, list each on a
separate line in the file's top-of-file comment block:

```
# Implements: ADR-0001 (stack), ADR-0002 (RLS), ADR-0035 (hash chain)
```

Or use multiple inline comments at the relevant code locations.

## Placement Rules

- **Module-wide decisions:** Top-of-file comment block OR module
  docstring. Example:
  ```python
  # Implements ADR-0002 (Tenancy & RLS architecture)
  # Implements ADR-0029 (Tenant resolution middleware)
  """Tenant middleware module."""
  ```

- **Class-level decisions:** Inline comment immediately preceding the
  class definition. Example:
  ```python
  # ADR-0035: hash-chain audit event
  class AuditEvent(models.Model):
  ```

- **Function-level decisions:** Inline comment immediately preceding
  the function definition.

## Allowlist (Exempt from Rule 17)

The following paths are exempt from linter rule 17 (ADR citation check):

- `migrations/` (Django migrations — auto-generated, no ADRs)
- `tests/` (test code — tests verify ADRs, don't implement them)
- `manage.py` (Django entry point)
- `settings/` (configuration — ADRs are cited in settings-split.md,
  not in code)
- `deploy/` (deployment scripts)
- `__init__.py` (empty package markers)
- Generated code: `docs/api/openapi.yaml` (drf-spectacular-generated)

## Supersession Handling

When an ADR is SUPERSEDED:
- Citations to the old ADR should be updated to the new ADR in the same
  PR that supersedes the ADR.
- The linter does not auto-flag citations to SUPERSEDED ADRs (they are
  still valid historical references) but a warning is emitted.

## Linter Integration

Enforced by `scripts/check_traceability.sh` Rule 17:
- **Regex:** `# ADR-\d{4}` (4-digit zero-padded)
- **Scope:** `src/` (excluding allowlist)
- **Failure mode:** any `# ADR-0XXX` token that does not resolve to an
  existing ADR with status ACCEPTED fails CI.
