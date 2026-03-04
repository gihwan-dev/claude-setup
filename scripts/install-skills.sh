#!/usr/bin/env bash
set -euo pipefail

MODE="link"
DRY_RUN=0
TARGETS=()
CUSTOM_DEST=""

usage() {
  cat <<'USAGE'
Usage: scripts/install-skills.sh [options]

Install skills and agents into AI agent tool directories.
By default, existing entries are overwritten (re-linked).

Options:
  --target <claude|codex|all>  Target platform (default: auto-detect)
  --copy         Copy instead of symlinking
  --link         Symlink (default)
  --dest <path>  Override destination directory (ignores --target)
  --dry-run      Show what would happen without making changes
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
    --copy)    MODE="copy"; shift ;;
    --link)    MODE="link"; shift ;;
    --dest)    CUSTOM_DEST="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_SRC="$REPO_ROOT/skills"
AGENTS_SRC="$REPO_ROOT/agents"

if [[ ! -d "$SKILLS_SRC" ]]; then
  echo "Skills directory not found: $SKILLS_SRC" >&2
  exit 1
fi

# ── helpers ──────────────────────────────────────────────

resolve_dest() {
  local target="$1" kind="$2"
  case "$target" in
    claude) echo "${CLAUDE_HOME:-$HOME/.claude}/$kind" ;;
    codex)  echo "${CODEX_HOME:-$HOME/.codex}/$kind" ;;
  esac
}

# Install source entries into dest directory.
# Usage: install_entries <source_dir> <dest_dir> <label> <glob_pattern>
#   glob_pattern: "*" for directories (skills), "*.md" for files (agents)
install_entries() {
  local src_dir="$1" dest_dir="$2" label="$3" pattern="$4"

  mkdir -p "$dest_dir"

  echo ""
  echo "[$label]"
  echo "  Source:      $src_dir"
  echo "  Destination: $dest_dir"
  echo "  Mode:        $MODE"

  local installed=0 updated=0 unchanged=0

  for entry in "$src_dir"/$pattern; do
    # skills: match directories only / agents: match files
    if [[ "$pattern" == "*" ]]; then
      [[ -d "$entry" ]] || continue
    else
      [[ -f "$entry" ]] || continue
    fi

    local name
    name="$(basename "$entry")"
    local target="$dest_dir/$name"
    local action="new"

    # Check if already exists and whether update is needed
    if [[ -L "$target" ]]; then
      local current
      current="$(readlink "$target")"
      if [[ "$current" == "$entry" ]]; then
        unchanged=$((unchanged + 1))
        continue
      fi
      action="update"
    elif [[ -e "$target" ]]; then
      action="update"
    fi

    if [[ "$DRY_RUN" -eq 1 ]]; then
      echo "  [dry-run] $action  $name"
      installed=$((installed + 1))
      continue
    fi

    rm -rf "$target"

    if [[ "$MODE" == "copy" ]]; then
      cp -R "$entry" "$target"
    else
      ln -s "$entry" "$target"
    fi

    if [[ "$action" == "update" ]]; then
      echo "  update  $name"
      updated=$((updated + 1))
    else
      echo "  new     $name"
      installed=$((installed + 1))
    fi
  done

  echo "  New: $installed / Updated: $updated / Unchanged: $unchanged"
}

# Remove symlinks in dest that point to missing targets.
cleanup_broken() {
  local dest_dir="$1" label="$2"
  local removed=0

  for entry in "$dest_dir"/*; do
    [[ -L "$entry" ]] || continue
    [[ -e "$entry" ]] && continue

    local name
    name="$(basename "$entry")"

    if [[ "$DRY_RUN" -eq 1 ]]; then
      echo "  [dry-run] remove broken  $name -> $(readlink "$entry")"
    else
      rm -f "$entry"
      echo "  remove broken  $name -> $(readlink "$entry" 2>/dev/null || echo '?')"
    fi
    removed=$((removed + 1))
  done

  if [[ "$removed" -gt 0 ]]; then
    echo "  Cleaned up $removed broken symlink(s) in $label"
  fi
}

# ── main ─────────────────────────────────────────────────

if [[ -n "$CUSTOM_DEST" ]]; then
  install_entries "$SKILLS_SRC" "$CUSTOM_DEST" "custom/skills" "*"
else
  # Auto-detect if no targets specified
  if [[ ${#TARGETS[@]} -eq 0 ]]; then
    claude_home="${CLAUDE_HOME:-$HOME/.claude}"
    codex_home="${CODEX_HOME:-$HOME/.codex}"

    [[ -d "$claude_home" ]] && TARGETS+=("claude")
    [[ -d "$codex_home" ]]  && TARGETS+=("codex")

    if [[ ${#TARGETS[@]} -eq 0 ]]; then
      echo "No AI agent tools detected." >&2
      echo "Checked: $claude_home, $codex_home" >&2
      echo "" >&2
      echo "Use --target to specify a platform or --dest for a custom path." >&2
      exit 1
    fi
  fi

  for t in "${TARGETS[@]}"; do
    # Skills
    skills_dest="$(resolve_dest "$t" "skills")"
    install_entries "$SKILLS_SRC" "$skills_dest" "$t/skills" "*"
    cleanup_broken "$skills_dest" "$t/skills"

    # Agents (claude: .md files)
    if [[ "$t" == "claude" && -d "$AGENTS_SRC" ]]; then
      agents_dest="$(resolve_dest "$t" "agents")"
      install_entries "$AGENTS_SRC" "$agents_dest" "$t/agents" "*.md"
      cleanup_broken "$agents_dest" "$t/agents"
    fi
  done
fi

# Sync INSTRUCTIONS.md → CLAUDE.md / AGENTS.md
if [[ -x "$SCRIPT_DIR/sync-instructions.sh" ]]; then
  echo ""
  echo "[sync]"
  "$SCRIPT_DIR/sync-instructions.sh"
fi

echo ""
echo "Done. Restart your AI agent to load updated configurations."
