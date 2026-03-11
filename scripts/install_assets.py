#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

from workflow_contract import (
    GENERATED_SKILL_MANIFEST_NAME,
    LEGACY_MILESTONE_SKILL_NAMES,
    REQUIRED_HELPER_AGENT_IDS,
)

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
SECTION_HEADER_PATTERN = re.compile(r"^\s*\[([^\[\]]+)\]\s*$")
MANAGED_BLOCK_PLACEHOLDER = "[__claude_setup_managed_agents_placeholder__]"


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
    sync_skills_index = scripts_dir / "sync_skills_index.py"
    python = sys.executable

    commands = [
        [python, str(sync_instructions), "--check" if dry_run else ""],
        [python, str(sync_agents), "--check" if dry_run else ""],
        [python, str(sync_skills_index), "--check" if dry_run else ""],
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


def _is_installable_skill_dir(path: Path) -> bool:
    return path.is_dir() and (path / "SKILL.md").exists()


def _iter_installable_skill_dirs(source_dir: Path) -> list[Path]:
    if not source_dir.exists():
        return []
    return sorted(
        path
        for path in source_dir.iterdir()
        if _is_installable_skill_dir(path)
    )


def _iter_internal_skill_asset_dirs(source_dir: Path) -> list[Path]:
    if not source_dir.exists():
        return []
    # Internal asset dirs such as skills/_shared are shipped for relative references
    # but must stay out of the generated skill catalog and prune surface.
    return sorted(
        path
        for path in source_dir.iterdir()
        if path.is_dir() and path.name.startswith("_") and not _is_installable_skill_dir(path)
    )


def expected_generated_skill_names(*source_dirs: Path) -> set[str]:
    names: set[str] = set()
    for source_dir in source_dirs:
        for source in _iter_installable_skill_dirs(source_dir):
            names.add(source.name)
    return names


def _legacy_overlay_message(source_dir: Path) -> str:
    return f"legacy overlay detected: {source_dir} (canonical source remains skills/)"


def _print_skill_source_summary(
    *,
    canonical_skills_src: Path,
    legacy_overlay_src: Path,
    dry_run: bool,
) -> None:
    mode = "[dry-run] " if dry_run else ""
    print(f"{mode}skill canonical source: {canonical_skills_src}")
    if legacy_overlay_src.exists():
        print(f"{mode}{_legacy_overlay_message(legacy_overlay_src)}")


def _install_skill_sources(
    *,
    canonical_skills_src: Path,
    legacy_overlay_src: Path,
    destination: Path,
    mode: str,
    dry_run: bool,
) -> None:
    for source in _iter_installable_skill_dirs(canonical_skills_src):
        install_path(source, destination / source.name, mode, dry_run)
    for source in _iter_installable_skill_dirs(legacy_overlay_src):
        install_path(source, destination / source.name, mode, dry_run)


def _install_internal_skill_assets(
    *,
    canonical_skills_src: Path,
    destination: Path,
    mode: str,
    dry_run: bool,
) -> None:
    # Copy/link internal assets separately so they do not appear as runnable skills.
    for source in _iter_internal_skill_asset_dirs(canonical_skills_src):
        prefix = "[dry-run] " if dry_run else ""
        print(f"{prefix}internal skill asset: {source}")
        install_path(source, destination / source.name, mode, dry_run)


def _skill_manifest_path(skills_dir: Path) -> Path:
    return skills_dir / GENERATED_SKILL_MANIFEST_NAME


def read_generated_skill_manifest(skills_dir: Path) -> set[str]:
    manifest_path = _skill_manifest_path(skills_dir)
    if not manifest_path.exists():
        return set()
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    names = payload.get("generated_skills")
    if not isinstance(names, list):
        return set()
    return {name for name in names if isinstance(name, str) and name}


def write_generated_skill_manifest(
    skills_dir: Path,
    generated_skill_names: set[str],
    *,
    dry_run: bool,
) -> None:
    manifest_path = _skill_manifest_path(skills_dir)
    payload = {"generated_skills": sorted(generated_skill_names)}
    if dry_run:
        print(f"[dry-run] update skill manifest {manifest_path}")
        return
    skills_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def prune_generated_skills(
    *,
    skills_dir: Path,
    expected_generated_names: set[str],
    previous_generated_names: set[str],
    dry_run: bool,
) -> None:
    stale_names = sorted(previous_generated_names - expected_generated_names)
    for name in stale_names:
        path = skills_dir / name
        if not path.exists() and not path.is_symlink():
            continue
        _prune_file(path, reason="stale generated skill", dry_run=dry_run)

    for name in LEGACY_MILESTONE_SKILL_NAMES:
        if name in expected_generated_names:
            continue
        path = skills_dir / name
        if not path.exists() and not path.is_symlink():
            continue
        _prune_file(path, reason="legacy milestone generated skill", dry_run=dry_run)

    for path in sorted(skills_dir.iterdir() if skills_dir.exists() else []):
        if not path.is_symlink() or path.name in expected_generated_names:
            continue
        if path.exists():
            continue
        _prune_file(path, reason="broken stale skill symlink", dry_run=dry_run)


def _load_codex_config(codex_home: Path) -> tuple[Path, dict[str, object]]:
    config_path = codex_home / "config.toml"
    if not config_path.exists():
        raise SystemExit(f"codex preflight failed: missing config: {config_path}")
    try:
        config_data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise SystemExit(f"codex preflight failed: invalid config.toml: {exc}") from exc
    if not isinstance(config_data, dict):
        raise SystemExit("codex preflight failed: config.toml must decode to a table")
    return config_path, config_data


def validate_required_codex_helpers(
    codex_home: Path,
    *,
    config_text: str | None = None,
    profile_root: Path | None = None,
) -> None:
    config_path = codex_home / "config.toml"
    if config_text is None:
        config_path, config_data = _load_codex_config(codex_home)
    else:
        try:
            config_data = tomllib.loads(config_text)
        except tomllib.TOMLDecodeError as exc:
            raise SystemExit(
                f"codex preflight failed: invalid config.toml payload: {exc}"
            ) from exc
        if not isinstance(config_data, dict):
            raise SystemExit("codex preflight failed: config.toml must decode to a table")

    helper_root = profile_root or codex_home
    agents = config_data.get("agents")
    if not isinstance(agents, dict):
        raise SystemExit(
            f"codex preflight failed: missing [agents] table in {config_path}"
        )

    errors: list[str] = []
    for agent_key in REQUIRED_HELPER_AGENT_IDS:
        entry = agents.get(agent_key)
        if not isinstance(entry, dict):
            errors.append(f"missing helper agent key: agents.{agent_key}")
            continue

        config_file = entry.get("config_file")
        if not isinstance(config_file, str) or not config_file.strip():
            errors.append(f"missing config_file for agents.{agent_key}")
            continue

        profile_path = helper_root / config_file
        if not profile_path.exists():
            errors.append(f"missing helper profile file: {profile_path}")
            continue

        try:
            tomllib.loads(profile_path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            errors.append(f"invalid helper profile TOML: {profile_path} ({exc})")

    if errors:
        lines = ["codex preflight failed:"]
        lines.extend(f"- {error}" for error in errors)
        raise SystemExit("\n".join(lines))


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _extract_existing_managed_body(config_text: str) -> str | None:
    match = MANAGED_BLOCK_PATTERN.search(config_text)
    if not match:
        return None
    return match.group(1)


def _parse_managed_agent_ids(managed_body: str) -> set[str]:
    try:
        parsed = tomllib.loads(managed_body)
    except tomllib.TOMLDecodeError:
        return set()

    agents = parsed.get("agents")
    if not isinstance(agents, dict):
        return set()
    return {agent_id for agent_id in agents if isinstance(agent_id, str) and agent_id}


def _is_managed_agent_section(section_name: str, managed_agent_ids: set[str]) -> bool:
    normalized = section_name.strip()
    for agent_id in managed_agent_ids:
        prefix = f"agents.{agent_id}"
        if normalized == prefix or normalized.startswith(f"{prefix}."):
            return True
    return False


def _remove_managed_agent_sections(
    config_text: str, managed_agent_ids: set[str]
) -> str:
    if not managed_agent_ids:
        return config_text

    managed_block = MANAGED_BLOCK_PATTERN.search(config_text)
    if managed_block:
        sanitized = (
            f"{config_text[:managed_block.start()]}"
            f"{MANAGED_BLOCK_PLACEHOLDER}\n"
            f"{config_text[managed_block.end():]}"
        )
    else:
        sanitized = config_text

    kept_lines: list[str] = []
    skip_section = False
    for line in sanitized.splitlines(keepends=True):
        header_match = SECTION_HEADER_PATTERN.match(line)
        if header_match:
            skip_section = _is_managed_agent_section(
                header_match.group(1), managed_agent_ids
            )
        if skip_section:
            continue
        kept_lines.append(line)

    updated = "".join(kept_lines)
    if managed_block:
        updated = updated.replace(
            f"{MANAGED_BLOCK_PLACEHOLDER}\n", managed_block.group(0), 1
        )
    return updated


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
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
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
) -> str:
    config_path = codex_home / "config.toml"
    managed = managed_config_path.read_text(encoding="utf-8").rstrip()
    managed_block = f"{BEGIN_MANAGED}\n{managed}\n{END_MANAGED}\n"
    managed_agent_ids = _parse_managed_agent_ids(managed)

    if config_path.exists():
        existing = config_path.read_text(encoding="utf-8")
    else:
        existing = ""
    current = _remove_managed_agent_sections(existing, managed_agent_ids)

    if MANAGED_BLOCK_PATTERN.search(current):
        updated = MANAGED_BLOCK_PATTERN.sub(lambda _: managed_block, current)
    else:
        separator = "" if current.endswith("\n") or not current else "\n"
        updated = f"{current}{separator}{managed_block}"

    try:
        tomllib.loads(updated)
    except tomllib.TOMLDecodeError as exc:
        raise SystemExit(
            f"codex preflight failed: updated config would be invalid TOML: {exc}"
        ) from exc

    if existing == updated:
        print(f"ok  {config_path} (managed block unchanged)")
        return updated

    if dry_run:
        print(f"[dry-run] update managed block in {config_path}")
        return updated

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(updated, encoding="utf-8")
    print(f"ok  {config_path} (managed block updated)")
    return updated


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    mode = "copy" if args.copy else "link"

    run_sync(repo_root, dry_run=args.dry_run)

    skills_src = repo_root / "skills"
    legacy_overlay_skills_src = repo_root / ".agents" / "skills"
    repo_agents_src = repo_root / "agents"
    codex_agents_src = repo_root / "dist" / "codex" / "agents"
    codex_managed_src = repo_root / "dist" / "codex" / "config.managed-agents.toml"
    expected_skill_names = expected_generated_skill_names(
        skills_src,
        legacy_overlay_skills_src,
    )
    expected_repo_agent_names = {path.name for path in repo_agents_src.glob("*.md")}
    expected_codex_agent_names = {path.name for path in codex_agents_src.glob("*.toml")}

    _print_skill_source_summary(
        canonical_skills_src=skills_src,
        legacy_overlay_src=legacy_overlay_skills_src,
        dry_run=args.dry_run,
    )

    if args.dest:
        destination = Path(args.dest)
        previous_skill_names = read_generated_skill_manifest(destination)
        _install_skill_sources(
            canonical_skills_src=skills_src,
            legacy_overlay_src=legacy_overlay_skills_src,
            destination=destination,
            mode=mode,
            dry_run=args.dry_run,
        )
        _install_internal_skill_assets(
            canonical_skills_src=skills_src,
            destination=destination,
            mode=mode,
            dry_run=args.dry_run,
        )
        prune_generated_skills(
            skills_dir=destination,
            expected_generated_names=expected_skill_names,
            previous_generated_names=previous_skill_names,
            dry_run=args.dry_run,
        )
        write_generated_skill_manifest(
            destination,
            expected_skill_names,
            dry_run=args.dry_run,
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
        previous_skill_names = read_generated_skill_manifest(skills_dest)
        _install_skill_sources(
            canonical_skills_src=skills_src,
            legacy_overlay_src=legacy_overlay_skills_src,
            destination=skills_dest,
            mode=mode,
            dry_run=args.dry_run,
        )
        _install_internal_skill_assets(
            canonical_skills_src=skills_src,
            destination=skills_dest,
            mode=mode,
            dry_run=args.dry_run,
        )
        prune_generated_skills(
            skills_dir=skills_dest,
            expected_generated_names=expected_skill_names,
            previous_generated_names=previous_skill_names,
            dry_run=args.dry_run,
        )
        write_generated_skill_manifest(
            skills_dest,
            expected_skill_names,
            dry_run=args.dry_run,
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
            updated_config = update_codex_config(
                home, codex_managed_src, dry_run=args.dry_run
            )
            validate_required_codex_helpers(
                home,
                config_text=updated_config,
                profile_root=(repo_root / "dist" / "codex") if args.dry_run else home,
            )

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
