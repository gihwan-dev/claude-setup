#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
import sys
import tomllib
from pathlib import Path

@dataclass(frozen=True)
class CodexBuiltinProfile:
    agent_key: str
    description: str
    config_file: str
    model: str
    reasoning_effort: str
    sandbox_mode: str
    developer_instructions: str


def _quote_toml(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _normalize_instructions(text: str) -> str:
    normalized = text.replace("\r\n", "\n").rstrip()
    return f"{normalized}\n"


def _parse_frontmatter(markdown: str) -> tuple[dict[str, str], str]:
    lines = markdown.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        raise ValueError("frontmatter not found")

    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break
    if end_index is None:
        raise ValueError("frontmatter closing marker not found")

    meta: dict[str, str] = {}
    for line in lines[1:end_index]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"')

    body = "\n".join(lines[end_index + 1 :]).lstrip("\n")
    return meta, body


def _strip_generated_notice(body: str) -> str:
    lines = body.splitlines()
    notice_1 = "<!-- AUTO-GENERATED from agent-registry. Do not edit directly. -->"
    notice_2 = "<!-- Run: python3 scripts/sync_agents.py -->"
    while len(lines) >= 2 and lines[0].strip() == notice_1 and lines[1].strip() == notice_2:
        lines = lines[2:]
        while lines and not lines[0].strip():
            lines = lines[1:]
    return "\n".join(lines).strip("\n")


def _serialize_agent_toml(
    *,
    agent_id: str,
    role: str,
    description: str,
    source: str,
    repo_projection: bool,
    codex_projection: bool,
    repo_model: str | None,
    repo_tools: list[str],
    codex_agent_key: str | None,
    codex_config_file: str | None,
    codex_model: str | None,
    codex_reasoning_effort: str | None,
    codex_sandbox_mode: str | None,
) -> str:
    lines = [
        f'id = {_quote_toml(agent_id)}',
        f'role = {_quote_toml(role)}',
        f'description = {_quote_toml(description)}',
        f'source = {_quote_toml(source)}',
        "",
        "[projection]",
        f"repo = {str(repo_projection).lower()}",
        f"codex = {str(codex_projection).lower()}",
        "",
    ]
    if repo_projection:
        if repo_model is None:
            raise ValueError(f"repo model missing for {agent_id}")
        lines.extend(
            [
                "[repo]",
                f'model = {_quote_toml(repo_model)}',
                f"tools = [{', '.join(_quote_toml(tool) for tool in repo_tools)}]",
                "",
            ]
        )
    if codex_projection:
        if (
            codex_agent_key is None
            or codex_config_file is None
            or codex_model is None
            or codex_reasoning_effort is None
            or codex_sandbox_mode is None
        ):
            raise ValueError(f"codex settings missing for {agent_id}")
        lines.extend(
            [
                "[codex]",
                f'agent_key = {_quote_toml(codex_agent_key)}',
                f'config_file = {_quote_toml(codex_config_file)}',
                f'model = {_quote_toml(codex_model)}',
                f'reasoning_effort = {_quote_toml(codex_reasoning_effort)}',
                f'sandbox_mode = {_quote_toml(codex_sandbox_mode)}',
                "",
            ]
        )
    return "\n".join(lines)


def _write_registry_entry(
    registry_root: Path,
    *,
    agent_id: str,
    role: str,
    description: str,
    source: str,
    repo_projection: bool,
    codex_projection: bool,
    repo_model: str | None,
    repo_tools: list[str],
    codex_agent_key: str | None,
    codex_config_file: str | None,
    codex_model: str | None,
    codex_reasoning_effort: str | None,
    codex_sandbox_mode: str | None,
    instructions: str,
) -> None:
    entry_dir = registry_root / agent_id
    entry_dir.mkdir(parents=True, exist_ok=True)
    (entry_dir / "agent.toml").write_text(
        _serialize_agent_toml(
            agent_id=agent_id,
            role=role,
            description=description,
            source=source,
            repo_projection=repo_projection,
            codex_projection=codex_projection,
            repo_model=repo_model,
            repo_tools=repo_tools,
            codex_agent_key=codex_agent_key,
            codex_config_file=codex_config_file,
            codex_model=codex_model,
            codex_reasoning_effort=codex_reasoning_effort,
            codex_sandbox_mode=codex_sandbox_mode,
        ),
        encoding="utf-8",
    )
    (entry_dir / "instructions.md").write_text(
        _normalize_instructions(instructions),
        encoding="utf-8",
    )


def _load_toml(path: Path) -> dict[str, object]:
    try:
        loaded = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"invalid TOML: {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ValueError(f"TOML must decode to a table: {path}")
    return loaded


def _load_policy(repo_root: Path) -> dict[str, object]:
    return _load_toml(repo_root / "policy" / "workflow.toml")


def _string_list(value: object, *, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"invalid workflow policy string list: {label}")
    return tuple(value)


def _string_map(value: object, *, label: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError(f"invalid workflow policy string map: {label}")
    parsed: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str) or not item.strip():
            raise ValueError(f"invalid workflow policy string map entry: {label}")
        parsed[key] = item
    return parsed


def _optional_string_map(value: object, *, label: str) -> dict[str, str]:
    if value is None:
        return {}
    return _string_map(value, label=label)


def _policy_lists(
    repo_root: Path,
) -> tuple[tuple[str, ...], tuple[str, ...], dict[str, str], str, dict[str, str]]:
    policy = _load_policy(repo_root)
    projection = policy.get("projection", {})
    codex = policy.get("codex", {})
    if not isinstance(projection, dict) or not isinstance(codex, dict):
        raise ValueError("missing [projection] or [codex] in policy/workflow.toml")
    required_helpers = _string_list(
        projection.get("required_helper_agent_ids"),
        label="projection.required_helper_agent_ids",
    )
    documentation_only = _string_list(
        projection.get("documentation_only_builtins"),
        label="projection.documentation_only_builtins",
    )
    sandbox_overrides = _optional_string_map(
        codex.get("sandbox_overrides"),
        label="codex.sandbox_overrides",
    )
    default_reasoning_effort = codex.get("default_reasoning_effort")
    if not isinstance(default_reasoning_effort, str) or not default_reasoning_effort.strip():
        raise ValueError("missing codex.default_reasoning_effort in policy/workflow.toml")
    reasoning_effort_overrides = _optional_string_map(
        codex.get("reasoning_effort_overrides"),
        label="codex.reasoning_effort_overrides",
    )
    return (
        required_helpers,
        documentation_only,
        sandbox_overrides,
        default_reasoning_effort,
        reasoning_effort_overrides,
    )


def _load_codex_builtin_profiles(repo_root: Path) -> list[CodexBuiltinProfile]:
    (
        _required_helper_agent_ids,
        documentation_only_builtins,
        sandbox_overrides,
        default_reasoning_effort,
        reasoning_effort_overrides,
    ) = _policy_lists(repo_root)

    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    config_path = codex_home / "config.toml"
    if not config_path.exists():
        raise ValueError(f"bootstrap preflight failed: config not found: {config_path}")

    config_data = _load_toml(config_path)
    agents = config_data.get("agents")
    if not isinstance(agents, dict):
        raise ValueError(f"bootstrap preflight failed: missing [agents] table in {config_path}")

    profiles: list[CodexBuiltinProfile] = []
    for agent_key, info in sorted(agents.items()):
        if not isinstance(agent_key, str):
            raise ValueError("bootstrap preflight failed: [agents] keys must be strings")
        if agent_key in documentation_only_builtins:
            continue
        if agent_key not in _required_helper_agent_ids:
            continue
        if not isinstance(info, dict):
            raise ValueError(f"bootstrap preflight failed: agents.{agent_key} must be a table")

        config_file = str(info.get("config_file", "")).strip()
        if not config_file:
            raise ValueError(
                f"bootstrap preflight failed: missing agents.{agent_key}.config_file"
            )

        profile_path = codex_home / config_file
        if not profile_path.exists():
            raise ValueError(
                f"bootstrap preflight failed: profile not found for {agent_key}: {profile_path}"
            )

        profile = _load_toml(profile_path)
        profiles.append(
            CodexBuiltinProfile(
                agent_key=agent_key,
                description=str(info.get("description", agent_key)).strip() or agent_key,
                config_file=Path(config_file).name,
                model=str(profile.get("model", "gpt-5.4")),
                reasoning_effort=str(
                    profile.get(
                        "model_reasoning_effort",
                        reasoning_effort_overrides.get(agent_key, default_reasoning_effort),
                    )
                ),
                sandbox_mode=str(
                    profile.get(
                        "sandbox_mode",
                        _sandbox_for_agent(agent_key, sandbox_overrides),
                    )
                ),
                developer_instructions=str(profile.get("developer_instructions", "")).strip(),
            )
        )
    return profiles


def _sandbox_for_agent(agent_id: str, sandbox_overrides: dict[str, str]) -> str:
    return sandbox_overrides.get(agent_id, "read-only")


def _role_for_codex_builtin(agent_key: str) -> str:
    if agent_key == "explorer":
        return "explorer"
    return "reviewer"


def _repo_tools_for_helper(agent_key: str) -> list[str]:
    return ["Read", "Grep", "Glob"]


def _bootstrap_repo_agents(repo_root: Path, registry_root: Path) -> None:
    (
        _required_helper_agent_ids,
        _documentation_only_builtins,
        sandbox_overrides,
        default_reasoning_effort,
        reasoning_effort_overrides,
    ) = _policy_lists(repo_root)
    for path in sorted((repo_root / "agents").glob("*.md")):
        markdown = path.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(markdown)

        agent_id = meta.get("name", path.stem).strip()
        role = meta.get("role", "reviewer").strip()
        description = meta.get("description", "").strip() or f"{agent_id} agent"
        tools = [item.strip() for item in meta.get("tools", "").split(",") if item.strip()]
        repo_model = meta.get("model", "sonnet").strip() or "sonnet"

        _write_registry_entry(
            registry_root,
            agent_id=agent_id,
            role=role,
            description=description,
            source="repo-agent",
            repo_projection=True,
            codex_projection=True,
            repo_model=repo_model,
            repo_tools=tools,
            codex_agent_key=agent_id,
            codex_config_file=f"{agent_id}.toml",
            codex_model="gpt-5.4",
            codex_reasoning_effort=reasoning_effort_overrides.get(agent_id, default_reasoning_effort),
            codex_sandbox_mode=_sandbox_for_agent(agent_id, sandbox_overrides),
            instructions=_strip_generated_notice(body),
        )


def _bootstrap_codex_builtins(
    repo_root: Path,
    registry_root: Path,
    builtin_profiles: list[CodexBuiltinProfile] | None = None,
) -> None:
    (
        required_helper_agent_ids,
        _documentation_only_builtins,
        _sandbox_overrides,
        _default_reasoning_effort,
        _reasoning_effort_overrides,
    ) = _policy_lists(repo_root)
    profiles = (
        builtin_profiles
        if builtin_profiles is not None
        else _load_codex_builtin_profiles(repo_root)
    )

    for profile in profiles:
        agent_key = profile.agent_key
        is_required_helper = agent_key in required_helper_agent_ids

        _write_registry_entry(
            registry_root,
            agent_id=agent_key,
            role=_role_for_codex_builtin(agent_key),
            description=profile.description,
            source="codex-builtin",
            repo_projection=is_required_helper,
            codex_projection=True,
            repo_model="sonnet" if is_required_helper else None,
            repo_tools=_repo_tools_for_helper(agent_key) if is_required_helper else [],
            codex_agent_key=agent_key,
            codex_config_file=profile.config_file,
            codex_model=profile.model,
            codex_reasoning_effort=profile.reasoning_effort,
            codex_sandbox_mode=profile.sandbox_mode,
            instructions=profile.developer_instructions,
        )


def bootstrap_from_current(repo_root: Path, registry_root: Path) -> None:
    builtin_profiles = _load_codex_builtin_profiles(repo_root)
    _bootstrap_repo_agents(repo_root, registry_root)
    _bootstrap_codex_builtins(repo_root, registry_root, builtin_profiles)
    print(f"ok  {registry_root}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bootstrap agent-registry from current repo agents and CODEX_HOME profiles"
    )
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root path",
    )
    parser.add_argument(
        "--registry-root",
        help="Optional registry root override",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    registry_root = (
        Path(args.registry_root).resolve()
        if args.registry_root
        else repo_root / "agent-registry"
    )
    try:
        bootstrap_from_current(repo_root, registry_root)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
