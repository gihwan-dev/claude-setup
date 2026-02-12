#!/usr/bin/env bash
set -euo pipefail

MODE="link"
FORCE=0
DEST_DIR="${CODEX_HOME:-$HOME/.codex}/skills"

usage() {
  cat <<'USAGE'
Usage: scripts/install-codex-skills.sh [options]

Install this repository's skills into Codex skills directory.

Options:
  --copy         Copy skill folders instead of symlinking
  --link         Symlink skill folders (default)
  --dest <path>  Override destination directory (default: $CODEX_HOME/skills)
  --force        Overwrite existing destination skill folders
  -h, --help     Show help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --copy)
      MODE="copy"
      shift
      ;;
    --link)
      MODE="link"
      shift
      ;;
    --dest)
      DEST_DIR="$2"
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

mkdir -p "$DEST_DIR"

echo "Source: $SOURCE_DIR"
echo "Destination: $DEST_DIR"
echo "Mode: $MODE"

installed=0
skipped=0

for skill_dir in "$SOURCE_DIR"/*; do
  [[ -d "$skill_dir" ]] || continue

  skill_name="$(basename "$skill_dir")"
  target="$DEST_DIR/$skill_name"

  if [[ -e "$target" || -L "$target" ]]; then
    if [[ "$FORCE" -eq 1 ]]; then
      rm -rf "$target"
    else
      echo "skip  $skill_name (already exists: $target)"
      skipped=$((skipped + 1))
      continue
    fi
  fi

  if [[ "$MODE" == "copy" ]]; then
    cp -R "$skill_dir" "$target"
  else
    ln -s "$skill_dir" "$target"
  fi

  echo "ok    $skill_name"
  installed=$((installed + 1))
done

echo
echo "Installed: $installed"
echo "Skipped:   $skipped"
echo "Restart Codex to load updated skills."
