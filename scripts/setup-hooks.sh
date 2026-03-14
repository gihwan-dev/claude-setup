#!/usr/bin/env bash
# One-time setup: point git's core.hooksPath to the repo's hooks/ directory.
# This covers all worktrees sharing the same git config.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

git -C "$REPO_ROOT" config core.hooksPath "$REPO_ROOT/hooks"

echo "[claude-setup] core.hooksPath set to $REPO_ROOT/hooks"
echo "[claude-setup] Hooks are now active for commit, merge, and branch switch."
