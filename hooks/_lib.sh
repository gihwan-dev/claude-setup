#!/usr/bin/env bash
# Shared logic for git hooks that auto-run install_assets.py
# Each hook sources this file and calls claude_setup_auto_install OLD NEW.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$REPO_ROOT" ]; then
  exit 0
fi

# Paths whose changes should trigger install_assets.py
_WATCHED_PATTERNS=(
  "agent-registry/"
  "skills/"
  "policy/"
  "scripts/sync_agents.py"
  "scripts/sync_skills_index.py"
  "scripts/install_assets.py"
  "scripts/workflow_contract.py"
)

claude_setup_auto_install() {
  local old_ref="${1:-}"
  local new_ref="${2:-}"

  # --- python3 check ---
  if ! command -v python3 &>/dev/null; then
    echo "[claude-setup hook] WARNING: python3 not found, skipping auto-install." >&2
    return 0
  fi

  # --- debounce (5 seconds) ---
  local stamp_file="$REPO_ROOT/.git/claude-setup-hook-stamp"
  if [ -f "$stamp_file" ]; then
    local now
    now="$(date +%s)"
    local last
    last="$(cat "$stamp_file" 2>/dev/null || echo 0)"
    if [ $((now - last)) -lt 5 ]; then
      return 0
    fi
  fi

  # --- diff check ---
  local changed=false
  if [ -n "$old_ref" ] && [ -n "$new_ref" ] && git rev-parse "$old_ref" &>/dev/null && git rev-parse "$new_ref" &>/dev/null; then
    local diff_files
    diff_files="$(git diff --name-only "$old_ref" "$new_ref" 2>/dev/null || true)"
    if [ -n "$diff_files" ]; then
      for pattern in "${_WATCHED_PATTERNS[@]}"; do
        if echo "$diff_files" | grep -q "^${pattern}"; then
          changed=true
          break
        fi
      done
    fi
  else
    # Cannot determine diff (e.g. initial commit) — run install as fallback
    changed=true
  fi

  if [ "$changed" = false ]; then
    return 0
  fi

  # --- update stamp ---
  date +%s > "$stamp_file"

  # --- run install ---
  echo "[claude-setup hook] Detected relevant changes, running install_assets.py --link ..." >&2
  if ! python3 "$REPO_ROOT/scripts/install_assets.py" --link 2>&1; then
    echo "[claude-setup hook] WARNING: install_assets.py failed. Git operation continues." >&2
  fi

  return 0
}
