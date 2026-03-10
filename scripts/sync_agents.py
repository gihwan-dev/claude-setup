#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from workflow_contract import INTERNAL_PLANNING_ROLE_IDS, REQUIRED_HELPER_AGENT_IDS

REPO_NOTICE = """<!-- AUTO-GENERATED from agent-registry. Do not edit directly. -->
<!-- Run: python3 scripts/sync_agents.py -->"""

CODEX_NOTICE = """# AUTO-GENERATED from agent-registry. Do not edit directly.
# Run: python3 scripts/sync_agents.py"""

MANAGED_CONFIG_NOTICE = """# AUTO-GENERATED from agent-registry. Do not edit directly.
# Run: python3 scripts/sync_agents.py"""

REPO_NOTICE_LINE_1 = "<!-- AUTO-GENERATED from agent-registry. Do not edit directly. -->"
REPO_NOTICE_LINE_2 = "<!-- Run: python3 scripts/sync_agents.py -->"

@dataclass
class AgentEntry:
    agent_id: str
    role: str
    description: str
    source: str
    repo_projection: bool
    codex_projection: bool
    repo_model: str | None
    repo_tools: list[str]
    codex_agent_key: str | None
    codex_config_file: str | None
    codex_model: str | None
    codex_reasoning_effort: str | None
    codex_sandbox_mode: str | None
    orchestration: dict[str, str] | None
    instructions: str


def _quote_toml(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _normalize_instructions(text: str) -> str:
    normalized = text.replace("\r\n", "\n").rstrip()
    return f"{normalized}\n"


def _yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


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
    while len(lines) >= 2 and lines[0].strip() == REPO_NOTICE_LINE_1 and lines[1].strip() == REPO_NOTICE_LINE_2:
        lines = lines[2:]
        while lines and not lines[0].strip():
            lines = lines[1:]
    return "\n".join(lines).strip("\n")


def _format_repo_markdown(entry: AgentEntry) -> str:
    if entry.repo_model is None:
        raise ValueError(f"repo model missing for {entry.agent_id}")

    frontmatter = [
        "---",
        f"name: {entry.agent_id}",
        f"role: {entry.role}",
        f"description: {_yaml_quote(entry.description)}",
    ]
    if entry.repo_tools:
        frontmatter.append(f"tools: {', '.join(entry.repo_tools)}")
    frontmatter.append(f"model: {entry.repo_model}")
    frontmatter.append("---")

    body = _normalize_instructions(entry.instructions).rstrip("\n")
    return "\n".join(frontmatter) + "\n\n" + REPO_NOTICE + "\n\n" + body + "\n"


def _format_codex_agent_toml(entry: AgentEntry) -> str:
    if (
        entry.codex_model is None
        or entry.codex_reasoning_effort is None
        or entry.codex_sandbox_mode is None
    ):
        raise ValueError(f"codex profile fields missing for {entry.agent_id}")

    instructions = _normalize_instructions(entry.instructions).replace('"""', '\\"""')
    lines = [
        CODEX_NOTICE,
        "",
        f"model = {_quote_toml(entry.codex_model)}",
        f"model_reasoning_effort = {_quote_toml(entry.codex_reasoning_effort)}",
        f"sandbox_mode = {_quote_toml(entry.codex_sandbox_mode)}",
        "",
        'developer_instructions = """',
        instructions.rstrip("\n"),
        '"""',
        "",
    ]
    return "\n".join(lines)


def _format_managed_config(entries: list[AgentEntry]) -> str:
    projected = [
        entry
        for entry in entries
        if entry.codex_projection
        and entry.codex_agent_key
        and entry.codex_config_file
    ]
    projected.sort(key=lambda entry: entry.codex_agent_key or "")

    chunks = [MANAGED_CONFIG_NOTICE, ""]
    for entry in projected:
        chunks.extend(
            [
                f"[agents.{entry.codex_agent_key}]",
                f"description = {_quote_toml(entry.description)}",
                f'config_file = {_quote_toml(f"agents/{entry.codex_config_file}")}',
                "",
            ]
        )
    return "\n".join(chunks)


def _read_agent_entries(registry_root: Path) -> list[AgentEntry]:
    entries: list[AgentEntry] = []
    if not registry_root.exists():
        return entries

    for agent_dir in sorted(p for p in registry_root.iterdir() if p.is_dir()):
        config_path = agent_dir / "agent.toml"
        instructions_path = agent_dir / "instructions.md"
        if not config_path.exists() or not instructions_path.exists():
            continue

        raw = tomllib.loads(config_path.read_text(encoding="utf-8"))
        projection = raw.get("projection", {})
        orchestration_raw = raw.get("orchestration")
        repo = raw.get("repo", {})
        codex = raw.get("codex", {})

        orchestration: dict[str, str] | None = None
        if isinstance(orchestration_raw, dict):
            parsed_orchestration: dict[str, str] = {}
            for key, value in orchestration_raw.items():
                if isinstance(key, str) and isinstance(value, str):
                    parsed_orchestration[key] = value
            if parsed_orchestration:
                orchestration = parsed_orchestration

        entry = AgentEntry(
            agent_id=str(raw["id"]),
            role=str(raw["role"]),
            description=str(raw["description"]),
            source=str(raw.get("source", "registry")),
            repo_projection=bool(projection.get("repo", False)),
            codex_projection=bool(projection.get("codex", False)),
            repo_model=repo.get("model"),
            repo_tools=list(repo.get("tools", [])),
            codex_agent_key=codex.get("agent_key"),
            codex_config_file=codex.get("config_file"),
            codex_model=codex.get("model"),
            codex_reasoning_effort=codex.get("reasoning_effort"),
            codex_sandbox_mode=codex.get("sandbox_mode"),
            orchestration=orchestration,
            instructions=_normalize_instructions(
                _strip_generated_notice(instructions_path.read_text(encoding="utf-8"))
            ),
        )
        if entry.agent_id != agent_dir.name:
            raise ValueError(
                f"registry id mismatch: {entry.agent_id} vs directory {agent_dir.name}"
            )
        entries.append(entry)
    return entries


def _find_duplicates(items: list[tuple[str, str]]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for key, agent_id in items:
        grouped.setdefault(key, []).append(agent_id)
    return {
        key: sorted(agent_ids)
        for key, agent_ids in grouped.items()
        if len(agent_ids) > 1
    }


def _validate_entries(entries: list[AgentEntry]) -> None:
    errors: list[str] = []

    duplicate_agent_ids = _find_duplicates(
        [(entry.agent_id, entry.agent_id) for entry in entries]
    )
    for agent_id, duplicates in duplicate_agent_ids.items():
        errors.append(
            f"duplicate agent id '{agent_id}': {', '.join(duplicates)}"
        )

    duplicate_repo_files = _find_duplicates(
        [
            (f"{entry.agent_id}.md", entry.agent_id)
            for entry in entries
            if entry.repo_projection
        ]
    )
    for file_name, agent_ids in duplicate_repo_files.items():
        errors.append(
            f"duplicate repo projection '{file_name}': {', '.join(agent_ids)}"
        )

    duplicate_codex_keys = _find_duplicates(
        [
            (str(entry.codex_agent_key), entry.agent_id)
            for entry in entries
            if entry.codex_projection and entry.codex_agent_key
        ]
    )
    for agent_key, agent_ids in duplicate_codex_keys.items():
        errors.append(
            f"duplicate codex.agent_key '{agent_key}': {', '.join(agent_ids)}"
        )

    duplicate_codex_files = _find_duplicates(
        [
            (str(entry.codex_config_file), entry.agent_id)
            for entry in entries
            if entry.codex_projection and entry.codex_config_file
        ]
    )
    for file_name, agent_ids in duplicate_codex_files.items():
        errors.append(
            f"duplicate codex.config_file '{file_name}': {', '.join(agent_ids)}"
        )

    if errors:
        lines = ["registry validation failed:"]
        lines.extend(f"- {error}" for error in errors)
        raise ValueError("\n".join(lines))


def _write_or_check_file(path: Path, content: str, check: bool, drift: list[str]) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else None
    if existing == content:
        return
    if check:
        drift.append(str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _cleanup_or_check_stale(
    directory: Path,
    expected_names: set[str],
    suffix: str,
    check: bool,
    drift: list[str],
) -> None:
    if not directory.exists():
        return
    for file_path in sorted(directory.glob(f"*{suffix}")):
        if file_path.name in expected_names:
            continue
        if check:
            drift.append(str(file_path))
            continue
        file_path.unlink()


def _sync_from_registry(repo_root: Path, entries: list[AgentEntry], check: bool) -> int:
    agents_dir = repo_root / "agents"
    codex_agents_dir = repo_root / "dist" / "codex" / "agents"
    codex_config_path = repo_root / "dist" / "codex" / "config.managed-agents.toml"

    drift: list[str] = []

    expected_repo_names: set[str] = set()
    expected_codex_names: set[str] = set()
    for entry in entries:
        if entry.repo_projection:
            file_name = f"{entry.agent_id}.md"
            expected_repo_names.add(file_name)
            content = _format_repo_markdown(entry)
            _write_or_check_file(agents_dir / file_name, content, check, drift)

        if entry.codex_projection:
            if not entry.codex_config_file:
                raise ValueError(f"codex config_file missing for {entry.agent_id}")
            file_name = entry.codex_config_file
            expected_codex_names.add(file_name)
            content = _format_codex_agent_toml(entry)
            _write_or_check_file(codex_agents_dir / file_name, content, check, drift)

    managed_content = _format_managed_config(entries)
    _write_or_check_file(codex_config_path, managed_content, check, drift)

    _cleanup_or_check_stale(agents_dir, expected_repo_names, ".md", check, drift)
    _cleanup_or_check_stale(codex_agents_dir, expected_codex_names, ".toml", check, drift)

    if check:
        if drift:
            print("sync-agents: drift detected")
            for item in drift:
                print(f"drift: {item}")
            return 1
        print("sync-agents: up to date")
        return 0

    print(f"ok  {agents_dir}")
    print(f"ok  {codex_agents_dir}")
    print(f"ok  {codex_config_path}")
    return 0


def _sandbox_for_role(role: str) -> str:
    return "workspace-write" if role in {"implementer", "orchestrator"} else "read-only"


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
    orchestration: dict[str, str] | None,
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
    if orchestration:
        lines.append("[orchestration]")
        for key, value in orchestration.items():
            lines.append(f"{key} = {_quote_toml(value)}")
        lines.append("")
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
    orchestration: dict[str, str] | None,
    instructions: str,
) -> None:
    entry_dir = registry_root / agent_id
    entry_dir.mkdir(parents=True, exist_ok=True)
    toml_content = _serialize_agent_toml(
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
        orchestration=orchestration,
    )
    (entry_dir / "agent.toml").write_text(toml_content, encoding="utf-8")
    (entry_dir / "instructions.md").write_text(
        _normalize_instructions(instructions), encoding="utf-8"
    )


def _bootstrap_repo_agents(repo_root: Path, registry_root: Path) -> None:
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
            codex_reasoning_effort="xhigh",
            codex_sandbox_mode=_sandbox_for_role(role),
            orchestration=None,
            instructions=_strip_generated_notice(body),
        )


def _role_for_codex_builtin(agent_key: str) -> str:
    if agent_key == "explorer":
        return "explorer"
    if agent_key == "verification-worker":
        return "reviewer"
    return "reviewer"


def _repo_tools_for_helper(agent_key: str) -> list[str]:
    return ["Read", "Grep", "Glob"]


def _bootstrap_codex_builtins(registry_root: Path) -> None:
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    config_path = codex_home / "config.toml"
    if not config_path.exists():
        print(f"bootstrap skipped: config not found: {config_path}", file=sys.stderr)
        return

    config_data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    agents = config_data.get("agents", {})
    if not isinstance(agents, dict):
        return

    for agent_key, info in agents.items():
        if not isinstance(info, dict):
            continue
        config_file = str(info.get("config_file", ""))
        if not config_file:
            continue
        profile_path = codex_home / config_file
        if not profile_path.exists():
            continue

        profile = tomllib.loads(profile_path.read_text(encoding="utf-8"))
        description = str(info.get("description", agent_key))
        role = _role_for_codex_builtin(agent_key)
        instructions = str(profile.get("developer_instructions", "")).strip()
        filename = Path(config_file).name

        _write_registry_entry(
            registry_root,
            agent_id=agent_key,
            role=role,
            description=description,
            source="codex-builtin",
            repo_projection=agent_key in REQUIRED_HELPER_AGENT_IDS,
            codex_projection=True,
            repo_model="sonnet" if agent_key in REQUIRED_HELPER_AGENT_IDS else None,
            repo_tools=_repo_tools_for_helper(agent_key)
            if agent_key in REQUIRED_HELPER_AGENT_IDS
            else [],
            codex_agent_key=agent_key,
            codex_config_file=filename,
            codex_model=str(profile.get("model", "gpt-5.4")),
            codex_reasoning_effort=str(profile.get("model_reasoning_effort", "xhigh")),
            codex_sandbox_mode=str(profile.get("sandbox_mode", "read-only")),
            orchestration=None,
            instructions=instructions,
        )


def _planning_role_templates() -> dict[str, dict[str, str]]:
    return {
        "web-researcher": {
            "role": "explorer",
            "description": "Web research specialist for competitor scans and external solution benchmarking.",
            "instructions": """너는 web-researcher다.

핵심 임무
- 경쟁사/대안/최신 사례를 신뢰 가능한 출처로 조사한다.
- 사실과 해석을 분리해 보고한다.

규칙
- 출처 링크와 날짜를 반드시 남긴다.
- 확인된 사실과 추정을 분리한다.
- 과장된 결론을 피하고 의사결정에 필요한 비교 축을 제시한다.

출력 포맷
1. 핵심결론
2. 근거 (source 링크 + 날짜)
3. 리스크/불확실성
4. 권장 다음 행동""",
        },
        "solution-analyst": {
            "role": "reviewer",
            "description": "Compare implementation options and tradeoffs with clear decision criteria.",
            "instructions": """너는 solution-analyst다.

핵심 임무
- 최소 2개 이상의 현실적 옵션을 비교한다.
- 비용/복잡도/리스크/확장성 기준으로 트레이드오프를 정리한다.

규칙
- 결론보다 비교 근거를 우선 제시한다.
- 선택/비선택 사유를 분리한다.

출력 포맷
1. 핵심결론
2. 근거 (옵션별 비교 근거)
3. 리스크
4. 권장 다음 행동""",
        },
        "product-planner": {
            "role": "orchestrator",
            "description": "Structure ambiguous requests into goal, scope, and acceptance criteria.",
            "instructions": """너는 product-planner다.

핵심 임무
- 모호한 요청을 실행 가능한 요구사항으로 구조화한다.
- goal/scope/acceptance/open questions를 명확히 만든다.

규칙
- 사용자 가치와 성공 기준을 먼저 고정한다.
- 구현 디테일보다 제품 동작/경계 정의를 우선한다.

출력 포맷
1. 핵심결론
2. 근거 (요구사항/컨텍스트 근거)
3. 리스크
4. 권장 다음 행동""",
        },
        "ux-journey-critic": {
            "role": "reviewer",
            "description": "Evaluate user journey friction, edge states, and accessibility risks.",
            "instructions": """너는 ux-journey-critic이다.

핵심 임무
- 사용자 여정의 마찰 지점을 찾고 개선 우선순위를 제시한다.
- empty/error/loading/permission edge case를 점검한다.

규칙
- 주관적 미감보다 사용성 리스크를 우선한다.
- 접근성 영향(키보드/스크린리더)을 최소한으로라도 점검한다.

출력 포맷
1. 핵심결론
2. 근거 (journey 단계별 근거)
3. 리스크
4. 권장 다음 행동""",
        },
        "delivery-risk-planner": {
            "role": "reviewer",
            "description": "Plan rollout, migration, and operational guardrails before implementation.",
            "instructions": """너는 delivery-risk-planner다.

핵심 임무
- 배포/마이그레이션/운영 리스크를 사전에 식별한다.
- stop/replan 조건과 완화 전략을 정의한다.

규칙
- 영향 범위와 rollback 가능성을 명확히 적는다.
- 관측 가능성(로그/모니터링) 요구를 포함한다.

출력 포맷
1. 핵심결론
2. 근거 (리스크 근거)
3. 리스크
4. 권장 다음 행동""",
        },
        "prompt-systems-designer": {
            "role": "reviewer",
            "description": "Design prompt system contracts, evaluation rules, and fallback strategy.",
            "instructions": """너는 prompt-systems-designer다.

핵심 임무
- 프롬프트 시스템의 입력/출력 계약과 실패 복구 정책을 설계한다.
- 평가 기준과 fallback 체계를 제시한다.

규칙
- 모델/툴 경계를 명확히 분리한다.
- 재현 가능한 평가 기준을 포함한다.

출력 포맷
1. 핵심결론
2. 근거 (계약/평가 근거)
3. 리스크
4. 권장 다음 행동""",
        },
    }


def _bootstrap_planning_roles(registry_root: Path) -> None:
    templates = _planning_role_templates()
    for agent_id in INTERNAL_PLANNING_ROLE_IDS:
        template = templates[agent_id]
        role = template["role"]
        _write_registry_entry(
            registry_root,
            agent_id=agent_id,
            role=role,
            description=template["description"],
            source="planning-role",
            repo_projection=False,
            codex_projection=False,
            repo_model=None,
            repo_tools=[],
            codex_agent_key=None,
            codex_config_file=None,
            codex_model=None,
            codex_reasoning_effort=None,
            codex_sandbox_mode=None,
            orchestration=None,
            instructions=template["instructions"],
        )


def _bootstrap_from_current(repo_root: Path, registry_root: Path) -> None:
    _bootstrap_repo_agents(repo_root, registry_root)
    _bootstrap_codex_builtins(registry_root)
    _bootstrap_planning_roles(registry_root)
    print(f"ok  {registry_root}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync agent projections from registry")
    parser.add_argument("--check", action="store_true", help="Check drift only")
    parser.add_argument(
        "--bootstrap-from-current",
        action="store_true",
        help="One-shot import from current repo agents and CODEX_HOME profiles",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    registry_root = repo_root / "agent-registry"

    if args.bootstrap_from_current:
        _bootstrap_from_current(repo_root, registry_root)

    entries = _read_agent_entries(registry_root)
    if not entries:
        print(f"no registry entries found in {registry_root}", file=sys.stderr)
        return 1
    _validate_entries(entries)

    return _sync_from_registry(repo_root, entries, check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
