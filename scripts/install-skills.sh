#!/usr/bin/env bash
set -euo pipefail

MODE="link"
FORCE=0
TARGETS=()
CUSTOM_DEST=""

usage() {
  cat <<'USAGE'
Usage: scripts/install-skills.sh [options]

Install skills into AI agent tool directories.

Options:
  --target <claude|codex|all>  Target platform (default: auto-detect)
  --copy         Copy skill folders instead of symlinking
  --link         Symlink skill folders (default)
  --dest <path>  Override destination directory (ignores --target)
  --force        Overwrite existing destination skill folders
  -h, --help     Show help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      case "$2" in
        claude) TARGETS+=("claude") ;;
        codex)  TARGETS+=("codex") ;;
        all)    TARGETS+=("claude" "codex") ;;
        *)
          echo "Unknown target: $2 (use claude, codex, or all)" >&2
          exit 1
          ;;
      esac
      shift 2
      ;;
    --copy)
      MODE="copy"
      shift
      ;;
    --link)
      MODE="link"
      shift
      ;;
    --dest)
      CUSTOM_DEST="$2"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_DIR="$REPO_ROOT/skills"

if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "Skills directory not found: $SOURCE_DIR" >&2
  exit 1
fi

resolve_dest() {
  local target="$1"
  case "$target" in
    claude) echo "${CLAUDE_HOME:-$HOME/.claude}/skills" ;;
    codex)  echo "${CODEX_HOME:-$HOME/.codex}/skills" ;;
  esac
}

install_to() {
  local dest_dir="$1"
  local label="$2"

  mkdir -p "$dest_dir"

  echo ""
  echo "[$label]"
  echo "  Source:      $SOURCE_DIR"
  echo "  Destination: $dest_dir"
  echo "  Mode:        $MODE"

  local installed=0
  local skipped=0

  for skill_dir in "$SOURCE_DIR"/*; do
    [[ -d "$skill_dir" ]] || continue

    local skill_name
    skill_name="$(basename "$skill_dir")"
    local target="$dest_dir/$skill_name"

    if [[ -e "$target" || -L "$target" ]]; then
      if [[ "$FORCE" -eq 1 ]]; then
        rm -rf "$target"
      else
        echo "  skip  $skill_name (already exists)"
        skipped=$((skipped + 1))
        continue
      fi
    fi

    if [[ "$MODE" == "copy" ]]; then
      cp -R "$skill_dir" "$target"
    else
      ln -s "$skill_dir" "$target"
    fi

    echo "  ok    $skill_name"
    installed=$((installed + 1))
  done

  echo "  Installed: $installed / Skipped: $skipped"
}

# Custom destination: install once
if [[ -n "$CUSTOM_DEST" ]]; then
  install_to "$CUSTOM_DEST" "custom"
else
  # Auto-detect if no targets specified
  if [[ ${#TARGETS[@]} -eq 0 ]]; then
    claude_home="${CLAUDE_HOME:-$HOME/.claude}"
    codex_home="${CODEX_HOME:-$HOME/.codex}"

    if [[ -d "$claude_home" ]]; then
      TARGETS+=("claude")
    fi
    if [[ -d "$codex_home" ]]; then
      TARGETS+=("codex")
    fi

    if [[ ${#TARGETS[@]} -eq 0 ]]; then
      echo "No AI agent tools detected." >&2
      echo "Checked: $claude_home, $codex_home" >&2
      echo "" >&2
      echo "Use --target to specify a platform or --dest for a custom path." >&2
      exit 1
    fi
  fi

  for t in "${TARGETS[@]}"; do
    dest="$(resolve_dest "$t")"
    install_to "$dest" "$t"
  done
fi

# Sync INSTRUCTIONS.md → CLAUDE.md / AGENTS.md
if [[ -x "$SCRIPT_DIR/sync-instructions.sh" ]]; then
  echo ""
  echo "[sync]"
  "$SCRIPT_DIR/sync-instructions.sh"
fi

echo ""
echo "Done. Restart your AI agent to load updated skills."
