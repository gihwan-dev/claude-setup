#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE="$REPO_ROOT/INSTRUCTIONS.md"

if [[ ! -f "$SOURCE" ]]; then
  echo "INSTRUCTIONS.md not found: $SOURCE" >&2
  exit 1
fi

HEADER="<!-- AUTO-GENERATED from INSTRUCTIONS.md. Do not edit directly. -->
<!-- Run: ./scripts/sync-instructions.sh -->"

# AGENTS.md ← INSTRUCTIONS.md 전체 내용
{
  echo "$HEADER"
  echo ""
  cat "$SOURCE"
} > "$REPO_ROOT/AGENTS.md"
echo "ok  AGENTS.md"

# CLAUDE.md ← 빈 파일 (스킬/에이전트는 자동 로드)
echo "$HEADER" > "$REPO_ROOT/CLAUDE.md"
echo "ok  CLAUDE.md"
