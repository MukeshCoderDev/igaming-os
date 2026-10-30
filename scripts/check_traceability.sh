#!/usr/bin/env bash
# check_traceability.sh — Phase 25 FINAL traceability linter (rules 1–235). Validation, Readiness & Launch — 25 phases complete.
#
# Phase 1 rules (1-7) per BLUEPRINT v5.2 §11 and `traceability.md` §A:
#   1. Row completeness — every REQ row has 7 non-empty cells; every DEC row has 8.
#   2. Status enum — Status ∈ {Proposed, Accepted, Confirmed, HUMAN-APPROVED,
#      Superseded, Deprecated, Rejected, Blocked}.
#   3. Scope enum — Scope ∈ {Phase1, Phase2-3, Phase4-7, Phase8-10, Phase11,
#      Phase12+, CrossCutting, Foundational, OutOfScope-Increment1}.
#   4. Confirmed ⇒ citation (non-placeholder Source) or HUMAN-APPROVED.
#   5. Legal/Regulatory/Licensing/Business/Budget/Vendor + Confirmed ⇒
#      must be HUMAN-APPROVED.
#   6. IDs unique across REQ and DEC tables.
#   7. ADR-DEC mapping law:
#        a. every ADR stub cites exactly one DEC (front-matter `DEC: DEC-00XX`);
#        b. no DEC row cites more than one ADR;
#        c. every ADR is cited by exactly one DEC;
#        d. every ADR's cited DEC exists in the DEC table;
#        e. every ADR named in the DEC table has a stub file.
#
# Phase 2 rules (8-12) per DEC-0025 / DEC-0026 and Phase 2 hard acceptance:
#   8. Every NFR section in nfr.md has ≥1 mechanism row in nfr-allocation.md.
#   9. Every bounded context in domain-boundaries.md has ≥1 component in
#      docs/adr/INDEX.md §4 (03-view table).
#  10. Every ADR carries Nygard front-matter (ADR, Title, Status, DEC, Owner,
#      Created, Last-Reviewed, Supersedes) and five body sections
#      (Context, Decision, Alternatives, Consequences, Validation Plan).
#  11. INDEX ↔ DEC seed consistency:
#        a. DEC-0001..0020 ↔ ADR-0001..0020 (1:1);
#        b. DEC-0021 ↔ ADR-0021 (1:1);
#        c. DEC-0022..0026 carry ADR = "none" in the DEC table;
#        d. INDEX.md §2 status table rows match ADR file front-matter Status.
#  12. Phase 2/3 architecture inventory exists:
#        - docs/architecture/{security,nfr-allocation,capacity-assumptions,
#          data-classification,risk-register,settings-split}.md
#        - docs/adr/INDEX.md
#        - docs/api/openapi.yaml
#        - docs/stage-handoffs/stage-{02,03}-handoff.md
#        - docs/errata/v5.2.1-verification.md
#        - docs/audits/phase-{001,002,003}-audit.md
#        - src/noventra/{__init__,settings/base,api/health,...}
#        - pyproject.toml, Dockerfile, docker-compose.yml, .env.example,
#          Makefile, CODEOWNERS, README.md, manage.py, pytest.ini
#        - .github/workflows/ci.yml
#        - deploy/docker/init/0[0-3]-*.sql
#
# Phase 3 rules (13-16) per DEC-0027 / DEC-0028 / ADR-0022..0024:
#  13. .env.example covers every required env var (SECRET_KEY,
#      DATABASE_URL, REDIS_URL).
#  14. Makefile contains required targets: bootstrap, migrate, test,
#      lint, typecheck, runserver.
#  15. CODEOWNERS exists and references docs/requirements/roles.md.
#  16. README.md exists and links to docs/BLUEPRINT.md + docs/audits/.
#
# Phase 4 rules (17-23) per DEC-0030..0033 / ADR-0025..0028:
#  17. Phase 4 inventory files exist (observability/, middleware/,
#      errors/, metrics, traces.md, gitleaks baseline, pip-audit
#      allowlist, coverage baseline, branch-protection config).
#  18. mypy strict modules list present in pyproject.toml
#      ([[tool.mypy.overrides]] with noventra.observability/errors/middleware).
#  19. Error catalog (src/noventra/errors/catalog.py) parses; has ≥1
#      ErrorCode with code=, http_status=, i18n_key=, detail_template=.
#  20. Trace matrices (docs/architecture/traces.md) exist with NFR,
#      STRIDE, PII sections; all 15 PII IDs (PII-001..015) appear.
#  21. .gitleaks-baseline.json + .pip-audit-allowlist.txt exist and
#      are non-empty.
#  22. deploy/ci/branch-protection.json + apply-branch-protection.sh
#      exist (script executable); config has required_pull_request_reviews
#      and allow_force_pushes fields.
#  23. Five ADRs ACCEPTED (0017, 0025, 0026, 0027, 0028) with non-empty
#      Approver lines.
#
# Exit code: 0 on success; 1 on any violation; 2 on configuration error.

set -uo pipefail

# ─── Configuration (override via env) ───────────────────────────────────
TRACE_FILE="${TRACE_FILE:-docs/requirements/traceability.md}"
ADR_DIR="${ADR_DIR:-docs/adr}"
NFR_FILE="${NFR_FILE:-docs/requirements/nfr.md}"
NFR_ALLOC_FILE="${NFR_ALLOC_FILE:-docs/architecture/nfr-allocation.md}"
BOUNDARIES_FILE="${BOUNDARIES_FILE:-docs/requirements/domain-boundaries.md}"
ADR_INDEX_FILE="${ADR_INDEX_FILE:-docs/adr/INDEX.md}"

# Resolve to absolute paths so the script works from any CWD.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
[ -f "$TRACE_FILE" ] || TRACE_FILE="$ROOT/$TRACE_FILE"
[ -d "$ADR_DIR" ]    || ADR_DIR="$ROOT/$ADR_DIR"
[ -f "$NFR_FILE" ]       || NFR_FILE="$ROOT/$NFR_FILE"
[ -f "$NFR_ALLOC_FILE" ] || NFR_ALLOC_FILE="$ROOT/$NFR_ALLOC_FILE"
[ -f "$BOUNDARIES_FILE" ] || BOUNDARIES_FILE="$ROOT/$BOUNDARIES_FILE"
[ -f "$ADR_INDEX_FILE" ]  || ADR_INDEX_FILE="$ROOT/$ADR_INDEX_FILE"

# ─── Pre-flight ─────────────────────────────────────────────────────────
if [ ! -f "$TRACE_FILE" ]; then
    echo "LINT FAIL: traceability file not found: $TRACE_FILE" >&2
    exit 2
fi
if [ ! -d "$ADR_DIR" ]; then
    echo "LINT FAIL: ADR directory not found: $ADR_DIR" >&2
    exit 2
fi

# ─── State ──────────────────────────────────────────────────────────────
VIOLATIONS=0
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

REQS_TSV="$TMPDIR/reqs.tsv"
DECS_TSV="$TMPDIR/decs.tsv"
ALL_IDS="$TMPDIR/all_ids.txt"
ADR_TO_DEC="$TMPDIR/adr_to_dec.tsv"   # basename → cited DEC
DEC_TO_ADR="$TMPDIR/dec_to_adr.tsv"   # DEC ID → ADR basename
: > "$ALL_IDS"; : > "$ADR_TO_DEC"; : > "$DEC_TO_ADR"

# ─── Helpers ────────────────────────────────────────────────────────────
fail() {
    local rule="$1"; shift
    echo "LINT FAIL [rule $rule]: $*" >&2
    VIOLATIONS=$((VIOLATIONS + 1))
}

is_valid_status() {
    case "$1" in
        Proposed|Accepted|Confirmed|HUMAN-APPROVED|Superseded|Deprecated|Rejected|Blocked)
            return 0 ;;
        *) return 1 ;;
    esac
}

is_valid_scope() {
    case "$1" in
        Phase1|Phase2-3|Phase4-7|Phase8-10|Phase11|Phase12+|CrossCutting|Foundational|OutOfScope-Increment1)
            return 0 ;;
        *) return 1 ;;
    esac
}

is_rule5_category() {
    case "$1" in
        Legal|Regulatory|Licensing|Business|Budget|Vendor) return 0 ;;
        *) return 1 ;;
    esac
}

is_placeholder_source() {
    case "$1" in
        ""|"—"|"-"|"N/A"|"n/a"|"TBD"|"tbd"|"TODO"|"todo") return 0 ;;
        *) return 1 ;;
    esac
}

# ─── Extract REQ and DEC tables ─────────────────────────────────────────
# Awk scans traceability.md, finds §B (REQ) and §C (DEC) sections, parses
# pipe-table rows into TSV, trimming each cell. Separator rows (|---|) are
# skipped. §D ends table extraction.
awk -v reqs="$REQS_TSV" -v decs="$DECS_TSV" '
    BEGIN { mode = ""; seen_sep = 0 }
    /^## §B Requirements/ { mode = "req"; seen_sep = 0; next }
    /^## §C Decisions/    { mode = "dec"; seen_sep = 0; next }
    /^## §D /             { mode = "";    seen_sep = 0; next }
    /^## §E /             { mode = "";    seen_sep = 0; next }
    /^### /               { seen_sep = 0; next }   # sub-section header resets
    mode != "" && /^\|/ {
        # Skip the header separator row (|---|---|...).
        if ($0 ~ /^\|[[:space:]]*[-:]+/) { seen_sep = 1; next }
        # Skip the header row (it appears before the separator).
        if (!seen_sep) next
        line = $0
        sub(/^\|/, "", line)
        sub(/\|[[:space:]]*$/, "", line)
        n = split(line, f, "|")
        out = ""
        for (i = 1; i <= n; i++) {
            gsub(/^[[:space:]]+|[[:space:]]+$/, "", f[i])
            out = out f[i] "\t"
        }
        sub(/\t$/, "", out)
        if (mode == "req") print out > reqs
        else               print out > decs
    }
' "$TRACE_FILE"

# ─── Rule 6 prep: collect all IDs, check uniqueness ─────────────────────
while IFS=$'\t' read -r id _ _ _ _ _ _; do
    [ -n "$id" ] && echo "$id" >> "$ALL_IDS"
done < "$REQS_TSV"
while IFS=$'\t' read -r id _ _ _ _ _ _ _; do
    [ -n "$id" ] && echo "$id" >> "$ALL_IDS"
done < "$DECS_TSV"

if [ -s "$ALL_IDS" ]; then
    dup_ids="$(sort "$ALL_IDS" | uniq -d)"
    if [ -n "$dup_ids" ]; then
        while IFS= read -r dup; do
            [ -n "$dup" ] && fail 6 "duplicate ID: $dup"
        done <<< "$dup_ids"
    fi
fi

# ─── Rules 1–5 for REQ rows ─────────────────────────────────────────────
req_count=0
while IFS=$'\t' read -r id title cat status scope owner source; do
    req_count=$((req_count + 1))
    # Rule 1: row completeness (7 cells, all non-empty).
    if [ -z "$id" ] || [ -z "$title" ] || [ -z "$cat" ] || \
       [ -z "$status" ] || [ -z "$scope" ] || [ -z "$owner" ] || [ -z "$source" ]; then
        fail 1 "REQ row #$req_count has an empty required field"
        continue
    fi
    # Rule 2: status enum.
    if ! is_valid_status "$status"; then
        fail 2 "REQ $id has invalid status: '$status'"
    fi
    # Rule 3: scope enum.
    if ! is_valid_scope "$scope"; then
        fail 3 "REQ $id has invalid scope: '$scope'"
    fi
    # Rule 4: Confirmed ⇒ citation.
    if [ "$status" = "Confirmed" ] && is_placeholder_source "$source"; then
        fail 4 "REQ $id is Confirmed but source is empty/placeholder"
    fi
    # Rule 5: rule-5 category + Confirmed ⇒ must be HUMAN-APPROVED.
    if is_rule5_category "$cat" && [ "$status" = "Confirmed" ]; then
        fail 5 "REQ $id (category '$cat') is Confirmed; must be HUMAN-APPROVED"
    fi
done < "$REQS_TSV"

# ─── Rules 1–5, 7a for DEC rows ─────────────────────────────────────────
dec_count=0
while IFS=$'\t' read -r id title cat status scope owner source adr; do
    dec_count=$((dec_count + 1))
    # Rule 1: 8 cells, all non-empty (ADR column may be "none" but not empty).
    if [ -z "$id" ] || [ -z "$title" ] || [ -z "$cat" ] || \
       [ -z "$status" ] || [ -z "$scope" ] || [ -z "$owner" ] || [ -z "$source" ]; then
        fail 1 "DEC row #$dec_count has an empty required field (cols 1–7)"
        continue
    fi
    if [ -z "$adr" ]; then
        fail 1 "DEC $id has an empty ADR column (use 'none' if no ADR)"
        continue
    fi
    # Rule 2: status enum.
    if ! is_valid_status "$status"; then
        fail 2 "DEC $id has invalid status: '$status'"
    fi
    # Rule 3: scope enum.
    if ! is_valid_scope "$scope"; then
        fail 3 "DEC $id has invalid scope: '$scope'"
    fi
    # Rule 4: Confirmed ⇒ citation.
    if [ "$status" = "Confirmed" ] && is_placeholder_source "$source"; then
        fail 4 "DEC $id is Confirmed but source is empty/placeholder"
    fi
    # Rule 5: rule-5 category + Confirmed ⇒ must be HUMAN-APPROVED.
    if is_rule5_category "$cat" && [ "$status" = "Confirmed" ]; then
        fail 5 "DEC $id (category '$cat') is Confirmed; must be HUMAN-APPROVED"
    fi
    # Rule 7a: at most one ADR token in the ADR column.
    adr_token_count=$(grep -oE 'ADR-[0-9]{4}' <<<"$adr" | wc -l | tr -d ' ')
    if [ "$adr_token_count" -gt 1 ]; then
        fail 7 "DEC $id cites $adr_token_count ADRs; at most one allowed"
    fi
    # Record DEC→ADR mapping for rules 7c–7e.
    if [ "$adr" != "none" ] && [ "$adr_token_count" -ge 1 ]; then
        adr_id=$(grep -oE 'ADR-[0-9]{4}' <<<"$adr" | head -1)
        printf '%s\t%s\n' "$id" "$adr_id" >> "$DEC_TO_ADR"
    fi
done < "$DECS_TSV"

# ─── Rule 7b: each ADR stub cites exactly one DEC ───────────────────────
shopt -s nullglob
adr_files=("$ADR_DIR"/ADR-*.md)
adr_count=${#adr_files[@]}
if [ "$adr_count" -eq 0 ]; then
    fail 7 "no ADR stubs found in $ADR_DIR"
fi
for adr_file in "${adr_files[@]}"; do
    basename_noext="$(basename "$adr_file" .md)"
    # Front-matter is the block between the first two lines that are exactly '---'.
    dec_lines=$(awk '
        /^---[[:space:]]*$/ { fm++; next }
        fm == 1 && /^DEC:/ { print }
        fm >= 2 { exit }
    ' "$adr_file")
    dec_line_count=$(grep -c -- '^DEC:' <<<"$dec_lines" || true)
    if [ "$dec_line_count" -eq 0 ]; then
        fail 7 "$basename_noext: front-matter missing 'DEC: DEC-00XX' citation"
        continue
    fi
    if [ "$dec_line_count" -gt 1 ]; then
        fail 7 "$basename_noext: front-matter has $dec_line_count DEC lines; exactly 1 required"
        continue
    fi
    # Extract the DEC value.
    dec_value=$(printf '%s\n' "$dec_lines" | head -1 | sed -E 's/^DEC:[[:space:]]*//; s/[[:space:]]+$//')
    if ! grep -qE -- '^DEC-[0-9]{4}$' <<<"$dec_value"; then
        fail 7 "$basename_noext: DEC citation '$dec_value' is not in 'DEC-00XX' format"
        continue
    fi
    printf '%s\t%s\n' "$basename_noext" "$dec_value" >> "$ADR_TO_DEC"
done

# ─── Rule 7c: every ADR is cited by exactly one DEC ─────────────────────
while IFS=$'\t' read -r adr_basename dec_cited; do
    citing_dec_count=$(awk -v adr="$adr_basename" -F'\t' '$2 == adr { c++ } END { print c+0 }' "$DEC_TO_ADR")
    if [ "$citing_dec_count" -eq 0 ]; then
        fail 7 "$adr_basename: cited by 0 DECs (must be cited by exactly 1)"
    elif [ "$citing_dec_count" -gt 1 ]; then
        fail 7 "$adr_basename: cited by $citing_dec_count DECs (must be cited by exactly 1)"
    fi
done < "$ADR_TO_DEC"

# ─── Rule 7d: every ADR's cited DEC exists in the DEC table ─────────────
dec_ids_in_table=$(awk -F'\t' '{print $1}' "$DECS_TSV" | sort -u)
while IFS=$'\t' read -r adr_basename dec_cited; do
    if ! grep -qx -- "$dec_cited" <<<"$dec_ids_in_table"; then
        fail 7 "$adr_basename cites $dec_cited which is not in the DEC table"
    fi
done < "$ADR_TO_DEC"

# ─── Rule 7e: every ADR named in DEC table has a stub file ──────────────
while IFS=$'\t' read -r dec_id adr_id; do
    if [ ! -f "$ADR_DIR/$adr_id.md" ]; then
        fail 7 "DEC $dec_id cites $adr_id but no file $ADR_DIR/$adr_id.md exists"
    fi
done < "$DEC_TO_ADR"

# ═════════════════════════════════════════════════════════════════════════
# Phase 2 rules (8–12)
# ═════════════════════════════════════════════════════════════════════════

# ─── Rule 8: every NFR section in nfr.md → ≥1 mechanism row in
#     nfr-allocation.md ──────────────────────────────────────────────────
# Strategy: extract NFR IDs (§X.Y headings) from nfr.md, then verify each
# appears in nfr-allocation.md. We treat "appears" as the literal string
# "§X.Y" being present in the allocation file.
if [ ! -f "$NFR_FILE" ]; then
    fail 8 "NFR file not found: $NFR_FILE"
elif [ ! -f "$NFR_ALLOC_FILE" ]; then
    fail 8 "NFR allocation file not found: $NFR_ALLOC_FILE"
else
    nfr_alloc_text="$(cat "$NFR_ALLOC_FILE")"
    # Extract NFR IDs: lines like "### §1.1 Encryption at rest" or table rows
    # in nfr.md that start with "| §". We grep for `§<digit>.<digit>`.
    nfr_ids_in_nfr="$(grep -oE '§[0-9]+\.[0-9]+' "$NFR_FILE" | sort -u)"
    nfr_count_total=0
    nfr_count_missing=0
    while IFS= read -r nfr_id; do
        [ -z "$nfr_id" ] && continue
        nfr_count_total=$((nfr_count_total + 1))
        if ! grep -qF -- "$nfr_id" <<<"$nfr_alloc_text"; then
            fail 8 "NFR $nfr_id (from nfr.md) has no mechanism row in nfr-allocation.md"
            nfr_count_missing=$((nfr_count_missing + 1))
        fi
    done <<< "$nfr_ids_in_nfr"
fi

# ─── Rule 9: every bounded context in domain-boundaries.md → ≥1 component
#     in docs/adr/INDEX.md §4 (03-view table) ────────────────────────────
# Strategy: extract context names from domain-boundaries.md §1 table (first
# data column), then verify each appears in INDEX.md §4 component table.
if [ ! -f "$BOUNDARIES_FILE" ]; then
    fail 9 "Boundaries file not found: $BOUNDARIES_FILE"
elif [ ! -f "$ADR_INDEX_FILE" ]; then
    fail 9 "ADR INDEX file not found: $ADR_INDEX_FILE"
else
    index_text="$(cat "$ADR_INDEX_FILE")"
    # Bounded contexts appear as rows in domain-boundaries.md §1 with names
    # like "Tenancy", "Identity", "Audit", etc. We check each single-word
    # context name, then the three multi-word contexts explicitly.
    single_word_contexts="Tenancy Identity Audit Ledger Configuration Telemetry Reliability Sandbox Webhooks"
    for ctx in $single_word_contexts; do
        if ! grep -qF -- "$ctx" <<<"$index_text"; then
            fail 9 "Bounded context '$ctx' has no component row in ADR INDEX §4"
        fi
    done
    # Explicit checks for multi-word contexts:
    for multi in "Workflow Engine" "Feature Flags" "Backups & DR"; do
        if ! grep -qF -- "$multi" <<<"$index_text"; then
            fail 9 "Bounded context '$multi' has no component row in ADR INDEX §4"
        fi
    done
fi

# ─── Rule 10: every ADR carries Nygard front-matter + body sections ──────
# Front-matter required keys: ADR, Title, Status, DEC, Owner, Created,
# Last-Reviewed, Supersedes.
# Body required sections (## headings): Context, Decision, Alternatives,
# Consequences, Validation Plan.
nygard_fm_keys="ADR Title Status DEC Owner Created Last-Reviewed Supersedes"
nygard_body_sections=("Context" "Decision" "Alternatives" "Consequences" "Validation Plan")
for adr_file in "$ADR_DIR"/ADR-*.md; do
    basename_noext="$(basename "$adr_file" .md)"
    # Front-matter block is between first two `---` lines.
    fm_text=$(awk '
        /^---[[:space:]]*$/ { fm++; next }
        fm == 1 { print }
        fm >= 2 { exit }
    ' "$adr_file")
    for key in $nygard_fm_keys; do
        if ! grep -qE -- "^${key}:" <<<"$fm_text"; then
            fail 10 "$basename_noext: front-matter missing key '$key:'"
        fi
    done
    # Body sections: grep for `## <Section>` headings. Multi-word section
    # names (e.g. "Validation Plan") are matched as a literal phrase.
    body_text="$(cat "$adr_file")"
    for sec in "${nygard_body_sections[@]}"; do
        if ! grep -qE -- "^## ${sec}$" <<<"$body_text"; then
            fail 10 "$basename_noext: body missing section '## ${sec}'"
        fi
    done
done

# ─── Rule 11: INDEX ↔ DEC seed consistency ───────────────────────────────
# (a) DEC-0001..0020 ↔ ADR-0001..0020 (1:1 by number)
# (b) DEC-0021 ↔ ADR-0021 (1:1 by number)
# (c) DEC-0022..0026 carry ADR = "none" in the DEC table
# (d) INDEX.md §2 status rows match ADR file front-matter Status
# (e) DEC-0027 ↔ ADR-0022; DEC-0028 ↔ ADR-0023; DEC-0029 ↔ ADR-0024
#     (DEC and ADR number spaces are independent per DEC-0023 §A.4 invariant 4)
#
# Expected DEC → ADR mapping. For DEC-0001..0021, ADR number = DEC number.
# For DEC-0027/0028/0029, the ADR number is given explicitly. All other DECs
# (0022..0026) expect "none".
EXPECTED_MAP_FILE="$TMPDIR/expected_map.tsv"
{
    for n in 0001 0002 0003 0004 0005 0006 0007 0008 0009 0010 0011 0012 0013 0014 0015 0016 0017 0018 0019 0020 0021; do
        printf 'DEC-%s\tADR-%s\n' "$n" "$n"
    done
    printf 'DEC-0027\tADR-0022\n'
    printf 'DEC-0028\tADR-0023\n'
    printf 'DEC-0029\tADR-0024\n'
    printf 'DEC-0030\tADR-0025\n'
    printf 'DEC-0031\tADR-0026\n'
    printf 'DEC-0032\tADR-0027\n'
    printf 'DEC-0033\tADR-0028\n'
    printf 'DEC-0034\tADR-0029\n'
    printf 'DEC-0035\tADR-0030\n'
    printf 'DEC-0036\tADR-0031\n'
    printf 'DEC-0037\tADR-0032\n'
    printf 'DEC-0038\tADR-0033\n'
    printf 'DEC-0039\tADR-0034\n'
    printf 'DEC-0040\tADR-0035\n'
    printf 'DEC-0041\tADR-0036\n'
    printf 'DEC-0042\tADR-0037\n'
    printf 'DEC-0043\tADR-0038\n'
    printf 'DEC-0044\tADR-0039\n'
    printf 'DEC-0045\tADR-0040\n'
    printf 'DEC-0046\tADR-0041\n'
    printf 'DEC-0047\tADR-0042\n'
    printf 'DEC-0048\tADR-0043\n'
    printf 'DEC-0049\tADR-0044\n'
    printf 'DEC-0050\tADR-0045\n'
    printf 'DEC-0051\tADR-0046\n'
    printf 'DEC-0052\tADR-0047\n'
    printf 'DEC-0053\tADR-0048\n'
    printf 'DEC-0054\tADR-0049\n'
    printf 'DEC-0055\tADR-0050\n'
    printf 'DEC-0056\tADR-0051\n'
    printf 'DEC-0057\tADR-0052\n'
    printf 'DEC-0058\tADR-0053\n'
    printf 'DEC-0059\tADR-0054\n'
    printf 'DEC-0060\tADR-0055\n'
    printf 'DEC-0061\tADR-0056\n'
    printf 'DEC-0062\tADR-0057\n'
    printf 'DEC-0063\tADR-0058\n'
    printf 'DEC-0065\tADR-0059\n'
    printf 'DEC-0066\tADR-0060\n'
    printf 'DEC-0067\tADR-0061\n'
    printf 'DEC-0068\tADR-0062\n'
    printf 'DEC-0069\tADR-0063\n'
    printf 'DEC-0070\tADR-0064\n'
    printf 'DEC-0071\tADR-0065\n'
    printf 'DEC-0072\tADR-0072\n'
    printf 'DEC-0073\tADR-0073\n'
    printf 'DEC-0074\tADR-0074\n'
    printf 'DEC-0075\tADR-0075\n'
    printf 'DEC-0076\tADR-0076\n'
    printf 'DEC-0077\tADR-0077\n'
    printf 'DEC-0078\tADR-0078\n'
    printf 'DEC-0079\tADR-0079\n'
    printf 'DEC-0080\tADR-0080\n'
    printf 'DEC-0081\tADR-0081\n'
    printf 'DEC-0082\tADR-0082\n'
    printf 'DEC-0083\tADR-0083\n'
    printf 'DEC-0084\tADR-0084\n'
    printf 'DEC-0085\tADR-0085\n'
    printf 'DEC-0086\tADR-0086\n'
    printf 'DEC-0087\tADR-0087\n'
    printf 'DEC-0088\tADR-0088\n'
    printf 'DEC-0089\tADR-0089\n'
    printf 'DEC-0090\tADR-0090\n'
    printf 'DEC-0091\tADR-0091\n'
    printf 'DEC-0093\tADR-0092\n'
    printf 'DEC-0094\tADR-0093\n'
    printf 'DEC-0095\tADR-0094\n'
    printf 'DEC-0096\tADR-0095\n'
    printf 'DEC-0097\tADR-0096\n'
    printf 'DEC-0098\tADR-0097\n'
    printf 'DEC-0099\tADR-0098\n'
    printf 'DEC-0100\tADR-0099\n'
    printf 'DEC-0101\tADR-0100\n'
    printf 'DEC-0102\tADR-0101\n'
    printf 'DEC-0103\tADR-0102\n'
    printf 'DEC-0104\tADR-0103\n'
    printf 'DEC-0105\tADR-0104\n'
    printf 'DEC-0106\tADR-0105\n'
    printf 'DEC-0107\tADR-0106\n'
    printf 'DEC-0108\tADR-0107\n'
    printf 'DEC-0109\tADR-0108\n'
    printf 'DEC-0110\tADR-0109\n'
    printf 'DEC-0111\tADR-0110\n'
    printf 'DEC-0112\tADR-0111\n'
    printf 'DEC-0113\tADR-0112\n'
    printf 'DEC-0114\tADR-0113\n'
    printf 'DEC-0115\tADR-0114\n'
    printf 'DEC-0116\tADR-0115\n'
    printf 'DEC-0117\tADR-0116\n'
    printf 'DEC-0118\tADR-0117\n'
    printf 'DEC-0119\tADR-0118\n'
    printf 'DEC-0120\tADR-0119\n'
    printf 'DEC-0121\tADR-0120\n'
    printf 'DEC-0122\tADR-0121\n'
    printf 'DEC-0123\tADR-0122\n'
    printf 'DEC-0124\tADR-0123\n'
    printf 'DEC-0125\tADR-0124\n'
    printf 'DEC-0126\tADR-0125\n'
    printf 'DEC-0127\tADR-0126\n'
    printf 'DEC-0128\tADR-0127\n'
    printf 'DEC-0129\tADR-0128\n'
    printf 'DEC-0130\tADR-0129\n'
    printf 'DEC-0131\tADR-0130\n'
    printf 'DEC-0132\tADR-0131\n'
    printf 'DEC-0133\tADR-0132\n'
    printf 'DEC-0134\tADR-0133\n'
    printf 'DEC-0135\tADR-0134\n'
    printf 'DEC-0136\tADR-0135\n'
    printf 'DEC-0137\tADR-0136\n'
    printf 'DEC-0138\tADR-0137\n'
    printf 'DEC-0139\tADR-0138\n'
    printf 'DEC-0140\tADR-0139\n'
    printf 'DEC-0141\tADR-0140\n'
    printf 'DEC-0142\tADR-0141\n'
    printf 'DEC-0143\tADR-0142\n'
    printf 'DEC-0144\tADR-0143\n'
    printf 'DEC-0145\tADR-0144\n'
    printf 'DEC-0146\tADR-0145\n'
    printf 'DEC-0147\tADR-0146\n'
    printf 'DEC-0148\tADR-0147\n'
    printf 'DEC-0149\tADR-0148\n'
    printf 'DEC-0150\tADR-0149\n'
    printf 'DEC-0151\tADR-0150\n'
    printf 'DEC-0152\tADR-0151\n'
    printf 'DEC-0153\tADR-0152\n'
    printf 'DEC-0154\tADR-0153\n'
    printf 'DEC-0155\tADR-0154\n'
    printf 'DEC-0156\tADR-0155\n'
} > "$EXPECTED_MAP_FILE"

# (a) + (b) + (e): For each DEC in the expected map, verify the DEC table's
# ADR column matches.
while IFS=$'\t' read -r dec_id expected_adr; do
    actual_adr=$(awk -F'\t' -v dec="$dec_id" '$1 == dec { print $8 }' "$DECS_TSV")
    if [ -z "$actual_adr" ]; then
        fail 11 "$dec_id not found in DEC table"
    elif [ "$actual_adr" != "$expected_adr" ]; then
        fail 11 "$dec_id ADR column '$actual_adr' ≠ expected '$expected_adr'"
    fi
done < "$EXPECTED_MAP_FILE"
# (c): DEC-0022..0026 must have ADR = "none".
expected_dec_none="$(awk -F'\t' '
    /^DEC-00(2[2-6])\t/ { print $1 "\t" $8 }
    /^DEC-0064\t/ { print $1 "\t" $8 }
' "$DECS_TSV")"
while IFS=$'\t' read -r dec_id adr_col; do
    if [ "$adr_col" != "none" ]; then
        fail 11 "$dec_id ADR column '$adr_col' ≠ expected 'none'"
    fi
done <<< "$expected_dec_none"
# (d): INDEX.md §2 status rows match ADR file front-matter Status.
# INDEX.md §2 table columns: | ADR | Title | DEC | Owner | Status | Created |
# Last-Reviewed | Supersedes | Superseded-By |
# Split by `|`: $1=empty, $2=ADR, $3=Title, $4=DEC, $5=Owner, $6=Status.
if [ -f "$ADR_INDEX_FILE" ]; then
    while IFS= read -r line; do
        # Match table rows starting with "| ADR-XXXX |"
        if grep -qE -- '^\| ADR-[0-9]{4} \|' <<<"$line"; then
            adr_id=$(grep -oE 'ADR-[0-9]{4}' <<<"$line" | head -1)
            index_status=$(printf '%s' "$line" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $6); print $6}')
            adr_file="$ADR_DIR/${adr_id}.md"
            if [ -f "$adr_file" ]; then
                fm_status=$(awk '
                    /^---[[:space:]]*$/ { fm++; next }
                    fm == 1 && /^Status:/ { print substr($0, index($0, ":") + 1) }
                    fm >= 2 { exit }
                ' "$adr_file" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')
                if [ "$index_status" != "$fm_status" ]; then
                    fail 11 "$adr_id: INDEX status '$index_status' ≠ ADR front-matter status '$fm_status'"
                fi
            fi
        fi
    done < "$ADR_INDEX_FILE"
fi

# ─── Rule 12: Phase 2 architecture inventory files exist ────────────────
required_phase2_files=(
    "$ROOT/docs/architecture/security.md"
    "$ROOT/docs/architecture/nfr-allocation.md"
    "$ROOT/docs/architecture/capacity-assumptions.md"
    "$ROOT/docs/architecture/data-classification.md"
    "$ROOT/docs/architecture/risk-register.md"
    "$ROOT/docs/adr/INDEX.md"
    "$ROOT/docs/stage-handoffs/stage-02-handoff.md"
    "$ROOT/docs/errata/v5.2.1-verification.md"
    "$ROOT/docs/audits/phase-001-audit.md"
    "$ROOT/docs/audits/phase-002-audit.md"
    # Phase 3 additions:
    "$ROOT/docs/architecture/settings-split.md"
    "$ROOT/docs/api/openapi.yaml"
    "$ROOT/docs/stage-handoffs/stage-03-handoff.md"
    "$ROOT/docs/audits/phase-003-audit.md"
    "$ROOT/src/noventra/__init__.py"
    "$ROOT/src/noventra/settings/base.py"
    "$ROOT/src/noventra/settings/local.py"
    "$ROOT/src/noventra/settings/test.py"
    "$ROOT/src/noventra/settings/production.py"
    "$ROOT/src/noventra/api/health.py"
    "$ROOT/src/noventra/apps/core/migrations/0001_initial.py"
    "$ROOT/pyproject.toml"
    "$ROOT/Dockerfile"
    "$ROOT/docker-compose.yml"
    "$ROOT/.env.example"
    "$ROOT/Makefile"
    "$ROOT/CODEOWNERS"
    "$ROOT/README.md"
    "$ROOT/manage.py"
    "$ROOT/pytest.ini"
    "$ROOT/.github/workflows/ci.yml"
    "$ROOT/deploy/docker/init/00-extensions.sql"
    "$ROOT/deploy/docker/init/01-roles.sql"
    "$ROOT/deploy/docker/init/02-grants.sql"
    "$ROOT/deploy/docker/init/03-rls-function.sql"
)
for f in "${required_phase2_files[@]}"; do
    if [ ! -f "$f" ]; then
        fail 12 "Phase 2/3 inventory file missing: $f"
    elif [ ! -s "$f" ]; then
        fail 12 "Phase 2/3 inventory file empty: $f"
    fi
done

# ═════════════════════════════════════════════════════════════════════════
# Phase 3 rules (13–16)
# ═════════════════════════════════════════════════════════════════════════

# ─── Rule 13: .env.example covers every required env var ────────────────
# Per DEC-0028 / ADR-0023, required env vars are SECRET_KEY, DATABASE_URL,
# REDIS_URL. Each must appear as a key in .env.example.
ENV_EXAMPLE="$ROOT/.env.example"
required_env_vars="SECRET_KEY DATABASE_URL REDIS_URL"
if [ ! -f "$ENV_EXAMPLE" ]; then
    fail 13 ".env.example not found: $ENV_EXAMPLE"
else
    for var in $required_env_vars; do
        if ! grep -qE "^${var}=" "$ENV_EXAMPLE"; then
            fail 13 ".env.example missing required env var: $var"
        fi
    done
fi

# ─── Rule 14: Makefile contains required make targets ───────────────────
MAKEFILE="$ROOT/Makefile"
required_targets="bootstrap migrate test lint typecheck runserver"
if [ ! -f "$MAKEFILE" ]; then
    fail 14 "Makefile not found: $MAKEFILE"
else
    for target in $required_targets; do
        # Match lines like "bootstrap:  ## ..." or "bootstrap:"
        if ! grep -qE "^${target}:" "$MAKEFILE"; then
            fail 14 "Makefile missing required target: ${target}"
        fi
    done
fi

# ─── Rule 15: CODEOWNERS exists and references roles.md ─────────────────
CODEOWNERS="$ROOT/CODEOWNERS"
if [ ! -f "$CODEOWNERS" ]; then
    fail 15 "CODEOWNERS not found: $CODEOWNERS"
else
    if ! grep -q "docs/requirements/roles.md" "$CODEOWNERS"; then
        fail 15 "CODEOWNERS does not reference docs/requirements/roles.md"
    fi
fi

# ─── Rule 16: README exists and links to BLUEPRINT.md + docs/audits/ ────
README="$ROOT/README.md"
if [ ! -f "$README" ]; then
    fail 16 "README.md not found: $README"
else
    if ! grep -q "docs/BLUEPRINT.md" "$README"; then
        fail 16 "README.md does not link to docs/BLUEPRINT.md"
    fi
    if ! grep -q "docs/audits/" "$README"; then
        fail 16 "README.md does not link to docs/audits/"
    fi
fi

# ═════════════════════════════════════════════════════════════════════════
# Phase 4 rules (17–23)
# ═════════════════════════════════════════════════════════════════════════

# ─── Rule 17: Phase 4 inventory files exist ─────────────────────────────
required_phase4_files=(
    "$ROOT/src/noventra/observability/__init__.py"
    "$ROOT/src/noventra/observability/logging.py"
    "$ROOT/src/noventra/observability/redaction.py"
    "$ROOT/src/noventra/observability/sampling.py"
    "$ROOT/src/noventra/observability/prometheus.py"
    "$ROOT/src/noventra/observability/otel.py"
    "$ROOT/src/noventra/middleware/__init__.py"
    "$ROOT/src/noventra/middleware/correlation.py"
    "$ROOT/src/noventra/errors/__init__.py"
    "$ROOT/src/noventra/errors/catalog.py"
    "$ROOT/src/noventra/errors/handlers.py"
    "$ROOT/src/noventra/api/metrics.py"
    "$ROOT/src/noventra/api/metrics_urls.py"
    "$ROOT/docs/architecture/error-catalog.md"
    "$ROOT/docs/architecture/traces.md"
    "$ROOT/docs/stage-handoffs/stage-04-handoff.md"
    "$ROOT/docs/audits/phase-004-audit.md"
    "$ROOT/.gitleaks-baseline.json"
    "$ROOT/.pip-audit-allowlist.txt"
    "$ROOT/.coverage-baseline-phase4.txt"
    "$ROOT/deploy/ci/branch-protection.json"
    "$ROOT/deploy/ci/apply-branch-protection.sh"
)
for f in "${required_phase4_files[@]}"; do
    if [ ! -f "$f" ]; then
        fail 17 "Phase 4 inventory file missing: $f"
    elif [ ! -s "$f" ]; then
        fail 17 "Phase 4 inventory file empty: $f"
    fi
done

# ─── Rule 18: mypy strict modules list is present in pyproject.toml ────
# Per ADR-0027 / DEC-0032. Verifies the [tool.mypy.overrides] section
# exists with a non-empty module list. (Does not run mypy; CI does that.)
PYPROJECT="$ROOT/pyproject.toml"
if ! grep -q "\[\[tool.mypy.overrides\]\]" "$PYPROJECT"; then
    fail 18 "pyproject.toml missing [[tool.mypy.overrides]] section"
elif ! grep -q "noventra.observability" "$PYPROJECT"; then
    fail 18 "mypy strict list does not include noventra.observability"
elif ! grep -q "noventra.errors" "$PYPROJECT"; then
    fail 18 "mypy strict list does not include noventra.errors"
elif ! grep -q "noventra.middleware" "$PYPROJECT"; then
    fail 18 "mypy strict list does not include noventra.middleware"
fi

# ─── Rule 19: Error catalog parses; one HTTP status per code; i18n keys ─
# Per ADR-0026 / DEC-0031. Verifies catalog.py defines ERROR_CATALOG and
# every ErrorCode has required fields. Does not import the module (would
# require Django); uses regex extraction.
CATALOG="$ROOT/src/noventra/errors/catalog.py"
if [ ! -f "$CATALOG" ]; then
    fail 19 "Error catalog not found: $CATALOG"
else
    # Count ErrorCode entries.
    error_count=$(grep -cE "^\s*ErrorCode\(" "$CATALOG" || true)
    if [ "$error_count" -lt 1 ]; then
        fail 19 "Error catalog has no ErrorCode entries"
    fi
    # Verify each ErrorCode has all required fields (code, http_status, i18n_key, title, detail_template).
    if ! grep -q "code=" "$CATALOG"; then
        fail 19 "Error catalog has an ErrorCode missing 'code='"
    fi
    if ! grep -q "http_status=" "$CATALOG"; then
        fail 19 "Error catalog has an ErrorCode missing 'http_status='"
    fi
    if ! grep -q "i18n_key=" "$CATALOG"; then
        fail 19 "Error catalog has an ErrorCode missing 'i18n_key='"
    fi
    if ! grep -q "detail_template=" "$CATALOG"; then
        fail 19 "Error catalog has an ErrorCode missing 'detail_template='"
    fi
fi

# ─── Rule 20: Trace matrices exist (NFR, STRIDE, PII) ──────────────────
# Per Phase 4 spec output #15. Verifies traces.md has all three sections.
TRACES="$ROOT/docs/architecture/traces.md"
if [ ! -f "$TRACES" ]; then
    fail 20 "Traces doc not found: $TRACES"
else
    if ! grep -q "## 1. NFR → artifact" "$TRACES"; then
        fail 20 "traces.md missing §1 NFR → artifact section"
    fi
    if ! grep -q "## 2. STRIDE → artifact" "$TRACES"; then
        fail 20 "traces.md missing §2 STRIDE → artifact section"
    fi
    if ! grep -q "## 3. PII class → redaction rule" "$TRACES"; then
        fail 20 "traces.md missing §3 PII class → redaction rule section"
    fi
    # Verify every PII ID (PII-001..015) appears in the PII section.
    for n in 001 002 003 004 005 006 007 008 009 010 011 012 013 014 015; do
        if ! grep -q "PII-$n" "$TRACES"; then
            fail 20 "traces.md PII section missing PII-$n"
        fi
    done
fi

# ─── Rule 21: gitleaks baseline + pip-audit allowlist exist ────────────
GITLEAKS_BASELINE="$ROOT/.gitleaks-baseline.json"
PIP_AUDIT_ALLOWLIST="$ROOT/.pip-audit-allowlist.txt"
if [ ! -f "$GITLEAKS_BASELINE" ]; then
    fail 21 ".gitleaks-baseline.json not found"
elif [ ! -s "$GITLEAKS_BASELINE" ]; then
    fail 21 ".gitleaks-baseline.json is empty"
fi
if [ ! -f "$PIP_AUDIT_ALLOWLIST" ]; then
    fail 21 ".pip-audit-allowlist.txt not found"
elif [ ! -s "$PIP_AUDIT_ALLOWLIST" ]; then
    fail 21 ".pip-audit-allowlist.txt is empty"
fi

# ─── Rule 22: Branch protection config exists ──────────────────────────
BP_CONFIG="$ROOT/deploy/ci/branch-protection.json"
BP_SCRIPT="$ROOT/deploy/ci/apply-branch-protection.sh"
if [ ! -f "$BP_CONFIG" ]; then
    fail 22 "deploy/ci/branch-protection.json not found"
elif [ ! -s "$BP_CONFIG" ]; then
    fail 22 "deploy/ci/branch-protection.json is empty"
elif ! grep -q "required_pull_request_reviews" "$BP_CONFIG"; then
    fail 22 "branch-protection.json missing required_pull_request_reviews"
elif ! grep -q "allow_force_pushes" "$BP_CONFIG"; then
    fail 22 "branch-protection.json missing allow_force_pushes"
fi
if [ ! -x "$BP_SCRIPT" ]; then
    fail 22 "deploy/ci/apply-branch-protection.sh not executable"
fi

# ─── Rule 23: Five ADRs ACCEPTED (0017, 0025, 0026, 0027, 0028) ────────
# Per Phase 4 hard acceptance: 0017+0025..0028 ACCEPTED with approvers.
required_accepted_adrs="0017 0025 0026 0027 0028"
for n in $required_accepted_adrs; do
    adr_file="$ROOT/docs/adr/ADR-$n.md"
    if [ ! -f "$adr_file" ]; then
        fail 23 "ADR-$n.md not found"
        continue
    fi
    # Check Status: ACCEPTED in front-matter.
    fm_status=$(awk '
        /^---[[:space:]]*$/ { fm++; next }
        fm == 1 && /^Status:/ { print substr($0, index($0, ":") + 1) }
        fm >= 2 { exit }
    ' "$adr_file" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')
    if [ "$fm_status" != "ACCEPTED" ]; then
        fail 23 "ADR-$n status is '$fm_status' (expected ACCEPTED)"
    fi
    # Check Approver: line is present and non-empty.
    if ! grep -qE "^Approver: .+" "$adr_file"; then
        fail 23 "ADR-$n missing non-empty Approver line"
    fi
done

# ═════════════════════════════════════════════════════════════════════════
# Phase 5 rules (24–28)
# ═════════════════════════════════════════════════════════════════════════

# ─── Rule 24: check_rls_coverage is non-vacuous + Phase 5 ADRs ACCEPTED ─
# Per Phase 5 spec output #8: check_rls_coverage non-vacuous.
# Verifies the command file contains real checks (not just a vacuous
# pass message). Also verifies ADR-0002/0029/0030 are ACCEPTED.
RLS_CMD="$ROOT/src/noventra/apps/core/management/commands/check_rls_coverage.py"
if [ ! -f "$RLS_CMD" ]; then
    fail 24 "check_rls_coverage command not found: $RLS_CMD"
elif ! grep -q "relrowsecurity" "$RLS_CMD"; then
    fail 24 "check_rls_coverage is vacuous (does not query pg_class for RLS status)"
elif ! grep -q "pg_policy" "$RLS_CMD"; then
    fail 24 "check_rls_coverage does not check RLS policies (pg_policy)"
elif ! grep -q "sys.exit(1)" "$RLS_CMD"; then
    fail 24 "check_rls_coverage does not exit non-zero on failure"
fi
# Phase 5 ADRs ACCEPTED.
for n in 0002 0029 0030; do
    adr_file="$ROOT/docs/adr/ADR-$n.md"
    if [ ! -f "$adr_file" ]; then
        fail 24 "ADR-$n.md not found"
        continue
    fi
    fm_status=$(awk '
        /^---[[:space:]]*$/ { fm++; next }
        fm == 1 && /^Status:/ { print substr($0, index($0, ":") + 1) }
        fm >= 2 { exit }
    ' "$adr_file" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')
    if [ "$fm_status" != "ACCEPTED" ]; then
        fail 24 "ADR-$n status is '$fm_status' (expected ACCEPTED for Phase 5)"
    fi
done

# ─── Rule 25: Tenancy migration exists with RLS policies ────────────────
# Per Phase 5 spec output #6: migrations produce schema + RLS + baseline.
TENANCY_MIG="$ROOT/src/noventra/apps/tenancy/migrations/0001_initial.py"
if [ ! -f "$TENANCY_MIG" ]; then
    fail 25 "Tenancy migration not found: $TENANCY_MIG"
else
    if ! grep -q "ENABLE ROW LEVEL SECURITY" "$TENANCY_MIG"; then
        fail 25 "Tenancy migration does not enable RLS"
    fi
    if ! grep -q "FORCE ROW LEVEL SECURITY" "$TENANCY_MIG"; then
        fail 25 "Tenancy migration does not force RLS (owner subject to RLS)"
    fi
    if ! grep -q "CREATE POLICY" "$TENANCY_MIG"; then
        fail 25 "Tenancy migration does not create RLS policies"
    fi
    if ! grep -q "app.tenant_uuid()" "$TENANCY_MIG"; then
        fail 25 "Tenancy migration RLS policy does not use app.tenant_uuid()"
    fi
    if ! grep -q "WITH CHECK" "$TENANCY_MIG"; then
        fail 25 "Tenancy migration RLS policy missing WITH CHECK"
    fi
    if ! grep -q "noventra_admin" "$TENANCY_MIG"; then
        fail 25 "Tenancy migration does not create noventra_admin break-glass role"
    fi
fi

# ─── Rule 26: Tenant middleware exists with 400 on missing/malformed ────
# Per Phase 5 spec output #5: middleware 400s before DB on missing/malformed.
TENANT_MW="$ROOT/src/noventra/middleware/tenant.py"
if [ ! -f "$TENANT_MW" ]; then
    fail 26 "Tenant middleware not found: $TENANT_MW"
else
    if ! grep -q "TenantResolutionMiddleware" "$TENANT_MW"; then
        fail 26 "TenantResolutionMiddleware class not found"
    fi
    if ! grep -q "problem_response" "$TENANT_MW"; then
        fail 26 "Tenant middleware does not use problem_response for 400s"
    fi
    if ! grep -q "noventra.tenant.missing" "$TENANT_MW"; then
        fail 26 "Tenant middleware does not return E_TENANT_MISSING"
    fi
    if ! grep -q "noventra.tenant.invalid" "$TENANT_MW"; then
        fail 26 "Tenant middleware does not return E_TENANT_INVALID"
    fi
    if ! grep -q "SET LOCAL app.tenant_uuid" "$TENANT_MW"; then
        fail 26 "Tenant middleware does not SET LOCAL app.tenant_uuid"
    fi
fi

# ─── Rule 27: pgbouncer in docker-compose + pgbouncer compat doc ───────
# Per Phase 5 spec output #7: pgbouncer added to local docker-compose.yml.
COMPOSE="$ROOT/docker-compose.yml"
if ! grep -q "pgbouncer" "$COMPOSE"; then
    fail 27 "docker-compose.yml does not include pgbouncer service"
elif ! grep -q "POOL_MODE: transaction" "$COMPOSE"; then
    fail 27 "pgbouncer POOL_MODE is not 'transaction'"
fi
PGBOUNCER_DOC="$ROOT/docs/architecture/pgbouncer-compatibility.md"
if [ ! -f "$PGBOUNCER_DOC" ]; then
    fail 27 "pgbouncer-compatibility.md not found"
elif ! grep -q "SET LOCAL" "$PGBOUNCER_DOC"; then
    fail 27 "pgbouncer-compatibility.md does not mention SET LOCAL"
elif ! grep -q "ATOMIC_REQUESTS" "$PGBOUNCER_DOC"; then
    fail 27 "pgbouncer-compatibility.md does not mention ATOMIC_REQUESTS"
fi
# Verify ATOMIC_REQUESTS=True in settings.
if ! grep -q "ATOMIC_REQUESTS.*True" "$ROOT/src/noventra/settings/base.py"; then
    fail 27 "settings/base.py does not set ATOMIC_REQUESTS=True"
fi
if ! grep -q "prepare_threshold.*None" "$ROOT/src/noventra/settings/base.py"; then
    fail 27 "settings/base.py does not set prepare_threshold=None"
fi

# ─── Rule 28: Phase 5 inventory (tests, handoff, audit, break-glass) ───
required_phase5_files=(
    "$ROOT/src/noventra/apps/tenancy/domain/__init__.py"
    "$ROOT/src/noventra/apps/tenancy/domain/aggregates.py"
    "$ROOT/src/noventra/apps/tenancy/domain/commands.py"
    "$ROOT/src/noventra/apps/tenancy/domain/events.py"
    "$ROOT/src/noventra/apps/tenancy/domain/ports.py"
    "$ROOT/src/noventra/apps/tenancy/adapters/orm.py"
    "$ROOT/src/noventra/middleware/tenant.py"
    "$ROOT/docs/architecture/pgbouncer-compatibility.md"
    "$ROOT/docs/architecture/break-glass-admin.md"
    "$ROOT/docs/stage-handoffs/stage-05-handoff.md"
    "$ROOT/docs/audits/phase-005-audit.md"
    "$ROOT/tests/test_tenancy_rls.py"
    "$ROOT/tests/test_pgbouncer.py"
)
for f in "${required_phase5_files[@]}"; do
    if [ ! -f "$f" ]; then
        fail 28 "Phase 5 inventory file missing: $f"
    elif [ ! -s "$f" ]; then
        fail 28 "Phase 5 inventory file empty: $f"
    fi
done

# ═════════════════════════════════════════════════════════════════════════
# Phase 6 rules (29–35; 33, 34, 36 deferred to Phase 7)
# ═════════════════════════════════════════════════════════════════════════

# ─── Rule 29: Phase 6 ADRs ACCEPTED (0031, 0032, 0033, 0034) ────────────
for n in 0031 0032 0033 0034; do
    adr_file="$ROOT/docs/adr/ADR-$n.md"
    if [ ! -f "$adr_file" ]; then
        fail 29 "ADR-$n.md not found"
        continue
    fi
    fm_status=$(awk '
        /^---[[:space:]]*$/ { fm++; next }
        fm == 1 && /^Status:/ { print substr($0, index($0, ":") + 1) }
        fm >= 2 { exit }
    ' "$adr_file" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')
    if [ "$fm_status" != "ACCEPTED" ]; then
        fail 29 "ADR-$n status is '$fm_status' (expected ACCEPTED for Phase 6)"
    fi
    if ! grep -qE "^Approver: .+" "$adr_file"; then
        fail 29 "ADR-$n missing non-empty Approver line"
    fi
done

# ─── Rule 30: Identity migration exists with tables + RLS + baseline ───
IDENTITY_MIG="$ROOT/src/noventra/apps/identity/migrations/0001_initial.py"
if [ ! -f "$IDENTITY_MIG" ]; then
    fail 30 "Identity migration not found: $IDENTITY_MIG"
else
    for table in identity_user identity_tenant_membership identity_role identity_permission identity_role_permission identity_service_identity identity_refresh_token_blacklist; do
        if ! grep -q "$table" "$IDENTITY_MIG"; then
            fail 30 "Identity migration missing table: $table"
        fi
    done
    # RLS on tenant-scoped tables.
    if ! grep -q "ENABLE ROW LEVEL SECURITY" "$IDENTITY_MIG"; then
        fail 30 "Identity migration does not enable RLS on tenant-scoped tables"
    fi
    # Baseline roles seeded.
    if ! grep -q "'admin'" "$IDENTITY_MIG" || ! grep -q "'manager'" "$IDENTITY_MIG" || ! grep -q "'viewer'" "$IDENTITY_MIG" || ! grep -q "'service'" "$IDENTITY_MIG"; then
        fail 30 "Identity migration does not seed baseline roles (admin/manager/viewer/service)"
    fi
    # Baseline service identities.
    if ! grep -q "'shadow'" "$IDENTITY_MIG" || ! grep -q "'live'" "$IDENTITY_MIG"; then
        fail 30 "Identity migration does not seed shadow + live service identities"
    fi
fi

# ─── Rule 31: AuthN middleware exists with JWT verification ────────────
AUTHN_MW="$ROOT/src/noventra/middleware/authn.py"
if [ ! -f "$AUTHN_MW" ]; then
    fail 31 "AuthN middleware not found: $AUTHN_MW"
else
    if ! grep -q "AuthNMiddleware" "$AUTHN_MW"; then
        fail 31 "AuthNMiddleware class not found"
    fi
    if ! grep -q "verify_token" "$AUTHN_MW"; then
        fail 31 "AuthN middleware does not verify tokens"
    fi
    if ! grep -q "jwt_claims" "$AUTHN_MW"; then
        fail 31 "AuthN middleware does not set jwt_claims on request"
    fi
    if ! grep -q "jwt_tenant_id" "$AUTHN_MW"; then
        fail 31 "AuthN middleware does not set jwt_tenant_id for tenant middleware"
    fi
    if ! grep -q "problem_response" "$AUTHN_MW"; then
        fail 31 "AuthN middleware does not use problem_response for errors"
    fi
fi
# JWT utilities.
JWT_UTIL="$ROOT/src/noventra/apps/identity/adapters/jwt.py"
if [ ! -f "$JWT_UTIL" ]; then
    fail 31 "JWT utility not found: $JWT_UTIL"
elif ! grep -q "issue_access_token" "$JWT_UTIL" || ! grep -q "verify_token" "$JWT_UTIL"; then
    fail 31 "JWT utility missing issue_access_token or verify_token"
fi

# ─── Rule 32: Permission decorators + service/human separation ─────────
PERMS_MW="$ROOT/src/noventra/middleware/permissions.py"
if [ ! -f "$PERMS_MW" ]; then
    fail 32 "Permission decorators not found: $PERMS_MW"
else
    if ! grep -q "def human_only" "$PERMS_MW"; then
        fail 32 "human_only decorator not found"
    fi
    if ! grep -q "def service_only" "$PERMS_MW"; then
        fail 32 "service_only decorator not found"
    fi
    if ! grep -q "def require_permission" "$PERMS_MW"; then
        fail 32 "require_permission decorator not found"
    fi
    if ! grep -q "_service_is_live" "$PERMS_MW"; then
        fail 32 "require_permission does not check service_is_live for service.mutate"
    fi
fi

# ─── Rule 35: Permission catalog closed (every code in catalog) ────────
# Per ADR-0032 / DEC-0037. Verifies permissions.py has a closed
# enumeration (PermissionCode) + BASELINE_ROLE_PERMISSIONS.
PERMS_CAT="$ROOT/src/noventra/apps/identity/domain/permissions.py"
if [ ! -f "$PERMS_CAT" ]; then
    fail 35 "Permission catalog not found: $PERMS_CAT"
else
    if ! grep -q "class PermissionCode" "$PERMS_CAT"; then
        fail 35 "PermissionCode enum not found in catalog"
    fi
    if ! grep -q "PERMISSION_CATALOG" "$PERMS_CAT"; then
        fail 35 "PERMISSION_CATALOG tuple not found"
    fi
    if ! grep -q "BASELINE_ROLE_PERMISSIONS" "$PERMS_CAT"; then
        fail 35 "BASELINE_ROLE_PERMISSIONS dict not found"
    fi
    # Verify all 4 baseline roles present.
    for role in admin manager viewer service; do
        if ! grep -q "\"$role\"" "$PERMS_CAT"; then
            fail 35 "Baseline role '$role' not in BASELINE_ROLE_PERMISSIONS"
        fi
    done
    # Verify service.mutate + service.promote exist.
    if ! grep -q "service.mutate" "$PERMS_CAT"; then
        fail 35 "service.mutate permission not in catalog"
    fi
    if ! grep -q "service.promote" "$PERMS_CAT"; then
        fail 35 "service.promote permission not in catalog"
    fi
fi
# Permission matrix doc.
PERM_MATRIX="$ROOT/docs/architecture/permission-matrix.md"
if [ ! -f "$PERM_MATRIX" ]; then
    fail 35 "Permission matrix doc not found: $PERM_MATRIX"
fi

# ─── Rule 33 (DEFERRED to Phase 7): token storage strategy config ─────
# Phase 7 will enforce token storage config stability.

# ─── Rule 34 (DEFERRED to Phase 7): MFA config stability ──────────────
# Phase 7 will enforce MFA config stability.

# ─── Rule 36 (DEFERRED to Phase 7): invitation flow config stability ──
# Phase 7 will enforce invitation flow config stability.

# ═════════════════════════════════════════════════════════════════════════
# Phase 7 rules (37–43)
# ═════════════════════════════════════════════════════════════════════════

# ─── Rule 37: Phase 7 ADRs ACCEPTED (0035-0039) ─────────────────────────
for n in 0035 0036 0037 0038 0039; do
    adr_file="$ROOT/docs/adr/ADR-$n.md"
    if [ ! -f "$adr_file" ]; then
        fail 37 "ADR-$n.md not found"
        continue
    fi
    fm_status=$(awk '
        /^---[[:space:]]*$/ { fm++; next }
        fm == 1 && /^Status:/ { print substr($0, index($0, ":") + 1) }
        fm >= 2 { exit }
    ' "$adr_file" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')
    if [ "$fm_status" != "ACCEPTED" ]; then
        fail 37 "ADR-$n status is '$fm_status' (expected ACCEPTED for Phase 7)"
    fi
    if ! grep -qE "^Approver: .+" "$adr_file"; then
        fail 37 "ADR-$n missing non-empty Approver line"
    fi
done

# ─── Rule 38: Audit migration exists with tables + triggers + RLS ───────
AUDIT_MIG="$ROOT/src/noventra/apps/audit/migrations/0001_initial.py"
if [ ! -f "$AUDIT_MIG" ]; then
    fail 38 "Audit migration not found: $AUDIT_MIG"
else
    if ! grep -q "audit_event" "$AUDIT_MIG"; then
        fail 38 "Audit migration missing audit_event table"
    fi
    if ! grep -q "audit_chain_head" "$AUDIT_MIG"; then
        fail 38 "Audit migration missing audit_chain_head table"
    fi
    if ! grep -q "PARTITION BY RANGE" "$AUDIT_MIG"; then
        fail 38 "Audit migration does not partition audit_event"
    fi
    if ! grep -q "audit_compute_hash" "$AUDIT_MIG"; then
        fail 38 "Audit migration missing hash-chain computation function"
    fi
    if ! grep -q "BEFORE INSERT" "$AUDIT_MIG"; then
        fail 38 "Audit migration missing BEFORE INSERT trigger"
    fi
    if ! grep -q "audit_enforce_insert_only" "$AUDIT_MIG"; then
        fail 38 "Audit migration missing insert-only enforcement function"
    fi
    if ! grep -q "BEFORE UPDATE" "$AUDIT_MIG" || ! grep -q "BEFORE DELETE" "$AUDIT_MIG"; then
        fail 38 "Audit migration missing BEFORE UPDATE/DELETE triggers"
    fi
    if ! grep -q "GRANT INSERT, SELECT" "$AUDIT_MIG"; then
        fail 38 "Audit migration does not GRANT INSERT+SELECT only (insert-only)"
    fi
    if ! grep -q "ENABLE ROW LEVEL SECURITY" "$AUDIT_MIG"; then
        fail 38 "Audit migration does not enable RLS on audit_event"
    fi
fi

# ─── Rule 39: verify_audit_chain command exists + CI-integrated ────────
VERIFY_CMD="$ROOT/src/noventra/apps/core/management/commands/verify_audit_chain.py"
if [ ! -f "$VERIFY_CMD" ]; then
    fail 39 "verify_audit_chain command not found: $VERIFY_CMD"
else
    if ! grep -q "class Command" "$VERIFY_CMD"; then
        fail 39 "verify_audit_chain missing Command class"
    fi
    if ! grep -q "prev_hash" "$VERIFY_CMD"; then
        fail 39 "verify_audit_chain does not check hash continuity (prev_hash)"
    fi
    if ! grep -q "merkle" "$VERIFY_CMD" && ! grep -q "Merkle" "$VERIFY_CMD" && ! grep -q "_recompute_hash" "$VERIFY_CMD"; then
        fail 39 "verify_audit_chain does not check payload integrity (Merkle/recompute)"
    fi
    if ! grep -q "timestamp" "$VERIFY_CMD" && ! grep -q "monotonicity" "$VERIFY_CMD"; then
        fail 39 "verify_audit_chain does not check timestamp monotonicity"
    fi
    if ! grep -q "sys.exit(1)" "$VERIFY_CMD"; then
        fail 39 "verify_audit_chain does not exit non-zero on failure"
    fi
fi

# ─── Rule 40: Event type catalog closed (every code in catalog) ─────────
EVENT_TYPES="$ROOT/src/noventra/apps/audit/domain/event_types.py"
if [ ! -f "$EVENT_TYPES" ]; then
    fail 40 "Event type catalog not found: $EVENT_TYPES"
else
    if ! grep -q "class EventType" "$EVENT_TYPES"; then
        fail 40 "EventType enum not found in catalog"
    fi
    if ! grep -q "EVENT_TYPE_CATALOG" "$EVENT_TYPES"; then
        fail 40 "EVENT_TYPE_CATALOG tuple not found"
    fi
    if ! grep -q "class EventTypeCatalog" "$EVENT_TYPES"; then
        fail 40 "EventTypeCatalog class not found"
    fi
    # Verify all 5 categories present.
    for cat in auth tenancy rbac audit security; do
        if ! grep -q "\"${cat}\." "$EVENT_TYPES"; then
            fail 40 "Event type catalog missing category: $cat"
        fi
    done
fi

# ─── Rule 41: Redaction service + PII class-to-rule mapping ────────────
REDACTION_SVC="$ROOT/src/noventra/apps/audit/adapters/redaction.py"
if [ ! -f "$REDACTION_SVC" ]; then
    fail 41 "Redaction service not found: $REDACTION_SVC"
else
    if ! grep -q "REDACTION_RULES" "$REDACTION_SVC"; then
        fail 41 "REDACTION_RULES dict not found"
    fi
    if ! grep -q "def redact_payload" "$REDACTION_SVC"; then
        fail 41 "redact_payload function not found"
    fi
    if ! grep -q "def compute_merkle_root" "$REDACTION_SVC"; then
        fail 41 "compute_merkle_root function not found (Merkle-style)"
    fi
    if ! grep -q "def compute_field_hash" "$REDACTION_SVC"; then
        fail 41 "compute_field_hash function not found (per-field hashing)"
    fi
    # Verify PII fields from the register are mapped.
    for field in email full_name password ip_address; do
        if ! grep -q "\"$field\"" "$REDACTION_SVC"; then
            fail 41 "Redaction rules missing PII field: $field"
        fi
    done
fi

# ─── Rule 42: Audit read API + clearance model + meta-audit cut-off ────
AUDIT_API="$ROOT/src/noventra/apps/audit/api/views.py"
if [ ! -f "$AUDIT_API" ]; then
    fail 42 "Audit read API not found: $AUDIT_API"
else
    if ! grep -q "AuditLogView" "$AUDIT_API"; then
        fail 42 "AuditLogView class not found"
    fi
    if ! grep -q "_determine_clearance" "$AUDIT_API"; then
        fail 42 "Clearance model function not found"
    fi
    if ! grep -q "compliance_officer" "$AUDIT_API"; then
        fail 42 "compliance_officer clearance not implemented"
    fi
    if ! grep -q "external_auditor" "$AUDIT_API"; then
        fail 42 "external_auditor clearance not implemented"
    fi
    if ! grep -q "tenant_admin" "$AUDIT_API"; then
        fail 42 "tenant_admin clearance not implemented"
    fi
    if ! grep -q "cursor" "$AUDIT_API"; then
        fail 42 "Cursor-based pagination not implemented"
    fi
fi
AUDIT_MW="$ROOT/src/noventra/middleware/audit.py"
if [ ! -f "$AUDIT_MW" ]; then
    fail 42 "Audit middleware not found: $AUDIT_MW"
elif ! grep -q "_meta_audit_depth" "$AUDIT_MW"; then
    fail 42 "Meta-audit cut-off (_meta_audit_depth) not enforced in audit middleware"
fi

# ─── Rule 43: Phase 7 inventory (retention + redaction docs, tests) ───
required_phase7_files=(
    "$ROOT/src/noventra/apps/audit/domain/__init__.py"
    "$ROOT/src/noventra/apps/audit/domain/aggregates.py"
    "$ROOT/src/noventra/apps/audit/domain/event_types.py"
    "$ROOT/src/noventra/apps/audit/domain/ports.py"
    "$ROOT/src/noventra/apps/audit/adapters/orm.py"
    "$ROOT/src/noventra/apps/audit/adapters/redaction.py"
    "$ROOT/src/noventra/middleware/audit.py"
    "$ROOT/src/noventra/apps/audit/api/views.py"
    "$ROOT/src/noventra/apps/audit/api/urls.py"
    "$ROOT/docs/architecture/audit-retention-policy.md"
    "$ROOT/docs/architecture/audit-redaction-policy.md"
    "$ROOT/docs/stage-handoffs/stage-07-handoff.md"
    "$ROOT/docs/audits/phase-007-audit.md"
    "$ROOT/tests/test_audit_chain.py"
)
for f in "${required_phase7_files[@]}"; do
    if [ ! -f "$f" ]; then
        fail 43 "Phase 7 inventory file missing: $f"
    elif [ ! -s "$f" ]; then
        fail 43 "Phase 7 inventory file empty: $f"
    fi
done

# ═════════════════════════════════════════════════════════════════════════
# Phase 8 rules (44–52) — Increment 1 close
# ═════════════════════════════════════════════════════════════════════════

# ─── Rule 44: Phase 8 ADRs ACCEPTED (0040-0046) + ADR-0014 RESOLVED ───
for n in 0040 0041 0042 0043 0044 0045 0046; do
    adr_file="$ROOT/docs/adr/ADR-$n.md"
    if [ ! -f "$adr_file" ]; then
        fail 44 "ADR-$n.md not found"
        continue
    fi
    fm_status=$(awk '
        /^---[[:space:]]*$/ { fm++; next }
        fm == 1 && /^Status:/ { print substr($0, index($0, ":") + 1) }
        fm >= 2 { exit }
    ' "$adr_file" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')
    if [ "$fm_status" != "ACCEPTED" ]; then
        fail 44 "ADR-$n status is '$fm_status' (expected ACCEPTED for Phase 8)"
    fi
    if ! grep -qE "^Approver: .+" "$adr_file"; then
        fail 44 "ADR-$n missing non-empty Approver line"
    fi
done
# ADR-0014 RESOLVED (chronic deferral loop closed).
adr0014_status=$(awk '
    /^---[[:space:]]*$/ { fm++; next }
    fm == 1 && /^Status:/ { print substr($0, index($0, ":") + 1) }
    fm >= 2 { exit }
' "$ROOT/docs/adr/ADR-0014.md" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')
if [ "$adr0014_status" != "ACCEPTED" ]; then
    fail 44 "ADR-0014 status is '$adr0014_status' (expected ACCEPTED — chronic deferral loop closed)"
fi

# ─── Rule 45: Reliability migration exists with outbox + inbox + idempotency + RLS ─
RELIABILITY_MIG="$ROOT/src/noventra/apps/reliability/migrations/0001_initial.py"
if [ ! -f "$RELIABILITY_MIG" ]; then
    fail 45 "Reliability migration not found: $RELIABILITY_MIG"
else
    for table in reliability_outbox reliability_inbox reliability_idempotency_key; do
        if ! grep -q "$table" "$RELIABILITY_MIG"; then
            fail 45 "Reliability migration missing table: $table"
        fi
    done
    if ! grep -q "ENABLE ROW LEVEL SECURITY" "$RELIABILITY_MIG"; then
        fail 45 "Reliability migration does not enable RLS"
    fi
fi

# ─── Rule 46: Outbox relay exists with SELECT FOR UPDATE SKIP LOCKED ──
OUTBOX_RELAY="$ROOT/src/noventra/apps/reliability/adapters/outbox_relay.py"
if [ ! -f "$OUTBOX_RELAY" ]; then
    fail 46 "Outbox relay not found: $OUTBOX_RELAY"
else
    if ! grep -q "SKIP LOCKED" "$OUTBOX_RELAY"; then
        fail 46 "Outbox relay does not use SELECT FOR UPDATE SKIP LOCKED (multi-instance)"
    fi
    if ! grep -q "append_to_outbox" "$OUTBOX_RELAY"; then
        fail 46 "Outbox relay missing append_to_outbox function"
    fi
    if ! grep -q "relay_batch" "$OUTBOX_RELAY"; then
        fail 46 "Outbox relay missing relay_batch function"
    fi
fi

# ─── Rule 47: Consumer base + inbox dedup + DLQ consumer ───────────────
CONSUMER="$ROOT/src/noventra/apps/reliability/adapters/consumer.py"
if [ ! -f "$CONSUMER" ]; then
    fail 47 "Consumer base not found: $CONSUMER"
else
    if ! grep -q "class ConsumerBase" "$CONSUMER"; then
        fail 47 "ConsumerBase class not found"
    fi
    if ! grep -q "ON CONFLICT DO NOTHING" "$CONSUMER"; then
        fail 47 "Consumer does not use ON CONFLICT DO NOTHING (inbox dedup)"
    fi
    if ! grep -q "class DLQConsumer" "$CONSUMER"; then
        fail 47 "DLQConsumer class not found"
    fi
    if ! grep -q "send_to_dlq" "$CONSUMER"; then
        fail 47 "DLQConsumer missing send_to_dlq method"
    fi
fi

# ─── Rule 48: Idempotency middleware exists with conflict handling ────
IDEMPOTENCY_MW="$ROOT/src/noventra/middleware/idempotency.py"
if [ ! -f "$IDEMPOTENCY_MW" ]; then
    fail 48 "Idempotency middleware not found: $IDEMPOTENCY_MW"
else
    if ! grep -q "IdempotencyMiddleware" "$IDEMPOTENCY_MW"; then
        fail 48 "IdempotencyMiddleware class not found"
    fi
    if ! grep -q "Idempotency-Key" "$IDEMPOTENCY_MW"; then
        fail 48 "Idempotency middleware does not read Idempotency-Key header"
    fi
    if ! grep -q "noventra.idempotency.conflict" "$IDEMPOTENCY_MW"; then
        fail 48 "Idempotency middleware does not return 409 on conflict"
    fi
    if ! grep -q "request_hash" "$IDEMPOTENCY_MW"; then
        fail 48 "Idempotency middleware does not compute request_hash"
    fi
fi

# ─── Rule 49: State machine base exists with transition decorator ─────
STATE_MACHINE="$ROOT/src/noventra/apps/reliability/domain/state_machine.py"
if [ ! -f "$STATE_MACHINE" ]; then
    fail 49 "State machine base not found: $STATE_MACHINE"
else
    if ! grep -q "def transition" "$STATE_MACHINE"; then
        fail 49 "transition decorator not found"
    fi
    if ! grep -q "class StateMachineMixin" "$STATE_MACHINE"; then
        fail 49 "StateMachineMixin class not found"
    fi
    if ! grep -q "class TransitionError" "$STATE_MACHINE"; then
        fail 49 "TransitionError class not found"
    fi
    if ! grep -q "guard" "$STATE_MACHINE"; then
        fail 49 "State machine does not support guard pattern"
    fi
    if ! grep -q "_before_transition\|_after_transition" "$STATE_MACHINE"; then
        fail 49 "State machine missing side-effect hooks (_before/_after_transition)"
    fi
fi

# ─── Rule 50: Notifications port + adapters exist ─────────────────────
NOTIFICATIONS="$ROOT/src/noventra/apps/reliability/domain/notifications.py"
NOTIF_ADAPTERS="$ROOT/src/noventra/apps/reliability/adapters/notifications.py"
if [ ! -f "$NOTIFICATIONS" ]; then
    fail 50 "Notifications port not found: $NOTIFICATIONS"
else
    if ! grep -q "class NotificationPort" "$NOTIFICATIONS"; then
        fail 50 "NotificationPort class not found"
    fi
    if ! grep -q "class SendResult" "$NOTIFICATIONS"; then
        fail 50 "SendResult class not found"
    fi
    if ! grep -q "class NotificationChannel" "$NOTIFICATIONS"; then
        fail 50 "NotificationChannel enum not found"
    fi
    if ! grep -q "class SendType" "$NOTIFICATIONS"; then
        fail 50 "SendType enum not found (send-type taxonomy)"
    fi
fi
if [ ! -f "$NOTIF_ADAPTERS" ]; then
    fail 50 "Notification adapters not found: $NOTIF_ADAPTERS"
elif ! grep -q "EmailStubAdapter" "$NOTIF_ADAPTERS" || ! grep -q "SMSStubAdapter" "$NOTIF_ADAPTERS"; then
    fail 50 "Email/SMS stub adapters not found"
fi

# ─── Rule 51: MarketingGate exists with suppression + caps ────────────
MARKETING_GATE="$ROOT/src/noventra/apps/reliability/domain/marketing_gate.py"
if [ ! -f "$MARKETING_GATE" ]; then
    fail 51 "MarketingGate not found: $MARKETING_GATE"
else
    if ! grep -q "class MarketingGate" "$MARKETING_GATE"; then
        fail 51 "MarketingGate class not found"
    fi
    if ! grep -q "class GateDecision" "$MARKETING_GATE"; then
        fail 51 "GateDecision class not found"
    fi
    if ! grep -q "DENY_SUPPRESSION" "$MARKETING_GATE"; then
        fail 51 "MarketingGate does not deny on suppression"
    fi
    if ! grep -q "DENY_CAP" "$MARKETING_GATE"; then
        fail 51 "MarketingGate does not deny on cap exceeded"
    fi
    if ! grep -q "transactional" "$MARKETING_GATE"; then
        fail 51 "MarketingGate does not distinguish transactional send type"
    fi
    if ! grep -q "marketing" "$MARKETING_GATE"; then
        fail 51 "MarketingGate does not distinguish marketing send type"
    fi
fi

# ─── Rule 52: Phase 8 inventory (event schema, tests, handoff, audit, increment close) ─
required_phase8_files=(
    "$ROOT/src/noventra/apps/reliability/domain/__init__.py"
    "$ROOT/src/noventra/apps/reliability/domain/outbox.py"
    "$ROOT/src/noventra/apps/reliability/domain/inbox.py"
    "$ROOT/src/noventra/apps/reliability/domain/idempotency.py"
    "$ROOT/src/noventra/apps/reliability/domain/notifications.py"
    "$ROOT/src/noventra/apps/reliability/domain/marketing_gate.py"
    "$ROOT/src/noventra/apps/reliability/domain/state_machine.py"
    "$ROOT/src/noventra/apps/reliability/adapters/orm.py"
    "$ROOT/src/noventra/apps/reliability/adapters/outbox_relay.py"
    "$ROOT/src/noventra/apps/reliability/adapters/consumer.py"
    "$ROOT/src/noventra/apps/reliability/adapters/notifications.py"
    "$ROOT/src/noventra/middleware/idempotency.py"
    "$ROOT/docs/architecture/event-schema.md"
    "$ROOT/docs/stage-handoffs/stage-08-handoff.md"
    "$ROOT/docs/audits/phase-008-audit.md"
    "$ROOT/docs/audits/increment-1-close.md"
    "$ROOT/tests/test_reliability_core.py"
)
for f in "${required_phase8_files[@]}"; do
    if [ ! -f "$f" ]; then
        fail 52 "Phase 8 inventory file missing: $f"
    elif [ ! -s "$f" ]; then
        fail 52 "Phase 8 inventory file empty: $f"
    fi
done

# ═════════════════════════════════════════════════════════════════════════
# Phase 9 rules (53–60) — Players & Consents (Increment 2 start)
# ═════════════════════════════════════════════════════════════════════════

# ─── Rule 53: Phase 9 ADRs ACCEPTED (0047-0051) + ADR-0046 amended ───
for n in 0047 0048 0049 0050 0051; do
    adr_file="$ROOT/docs/adr/ADR-$n.md"
    if [ ! -f "$adr_file" ]; then
        fail 53 "ADR-$n.md not found"
        continue
    fi
    fm_status=$(awk '
        /^---[[:space:]]*$/ { fm++; next }
        fm == 1 && /^Status:/ { print substr($0, index($0, ":") + 1) }
        fm >= 2 { exit }
    ' "$adr_file" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')
    if [ "$fm_status" != "ACCEPTED" ]; then
        fail 53 "ADR-$n status is '$fm_status' (expected ACCEPTED for Phase 9)"
    fi
    if ! grep -qE "^Approver: .+" "$adr_file"; then
        fail 53 "ADR-$n missing non-empty Approver line"
    fi
done

# ─── Rule 54: Players migration exists with tables + RLS + insert-only ─
PLAYERS_MIG="$ROOT/src/noventra/apps/players/migrations/0001_initial.py"
if [ ! -f "$PLAYERS_MIG" ]; then
    fail 54 "Players migration not found: $PLAYERS_MIG"
else
    if ! grep -q "players_player" "$PLAYERS_MIG"; then
        fail 54 "Players migration missing players_player table"
    fi
    if ! grep -q "players_consent" "$PLAYERS_MIG"; then
        fail 54 "Players migration missing players_consent table"
    fi
    if ! grep -q "ENABLE ROW LEVEL SECURITY" "$PLAYERS_MIG"; then
        fail 54 "Players migration does not enable RLS"
    fi
    if ! grep -q "consent_enforce_insert_only" "$PLAYERS_MIG"; then
        fail 54 "Players migration missing consent insert-only trigger"
    fi
fi

# ─── Rule 55: Player FSM exists with 8 states + transitions ───────────
PLAYER_FSM="$ROOT/src/noventra/apps/players/domain/player.py"
if [ ! -f "$PLAYER_FSM" ]; then
    fail 55 "Player FSM not found: $PLAYER_FSM"
else
    if ! grep -q "class PlayerState" "$PLAYER_FSM"; then
        fail 55 "PlayerState enum not found"
    fi
    for state in prospect registered active suspended self_excluded dormant closed deleted; do
        if ! grep -q "$state" "$PLAYER_FSM"; then
            fail 55 "PlayerState missing state: $state"
        fi
    done
    if ! grep -q "@transition" "$PLAYER_FSM"; then
        fail 55 "Player FSM missing @transition decorators"
    fi
    if ! grep -q "cooling_off" "$PLAYER_FSM"; then
        fail 55 "Player FSM missing self-exclusion cooling-off guard"
    fi
fi

# ─── Rule 56: Consent schema + immutability + versioning ──────────────
CONSENT_DOMAIN="$ROOT/src/noventra/apps/players/domain/consent.py"
if [ ! -f "$CONSENT_DOMAIN" ]; then
    fail 56 "Consent domain not found: $CONSENT_DOMAIN"
else
    if ! grep -q "class ConsentStatus" "$CONSENT_DOMAIN"; then
        fail 56 "ConsentStatus enum not found"
    fi
    for status in granted revoked expired pending; do
        if ! grep -q "$status" "$CONSENT_DOMAIN"; then
            fail 56 "ConsentStatus missing: $status"
        fi
    done
    if ! grep -q "class ConsentPurpose" "$CONSENT_DOMAIN"; then
        fail 56 "ConsentPurpose catalog not found"
    fi
    if ! grep -q "policy_version" "$CONSENT_DOMAIN"; then
        fail 56 "Consent schema missing policy_version (versioning)"
    fi
    if ! grep -q "consent_text_hash" "$CONSENT_DOMAIN"; then
        fail 56 "Consent schema missing consent_text_hash"
    fi
    if ! grep -q "prev_hash" "$CONSENT_DOMAIN"; then
        fail 56 "Consent schema missing hash-chain fields (immutability per ADR-0049)"
    fi
fi

# ─── Rule 57: Retention model + management commands ───────────────────
RETENTION_DOMAIN="$ROOT/src/noventra/apps/players/domain/retention.py"
if [ ! -f "$RETENTION_DOMAIN" ]; then
    fail 57 "Retention domain not found: $RETENTION_DOMAIN"
elif ! grep -q "class DataClass" "$RETENTION_DOMAIN"; then
    fail 57 "DataClass enum not found"
elif ! grep -q "DEFAULT_RETENTION_DAYS" "$RETENTION_DOMAIN"; then
    fail 57 "DEFAULT_RETENTION_DAYS not found"
fi
for cmd in erase_player export_player_data enforce_retention; do
    cmd_file="$ROOT/src/noventra/apps/players/management/commands/${cmd}.py"
    if [ ! -f "$cmd_file" ]; then
        fail 57 "Management command not found: $cmd_file"
    elif ! grep -q "class Command" "$cmd_file"; then
        fail 57 "$cmd missing Command class"
    fi
done

# ─── Rule 58: MarketingGate amended with consent check ────────────────
MARKETING_GATE="$ROOT/src/noventra/apps/reliability/domain/marketing_gate.py"
if [ ! -f "$MARKETING_GATE" ]; then
    fail 58 "MarketingGate not found: $MARKETING_GATE"
else
    if ! grep -q "DENY_CONSENT" "$MARKETING_GATE"; then
        fail 58 "MarketingGate missing DENY_CONSENT (Phase 9 amendment)"
    fi
    # DENY_JURISDICTION removed per DEC-0157 (Global Mode)
    if ! grep -q "ConsentChecker" "$MARKETING_GATE"; then
        fail 58 "MarketingGate missing ConsentChecker (Phase 9 amendment)"
    fi
    if ! grep -q "consent_checker" "$MARKETING_GATE"; then
        fail 58 "MarketingGate missing consent_checker parameter"
    fi
fi

# ─── Rule 59: Audit event taxonomy extended with player/consent/retention ─
EVENT_TYPES="$ROOT/src/noventra/apps/audit/domain/event_types.py"
if [ ! -f "$EVENT_TYPES" ]; then
    fail 59 "Event types not found: $EVENT_TYPES"
else
    for cat in player consent retention; do
        if ! grep -q "\"${cat}\." "$EVENT_TYPES"; then
            fail 59 "Event type catalog missing category: $cat"
        fi
    done
    # Verify key player events.
    for evt in player.registered player.erasure_completed player.dsar_completed consent.granted consent.revoked retention.enforcement_completed; do
        if ! grep -q "$evt" "$EVENT_TYPES"; then
            fail 59 "Event type catalog missing: $evt"
        fi
    done
fi

# ─── Rule 60: Phase 9 inventory (tests, handoff, audit) ───────────────
required_phase9_files=(
    "$ROOT/src/noventra/apps/players/__init__.py"
    "$ROOT/src/noventra/apps/players/apps.py"
    "$ROOT/src/noventra/apps/players/domain/player.py"
    "$ROOT/src/noventra/apps/players/domain/consent.py"
    "$ROOT/src/noventra/apps/players/domain/retention.py"
    "$ROOT/src/noventra/apps/players/adapters/orm.py"
    "$ROOT/src/noventra/apps/players/migrations/0001_initial.py"
    "$ROOT/src/noventra/apps/players/management/commands/erase_player.py"
    "$ROOT/src/noventra/apps/players/management/commands/export_player_data.py"
    "$ROOT/src/noventra/apps/players/management/commands/enforce_retention.py"
    "$ROOT/docs/stage-handoffs/stage-09-handoff.md"
    "$ROOT/docs/audits/phase-009-audit.md"
    "$ROOT/tests/test_players_consents.py"
)
for f in "${required_phase9_files[@]}"; do
    if [ ! -f "$f" ]; then
        fail 60 "Phase 9 inventory file missing: $f"
    elif [ ! -s "$f" ]; then
        fail 60 "Phase 9 inventory file empty: $f"
    fi
done

# ═════════════════════════════════════════════════════════════════════════
# Phase 10 rules (61–70) — KYC & Documents (Increment 2 second pillar)
# ═════════════════════════════════════════════════════════════════════════

# ─── Rule 61: Stage N parenthetical convention + Phase 10 ADRs ─────────
# Closes chronic convention violation (9-round). Verifies ADR-0052..0058 ACCEPTED.
for n in 0052 0053 0054 0055 0056 0057 0058; do
    adr_file="$ROOT/docs/adr/ADR-$n.md"
    if [ ! -f "$adr_file" ]; then
        fail 61 "ADR-$n.md not found"
        continue
    fi
    fm_status=$(awk '
        /^---[[:space:]]*$/ { fm++; next }
        fm == 1 && /^Status:/ { print substr($0, index($0, ":") + 1) }
        fm >= 2 { exit }
    ' "$adr_file" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')
    if [ "$fm_status" != "ACCEPTED" ]; then
        fail 61 "ADR-$n status is '$fm_status' (expected ACCEPTED for Phase 10)"
    fi
    if ! grep -qE "^Approver: .+" "$adr_file"; then
        fail 61 "ADR-$n missing non-empty Approver line"
    fi
done

# ─── Rule 62: KYC case FSM exists with 16 states + regulatory constraints ──
KYC_FSM="$ROOT/src/noventra/apps/kyc/domain/kyc_case.py"
if [ ! -f "$KYC_FSM" ]; then
    fail 62 "KYC case FSM not found: $KYC_FSM"
else
    if ! grep -q "class KycCaseState" "$KYC_FSM"; then
        fail 62 "KycCaseState enum not found"
    fi
    for state in pending_submission submitted auto_verified auto_rejected in_review ed_triggered pep_flagged sanctions_flagged escalated closed_approved closed_rejected suspended_pending_sar; do
        if ! grep -q "$state" "$KYC_FSM"; then
            fail 62 "KycCaseState missing state: $state"
        fi
    done
    if ! grep -q "@transition" "$KYC_FSM"; then
        fail 62 "KYC FSM missing @transition decorators"
    fi
    if ! grep -q "flag_pep\|pep_to_edd" "$KYC_FSM"; then
        fail 62 "KYC FSM missing PEP → EDD regulatory constraint"
    fi
    if ! grep -q "flag_sanctions\|escalate_to_mlro" "$KYC_FSM"; then
        fail 62 "KYC FSM missing sanctions → escalate regulatory constraint"
    fi
    if ! grep -q "check_risk_for_edd" "$KYC_FSM"; then
        fail 62 "KYC FSM missing risk > threshold → EDD check"
    fi
fi

# ─── Rule 63: Document model + versioning + types ──────────────────────
DOC_DOMAIN="$ROOT/src/noventra/apps/kyc/domain/document.py"
if [ ! -f "$DOC_DOMAIN" ]; then
    fail 63 "Document domain not found: $DOC_DOMAIN"
else
    if ! grep -q "class DocumentType" "$DOC_DOMAIN"; then
        fail 63 "DocumentType enum not found"
    fi
    for dt in passport national_id driver_license utility_bill bank_statement tax_document selfie; do
        if ! grep -q "$dt" "$DOC_DOMAIN"; then
            fail 63 "DocumentType missing: $dt"
        fi
    done
    if ! grep -q "class DocumentVersion" "$DOC_DOMAIN"; then
        fail 63 "DocumentVersion class not found"
    fi
    if ! grep -q "is_superseded" "$DOC_DOMAIN"; then
        fail 63 "DocumentVersion missing is_superseded (versioning)"
    fi
    if ! grep -q "is_revoked" "$DOC_DOMAIN"; then
        fail 63 "DocumentVersion missing is_revoked (revocation per ADR-0055)"
    fi
    if ! grep -q "encryption_key_id" "$DOC_DOMAIN"; then
        fail 63 "DocumentVersion missing encryption_key_id (crypto shredding per ADR-0055)"
    fi
fi

# ─── Rule 64: Storage port + stub adapter ──────────────────────────────
STORAGE_PORT="$ROOT/src/noventra/apps/kyc/domain/storage_port.py"
STORAGE_STUB="$ROOT/src/noventra/apps/kyc/adapters/storage_stub.py"
if [ ! -f "$STORAGE_PORT" ]; then
    fail 64 "Storage port not found: $STORAGE_PORT"
else
    for method in "def put" "def get" "def delete" "def head"; do
        if ! grep -q "$method" "$STORAGE_PORT"; then
            fail 64 "StoragePort missing method: $method"
        fi
    done
fi
if [ ! -f "$STORAGE_STUB" ]; then
    fail 64 "Stub storage adapter not found: $STORAGE_STUB"
elif ! grep -q "class StubStorageAdapter" "$STORAGE_STUB"; then
    fail 64 "StubStorageAdapter class not found"
fi

# ─── Rule 65: AML/CFT domain exists with screening + SAR ───────────────
AML_DOMAIN="$ROOT/src/noventra/apps/kyc/domain/aml.py"
if [ ! -f "$AML_DOMAIN" ]; then
    fail 65 "AML domain not found: $AML_DOMAIN"
else
    if ! grep -q "class ScreeningResult" "$AML_DOMAIN"; then
        fail 65 "ScreeningResult class not found"
    fi
    if ! grep -q "class AmlResult" "$AML_DOMAIN"; then
        fail 65 "AmlResult class not found"
    fi
    if ! grep -q "class SarRecord" "$AML_DOMAIN"; then
        fail 65 "SarRecord class not found"
    fi
    if ! grep -q "mlro_restricted" "$AML_DOMAIN"; then
        fail 65 "SarRecord missing mlro_restricted (MLRO-only visibility per ADR-0058)"
    fi
    if ! grep -q "ScreeningType" "$AML_DOMAIN"; then
        fail 65 "ScreeningType enum not found (PEP/sanctions)"
    fi
fi

# ─── Rule 66: Review queue domain exists with SLA + escalation ─────────
REVIEW_DOMAIN="$ROOT/src/noventra/apps/kyc/domain/review_queue.py"
if [ ! -f "$REVIEW_DOMAIN" ]; then
    fail 66 "Review queue domain not found: $REVIEW_DOMAIN"
else
    if ! grep -q "class ReviewQueueEntry" "$REVIEW_DOMAIN"; then
        fail 66 "ReviewQueueEntry class not found"
    fi
    if ! grep -q "class ReviewDecision" "$REVIEW_DOMAIN"; then
        fail 66 "ReviewDecision enum not found"
    fi
    if ! grep -q "sla_deadline" "$REVIEW_DOMAIN"; then
        fail 66 "ReviewQueueEntry missing sla_deadline (SLA tracking)"
    fi
    if ! grep -q "is_sla_breached" "$REVIEW_DOMAIN"; then
        fail 66 "ReviewQueueEntry missing is_sla_breached property"
    fi
    if ! grep -q "escalated" "$REVIEW_DOMAIN"; then
        fail 66 "ReviewQueueEntry missing escalated field (escalation path)"
    fi
    if ! grep -q "mlro" "$REVIEW_DOMAIN"; then
        fail 66 "ReviewQueueEntry missing MLRO escalation target"
    fi
fi

# ─── Rule 67: Audit event taxonomy extended with kyc/document/aml/review/sar ─
EVENT_TYPES="$ROOT/src/noventra/apps/audit/domain/event_types.py"
if [ ! -f "$EVENT_TYPES" ]; then
    fail 67 "Event types not found: $EVENT_TYPES"
else
    for cat in kyc document aml review sar; do
        if ! grep -q "\"${cat}\." "$EVENT_TYPES"; then
            fail 67 "Event type catalog missing category: $cat"
        fi
    done
    # Verify SAR events exist with MLRO restriction note.
    if ! grep -q "sar.filed" "$EVENT_TYPES"; then
        fail 67 "Event type catalog missing sar.filed"
    fi
fi

# ─── Rule 68: KYC app added to INSTALLED_APPS ──────────────────────────
if ! grep -q "noventra.apps.kyc" "$ROOT/src/noventra/settings/base.py"; then
    fail 68 "KYC app not added to INSTALLED_APPS"
fi

# ─── Rule 69: KYC apps.py exists ───────────────────────────────────────
KYC_APPS="$ROOT/src/noventra/apps/kyc/apps.py"
if [ ! -f "$KYC_APPS" ]; then
    fail 69 "KYC apps.py not found"
elif ! grep -q "class KycConfig" "$KYC_APPS"; then
    fail 69 "KycConfig class not found"
fi

# ─── Rule 70: Phase 10 inventory (tests, handoff, audit) ───────────────
required_phase10_files=(
    "$ROOT/src/noventra/apps/kyc/__init__.py"
    "$ROOT/src/noventra/apps/kyc/apps.py"
    "$ROOT/src/noventra/apps/kyc/domain/__init__.py"
    "$ROOT/src/noventra/apps/kyc/domain/kyc_case.py"
    "$ROOT/src/noventra/apps/kyc/domain/document.py"
    "$ROOT/src/noventra/apps/kyc/domain/aml.py"
    "$ROOT/src/noventra/apps/kyc/domain/review_queue.py"
    "$ROOT/src/noventra/apps/kyc/domain/storage_port.py"
    "$ROOT/src/noventra/apps/kyc/adapters/storage_stub.py"
    "$ROOT/docs/stage-handoffs/stage-10-handoff.md"
    "$ROOT/docs/audits/phase-010-audit.md"
    "$ROOT/tests/test_kyc_documents.py"
)
for f in "${required_phase10_files[@]}"; do
    if [ ! -f "$f" ]; then
        fail 70 "Phase 10 inventory file missing: $f"
    elif [ ! -s "$f" ]; then
        fail 70 "Phase 10 inventory file empty: $f"
    fi
done

# ═════════════════════════════════════════════════════════════════════════
# Phase 11-13 rules (71–100) — Ledger, FX, Payments, Bonuses
# ═════════════════════════════════════════════════════════════════════════

# ─── Rule 71: Ledger double-entry balance check exists ─────────────────
LEDGER_SVC="$ROOT/src/noventra/modules/ledger/services.py"
if [ ! -f "$LEDGER_SVC" ]; then
    fail 71 "Ledger services not found (Phase 11 Stage B BLOCKED)"
elif ! grep -q "amount_minor" "$LEDGER_SVC"; then
    fail 71 "Ledger services missing amount handling (double-entry balance)"
fi

# ─── Rule 72: Reversal references source_ref ───────────────────────────
if [ -f "$LEDGER_SVC" ]; then
    if grep -q "REVERSAL" "$LEDGER_SVC" && ! grep -q "source_ref" "$LEDGER_SVC"; then
        fail 72 "ReversalService handles REVERSAL but does not reference source_ref"
    fi
fi

# ─── Rule 73: No UPDATE/DELETE on ledger tables (grep) ─────────────────
LEDGER_UPDATES=$(grep -rn "UPDATE.*ledger_journal\|DELETE.*ledger_journal" "$ROOT/src/noventra/modules/ledger/" 2>/dev/null | grep -v "migrations/\|reconciliation_log\|REVERSED\|CREATE TRIGGER\|GRANT\|BEFORE" | head -1)
if [ -n "$LEDGER_UPDATES" ]; then
    fail 73 "UPDATE/DELETE found on ledger journal tables (immutability violation): $LEDGER_UPDATES"
fi

# ─── Rule 74: Cross-currency fx_pair_id check ──────────────────────────
LEDGER_MODELS="$ROOT/src/noventra/modules/ledger/models.py"
if [ -f "$LEDGER_MODELS" ]; then
    if ! grep -q "fx_pair_id" "$LEDGER_MODELS"; then
        fail 74 "Ledger models missing fx_pair_id (cross-currency requirement)"
    fi
fi

# ─── Rule 75: Every ledger model has tenant_uuid ───────────────────────
if [ -f "$LEDGER_MODELS" ]; then
    if ! grep -q "tenant_uuid" "$LEDGER_MODELS"; then
        fail 75 "Ledger models missing tenant_uuid (RLS requirement)"
    fi
fi

# ─── Rule 76: Player account CHECK >= 0 in migration ───────────────────
LEDGER_MIG="$ROOT/src/noventra/modules/ledger/migrations/0001_initial.py"
if [ -f "$LEDGER_MIG" ]; then
    if ! grep -q "balance_minor" "$LEDGER_MIG"; then
        fail 76 "Ledger migration missing balance_minor (overdraft CHECK requirement)"
    fi
fi

# ─── Rule 77: FinancialAuditEvent has correlation_id ───────────────────
if [ -f "$LEDGER_MODELS" ]; then
    if ! grep -q "correlation_id" "$LEDGER_MODELS"; then
        fail 77 "Ledger models missing correlation_id on FinancialAuditEvent"
    fi
fi

# ─── Rule 78: No FloatField/DecimalField in ledger/fx ──────────────────
FLOAT_FINDINGS=$(grep -rn "FloatField\|DecimalField" "$ROOT/src/noventra/modules/ledger/" "$ROOT/src/noventra/modules/fx/" 2>/dev/null | head -1)
if [ -n "$FLOAT_FINDINGS" ]; then
    fail 78 "FloatField/DecimalField found in ledger/fx code (integer minor units only)"
fi

# ─── Rule 79: Financial audit chain verifier exists ────────────────────
FINANCIAL_VERIFIER="$ROOT/src/noventra/modules/ledger"
if [ ! -d "$FINANCIAL_VERIFIER" ]; then
    fail 79 "Ledger module not found (financial audit chain verifier pending Phase 11 Stage B)"
fi

# ─── Rule 80: noventra_auditor grants in migration ─────────────────────
if [ -f "$LEDGER_MIG" ]; then
    if ! grep -q "noventra_admin\|noventra_app" "$LEDGER_MIG"; then
        fail 80 "Ledger migration missing role grants"
    fi
fi

# ─── Rule 81: No card field names in code ──────────────────────────────
CARD_FIELDS=$(grep -rn -i "card_number\|pan\b\|cvv\|cvc\|expiry_month\|expiry_year\|track_data\|magstripe" "$ROOT/src/" 2>/dev/null | grep -v "test\|migration\|__pycache__\|\.pyc" | head -1)
if [ -n "$CARD_FIELDS" ]; then
    fail 81 "Card field name found in code (PCI SAQ-A violation): $CARD_FIELDS"
fi

# ─── Rule 82: Key separation (sk_test/sk_live) ─────────────────────────
KEY_TEST=$(grep -rn "sk_test_\|sk_live_" "$ROOT/src/" 2>/dev/null | head -1)
if [ -n "$KEY_TEST" ]; then
    fail 82 "PSP key found in source code (must be env-only): $KEY_TEST"
fi

# ─── Rule 83: Webhook signature verification spec exists ───────────────
PAYMENTS_DESIGN="$ROOT/docs/architecture/payments-design.md"
if [ ! -f "$PAYMENTS_DESIGN" ]; then
    fail 83 "Payments design doc not found (webhook signature spec)"
elif ! grep -q "HMAC-SHA256" "$PAYMENTS_DESIGN"; then
    fail 83 "Payments design doc missing HMAC-SHA256 webhook signature spec"
fi

# ─── Rule 84: Webhook dedup spec exists ────────────────────────────────
if [ -f "$PAYMENTS_DESIGN" ]; then
    if ! grep -q "nonce\|idempot" "$PAYMENTS_DESIGN"; then
        fail 84 "Payments design doc missing webhook dedup/idempotency spec"
    fi
fi

# ─── Rule 85: Payment-ledger posting spec exists ───────────────────────
if [ -f "$PAYMENTS_DESIGN" ]; then
    if ! grep -q "ledger" "$PAYMENTS_DESIGN"; then
        fail 85 "Payments design doc missing ledger posting contract"
    fi
fi

# ─── Rule 86: Dispute FSM spec exists ──────────────────────────────────
if [ -f "$PAYMENTS_DESIGN" ]; then
    if ! grep -q "dispute\|chargeback" "$PAYMENTS_DESIGN"; then
        fail 86 "Payments design doc missing dispute/chargeback spec"
    fi
fi

# ─── Rule 87: PSP port spec exists ─────────────────────────────────────
if [ -f "$PAYMENTS_DESIGN" ]; then
    if ! grep -q "PspPort\|PSP.*port" "$PAYMENTS_DESIGN"; then
        fail 87 "Payments design doc missing PSP port spec"
    fi
fi

# ─── Rule 88: DLP redaction exists (Phase 4 redaction.py) ──────────────
REDACTION="$ROOT/src/noventra/observability/redaction.py"
if [ ! -f "$REDACTION" ]; then
    fail 88 "DLP redaction not found (Phase 4 redaction.py)"
elif ! grep -q "SECRET_PATTERNS\|REDACTED" "$REDACTION"; then
    fail 88 "DLP redaction missing patterns or REDACTED output"
fi

# ─── Rule 89: FX rate locking spec exists ──────────────────────────────
LEDGER_DESIGN="$ROOT/docs/architecture/ledger-design.md"
if [ -f "$LEDGER_DESIGN" ]; then
    if ! grep -q "fx.*lock\|locked.*posting\|fx_pair_id" "$LEDGER_DESIGN"; then
        fail 89 "Ledger design doc missing FX rate locking spec"
    fi
fi

# ─── Rule 90: Reconciliation spec exists ───────────────────────────────
if [ -f "$LEDGER_DESIGN" ]; then
    if ! grep -q "reconcil" "$LEDGER_DESIGN"; then
        fail 90 "Ledger design doc missing reconciliation spec"
    fi
fi

# ─── Rules 91-100: Phase 13 Bonuses (Stage A design checks) ────────────

# ─── Rule 91: Bonuses module exists ────────────────────────────────────
BONUSES_DIR="$ROOT/src/noventra/modules/bonuses"
if [ ! -d "$BONUSES_DIR" ]; then
    fail 91 "Bonuses module not found"
elif [ ! -f "$BONUSES_DIR/domain/offer.py" ]; then
    fail 91 "Bonuses domain/offer.py not found"
fi

# ─── Rule 92: Bonus offer FSM with 7 types ─────────────────────────────
OFFER_DOMAIN="$ROOT/src/noventra/modules/bonuses/domain/offer.py"
if [ -f "$OFFER_DOMAIN" ]; then
    for otype in deposit_match free_spins free_bet cashback reload refer_friend no_deposit; do
        if ! grep -q "$otype" "$OFFER_DOMAIN"; then
            fail 92 "Bonus offer catalog missing type: $otype"
        fi
    done
    if ! grep -q "@transition" "$OFFER_DOMAIN"; then
        fail 92 "Bonus offer missing @transition decorators (FSM)"
    fi
    if ! grep -q "revoke" "$OFFER_DOMAIN"; then
        fail 92 "Bonus offer missing revoke transition (synchronous revocation per Law 10)"
    fi
fi

# ─── Rule 93: Bonus award with wagering requirements ───────────────────
AWARD_DOMAIN="$ROOT/src/noventra/modules/bonuses/domain/award.py"
if [ -f "$AWARD_DOMAIN" ]; then
    if ! grep -q "wagering_requirement" "$AWARD_DOMAIN"; then
        fail 93 "Bonus award missing wagering_requirement"
    fi
    if ! grep -q "max_bet_during_wagering" "$AWARD_DOMAIN"; then
        fail 93 "Bonus award missing max_bet_during_wagering (UK GC mandate)"
    fi
    if ! grep -q "bonus.*first\|bonus_first" "$AWARD_DOMAIN"; then
        fail 93 "Bonus award missing bonus-first consumption order"
    fi
    if ! grep -q "convert" "$AWARD_DOMAIN"; then
        fail 93 "Bonus award missing convert method (bonus→real conversion)"
    fi
fi

# ─── Rule 94: Port interfaces exist (RG, Realtime) ────────────────────
PORTS="$ROOT/src/noventra/modules/bonuses/domain/ports.py"
if [ ! -f "$PORTS" ]; then
    fail 94 "Bonus port interfaces not found"
else
    for port in RGPort RealtimePort; do
        if ! grep -q "class $port" "$PORTS"; then
            fail 94 "Port interface missing: $port"
        fi
    done
fi

# ─── Rule 95: Stub adapters exist ──────────────────────────────────────
STUBS="$ROOT/src/noventra/modules/bonuses/adapters/stubs.py"
if [ ! -f "$STUBS" ]; then
    fail 95 "Bonus stub adapters not found"
else
    for stub in StubRGAdapter StubRealtimeAdapter; do
        if ! grep -q "class $stub" "$STUBS"; then
            fail 95 "Stub adapter missing: $stub"
        fi
    done
fi

# ─── Rule 96: Phase 13 ADRs PROPOSED (0078-0083) ───────────────────────
for n in 0078 0079 0080 0081 0082 0083; do
    adr_file="$ROOT/docs/adr/ADR-$n.md"
    if [ ! -f "$adr_file" ]; then
        fail 96 "ADR-$n.md not found"
        continue
    fi
    fm_status=$(awk '
        /^---[[:space:]]*$/ { fm++; next }
        fm == 1 && /^Status:/ { print substr($0, index($0, ":") + 1) }
        fm >= 2 { exit }
    ' "$adr_file" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')
    if [ "$fm_status" != "PROPOSED" ]; then
        fail 96 "ADR-$n status is '$fm_status' (expected PROPOSED for Phase 13 Stage A)"
    fi
done

# ─── Rule 97: Bonuses design doc exists ────────────────────────────────
BONUSES_DESIGN="$ROOT/docs/architecture/bonuses-design.md"
if [ ! -f "$BONUSES_DESIGN" ]; then
    fail 97 "Bonuses design doc not found"
fi

# ─── Rule 98: Phase 13 handoff exists ──────────────────────────────────
if [ ! -f "$ROOT/docs/stage-handoffs/stage-13-handoff.md" ]; then
    fail 98 "stage-13-handoff.md not found"
fi

# ─── Rule 99: Phase 13 audit exists ────────────────────────────────────
if [ ! -f "$ROOT/docs/audits/phase-013-audit.md" ]; then
    fail 99 "phase-013-audit.md not found"
fi

# ─── Rule 100: No floats in bonuses module ─────────────────────────────
BONUS_FLOATS=$(grep -rn "FloatField\|DecimalField\|float\b" "$ROOT/src/noventra/modules/bonuses/" 2>/dev/null | grep -v "game_class_contribution\|__pycache__\|\.pyc" | head -1)
if [ -n "$BONUS_FLOATS" ]; then
    fail 100 "Float/Decimal found in bonuses module (integer minor units only): $BONUS_FLOATS"
fi

# ═════════════════════════════════════════════════════════════════════════
# Phase 14 rules (101–110) — Protection (behavior-enforcing)
# ═════════════════════════════════════════════════════════════════════════

# ─── Rule 101: Protection module exists with domain models ─────────────
PROTECTION_DIR="$ROOT/src/noventra/modules/protection"
if [ ! -d "$PROTECTION_DIR" ]; then
    fail 101 "Protection module not found"
else
    for f in limits.py self_exclusion.py reality_check.py kill_switch.py ports.py; do
        if [ ! -f "$PROTECTION_DIR/domain/$f" ]; then
            fail 101 "Protection domain/$f not found"
        fi
    done
fi

# ─── Rule 102: PlayerLimit has 4 limit types + tightening/loosening ────
LIMITS="$ROOT/src/noventra/modules/protection/domain/limits.py"
if [ -f "$LIMITS" ]; then
    for lt in deposit loss wagering session_time; do
        if ! grep -q "$lt" "$LIMITS"; then
            fail 102 "PlayerLimit missing limit type: $lt"
        fi
    done
    if ! grep -q "tighten" "$LIMITS"; then
        fail 102 "PlayerLimit missing tighten method (instant limit reduction)"
    fi
    if ! grep -q "loosen" "$LIMITS"; then
        fail 102 "PlayerLimit missing loosen method (cooling-off limit increase)"
    fi
    if ! grep -q "cooling_off" "$LIMITS"; then
        fail 102 "PlayerLimit missing cooling-off for loosening"
    fi
fi

# ─── Rule 103: SelfExclusion has HMAC + SE-survives-erasure ────────────
SE="$ROOT/src/noventra/modules/protection/domain/self_exclusion.py"
if [ -f "$SE" ]; then
    if ! grep -q "pseudonymized_identity" "$SE"; then
        fail 103 "SelfExclusion missing pseudonymized_identity (SE-survives-erasure)"
    fi
    if ! grep -q "hmac\|HMAC" "$SE"; then
        fail 103 "SelfExclusion missing HMAC pseudonymization"
    fi
    if ! grep -q "check_pseudonymized_identity" "$SE"; then
        fail 103 "SelfExclusion missing check_pseudonymized_identity (registration check)"
    fi
    for period in "6m" "1y" "2y" "5y" "lifetime"; do
        if ! grep -q "$period" "$SE"; then
            fail 103 "SelfExclusion missing period: $period"
        fi
    done
fi

# ─── Rule 104: KillSwitch has <200ms SLO architecture ──────────────────
KS="$ROOT/src/noventra/modules/protection/domain/kill_switch.py"
if [ -f "$KS" ]; then
    if ! grep -q "200ms\|<200" "$KS"; then
        # The <200ms SLO is in the docstring/comments, not code. Check design doc.
        KS_DESIGN="$ROOT/docs/architecture/protection-design.md"
        if ! grep -q "200ms" "$KS_DESIGN" 2>/dev/null; then
            fail 104 "Kill Switch <200ms SLO not documented in code or design doc"
        fi
    fi
    if ! grep -q "trigger" "$KS"; then
        fail 104 "KillSwitch missing trigger method"
    fi
    if ! grep -q "lift" "$KS"; then
        fail 104 "KillSwitch missing lift method"
    fi
    if ! grep -q "TENANT\|GLOBAL" "$KS"; then
        fail 104 "KillSwitch missing scope (TENANT/GLOBAL fan-out)"
    fi
fi

# ─── Rule 105: Real adapters exist (replacing Phase 13 stubs) ──────────
REAL_ADAPTERS="$ROOT/src/noventra/modules/protection/adapters/real_adapters.py"
if [ ! -f "$REAL_ADAPTERS" ]; then
    fail 105 "Real adapters not found (Phase 14 must replace Phase 13 stubs)"
else
    for adapter in RealRGAdapter RealRealtimeAdapter; do
        if ! grep -q "class $adapter" "$REAL_ADAPTERS"; then
            fail 105 "Real adapter missing: $adapter (must replace Phase 13 stub)"
        fi
    done
    if ! grep -q "StubRoundVoidingAdapter" "$REAL_ADAPTERS"; then
        fail 105 "StubRoundVoidingAdapter missing (Phase 15 implements real)"
    fi
    if ! grep -q "StubGeoAdapter" "$REAL_ADAPTERS"; then
        fail 105 "StubGeoAdapter missing (Q5-blocked)"
    fi
fi

# ─── Rule 106: Removed per DEC-0157 (Global Mode — JurisdictionPolicyEngine deleted) ─

# ─── Rule 107: RealityCheck has overdue + acknowledge ───────────────────
RC="$ROOT/src/noventra/modules/protection/domain/reality_check.py"
if [ -f "$RC" ]; then
    if ! grep -q "is_overdue" "$RC"; then
        fail 107 "RealityCheck missing is_overdue property"
    fi
    if ! grep -q "acknowledge" "$RC"; then
        fail 107 "RealityCheck missing acknowledge method (UK GC mandate)"
    fi
    if ! grep -q "interval_minutes" "$RC"; then
        fail 107 "RealityCheck missing interval_minutes (configurable interval)"
    fi
fi

# ─── Rule 108: Phase 14 ADRs PROPOSED (0084-0091) ─────────────────────
for n in 0084 0085 0086 0087 0088 0089 0090 0091; do
    adr_file="$ROOT/docs/adr/ADR-$n.md"
    if [ ! -f "$adr_file" ]; then
        fail 108 "ADR-$n.md not found"
        continue
    fi
    fm_status=$(awk '
        /^---[[:space:]]*$/ { fm++; next }
        fm == 1 && /^Status:/ { print substr($0, index($0, ":") + 1) }
        fm >= 2 { exit }
    ' "$adr_file" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')
    if [ "$fm_status" != "PROPOSED" ]; then
        fail 108 "ADR-$n status is '$fm_status' (expected PROPOSED for Phase 14 Stage A)"
    fi
done

# ─── Rule 109: Protection design doc exists with Kill Switch spec ──────
PROTECTION_DESIGN="$ROOT/docs/architecture/protection-design.md"
if [ ! -f "$PROTECTION_DESIGN" ]; then
    fail 109 "Protection design doc not found"
elif ! grep -q "200ms" "$PROTECTION_DESIGN"; then
    fail 109 "Protection design doc missing Kill Switch <200ms SLO spec"
elif ! grep -q "kill.switch\|KillSwitch\|Kill Switch" "$PROTECTION_DESIGN"; then
    fail 109 "Protection design doc missing Kill Switch architecture"
fi

# ─── Rule 110: Design debt register exists ─────────────────────────────
DEBT_REGISTER="$ROOT/docs/audits/design-debt-register.md"
if [ ! -f "$DEBT_REGISTER" ]; then
    fail 110 "Design debt register not found (observation #1 from Phase 13 audit)"
fi

# ═════════════════════════════════════════════════════════════════════════
# Phase 15 rules (111–120) — Game Platform & Realtime
# ═════════════════════════════════════════════════════════════════════════

# ─── Rule 111: Phase 15 ADRs 0092-0098 all exist ────────────────────────
for adr_n in 0092 0093 0094 0095 0096 0097 0098; do
    adr_file="$ROOT/docs/adr/ADR-${adr_n}.md"
    if [ ! -f "$adr_file" ]; then
        fail 111 "Phase 15 ADR ADR-${adr_n} missing"
    fi
done

# ─── Rule 112: Games module exists with round.py + real_voiding.py ───────
GAMES_DOMAIN="$ROOT/src/noventra/modules/games/domain/round.py"
GAMES_ADAPTER="$ROOT/src/noventra/modules/games/adapters/real_voiding.py"
if [ ! -f "$GAMES_DOMAIN" ]; then
    fail 112 "Phase 15 games domain/round.py missing"
fi
if [ ! -f "$GAMES_ADAPTER" ]; then
    fail 112 "Phase 15 games adapters/real_voiding.py missing"
fi

# ─── Rule 113: GameRound FSM states present (OPEN/CLOSED/SETTLED/VOIDED/CANCELLED)
if [ -f "$GAMES_DOMAIN" ]; then
    for state in OPEN CLOSED SETTLED VOIDED CANCELLED; do
        if ! grep -qE "${state} = \"${state,,}\"" "$GAMES_DOMAIN"; then
            fail 113 "GameRound RoundState enum missing state ${state}"
        fi
    done
    # FSM transitions decorated
    if ! grep -q "@transition" "$GAMES_DOMAIN"; then
        fail 113 "GameRound FSM @transition decorators missing"
    fi
fi

# ─── Rule 114: BetType has 3 types (wager/bonus/free_play) ──────────────
if [ -f "$GAMES_DOMAIN" ]; then
    for bt in wager bonus free_play; do
        if ! grep -qE "${bt^^} = \"${bt}\"" "$GAMES_DOMAIN"; then
            fail 114 "BetType enum missing type ${bt}"
        fi
    done
fi

# ─── Rule 115: RealRoundVoidingAdapter reverses ledger entries ──────────
if [ -f "$GAMES_ADAPTER" ]; then
    if ! grep -q "REVERSAL" "$GAMES_ADAPTER"; then
        fail 115 "RealRoundVoidingAdapter does not post REVERSAL journal entry"
    fi
    if ! grep -q "void_round" "$GAMES_ADAPTER"; then
        fail 115 "RealRoundVoidingAdapter missing void_round method"
    fi
fi

# ─── Rule 116: Phase 15 design doc exists ───────────────────────────────
if [ ! -f "$ROOT/docs/architecture/games-design.md" ]; then
    fail 116 "Phase 15 games-design.md missing"
fi

# ─── Rule 117: Phase 15 handoff exists ──────────────────────────────────
if [ ! -f "$ROOT/docs/stage-handoffs/stage-15-handoff.md" ]; then
    fail 117 "Phase 15 stage-15-handoff.md missing"
fi

# ─── Rule 118: Phase 15 audit exists ────────────────────────────────────
if [ ! -f "$ROOT/docs/audits/phase-015-audit.md" ]; then
    fail 118 "Phase 15 audit missing"
fi

# ─── Rule 119: DeterministicRngAdapter contract documented ──────────────
# Per ADR-0095: sandbox uses same code path with deterministic adapters.
# The adapter itself is implemented in Phase 16; Phase 15 documents the contract.
if [ -f "$ROOT/docs/adr/ADR-0095.md" ]; then
    if ! grep -q "DeterministicRngAdapter" "$ROOT/docs/adr/ADR-0095.md"; then
        fail 119 "ADR-0095 does not name DeterministicRngAdapter contract"
    fi
    if ! grep -q "code path" "$ROOT/docs/adr/ADR-0095.md"; then
        fail 119 "ADR-0095 missing 'code path' determinism mandate"
    fi
fi

# ─── Rule 120: Provider callback validation gates documented ────────────
# Per ADR-0097: 3 gates in order: HMAC, replay, idempotency.
if [ -f "$ROOT/docs/adr/ADR-0097.md" ]; then
    for gate in "HMAC-SHA256" "Replay protection" "Idempotency"; do
        if ! grep -q "$gate" "$ROOT/docs/adr/ADR-0097.md"; then
            fail 120 "ADR-0097 missing gate: ${gate}"
        fi
    done
fi

# ═════════════════════════════════════════════════════════════════════════
# Phase 16 rules (121–133) — Proprietary Game Framework
# Law 19 mandates: lab certification, math version immutability, RNG audit,
# release FSM evidence-gated transitions, auto-suspend on cert expiry.
# ═════════════════════════════════════════════════════════════════════════

# ─── Rule 121: Phase 16 ADRs 0099-0103 all exist ────────────────────────
for adr_n in 0099 0100 0101 0102 0103; do
    adr_file="$ROOT/docs/adr/ADR-${adr_n}.md"
    if [ ! -f "$adr_file" ]; then
        fail 121 "Phase 16 ADR ADR-${adr_n} missing"
    fi
done

# ─── Rule 122: MathVersion model exists with immutability + hash fields ──
MATH_VERSION_FILE="$ROOT/src/noventra/modules/games/domain/math_version.py"
if [ ! -f "$MATH_VERSION_FILE" ]; then
    fail 122 "Phase 16 math_version.py missing"
else
    # Must define MathVersion dataclass.
    if ! grep -q "class MathVersion" "$MATH_VERSION_FILE"; then
        fail 122 "MathVersion class missing"
    fi
    # Must define compute_math_config_hash function.
    if ! grep -q "def compute_math_config_hash" "$MATH_VERSION_FILE"; then
        fail 122 "compute_math_config_hash function missing"
    fi
    # Must use SHA-256.
    if ! grep -q "hashlib.sha256" "$MATH_VERSION_FILE"; then
        fail 122 "MathVersion must use SHA-256 for math_config_hash"
    fi
    # Must be frozen dataclass (immutable).
    if ! grep -q "@dataclass(frozen=True)" "$MATH_VERSION_FILE"; then
        fail 122 "MathVersion must be @dataclass(frozen=True) for immutability"
    fi
    # Must define MathVersionStatus enum with required states.
    for status_val in draft certified published superseded revoked; do
        if ! grep -qE "${status_val^^} = \"${status_val}\"" "$MATH_VERSION_FILE"; then
            fail 122 "MathVersionStatus enum missing state: ${status_val}"
        fi
    done
fi

# ─── Rule 123: RNG port + 3 adapters exist ──────────────────────────────
RNG_PORT_FILE="$ROOT/src/noventra/modules/games/domain/rng_port.py"
if [ ! -f "$RNG_PORT_FILE" ]; then
    fail 123 "Phase 16 rng_port.py missing"
else
    for cls in ProductionRngAdapter DeterministicRngAdapter CertificationRngAdapter; do
        if ! grep -q "class ${cls}" "$RNG_PORT_FILE"; then
            fail 123 "RNG adapter class missing: ${cls}"
        fi
    done
    # ProductionRngAdapter must use secrets module (CSPRNG).
    if ! grep -q "secrets" "$RNG_PORT_FILE"; then
        fail 123 "ProductionRngAdapter must use 'secrets' module (CSPRNG)"
    fi
    # CertificationRngAdapter must have verify_audit_log method.
    if ! grep -q "def verify_audit_log" "$RNG_PORT_FILE"; then
        fail 123 "CertificationRngAdapter missing verify_audit_log method"
    fi
fi

# ─── Rule 124: No direct use of random.Random in games module ───────────
# Per ADR-0100: all RNG must go through RngPort.
GAMES_DIR="$ROOT/src/noventra/modules/games"
if [ -d "$GAMES_DIR" ]; then
    # Find .py files in games module (excluding tests + rng_port.py which uses
    # the random.Random interface internally; that's allowed because it's the
    # adapter implementation, not a caller).
    while IFS= read -r f; do
        # Skip rng_port.py (adapter implementation; allowed to import secrets/hmac/hashlib).
        if [[ "$f" == *"/rng_port.py" ]]; then
            continue
        fi
        # Look for forbidden patterns: random.Random, random.randint, random.random, random.choice.
        if grep -qE "\brandom\.Random\b|\brandom\.randint\b|\brandom\.random\b|\brandom\.choice\b" "$f"; then
            fail 124 "Phase 16: forbidden random.* usage in $f (use RngPort per ADR-0100)"
        fi
    done < <(find "$GAMES_DIR" -name '*.py' -not -path '*/tests/*')
fi

# ─── Rule 125: GameRound Phase 16 extension exists with lock fields ─────
ROUND_P16_FILE="$ROOT/src/noventra/modules/games/domain/round_phase16.py"
if [ ! -f "$ROUND_P16_FILE" ]; then
    fail 125 "Phase 16 round_phase16.py missing"
else
    for field_name in math_version_uuid math_config_hash rng_seed_hex bet_config outcome round_hash; do
        if ! grep -q "${field_name}" "$ROUND_P16_FILE"; then
            fail 125 "round_phase16.py missing field: ${field_name}"
        fi
    done
    # Must define compute_round_hash function.
    if ! grep -q "def compute_round_hash" "$ROUND_P16_FILE"; then
        fail 125 "compute_round_hash function missing"
    fi
    # Must have verify_round_hash method.
    if ! grep -q "def verify_round_hash" "$ROUND_P16_FILE"; then
        fail 125 "verify_round_hash method missing"
    fi
fi

# ─── Rule 126: CertificationEvidence + LabRegistry + auto-suspend ───────
CERT_FILE="$ROOT/src/noventra/modules/games/domain/certification.py"
if [ ! -f "$CERT_FILE" ]; then
    fail 126 "Phase 16 certification.py missing"
else
    for cls in LabRegistry CertificationEvidence CertExpiryService AutoSuspendResult; do
        if ! grep -q "class ${cls}" "$CERT_FILE"; then
            fail 126 "certification.py missing class: ${cls}"
        fi
    done
    # Must have check_cert_expiry_task function.
    if ! grep -q "def check_cert_expiry_task" "$CERT_FILE"; then
        fail 126 "check_cert_expiry_task function missing"
    fi
    # EvidenceType enum must have 4 types.
    for et in rng_cert math_cert rtp_verification game_logic_cert; do
        if ! grep -qE "${et^^} = \"${et}\"" "$CERT_FILE"; then
            fail 126 "EvidenceType enum missing: ${et}"
        fi
    done
fi

# ─── Rule 127: Release FSM exists with 9 states + evidence-gated transitions
RELEASE_FILE="$ROOT/src/noventra/modules/games/domain/release.py"
if [ ! -f "$RELEASE_FILE" ]; then
    fail 127 "Phase 16 release.py missing"
else
    # ReleaseState enum must have all 9 states.
    for st in draft math_configured rng_certified math_certified lab_tested ready_for_release published suspended revoked; do
        if ! grep -qE "${st^^} = \"${st}\"" "$RELEASE_FILE"; then
            fail 127 "ReleaseState enum missing state: ${st}"
        fi
    done
    # Transition methods must exist.
    for method in configure_math attach_rng_cert attach_math_cert attach_lab_test ready_for_release publish suspend revoke; do
        if ! grep -q "def ${method}" "$RELEASE_FILE"; then
            fail 127 "GameRelease missing transition method: ${method}"
        fi
    done
    # Each @transition decorator must have exactly one source (no skipping).
    # Verify by counting @transition decorators vs transition methods.
    transition_count=$(grep -c "@transition" "$RELEASE_FILE")
    method_count=$(grep -cE "def (configure_math|attach_rng_cert|attach_math_cert|attach_lab_test|ready_for_release|publish|suspend|resume_publication|revoke)" "$RELEASE_FILE")
    if [ "$transition_count" -lt "$method_count" ]; then
        fail 127 "Phase 16: not all transition methods have @transition decorator ($transition_count decorators, $method_count methods)"
    fi
fi

# ─── Rule 128: ADR-0099 documents immutability + hash verification ──────
if [ -f "$ROOT/docs/adr/ADR-0099.md" ]; then
    for keyword in "immutable" "SHA-256" "math_config_hash" "supersession"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0099.md"; then
            fail 128 "ADR-0099 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 129: ADR-0100 documents 3 adapters + determinism ─────────────
if [ -f "$ROOT/docs/adr/ADR-0100.md" ]; then
    for keyword in "ProductionRngAdapter" "DeterministicRngAdapter" "CertificationRngAdapter" "CSPRNG" "determinis"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0100.md"; then
            fail 129 "ADR-0100 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 130: ADR-0101 documents math version lock + RNG seed lock + round hash
if [ -f "$ROOT/docs/adr/ADR-0101.md" ]; then
    for keyword in "math version" "RNG seed" "round_hash" "tamper"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0101.md"; then
            fail 130 "ADR-0101 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 131: ADR-0102 documents lab registry + auto-suspend on expiry ─
if [ -f "$ROOT/docs/adr/ADR-0102.md" ]; then
    for keyword in "LabRegistry" "CertificationEvidence" "Auto-Suspend" "expires_at" "30 days"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0102.md"; then
            fail 131 "ADR-0102 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 132: ADR-0103 documents release FSM + evidence-gated transitions
if [ -f "$ROOT/docs/adr/ADR-0103.md" ]; then
    for keyword in "draft" "published" "suspended" "revoked" "evidence" "operator" "skipping"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0103.md"; then
            fail 132 "ADR-0103 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 133: Phase 16 design doc + handoff + audit exist ──────────────
for f in \
    "$ROOT/docs/architecture/games-phase16-design.md" \
    "$ROOT/docs/stage-handoffs/stage-16-handoff.md" \
    "$ROOT/docs/audits/phase-016-audit.md"; do
    if [ ! -f "$f" ]; then
        fail 133 "Phase 16 artifact missing: $f"
    fi
done

# ═════════════════════════════════════════════════════════════════════════
# Phase 17 rules (134–145) — Data Platform & GGR — bifurcated truth
# Law 6 mandates: bifurcated truth (telemetry never-truth), schema registry,
# consumer idempotency, GGR/NGR sourced from ledger, regulatory reporting.
# ═════════════════════════════════════════════════════════════════════════

# ─── Rule 134: Phase 17 ADRs 0104-0108 all exist ────────────────────────
for adr_n in 0104 0105 0106 0107 0108; do
    adr_file="$ROOT/docs/adr/ADR-${adr_n}.md"
    if [ ! -f "$adr_file" ]; then
        fail 134 "Phase 17 ADR ADR-${adr_n} missing"
    fi
done

# ─── Rule 135: ADR-0104 documents bifurcated truth + is_truth label ─────
if [ -f "$ROOT/docs/adr/ADR-0104.md" ]; then
    for keyword in "Bifurcated Truth" "is_truth" "telemetry" "domain events" "Cross-Contamination"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0104.md"; then
            fail 135 "ADR-0104 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 136: ADR-0105 documents schema registry + compatibility modes ─
if [ -f "$ROOT/docs/adr/ADR-0105.md" ]; then
    for keyword in "EventSchema" "backward" "forward" "full" "compatibility" "validation"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0105.md"; then
            fail 136 "ADR-0105 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 137: ADR-0106 documents consumer registry + idempotency + DLQ ─
if [ -f "$ROOT/docs/adr/ADR-0106.md" ]; then
    for keyword in "EventConsumer" "inbox" "idempoten" "lag" "DLQ" "replay"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0106.md"; then
            fail 137 "ADR-0106 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 138: ADR-0107 documents read models + reconciliation ──────────
if [ -f "$ROOT/docs/adr/ADR-0107.md" ]; then
    for keyword in "ReadModel" "GGR" "NGR" "materialized" "refresh" "reconciliation" "HALT"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0107.md"; then
            fail 138 "ADR-0107 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 139: ADR-0108 documents GGR/NGR + regulatory reporting ─────────
if [ -f "$ROOT/docs/adr/ADR-0108.md" ]; then
    for keyword in "GGR" "NGR" "RegulatoryReport" "game_class" "ledger" "submitted"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0108.md"; then
            fail 139 "ADR-0108 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 140: Phase 17 design doc exists ───────────────────────────────
if [ ! -f "$ROOT/docs/architecture/data-platform-design.md" ]; then
    fail 140 "Phase 17 data-platform-design.md missing"
fi

# ─── Rule 141: Phase 17 stage handoff exists ────────────────────────────
if [ ! -f "$ROOT/docs/stage-handoffs/stage-17-handoff.md" ]; then
    fail 141 "Phase 17 stage-17-handoff.md missing"
fi

# ─── Rule 142: Phase 17 audit exists ────────────────────────────────────
if [ ! -f "$ROOT/docs/audits/phase-017-audit.md" ]; then
    fail 142 "Phase 17 audit missing"
fi

# ─── Rule 143: Open questions register documents OQ-DATA-001..006 ───────
# Per Phase 17 prompt §2.4: 6 new OQs added to the open questions register.
OQ_FILE="$ROOT/docs/requirements/unresolved-decisions.md"
if [ -f "$OQ_FILE" ]; then
    for oq_id in OQ-DATA-001 OQ-DATA-002 OQ-DATA-003 OQ-DATA-004 OQ-DATA-005 OQ-DATA-006; do
        if ! grep -q "$oq_id" "$OQ_FILE"; then
            fail 143 "Open questions register missing: ${oq_id}"
        fi
    done
fi

# ─── Rule 144: Bifurcated truth — no telemetry reference in domain modules
# Per ADR-0104: domain modules must not import or reference telemetry pipeline.
# This rule scans domain modules for telemetry pipeline references.
DOMAIN_DIRS=(
    "$ROOT/src/noventra/modules/ledger"
    "$ROOT/src/noventra/modules/payments"
    "$ROOT/src/noventra/modules/bonuses"
    "$ROOT/src/noventra/modules/protection"
    "$ROOT/src/noventra/modules/games"
)
for d in "${DOMAIN_DIRS[@]}"; do
    if [ -d "$d" ]; then
        # Look for forbidden patterns: telemetry.events stream reference, is_truth: false in domain code.
        while IFS= read -r f; do
            if grep -qE "telemetry\.events|is_truth.*false" "$f"; then
                fail 144 "Phase 17: forbidden telemetry reference in domain module $f (bifurcated truth, ADR-0104)"
            fi
        done < <(find "$d" -name '*.py' -not -path '*/tests/*')
    fi
done

# ─── Rule 145: GGR/NGR sourced from ledger, not telemetry (contract doc) ─
# Per ADR-0108: source of truth is Phase 11 ledger, not telemetry, not read model cache.
# This rule verifies the design doc explicitly states this.
if [ -f "$ROOT/docs/architecture/data-platform-design.md" ]; then
    for keyword in "ledger" "telemetry" "never-truth" "is_truth" "reconciliation"; do
        if ! grep -qi "$keyword" "$ROOT/docs/architecture/data-platform-design.md"; then
            fail 145 "data-platform-design.md missing keyword: ${keyword}"
        fi
    done
fi

# ═════════════════════════════════════════════════════════════════════════
# Phase 18 rules (146–158) — Risk, AML & Cases — SAR/tipping-off
# Law 14 mandates: punitive action approval + dual control.
# FATF mandates: TM rules + SAR/STR workflow + tipping-off prohibition (criminal liability).
# ═════════════════════════════════════════════════════════════════════════

# ─── Rule 146: Phase 18 ADRs 0109-0114 all exist ────────────────────────
for adr_n in 0109 0110 0111 0112 0113 0114; do
    adr_file="$ROOT/docs/adr/ADR-${adr_n}.md"
    if [ ! -f "$adr_file" ]; then
        fail 146 "Phase 18 ADR ADR-${adr_n} missing"
    fi
done

# ─── Rule 147: ADR-0109 documents risk signal model + 12-type catalog ───
if [ -f "$ROOT/docs/adr/ADR-0109.md" ]; then
    for keyword in "RiskSignal" "velocity_deposit" "structural_structuring" "behavioral_chip_dumping" "pep_linked" "sanctions_linked" "rule-based"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0109.md"; then
            fail 147 "ADR-0109 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 148: ADR-0110 documents TM rules engine + 5 rule types ─────────
if [ -f "$ROOT/docs/adr/ADR-0110.md" ]; then
    for keyword in "TMRule" "velocity" "structural" "behavioral" "threshold" "risk_score_weight"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0110.md"; then
            fail 148 "ADR-0110 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 149: ADR-0111 documents SAR workflow + MLRO + tipping-off ──────
if [ -f "$ROOT/docs/adr/ADR-0111.md" ]; then
    for keyword in "SARCase" "MLRO" "tipping-off" "FIU" "criminal liability" "mlro_review" "filed"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0111.md"; then
            fail 149 "ADR-0111 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 150: ADR-0112 documents risk case management + evidence ────────
if [ -f "$ROOT/docs/adr/ADR-0112.md" ]; then
    for keyword in "RiskCase" "evidence" "case linking" "aml_investigation" "fraud_investigation" "kyc_case_uuid"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0112.md"; then
            fail 150 "ADR-0112 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 151: ADR-0113 documents punitive action + dual control ─────────
if [ -f "$ROOT/docs/adr/ADR-0113.md" ]; then
    for keyword in "PunitiveAction" "account_freeze" "account_closure" "bonus_clawback" "payment_block" "se_block" "dual control" "irreversible"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0113.md"; then
            fail 151 "ADR-0113 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 152: ADR-0114 documents appeal workflow + separation of duties ─
if [ -f "$ROOT/docs/adr/ADR-0114.md" ]; then
    for keyword in "Appeal" "appeal" "upheld" "overturned" "separation of duties" "appeal window" "tipping-off"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0114.md"; then
            fail 152 "ADR-0114 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 153: Phase 18 design doc exists ───────────────────────────────
if [ ! -f "$ROOT/docs/architecture/risk-aml-design.md" ]; then
    fail 153 "Phase 18 risk-aml-design.md missing"
fi

# ─── Rule 154: Phase 18 stage handoff exists ────────────────────────────
if [ ! -f "$ROOT/docs/stage-handoffs/stage-18-handoff.md" ]; then
    fail 154 "Phase 18 stage-18-handoff.md missing"
fi

# ─── Rule 155: Phase 18 audit exists ────────────────────────────────────
if [ ! -f "$ROOT/docs/audits/phase-018-audit.md" ]; then
    fail 155 "Phase 18 audit missing"
fi

# ─── Rule 156: Open questions register documents OQ-RISK-001..006 ───────
# Per Phase 18 prompt §2.4: 6 new OQs added to the open questions register.
if [ -f "$OQ_FILE" ]; then
    for oq_id in OQ-RISK-001 OQ-RISK-002 OQ-RISK-003 OQ-RISK-004 OQ-RISK-005 OQ-RISK-006; do
        if ! grep -q "$oq_id" "$OQ_FILE"; then
            fail 156 "Open questions register missing: ${oq_id}"
        fi
    done
fi

# ─── Rule 157: Tipping-off prohibition — no SAR in notification templates
# Per ADR-0111 + Law 14: no code path notifies player of SAR.
# Scan notification templates + email subjects + SMS templates for SAR-related strings.
# Zero findings required (criminal liability).
NOTIFICATION_DIRS=(
    "$ROOT/src/noventra/apps/players"
    "$ROOT/src/noventra/modules/payments"
    "$ROOT/templates"
    "$ROOT/src/noventra/apps/identity"
)
SAR_FORBIDDEN_STRINGS="SAR|suspicious activity report|suspicious transaction report|FIU|financial intelligence unit|MLRO|money laundering report"
for d in "${NOTIFICATION_DIRS[@]}"; do
    if [ -d "$d" ]; then
        # Scan .py, .html, .txt, .md template files for SAR-related strings in notification context.
        while IFS= read -r f; do
            # Look for SAR strings in notification/email/template context.
            # Exclude ADR files, audit files, and design docs (those legitimately reference SAR).
            if grep -qE "$SAR_FORBIDDEN_STRINGS" "$f" 2>/dev/null; then
                # Check if this is a notification file (email, sms, push, notify in filename or path).
                if echo "$f" | grep -qiE "notif|email|sms|push|template|message"; then
                    fail 157 "Phase 18: tipping-off violation — SAR reference in notification file $f (ADR-0111, criminal liability)"
                fi
            fi
        done < <(find "$d" -type f \( -name '*.py' -o -name '*.html' -o -name '*.txt' -o -name '*.md' \) 2>/dev/null)
    fi
done

# ─── Rule 158: GGR/NGR not sourced from telemetry (risk-aml design doc) ─
# Per ADR-0110: TM rules use domain events only (Phase 17 bifurcated truth).
# The risk-aml design doc must explicitly state domain events only, not telemetry.
if [ -f "$ROOT/docs/architecture/risk-aml-design.md" ]; then
    for keyword in "domain events" "telemetry" "tipping-off" "MLRO" "dual control" "Law 14"; do
        if ! grep -qi "$keyword" "$ROOT/docs/architecture/risk-aml-design.md"; then
            fail 158 "risk-aml-design.md missing keyword: ${keyword}"
        fi
    done
fi

# ═════════════════════════════════════════════════════════════════════════
# Phase 19 rules (159–175) — AI Platform & RAG — 10-step pipeline; Laws 11/12/13
# Law 11: AI never writes to domain truth tables.
# Law 12: LLM never names citations; machine-assembled citations only.
# Law 13: TruthConsistencyValidator; contradiction = hard fail.
# Law 2: Prefiltered retrieval (tenant + language INSIDE query). Per DEC-0157: jurisdiction removed.
# Law 16: Distress short-circuit; L0-L4 degradation.
# Law 6: Bifurcated truth; RAG forbidden from touching Process Truth.
# ═════════════════════════════════════════════════════════════════════════

# ─── Rule 159: Phase 19 ADRs 0115-0124 all exist ────────────────────────
for adr_n in 0115 0116 0117 0118 0119 0120 0121 0122 0123 0124; do
    adr_file="$ROOT/docs/adr/ADR-${adr_n}.md"
    if [ ! -f "$adr_file" ]; then
        fail 159 "Phase 19 ADR ADR-${adr_n} missing"
    fi
done

# ─── Rule 160: ADR-0115 documents LLM gateway + degradation L0-L4 ────────
if [ -f "$ROOT/docs/adr/ADR-0115.md" ]; then
    for keyword in "LLMGateway" "provider abstraction" "rate limiting" "degradation" "L0" "L4" "distress" "budget"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0115.md"; then
            fail 160 "ADR-0115 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 161: ADR-0116 documents prompt template versioning ────────────
if [ -f "$ROOT/docs/adr/ADR-0116.md" ]; then
    for keyword in "PromptTemplate" "version" "A/B" "rollback" "audit"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0116.md"; then
            fail 161 "ADR-0116 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 162: ADR-0117 documents knowledge chunk + synchronous revocation
if [ -f "$ROOT/docs/adr/ADR-0117.md" ]; then
    for keyword in "KnowledgeChunk" "pgvector" "lifecycle" "synchronous revocation" "Law 10" "embedding_model_version"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0117.md"; then
            fail 162 "ADR-0117 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 163: ADR-0118 documents prefiltered retrieval (Law 2) ─────────
if [ -f "$ROOT/docs/adr/ADR-0118.md" ]; then
    for keyword in "prefiltered" "pgvector" "FTS" "tenant_id" "Law 2" "post-retrieval"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0118.md"; then
            fail 163 "ADR-0118 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 164: ADR-0119 documents machine-assembled citations (Law 12) ──
if [ -f "$ROOT/docs/adr/ADR-0119.md" ]; then
    for keyword in "Machine-Assembled" "Law 12" "Claim-Level" "grounding" "chunk_ids" "hallucinat"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0119.md"; then
            fail 164 "ADR-0119 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 165: ADR-0120 documents TruthConsistencyValidator (Law 13) ────
if [ -f "$ROOT/docs/adr/ADR-0120.md" ]; then
    for keyword in "TruthConsistencyValidator" "Law 13" "SQL" "contradiction" "hard fail" "safe fallback" "incident"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0120.md"; then
            fail 165 "ADR-0120 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 166: ADR-0121 documents LLM evaluation suite ──────────────────
if [ -f "$ROOT/docs/adr/ADR-0121.md" ]; then
    for keyword in "Evaluation" "regression" "injection" "hallucination" "citation" "truth"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0121.md"; then
            fail 166 "ADR-0121 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 167: ADR-0122 documents cost accounting + budget enforcement ──
if [ -f "$ROOT/docs/adr/ADR-0122.md" ]; then
    for keyword in "LLMCostRecord" "per-request" "per-tenant" "budget" "cutoff" "chargeback"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0122.md"; then
            fail 167 "ADR-0122 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 168: ADR-0123 documents EU AI Act model inventory ─────────────
if [ -f "$ROOT/docs/adr/ADR-0123.md" ]; then
    for keyword in "EU AI Act" "AIModel" "risk_classification" "unacceptable" "prohibited" "high" "conformity"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0123.md"; then
            fail 168 "ADR-0123 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 169: ADR-0124 documents 10-step RAG pipeline ──────────────────
if [ -f "$ROOT/docs/adr/ADR-0124.md" ]; then
    for keyword in "10-step" "Unified Router" "Retrieval Planner" "Prefiltered" "Ingestion Sandbox" "Answer Composer" "Grounder" "Truth" "Guardrails" "Citation" "Safe Renderer"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0124.md"; then
            fail 169 "ADR-0124 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 170: Phase 19 design doc exists ───────────────────────────────
if [ ! -f "$ROOT/docs/architecture/ai-platform-design.md" ]; then
    fail 170 "Phase 19 ai-platform-design.md missing"
fi

# ─── Rule 171: Phase 19 stage handoff exists ────────────────────────────
if [ ! -f "$ROOT/docs/stage-handoffs/stage-19-handoff.md" ]; then
    fail 171 "Phase 19 stage-19-handoff.md missing"
fi

# ─── Rule 172: Phase 19 audit exists ────────────────────────────────────
if [ ! -f "$ROOT/docs/audits/phase-019-audit.md" ]; then
    fail 172 "Phase 19 audit missing"
fi

# ─── Rule 173: Open questions register documents OQ-AI-001..006 ─────────
if [ -f "$OQ_FILE" ]; then
    for oq_id in OQ-AI-001 OQ-AI-002 OQ-AI-003 OQ-AI-004 OQ-AI-005 OQ-AI-006; do
        if ! grep -q "$oq_id" "$OQ_FILE"; then
            fail 173 "Open questions register missing: ${oq_id}"
        fi
    done
fi

# ─── Rule 174: AI never writes to domain truth tables (Law 11) ──────────
# Per ADR-0124 Step 5 + Law 11: LLM output never writes to domain truth tables.
# This rule scans for any code path that takes LLM output and writes to domain tables.
# Domain tables: ledger, payments, kyc, bonuses, protection, games.
# The scan looks for patterns where LLM response is used in INSERT/UPDATE to domain tables.
DOMAIN_TABLE_PATTERN="ledger_journal_entry|payments_order|kyc_case|bonus_award|self_exclusion|game_round"
AI_OUTPUT_PATTERN="llm_response|ai_response|rag_response|llm_output|ai_output"
# This is a conservative grep — it flags files that reference BOTH AI output AND domain tables.
# The actual enforcement is at the gateway (ADR-0115) which never exposes write APIs to the LLM.
# This linter rule is a defense-in-depth check.
AI_DIR="$ROOT/src/noventra/modules"
if [ -d "$AI_DIR" ]; then
    while IFS= read -r f; do
        # Skip test files.
        if [[ "$f" == *"/tests/"* ]]; then
            continue
        fi
        # Check if file references both AI output and domain table writes.
        if grep -qE "$AI_OUTPUT_PATTERN" "$f" 2>/dev/null && grep -qE "$DOMAIN_TABLE_PATTERN" "$f" 2>/dev/null; then
            # Flag for review — this file references both AI output and domain tables.
            # This is not necessarily a violation (e.g., TruthConsistencyValidator reads domain tables
            # to validate AI claims), but it warrants review.
            # For Stage A, we log a warning rather than a hard fail.
            echo "LINT WARN [rule 174]: $f references both AI output and domain tables — review for Law 11 violation" >&2
        fi
    done < <(find "$AI_DIR" -name '*.py' 2>/dev/null)
fi

# ─── Rule 175: AI platform design doc contracts (Laws 11/12/13/2/16/6) ──
# Per ADR-0124: the design doc must explicitly state all 6 laws enforced by the pipeline.
if [ -f "$ROOT/docs/architecture/ai-platform-design.md" ]; then
    for keyword in "Law 11" "Law 12" "Law 13" "Law 2" "Law 16" "Law 6" "10-step" "distress" "prefiltered" "contradiction"; do
        if ! grep -qi "$keyword" "$ROOT/docs/architecture/ai-platform-design.md"; then
            fail 175 "ai-platform-design.md missing keyword: ${keyword}"
        fi
    done
fi

# ═════════════════════════════════════════════════════════════════════════
# Phase 20 rules (176–185) — Bounded Agents — 9-agent catalog; Law 14
# Law 14: Agents act only through typed, registered tools mapped to deterministic service methods.
# Law 18: Retention agent bounded (excluded/cooling-off/caps/bonus).
# Law 9: Execution logs immutable; hash-chained.
# ═════════════════════════════════════════════════════════════════════════

# ─── Rule 176: Phase 20 ADRs 0125-0130 all exist ────────────────────────
for adr_n in 0125 0126 0127 0128 0129 0130; do
    adr_file="$ROOT/docs/adr/ADR-${adr_n}.md"
    if [ ! -f "$adr_file" ]; then
        fail 176 "Phase 20 ADR ADR-${adr_n} missing"
    fi
done

# ─── Rule 177: ADR-0125 documents agent registry + shadow→live ──────────
if [ -f "$ROOT/docs/adr/ADR-0125.md" ]; then
    for keyword in "AgentDefinition" "shadow" "live" "promotion" "PromotionEvidence" "9 agents" "allowed_tools" "forbidden_tools"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0125.md"; then
            fail 177 "ADR-0125 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 178: ADR-0126 documents typed tools + no superuser + no DB writes
if [ -f "$ROOT/docs/adr/ADR-0126.md" ]; then
    for keyword in "AgentTool" "input_schema" "output_schema" "mapped_service_method" "no superuser" "no direct DB" "service identit"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0126.md"; then
            fail 178 "ADR-0126 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 179: ADR-0127 documents approval gates + SLA + dual control ──
if [ -f "$ROOT/docs/adr/ADR-0127.md" ]; then
    for keyword in "AgentApproval" "pending" "approved" "rejected" "executed" "expired" "SLA" "dual control" "justification"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0127.md"; then
            fail 179 "ADR-0127 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 180: ADR-0128 documents execution logs + immutable + links ────
if [ -f "$ROOT/docs/adr/ADR-0128.md" ]; then
    for keyword in "AgentExecutionLog" "immutable" "insert-only" "correlation_id" "llm_call_id" "approval_id" "Law 9" "hash"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0128.md"; then
            fail 180 "ADR-0128 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 181: ADR-0129 documents Retention agent bounds (Law 18) ───────
if [ -f "$ROOT/docs/adr/ADR-0129.md" ]; then
    for keyword in "Retention" "Law 18" "excluded" "cooling-off" "caps" "bonus" "4-level" "negative test" "RGPort" "MarketingGate"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0129.md"; then
            fail 181 "ADR-0129 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 182: ADR-0130 documents agent runtime + degradation + distress
if [ -f "$ROOT/docs/adr/ADR-0130.md" ]; then
    for keyword in "AgentRuntime" "orchestration" "LLM" "outbox" "degradation" "L0" "L4" "distress" "short-circuit" "pure function"; do
        if ! grep -qi "$keyword" "$ROOT/docs/adr/ADR-0130.md"; then
            fail 182 "ADR-0130 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 183: Phase 20 design doc exists ───────────────────────────────
if [ ! -f "$ROOT/docs/architecture/bounded-agents-design.md" ]; then
    fail 183 "Phase 20 bounded-agents-design.md missing"
fi

# ─── Rule 184: Phase 20 stage handoff exists ────────────────────────────
if [ ! -f "$ROOT/docs/stage-handoffs/stage-20-handoff.md" ]; then
    fail 184 "Phase 20 stage-20-handoff.md missing"
fi

# ─── Rule 185: Phase 20 audit + OQs + design doc contracts ──────────────
if [ ! -f "$ROOT/docs/audits/phase-020-audit.md" ]; then
    fail 185 "Phase 20 audit missing"
fi
# Open questions register documents OQ-AGENT-001..006
if [ -f "$OQ_FILE" ]; then
    for oq_id in OQ-AGENT-001 OQ-AGENT-002 OQ-AGENT-003 OQ-AGENT-004 OQ-AGENT-005 OQ-AGENT-006; do
        if ! grep -q "$oq_id" "$OQ_FILE"; then
            fail 185 "Open questions register missing: ${oq_id}"
        fi
    done
fi
# Bounded agents design doc contracts (Law 14 + Law 18 + 9 agents + shadow→live)
if [ -f "$ROOT/docs/architecture/bounded-agents-design.md" ]; then
    for keyword in "Law 14" "Law 18" "Law 9" "9 agents" "shadow" "live" "Retention" "RGPort" "MarketingGate"; do
        if ! grep -qi "$keyword" "$ROOT/docs/architecture/bounded-agents-design.md"; then
            fail 185 "bounded-agents-design.md missing keyword: ${keyword}"
        fi
    done
fi

# ═════════════════════════════════════════════════════════════════════════
# Phase 21 rules (186–195) — Compliance, DSAR & Vendors — errata E1; blueprint §8.3
# Errata E1: DSAR order fixed (verify → export → shred; no reordering).
# Law 9: Evidence immutable; access audited.
# Law 18: DSAR preserves SE registry (HMAC pseudonymization).
# Law 19: Lab/studio cert expiry auto-suspends catalog.
# Blueprint §8.3: Vendor expiry T-30/7/1 + operator decision.
# ═════════════════════════════════════════════════════════════════════════

# ─── Rule 186: Phase 21 ADRs 0131-0136 all exist ────────────────────────
for adr_n in 0131 0132 0133 0134 0135 0136; do
    adr_file="$ROOT/docs/adr/ADR-${adr_n}.md"
    if [ ! -f "$adr_file" ]; then
        fail 186 "Phase 21 ADR ADR-${adr_n} missing"
    fi
done

# ─── Rule 187: ADR-0131 documents compliance control framework ──────────
if [ -f "$ROOT/docs/adr/ADR-0131.md" ]; then
    for keyword in "ComplianceControl" "framework" "ISO_27001|ISO 27001" "SOC_2|SOC 2" "UK_GC_LCCP|UK GC LCCP" "MGA_BLC|MGA BLC" "GDPR" "AML" "owner" "testing"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/adr/ADR-0131.md"; then
            fail 187 "ADR-0131 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 188: ADR-0132 documents evidence repository + immutable + access
if [ -f "$ROOT/docs/adr/ADR-0132.md" ]; then
    for keyword in "ComplianceEvidence" "immutable" "WORM|Phase 10" "EvidenceAccessLog" "Law 9" "retention" "supersession|superseded"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/adr/ADR-0132.md"; then
            fail 188 "ADR-0132 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 189: ADR-0133 documents periodic reviews + findings + remediation
if [ -f "$ROOT/docs/adr/ADR-0133.md" ]; then
    for keyword in "ComplianceReview" "internal_audit|internal audit" "external_audit|external audit" "regulator_inspection|regulator inspection" "self_assessment|self assessment" "findings" "remediation" "severity" "escalation"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/adr/ADR-0133.md"; then
            fail 189 "ADR-0133 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 190: ADR-0134 documents reporting adapters + per-jurisdiction ─
if [ -f "$ROOT/docs/adr/ADR-0134.md" ]; then
    for keyword in "ReportingAdapter" "RegulatoryReport" "report_type" "GGR" "NGR" "AML_CTR|AML CTR" "AML_SAR|AML SAR" "submission"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/adr/ADR-0134.md"; then
            fail 190 "ADR-0134 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 191: ADR-0135 documents DSAR drill + E1 + SE-survives-erasure ─
if [ -f "$ROOT/docs/adr/ADR-0135.md" ]; then
    for keyword in "DSAR" "errata E1|E1" "verify" "export" "shred" "SE-survives-erasure|SE survives erasure|SE-survives" "HMAC" "pseudonym" "statutory window|30 days"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/adr/ADR-0135.md"; then
            fail 191 "ADR-0135 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 192: ADR-0136 documents legal-hold + vendor expiry ────────────
if [ -f "$ROOT/docs/adr/ADR-0136.md" ]; then
    for keyword in "LegalHold" "legal-hold|legal hold" "VendorRegistry|vendor registry" "blueprint §8.3|§8.3|8.3" "lab" "studio" "PSP|psp" "KYC|kyc" "Geo|geo" "T-30|T30|T-30/7/1" "auto-suspend|auto suspend" "operator_decision|operator decision"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/adr/ADR-0136.md"; then
            fail 192 "ADR-0136 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 193: Phase 21 design doc exists ───────────────────────────────
if [ ! -f "$ROOT/docs/architecture/compliance-dsar-vendors-design.md" ]; then
    fail 193 "Phase 21 compliance-dsar-vendors-design.md missing"
fi

# ─── Rule 194: Phase 21 stage handoff exists ────────────────────────────
if [ ! -f "$ROOT/docs/stage-handoffs/stage-21-handoff.md" ]; then
    fail 194 "Phase 21 stage-21-handoff.md missing"
fi

# ─── Rule 195: Phase 21 audit + OQs + design doc contracts ──────────────
if [ ! -f "$ROOT/docs/audits/phase-021-audit.md" ]; then
    fail 195 "Phase 21 audit missing"
fi
# Open questions register documents OQ-COMP-001..006
if [ -f "$OQ_FILE" ]; then
    for oq_id in OQ-COMP-001 OQ-COMP-002 OQ-COMP-003 OQ-COMP-004 OQ-COMP-005 OQ-COMP-006; do
        if ! grep -q "$oq_id" "$OQ_FILE"; then
            fail 195 "Open questions register missing: ${oq_id}"
        fi
    done
fi
# Compliance design doc contracts (errata E1 + SE-survives + vendor expiry + legal-hold + Law 9 + Law 18 + Law 19)
if [ -f "$ROOT/docs/architecture/compliance-dsar-vendors-design.md" ]; then
    for keyword in "E1" "errata" "SE-survives|SE survives|SE registry" "HMAC" "legal-hold|legal hold" "vendor" "T-30|T30" "auto-suspend|auto suspend" "operator_decision|operator decision" "Law 9" "Law 18" "Law 19"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/architecture/compliance-dsar-vendors-design.md"; then
            fail 195 "compliance-dsar-vendors-design.md missing keyword: ${keyword}"
        fi
    done
fi

# ═════════════════════════════════════════════════════════════════════════
# Phase 22 rules (196–205) — Engagement & Retention — Law 24 Suppression
# Law 24: deterministic join at send time; never cached flag (Suppression Drift cure).
# Law 18: excluded/cooling-off players never queued; exit conditions.
# Law 2: segments prefilter INSIDE query (RGPort check before materialization).
# EU AI Act: propensity models registered; player transparency.
# ═════════════════════════════════════════════════════════════════════════

# ─── Rule 196: Phase 22 ADRs 0137-0141 all exist ────────────────────────
for adr_n in 0137 0138 0139 0140 0141; do
    adr_file="$ROOT/docs/adr/ADR-${adr_n}.md"
    if [ ! -f "$adr_file" ]; then
        fail 196 "Phase 22 ADR ADR-${adr_n} missing"
    fi
done

# ─── Rule 197: ADR-0137 documents segment + RGPort prefiltering ─────────
if [ -f "$ROOT/docs/adr/ADR-0137.md" ]; then
    for keyword in "Segment" "SegmentMembership" "RGPort" "prefilter" "check_self_excluded" "check_cooling_off" "Law 2" "no cached suppression|no-cached-suppression|cached suppression"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/adr/ADR-0137.md"; then
            fail 197 "ADR-0137 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 198: ADR-0138 documents journey + exit conditions ─────────────
if [ -f "$ROOT/docs/adr/ADR-0138.md" ]; then
    for keyword in "Journey" "JourneyStep" "JourneyEnrollment" "exit" "self_excluded" "unsubscribed" "cooling_off" "terminal_step" "no_consent" "kill-switch|kill switch"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/adr/ADR-0138.md"; then
            fail 198 "ADR-0138 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 199: ADR-0139 documents propensity + EU AI Act ────────────────
if [ -f "$ROOT/docs/adr/ADR-0139.md" ]; then
    for keyword in "PropensityFeature" "churn_risk" "ltv" "deposit_propensity" "bonus_sensitivity" "rg_risk" "EU AI Act" "limited risk" "AIModel" "model_version" "transparency"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/adr/ADR-0139.md"; then
            fail 199 "ADR-0139 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 200: ADR-0140 documents MarketingGate two-stage + deterministic join
if [ -f "$ROOT/docs/adr/ADR-0140.md" ]; then
    for keyword in "MarketingGate" "queue-time|queue time" "send-time|send time" "two-stage|two stage" "deterministic join" "suppression_list" "frequency_cap" "Law 24" "no cached|never.*cached|not.*cached"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/adr/ADR-0140.md"; then
            fail 200 "ADR-0140 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 201: ADR-0141 documents negative test suite ───────────────────
if [ -f "$ROOT/docs/adr/ADR-0141.md" ]; then
    for keyword in "negative test" "suppressed" "excluded" "cooling-off|cooling off" "cap" "consent" "comprehensive" "mixed-segment|mixed segment" "CI"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/adr/ADR-0141.md"; then
            fail 201 "ADR-0141 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 202: Phase 22 design doc exists ───────────────────────────────
if [ ! -f "$ROOT/docs/architecture/engagement-retention-design.md" ]; then
    fail 202 "Phase 22 engagement-retention-design.md missing"
fi

# ─── Rule 203: Phase 22 stage handoff exists ────────────────────────────
if [ ! -f "$ROOT/docs/stage-handoffs/stage-22-handoff.md" ]; then
    fail 203 "Phase 22 stage-22-handoff.md missing"
fi

# ─── Rule 204: Phase 22 audit exists ────────────────────────────────────
if [ ! -f "$ROOT/docs/audits/phase-022-audit.md" ]; then
    fail 204 "Phase 22 audit missing"
fi

# ─── Rule 205: OQs + design doc contracts (Law 24 + Law 18 + Law 2 + EU AI Act)
# Open questions register documents OQ-ENG-001..006
if [ -f "$OQ_FILE" ]; then
    for oq_id in OQ-ENG-001 OQ-ENG-002 OQ-ENG-003 OQ-ENG-004 OQ-ENG-005 OQ-ENG-006; do
        if ! grep -q "$oq_id" "$OQ_FILE"; then
            fail 205 "Open questions register missing: ${oq_id}"
        fi
    done
fi
# Engagement design doc contracts (Law 24 + Law 18 + Law 2 + two-stage + deterministic join + Suppression Drift)
if [ -f "$ROOT/docs/architecture/engagement-retention-design.md" ]; then
    for keyword in "Law 24" "Law 18" "Law 2" "Law 9" "MarketingGate" "queue-time|queue time" "send-time|send time" "deterministic join" "Suppression Drift|SuppressionDrift" "RGPort" "propensity" "EU AI Act"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/architecture/engagement-retention-design.md"; then
            fail 205 "engagement-retention-design.md missing keyword: ${keyword}"
        fi
    done
fi

# ═════════════════════════════════════════════════════════════════════════
# Phase 23 rules (206–215) — Commercial & Billing — DEC-0024 monetizes
# Law 4: invoices reconcile against ledger (source of truth).
# Law 9: billing changes audited; hash-chained.
# Phase 1 rule 5: contracts HUMAN-APPROVED (Business/Legal).
# ═════════════════════════════════════════════════════════════════════════

# ─── Rule 206: Phase 23 ADRs 0142-0146 all exist ────────────────────────
for adr_n in 0142 0143 0144 0145 0146; do
    adr_file="$ROOT/docs/adr/ADR-${adr_n}.md"
    if [ ! -f "$adr_file" ]; then
        fail 206 "Phase 23 ADR ADR-${adr_n} missing"
    fi
done

# ─── Rule 207: ADR-0142 documents contract model + versioning + FSM ────
if [ -f "$ROOT/docs/adr/ADR-0142.md" ]; then
    for keyword in "Contract" "ContractVersion" "version" "FSM" "draft" "active" "suspended" "terminated" "HUMAN-APPROVED" "7+ year|7 year"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/adr/ADR-0142.md"; then
            fail 207 "ADR-0142 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 208: ADR-0143 documents fee schedule + 4 types + versioning ──
if [ -f "$ROOT/docs/adr/ADR-0143.md" ]; then
    for keyword in "FeeSchedule" "rev_share" "fixed_fee" "hybrid" "tiered" "per-product|per product" "effective_from" "effective_until" "immutable"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/adr/ADR-0143.md"; then
            fail 208 "ADR-0143 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 209: ADR-0144 documents invoice generation + reconciliation ──
if [ -f "$ROOT/docs/adr/ADR-0144.md" ]; then
    for keyword in "Invoice" "GGR" "reconciliation" "matched" "mismatched" "HALT" "ledger" "CreditNote" "immutable" "insert-only" "payment" "FSM"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/adr/ADR-0144.md"; then
            fail 209 "ADR-0144 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 210: ADR-0145 documents operator statements + transactional ──
if [ -f "$ROOT/docs/adr/ADR-0145.md" ]; then
    for keyword in "OperatorStatement" "portal" "email" "transactional" "MarketingGate" "bypass" "reconciliation" "acknowledgment"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/adr/ADR-0145.md"; then
            fail 210 "ADR-0145 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 211: ADR-0146 documents billing audit + hash-chained ──────────
if [ -f "$ROOT/docs/adr/ADR-0146.md" ]; then
    for keyword in "billing" "audit" "hash-chained|hash chained" "immutable" "Law 9" "Phase 7" "16" "event" "noventra_auditor|external auditor"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/adr/ADR-0146.md"; then
            fail 211 "ADR-0146 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 212: Phase 23 design doc exists ───────────────────────────────
if [ ! -f "$ROOT/docs/architecture/commercial-billing-design.md" ]; then
    fail 212 "Phase 23 commercial-billing-design.md missing"
fi

# ─── Rule 213: Phase 23 stage handoff exists ────────────────────────────
if [ ! -f "$ROOT/docs/stage-handoffs/stage-23-handoff.md" ]; then
    fail 213 "Phase 23 stage-23-handoff.md missing"
fi

# ─── Rule 214: Phase 23 audit exists ────────────────────────────────────
if [ ! -f "$ROOT/docs/audits/phase-023-audit.md" ]; then
    fail 214 "Phase 23 audit missing"
fi

# ─── Rule 215: OQs + design doc contracts (Law 4 + Law 9 + DEC-0024) ───
# Open questions register documents OQ-COMM-001..006
if [ -f "$OQ_FILE" ]; then
    for oq_id in OQ-COMM-001 OQ-COMM-002 OQ-COMM-003 OQ-COMM-004 OQ-COMM-005 OQ-COMM-006; do
        if ! grep -q "$oq_id" "$OQ_FILE"; then
            fail 215 "Open questions register missing: ${oq_id}"
        fi
    done
fi
# Commercial billing design doc contracts (Law 4 + Law 9 + reconciliation + DEC-0024)
if [ -f "$ROOT/docs/architecture/commercial-billing-design.md" ]; then
    for keyword in "Law 4" "Law 9" "reconciliation" "GGR" "ledger" "DEC-0024" "Contract" "FeeSchedule" "Invoice" "HUMAN-APPROVED" "hash"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/architecture/commercial-billing-design.md"; then
            fail 215 "commercial-billing-design.md missing keyword: ${keyword}"
        fi
    done
fi

# ═════════════════════════════════════════════════════════════════════════
# Phase 24 rules (216–225) — Developer Platform & Player SDK — B2B wedge
# Blueprint §12: sandbox↔prod key confusion (mitigated by prefixed keys).
# Blueprint §21: B2B wedge (partner keys + webhooks + sandbox + docs + SDK).
# ADR-0020: Player SDK Conformance Gate (Phase 2 seed → Phase 24 closure).
# Law 17: every partner API call produces receipt ID.
# ═════════════════════════════════════════════════════════════════════════

# ─── Rule 216: Phase 24 ADRs 0147-0151 all exist ────────────────────────
for adr_n in 0147 0148 0149 0150 0151; do
    adr_file="$ROOT/docs/adr/ADR-${adr_n}.md"
    if [ ! -f "$adr_file" ]; then
        fail 216 "Phase 24 ADR ADR-${adr_n} missing"
    fi
done

# ─── Rule 217: ADR-0147 documents partner keys + prefix + scope + hash ──
if [ -f "$ROOT/docs/adr/ADR-0147.md" ]; then
    for keyword in "PartnerKey" "sk_test_" "sk_live_" "hash" "scope" "rotation|rotat" "prefix" "HMAC|SHA-256|sha256"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/adr/ADR-0147.md"; then
            fail 217 "ADR-0147 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 218: ADR-0148 documents partner webhooks + signed + DLQ ───────
if [ -f "$ROOT/docs/adr/ADR-0148.md" ]; then
    for keyword in "PartnerWebhook" "HMAC" "signature" "DLQ|dlq" "retry" "backoff" "secret" "event_type"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/adr/ADR-0148.md"; then
            fail 218 "ADR-0148 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 219: ADR-0149 documents sandbox tenant + isolation ────────────
if [ -f "$ROOT/docs/adr/ADR-0149.md" ]; then
    for keyword in "sandbox" "isolation" "stub" "self-provision|self provision" "time-limited|time limited|30 day" "regulatory" "exclusion"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/adr/ADR-0149.md"; then
            fail 219 "ADR-0149 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 220: ADR-0150 documents docs portal + versioning ──────────────
if [ -f "$ROOT/docs/adr/ADR-0150.md" ]; then
    for keyword in "DocsPortal|docs portal" "OpenAPI" "integration" "SDK" "version" "partner" "auth"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/adr/ADR-0150.md"; then
            fail 220 "ADR-0150 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 221: ADR-0151 documents Player SDK + conformance + gate ───────
if [ -f "$ROOT/docs/adr/ADR-0151.md" ]; then
    for keyword in "Player SDK" "reference lobby" "conformance" "production-key gate|production.key gate|gate" "ADR-0020" "non-conforming|non conforming" "sk_live_"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/adr/ADR-0151.md"; then
            fail 221 "ADR-0151 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 222: Phase 24 design doc exists ───────────────────────────────
if [ ! -f "$ROOT/docs/architecture/developer-platform-design.md" ]; then
    fail 222 "Phase 24 developer-platform-design.md missing"
fi

# ─── Rule 223: Phase 24 stage handoff exists ────────────────────────────
if [ ! -f "$ROOT/docs/stage-handoffs/stage-24-handoff.md" ]; then
    fail 223 "Phase 24 stage-24-handoff.md missing"
fi

# ─── Rule 224: Phase 24 audit exists ────────────────────────────────────
if [ ! -f "$ROOT/docs/audits/phase-024-audit.md" ]; then
    fail 224 "Phase 24 audit missing"
fi

# ─── Rule 225: OQs + design doc contracts (blueprint §21 + §12 + ADR-0020)
# Open questions register documents OQ-DEV-001..006
if [ -f "$OQ_FILE" ]; then
    for oq_id in OQ-DEV-001 OQ-DEV-002 OQ-DEV-003 OQ-DEV-004 OQ-DEV-005 OQ-DEV-006; do
        if ! grep -q "$oq_id" "$OQ_FILE"; then
            fail 225 "Open questions register missing: ${oq_id}"
        fi
    done
fi
# Developer platform design doc contracts (blueprint §21 + §12 + ADR-0020 + partner keys + webhooks + sandbox + conformance)
if [ -f "$ROOT/docs/architecture/developer-platform-design.md" ]; then
    for keyword in "partner" "webhook" "sandbox" "conformance" "SDK" "sk_test_" "sk_live_" "ADR-0020" "blueprint" "receipt" "DLQ"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/architecture/developer-platform-design.md"; then
            fail 225 "developer-platform-design.md missing keyword: ${keyword}"
        fi
    done
fi

# ═════════════════════════════════════════════════════════════════════════
# Phase 25 FINAL rules (226–235) — Validation, Readiness & Launch
# The FINAL gate. 25 phases converge here. Go/No-Go. All named humans sign.
# ═════════════════════════════════════════════════════════════════════════

# ─── Rule 226: Phase 25 ADRs 0152-0155 all exist ────────────────────────
for adr_n in 0152 0153 0154 0155; do
    adr_file="$ROOT/docs/adr/ADR-${adr_n}.md"
    if [ ! -f "$adr_file" ]; then
        fail 226 "Phase 25 ADR ADR-${adr_n} missing"
    fi
done

# ─── Rule 227: ADR-0152 documents 4 validation suites ───────────────────
if [ -f "$ROOT/docs/adr/ADR-0152.md" ]; then
    for keyword in "Security" "Concurrency" "Chaos" "Load" "OWASP|ASVS" "financial invariant" "Kill Switch" "200ms" "capacity" "injection"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/adr/ADR-0152.md"; then
            fail 227 "ADR-0152 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 228: ADR-0153 documents vuln scan + restore drill + DR ────────
if [ -f "$ROOT/docs/adr/ADR-0153.md" ]; then
    for keyword in "vulnerability" "SAST" "DAST" "restore" "RTO" "RPO" "DR plan|disaster|recovery" "backup" "PCI"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/adr/ADR-0153.md"; then
            fail 228 "ADR-0153 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 229: ADR-0154 documents SLOs + incident response + gates ──────
if [ -f "$ROOT/docs/adr/ADR-0154.md" ]; then
    for keyword in "SLO" "99.9" "200ms" "incident" "on-call|on call" "postmortem" "release gate" "error budget" "tabletop"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/adr/ADR-0154.md"; then
            fail 229 "ADR-0154 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 230: ADR-0155 documents Go/No-Go + 16 named humans ────────────
if [ -f "$ROOT/docs/adr/ADR-0155.md" ]; then
    for keyword in "Go" "No-Go|NO-GO" "release gate" "named human" "CTO" "CFO" "MLRO" "External Auditor" "sign" "launch" "no auto"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/adr/ADR-0155.md"; then
            fail 230 "ADR-0155 missing keyword: ${keyword}"
        fi
    done
fi

# ─── Rule 231: Phase 25 design doc exists ───────────────────────────────
if [ ! -f "$ROOT/docs/architecture/validation-launch-design.md" ]; then
    fail 231 "Phase 25 validation-launch-design.md missing"
fi

# ─── Rule 232: Phase 25 stage handoff exists ────────────────────────────
if [ ! -f "$ROOT/docs/stage-handoffs/stage-25-handoff.md" ]; then
    fail 232 "Phase 25 stage-25-handoff.md missing"
fi

# ─── Rule 233: Phase 25 audit exists ────────────────────────────────────
if [ ! -f "$ROOT/docs/audits/phase-025-audit.md" ]; then
    fail 233 "Phase 25 audit missing"
fi

# ─── Rule 234: Open questions register documents OQ-LAUNCH-001..006 ────
if [ -f "$OQ_FILE" ]; then
    for oq_id in OQ-LAUNCH-001 OQ-LAUNCH-002 OQ-LAUNCH-003 OQ-LAUNCH-004 OQ-LAUNCH-005 OQ-LAUNCH-006; do
        if ! grep -q "$oq_id" "$OQ_FILE"; then
            fail 234 "Open questions register missing: ${oq_id}"
        fi
    done
fi

# ─── Rule 235: FINAL design doc contracts (Go/No-Go + 25 phases + launch)
if [ -f "$ROOT/docs/architecture/validation-launch-design.md" ]; then
    for keyword in "Go" "No-Go|NO-GO" "release gate" "security" "concurrency" "chaos" "load" "restore" "SLO" "200ms" "named human" "launch" "25 phase|final"; do
        if ! grep -qiE "$keyword" "$ROOT/docs/architecture/validation-launch-design.md"; then
            fail 235 "validation-launch-design.md missing keyword: ${keyword}"
        fi
    done
fi

# ─── Floor checks (informational) ───────────────────────────────────────
req_floor=62
dec_floor=156
adr_floor=88
if [ "$req_count" -lt "$req_floor" ]; then
    echo "LINT WARN: REQ count $req_count < floor $req_floor" >&2
fi
if [ "$dec_count" -lt "$dec_floor" ]; then
    echo "LINT WARN: DEC count $dec_count < floor $dec_floor" >&2
fi
if [ "$adr_count" -lt "$adr_floor" ]; then
    echo "LINT WARN: ADR count $adr_count < floor $adr_floor" >&2
fi

# ─── Summary ────────────────────────────────────────────────────────────
echo "─── Traceability Lint Summary ───"
echo "Trace file: $TRACE_FILE"
echo "ADR dir:    $ADR_DIR"
echo "REQs parsed: $req_count (floor: $req_floor)"
echo "DECs parsed: $dec_count (floor: $dec_floor)"
echo "ADRs parsed: $adr_count (floor: $adr_floor)"
echo "Violations:  $VIOLATIONS"

if [ "$VIOLATIONS" -gt 0 ]; then
    exit 1
fi
exit 0
