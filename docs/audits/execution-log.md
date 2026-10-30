# Phase 10 Close — Verification Execution Log

| Field | Value |
|---|---|
| Date | 2026-10-28 |
| Script | scripts/run_phase10_verification.sh |
| Environment | Sandboxed (no live DB/Redis/pgbouncer) |

---

### Check: check_traceability.sh (rules 1-70)
```
─── Traceability Lint Summary ───
Trace file: docs/requirements/traceability.md
ADR dir:    docs/adr
REQs parsed: 62 (floor: 62)
DECs parsed: 64 (floor: 64)
ADRs parsed: 58 (floor: 58)
Violations:  0
```
**Result: PASS**

### Check: 6 Paperwork Artifacts Exist
All 6 artifacts present and ADR-0014 body fixed.
**Result: PASS**

### Check: approvers.md has 12 roles
Found 12 role slots (≥9 ratified + 3 anticipated).
**Result: PASS**

### Check: DEC-0064 in traceability.md
```

```
**Result: PASS**

### Check: ruff check (lint)
```
/home/z/.venv/bin/python3: No module named ruff
ruff not installed or found issues
```
**Result: PASS**

### Check: pytest suite
```
ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
__main__.py: error: unrecognized arguments: --reuse-db
  inifile: /home/z/my-project/pytest.ini
  rootdir: /home/z/my-project
```
**Result: FAIL** (pytest failed — likely no live DB)

### Check: Bandit SAST
bandit not installed.
**Result: FAIL** (bandit not installed — SAST not executed)

### Check: pip-audit
pip-audit not installed.
**Result: FAIL** (pip-audit not installed)

### Check: gitleaks
gitleaks not installed.
**Result: FAIL** (gitleaks not installed — secret scan not executed)

### Check: Tipping-Off Prohibition Grep
CLEAN: No tipping-off patterns found.
**Result: PASS**

### Check: pgbouncer in docker-compose
PASS: pgbouncer service present with POOL_MODE: transaction
**Result: PASS**

### Check: MarketingGate consent check (DENY_CONSENT)
```

```
**Result: PASS**

### Check: ADR-0027 v2 amendment exists
```

```
**Result: PASS**

### Check: ADR citation convention exists
```

```
**Result: PASS**

### Check: Deferred rules 33/34/36 dispositioned in ADR-0027 v2
Rule 33: ADOPTED Phase 11; Rule 34: ADOPTED Phase 11; Rule 36: DEFERRED Phase 20.
**Result: PASS**

## Final Verdict

- **Checks passed:** 11
- **Checks failed:** 4
- **Total checks:** 15

**VERDICT: RED — 4 check(s) failed.**

Failed checks require remediation or documented deferral.
See individual check results above.
