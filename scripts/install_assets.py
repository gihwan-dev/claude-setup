#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

BEGIN_MANAGED = "# BEGIN MANAGED AGENTS (claude-setup)"
END_MANAGED = "# END MANAGED AGENTS (claude-setup)"
REPO_NOTICE_LINE_1 = "<!-- AUTO-GENERATED from agent-registry. Do not edit directly. -->"
REPO_NOTICE_LINE_2 = "<!-- Run: python3 scripts/sync_agents.py -->"
CODEX_NOTICE_LINE_1 = "# AUTO-GENERATED from agent-registry. Do not edit directly."
CODEX_NOTICE_LINE_2 = "# Run: python3 scripts/sync_agents.py"
MANAGED_BLOCK_PATTERN = re.compile(
    rf"{re.escape(BEGIN_MANAGED)}\n(.*?)\n{re.escape(END_MANAGED)}\n?",
    re.DOTALL,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install skills and agent assets for Claude/Codex"
    )
    parser.add_argument(
        "--target",
        choices=["claude", "codex", "all"],
        help="Target platform (default: auto-detect)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--copy", action="store_true", help="Copy files")
    mode.add_argument("--link", action="store_true", help="Symlink files (default)")
    parser.add_argument("--dest", help="Custom destination path (skills only)")
    parser.add_argument("--dry-run", action="store_true", help="Show planned actions only")
    return parser.parse_args()


def resolve_home(target: str) -> Path:
    if target == "claude":
        return Path(os.environ.get("CLAUDE_HOME", str(Path.home() / ".claude")))
    if target == "codex":
        return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    raise ValueError(f"unknown target: {target}")


def detect_targets() -> list[str]:
    result: list[str] = []
    if resolve_home("claude").exists():
        result.append("claude")
    if resolve_home("codex").exists():
        result.append("codex")
    return result


def run_sync(repo_root: Path, dry_run: bool) -> None:
    scripts_dir = repo_root / "scripts"
    sync_instructions = scripts_dir / "sync_instructions.py"
    sync_agents = scripts_dir / "sync_agents.py"
    python = sys.executable

    commands = [
        [python, str(sync_instructions), "--check" if dry_run else ""],
        [python, str(sync_agents), "--check" if dry_run else ""],
    ]
    for command in commands:
        cmd = [part for part in command if part]
        completed = subprocess.run(cmd, cwd=repo_root, check=False)
        if completed.returncode != 0:
            raise SystemExit(completed.returncode)


def install_path(source: Path, destination: Path, mode: str, dry_run: bool) -> None:
    action = "link" if mode == "link" else "copy"
    if dry_run:
        print(f"[dry-run] {action} {source} -> {destination}")
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink() or destination.exists():
        if destination.is_dir() and not destination.is_symlink():
            shutil.rmtree(destination)
        else:
            destination.unlink()

    if mode == "link":
        destination.symlink_to(source)
    else:
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)


def install_entries(
    source_dir: Path,
    destination_dir: Path,
    *,
    mode: str,
    dry_run: bool,
    include_dirs: bool,
    suffix: str | None = None,
) -> None:
    if not source_dir.exists():
        return

    if not dry_run:
        destination_dir.mkdir(parents=True, exist_ok=True)
    for source in sorted(source_dir.iterdir()):
        if include_dirs and not source.is_dir():
            continue
        if not include_dirs and not source.is_file():
            continue
        if suffix and source.suffix != suffix:
            continue
        install_path(source, destination_dir / source.name, mode, dry_run)


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _extract_existing_managed_body(config_text: str) -> str | None:
    match = MANAGED_BLOCK_PATTERN.search(config_text)
    if not match:
        return None
    return match.group(1)


def _parse_managed_agent_files(managed_body: str | None) -> set[str]:
    if not managed_body:
        return set()
    try:
        parsed = tomllib.loads(managed_body)
    except tomllib.TOMLDecodeError:
        return set()

    agents = parsed.get("agents", {})
    if not isinstance(agents, dict):
        return set()

    files: set[str] = set()
    for info in agents.values():
        if not isinstance(info, dict):
            continue
        config_file = info.get("config_file")
        if not isinstance(config_file, str):
            continue
        if not config_file.startswith("agents/"):
            continue
        name = Path(config_file).name
        if name.endswith(".toml"):
            files.add(name)
    return files


def _is_repo_generated_agent(path: Path) -> bool:
    text = _read_text(path)
    return REPO_NOTICE_LINE_1 in text and REPO_NOTICE_LINE_2 in text


def _is_codex_generated_agent(path: Path) -> bool:
    lines = _read_text(path).splitlines()
    return len(lines) >= 2 and lines[0].strip() == CODEX_NOTICE_LINE_1 and lines[1].strip() == CODEX_NOTICE_LINE_2


def _prune_file(path: Path, *, reason: str, dry_run: bool) -> None:
    if dry_run:
        print(f"[dry-run] prune {path} ({reason})")
        return
    if not path.exists() and not path.is_symlink():
        return
    path.unlink()
    print(f"prune {path} ({reason})")


def prune_claude_agents(
    *,
    agents_dir: Path,
    expected_names: set[str],
    dry_run: bool,
) -> None:
    if not agents_dir.exists():
        return
    for path in sorted(agents_dir.glob("*.md")):
        if path.name in expected_names:
            continue
        if path.is_symlink() and not path.exists():
            _prune_file(path, reason="broken stale claude agent symlink", dry_run=dry_run)
            continue
        if _is_repo_generated_agent(path):
            _prune_file(path, reason="stale generated claude agent", dry_run=dry_run)


def prune_codex_agents(
    *,
    agents_dir: Path,
    expected_names: set[str],
    previous_managed_names: set[str],
    dry_run: bool,
) -> None:
    stale_paths: dict[Path, str] = {}

    for name in sorted(previous_managed_names):
        if name in expected_names:
            continue
        stale_paths[agents_dir / name] = "stale from previous managed block"

    if agents_dir.exists():
        for path in sorted(agents_dir.glob("*.toml")):
            if path.name in expected_names:
                continue
            if path.is_symlink() and not path.exists():
                stale_paths[path] = "broken stale codex agent symlink"
                continue
            if _is_codex_generated_agent(path):
                stale_paths[path] = "stale generated codex agent"

    for path in sorted(stale_paths):
        _prune_file(path, reason=stale_paths[path], dry_run=dry_run)


def update_codex_config(
    codex_home: Path,
    managed_config_path: Path,
    *,
    dry_run: bool,
) -> None:
    config_path = codex_home / "config.toml"
    managed = managed_config_path.read_text(encoding="utf-8").rstrip()
    managed_block = f"{BEGIN_MANAGED}\n{managed}\n{END_MANAGED}\n"

    if config_path.exists():
        current = config_path.read_text(encoding="utf-8")
    else:
        current = ""

    if MANAGED_BLOCK_PATTERN.search(current):
        updated = MANAGED_BLOCK_PATTERN.sub(lambda _: managed_block, current)
    else:
        separator = "" if current.endswith("\n") or not current else "\n"
        updated = f"{current}{separator}{managed_block}"

    if current == updated:
        print(f"ok  {config_path} (managed block unchanged)")
        return

    if dry_run:
        print(f"[dry-run] update managed block in {config_path}")
        return

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(updated, encoding="utf-8")
    print(f"ok  {config_path} (managed block updated)")


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    mode = "copy" if args.copy else "link"

    run_sync(repo_root, dry_run=args.dry_run)

    skills_src = repo_root / "skills"
    agent_skills_src = repo_root / ".agents" / "skills"
    repo_agents_src = repo_root / "agents"
    codex_agents_src = repo_root / "dist" / "codex" / "agents"
    codex_managed_src = repo_root / "dist" / "codex" / "config.managed-agents.toml"
    expected_repo_agent_names = {path.name for path in repo_agents_src.glob("*.md")}
    expected_codex_agent_names = {path.name for path in codex_agents_src.glob("*.toml")}

    if args.dest:
        destination = Path(args.dest)
        install_entries(
            skills_src, destination, mode=mode, dry_run=args.dry_run, include_dirs=True
        )
        install_entries(
            agent_skills_src,
            destination,
            mode=mode,
            dry_run=args.dry_run,
            include_dirs=True,
        )
        print("Done.")
        return 0

    if args.target:
        targets = ["claude", "codex"] if args.target == "all" else [args.target]
    else:
        targets = detect_targets()
        if not targets:
            print("No AI agent tools detected. Use --target or --dest.", file=sys.stderr)
            return 1

    for target in targets:
        home = resolve_home(target)
        skills_dest = home / "skills"
        install_entries(
            skills_src, skills_dest, mode=mode, dry_run=args.dry_run, include_dirs=True
        )
        install_entries(
            agent_skills_src,
            skills_dest,
            mode=mode,
            dry_run=args.dry_run,
            include_dirs=True,
        )

        if target == "claude":
            install_entries(
                repo_agents_src,
                home / "agents",
                mode=mode,
                dry_run=args.dry_run,
                include_dirs=False,
                suffix=".md",
            )
            prune_claude_agents(
                agents_dir=home / "agents",
                expected_names=expected_repo_agent_names,
                dry_run=args.dry_run,
            )
        else:
            existing_config = _read_text(home / "config.toml")
            previous_managed_names = _parse_managed_agent_files(
                _extract_existing_managed_body(existing_config)
            )
            install_entries(
                codex_agents_src,
                home / "agents",
                mode=mode,
                dry_run=args.dry_run,
                include_dirs=False,
                suffix=".toml",
            )
            prune_codex_agents(
                agents_dir=home / "agents",
                expected_names=expected_codex_agent_names,
                previous_managed_names=previous_managed_names,
                dry_run=args.dry_run,
            )
            update_codex_config(
                home, codex_managed_src, dry_run=args.dry_run
            )

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
