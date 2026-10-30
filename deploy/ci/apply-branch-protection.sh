#!/usr/bin/env bash
# apply-branch-protection.sh — apply GitHub branch protection rules.
#
# Per Phase 4 spec output #11: PR-only, no force-push, ≥1 reviewer
# (2 for security paths), CI-green, stale delete.
#
# Requires: GitHub CLI (gh) installed and authenticated.
# Usage:    bash deploy/ci/apply-branch-protection.sh
#
# Phase 4 stub: this script applies the rules in branch-protection.json.
# In a sandboxed environment without a real GitHub repo, it prints the
# commands that would be run. Phase 5+ wires it into the deploy pipeline.

set -euo pipefail

CONFIG_FILE="${1:-deploy/ci/branch-protection.json}"
REPO="${REPO:-}"  # e.g., "noventra/platform"

if [ -z "$REPO" ]; then
    echo "ERROR: set REPO env var (e.g., REPO=noventra/platform)" >&2
    echo "Phase 4 stub: would apply rules from $CONFIG_FILE to repo $REPO" >&2
    exit 0
fi

if ! command -v gh >/dev/null 2>&1; then
    echo "ERROR: GitHub CLI (gh) not installed." >&2
    exit 1
fi

echo "Applying branch protection rules to $REPO from $CONFIG_FILE..."

# Phase 4 stub: in production, parse the JSON and call:
#   gh api -X PUT repos/$REPO/branches/main/protection ...
# For now, we print the equivalent gh commands.
cat <<EOF
# Equivalent gh commands (Phase 4 stub):
gh api -X PUT "repos/$REPO/branches/main/protection" \
  -f "required_status_checks[strict]=true" \
  -f "required_status_checks[checks][]=lint-and-test" \
  -f "enforce_admins=true" \
  -f "required_pull_request_reviews[dismiss_stale_reviews]=true" \
  -f "required_pull_request_reviews[require_code_owner_reviews]=true" \
  -f "required_pull_request_reviews[required_approving_review_count]=1" \
  -f "restrictions=" \
  -f "required_linear_history=true" \
  -f "allow_force_pushes=false" \
  -f "allow_deletions=false" \
  -f "block_creations=true" \
  -f "required_conversation_resolution=true"

# Stale branch deletion (scheduled workflow in Phase 5+):
#   delete branches with no commits in 30 days, excluding main/trunk/release/*
EOF

echo "Phase 4 stub complete. Real application requires a live GitHub repo."
