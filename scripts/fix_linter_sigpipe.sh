#!/usr/bin/env bash
# fix_linter_sigpipe.sh — Eliminate non-deterministic SIGPIPE+pipefail flakiness
# in check_traceability.sh.
#
# Root cause: `printf '%s' "$big_var" | grep -qF "needle"` patterns fail
# intermittently because:
#   1. `set -uo pipefail` is active.
#   2. When grep finds a match and exits, printf receives SIGPIPE on its
#      next write and dies with exit code 141.
#   3. pipefail reports the rightmost non-zero exit (141), so the pipe
#      returns 141 instead of 0.
#   4. `if !` inverts 141 → 0, executing the FAIL branch — false positive.
#
# The probability of triggering depends on input size, grep speed, and OS
# scheduling — non-deterministic by design.
#
# Fix strategy: replace every `printf '%s' "$var" | grep ...` with a
# here-string `grep ... <<<"$var"` (no pipe → no SIGPIPE → deterministic).
# Also fix the multi-printf-on-one-line bug at line 495.

set -euo pipefail

LINTER="/home/z/my-project/scripts/check_traceability.sh"

# Verify backup exists.
cp "$LINTER" "$LINTER.bak.$(date +%s)"

# Apply fixes via Python for atomicity and precision.
python3 <<'PYEOF'
import re
from pathlib import Path

p = Path("/home/z/my-project/scripts/check_traceability.sh")
src = p.read_text()

# ─── Fix 1: line 495 multi-printf-on-one-line ─────────────────────────────
# Before:  printf 'DEC-0091\tADR-0091\n'    printf 'DEC-0093\tADR-0092\n'    printf 'DEC-0094\tADR-0093\n'    printf 'DEC-0095\tADR-0094\n'
# After:   one printf per line.
old_line_495 = "    printf 'DEC-0091\\tADR-0091\\n'    printf 'DEC-0093\\tADR-0092\\n'    printf 'DEC-0094\\tADR-0093\\n'    printf 'DEC-0095\\tADR-0094\\n'"
new_line_495 = """    printf 'DEC-0091\\tADR-0091\\n'
    printf 'DEC-0093\\tADR-0092\\n'
    printf 'DEC-0094\\tADR-0093\\n'
    printf 'DEC-0095\\tADR-0094\\n'"""
assert old_line_495 in src, "line 495 pattern not found"
src = src.replace(old_line_495, new_line_495)

# ─── Fix 2: SIGPIPE-prone `printf '%s' "$var" | grep` patterns ────────────
# Replace with here-string `grep ... <<<"$var"`.
# Patterns to fix (preserving grep flags):
#   printf '%s' "$X"     | grep -qF "$Y"   →   grep -qF -- "$Y"    <<<"$X"
#   printf '%s' "$X"     | grep -qE "$RE"  →   grep -qE -- "$RE"   <<<"$X"
#   printf '%s\n' "$X"   | grep -qE "$RE"  →   grep -qE -- "$RE"   <<<"$X"
#   printf '%s\n' "$X"   | grep -qx "$RE"  →   grep -qx -- "$RE"   <<<"$X"
#   printf '%s\n' "$X"   | grep -c '^DEC:' →   grep -c -- '^DEC:'  <<<"$X"
#   printf '%s' "$X"     | grep -oE 'ADR-...' | wc -l  →  use grep -c
#   printf '%s' "$X"     | grep -oE 'ADR-...' | head -1  →  use awk
# Note: here-string `<<<` adds a trailing newline, equivalent to `printf '%s\n'`.
# For checks that don't care about trailing newline, this is safe.

# Pattern A: `if ! printf '%s' "$X" | grep -qF "$Y"; then` → `if ! grep -qF -- "$Y" <<<"$X"; then`
src = re.sub(
    r"if ! printf '%s' \"\$([a-z_]+)\" \| grep -qF \"\$([a-z_]+)\"; then",
    r'if ! grep -qF -- "$\2" <<<"$\1"; then',
    src,
)
src = re.sub(
    r"if ! printf '%s' \"\$([a-z_]+)\" \| grep -qE \"\^(\S+)\"; then",
    r'if ! grep -qE -- "^\2" <<<"$\1"; then',
    src,
)

# Pattern B: `if ! printf '%s\n' "$X" | grep -qE "^${key}:"; then`
src = src.replace(
    'if ! printf \'%s\\n\' "$fm_text" | grep -qE "^${key}:"; then',
    'if ! grep -qE -- "^${key}:" <<<"$fm_text"; then',
)

# Pattern C: `if ! printf '%s' "$body_text" | grep -qE "^## ${sec}$"; then`
src = src.replace(
    'if ! printf \'%s\' "$body_text" | grep -qE "^## ${sec}\\$"; then',
    'if ! grep -qE -- "^## ${sec}$" <<<"$body_text"; then',
)

# Pattern D: `if ! printf '%s\n' "$dec_ids_in_table" | grep -qx "$dec_cited"; then`
src = src.replace(
    'if ! printf \'%s\\n\' "$dec_ids_in_table" | grep -qx "$dec_cited"; then',
    'if ! grep -qx -- "$dec_cited" <<<"$dec_ids_in_table"; then',
)

# Pattern E: `if ! printf '%s' "$dec_value" | grep -qE '^DEC-[0-9]{4}$'; then`
src = src.replace(
    "if ! printf '%s' \"$dec_value\" | grep -qE '^DEC-[0-9]{4}$'; then",
    'if ! grep -qE -- \'^DEC-[0-9]{4}$\' <<<"$dec_value"; then',
)

# Pattern F: `dec_line_count=$(printf '%s\n' "$dec_lines" | grep -c '^DEC:' || true)`
src = src.replace(
    "dec_line_count=$(printf '%s\\n' \"$dec_lines\" | grep -c '^DEC:' || true)",
    "dec_line_count=$(grep -c -- '^DEC:' <<<\"$dec_lines\" || true)",
)

# Pattern G: adr_token_count - replace pipe chain with awk for determinism
src = src.replace(
    'adr_token_count=$(printf \'%s\' "$adr" | grep -oE \'ADR-[0-9]{4}\' | wc -l | tr -d \' \')',
    "adr_token_count=$(awk -v s=\"$adr\" 'BEGIN{c=0}; while (match(s,/ADR-[0-9][0-9][0-9][0-9]/)){c++; s=substr(s,RSTART+RLENGTH)}; print c}')",
)

# Pattern H: adr_id extraction (one-liner now)
src = src.replace(
    'adr_id=$(printf \'%s\' "$adr" | grep -oE \'ADR-[0-9]{4}\' | head -1)',
    "adr_id=$(awk -v s=\"$adr\" 'BEGIN{if(match(s,/ADR-[0-9][0-9][0-9][0-9]/)) print substr(s,RSTART,RLENGTH)}')",
)

# Pattern I: INDEX.md table-row check
src = src.replace(
    'if printf \'%s\' "$line" | grep -qE \'^\\| ADR-[0-9]{4} \\|\'; then',
    'if grep -qE -- \'^\\| ADR-[0-9]{4} \\|\' <<<"$line"; then',
)
src = src.replace(
    'adr_id=$(printf \'%s\' "$line" | grep -oE \'ADR-[0-9]{4}\' | head -1)',
    "adr_id=$(awk -v s=\"$line\" 'BEGIN{if(match(s,/ADR-[0-9][0-9][0-9][0-9]/)) print substr(s,RSTART,RLENGTH)}')",
)

p.write_text(src)
print("OK: linter SIGPIPE+pipefail flakiness fixed")
print("OK: line 495 multi-printf-on-one-line bug fixed")
PYEOF
