#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
import sys
import tomllib
from pathlib import Path
from typing import TypeAlias

OrchestrationValue: TypeAlias = str | list[str]


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


def _serialize_toml_value(value: OrchestrationValue) -> str:
    if isinstance(value, list):
        return f"[{', '.join(_quote_toml(item) for item in value)}]"
    return _quote_toml(value)


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
    orchestration: dict[str, OrchestrationValue] | None,
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
            lines.append(f"{key} = {_serialize_toml_value(value)}")
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
    orchestration: dict[str, OrchestrationValue] | None,
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
            orchestration=orchestration,
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


def _policy_lists(
    repo_root: Path,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], dict[str, str], str, dict[str, object]]:
    policy = _load_policy(repo_root)
    projection = policy.get("projection", {})
    codex = policy.get("codex", {})
    helper_close = policy.get("helper_close", {})
    if not isinstance(projection, dict) or not isinstance(codex, dict) or not isinstance(helper_close, dict):
        raise ValueError("missing [projection], [codex], or [helper_close] in policy/workflow.toml")
    required_helpers = _string_list(
        projection.get("required_helper_agent_ids"),
        label="projection.required_helper_agent_ids",
    )
    planning_roles = _string_list(
        projection.get("internal_planning_role_ids"),
        label="projection.internal_planning_role_ids",
    )
    documentation_only = _string_list(
        projection.get("documentation_only_builtins"),
        label="projection.documentation_only_builtins",
    )
    sandbox_overrides = _string_map(
        codex.get("sandbox_overrides"),
        label="codex.sandbox_overrides",
    )
    expected_reasoning_effort = codex.get("expected_reasoning_effort")
    if not isinstance(expected_reasoning_effort, str) or not expected_reasoning_effort.strip():
        raise ValueError("missing codex.expected_reasoning_effort in policy/workflow.toml")
    return (
        required_helpers,
        planning_roles,
        documentation_only,
        sandbox_overrides,
        expected_reasoning_effort,
        helper_close,
    )


def _validate_planning_role_templates(repo_root: Path) -> None:
    (
        _required_helpers,
        planning_role_ids,
        _documentation_only,
        _sandbox_overrides,
        _effort,
        _helper_close,
    ) = _policy_lists(repo_root)
    templates = _planning_role_templates()
    missing_templates = sorted(
        agent_id for agent_id in planning_role_ids if agent_id not in templates
    )
    if missing_templates:
        joined = ", ".join(missing_templates)
        raise ValueError(f"missing planning role template(s): {joined}")


def _load_codex_builtin_profiles(repo_root: Path) -> list[CodexBuiltinProfile]:
    (
        _required_helper_agent_ids,
        _planning_role_ids,
        documentation_only_builtins,
        sandbox_overrides,
        expected_reasoning_effort,
        _helper_close,
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
                    profile.get("model_reasoning_effort", expected_reasoning_effort)
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


def _existing_orchestration(
    registry_root: Path,
    agent_id: str,
) -> dict[str, OrchestrationValue] | None:
    path = registry_root / agent_id / "agent.toml"
    if not path.exists():
        return None
    data = _load_toml(path)
    raw = data.get("orchestration")
    if not isinstance(raw, dict):
        return None

    parsed: dict[str, OrchestrationValue] = {}
    for key, value in raw.items():
        if isinstance(key, str) and isinstance(value, str):
            parsed[key] = value
        elif isinstance(key, str) and isinstance(value, list) and all(
            isinstance(item, str) for item in value
        ):
            parsed[key] = list(value)
    return parsed or None


def _default_helper_orchestration(
    agent_id: str,
    helper_close: dict[str, object],
) -> dict[str, OrchestrationValue]:
    strong_close_reasons = _string_list(
        helper_close.get("strong_close_reasons"),
        label="helper_close.strong_close_reasons",
    )
    advisory_timeout_policy = helper_close.get("advisory_timeout_policy")
    non_advisory_timeout_policy = helper_close.get("non_advisory_timeout_policy")
    if not isinstance(advisory_timeout_policy, str) or not isinstance(
        non_advisory_timeout_policy, str
    ):
        raise ValueError("missing helper close timeout policies in policy/workflow.toml")

    if agent_id == "worker":
        return {
            "blocking_class": "blocking",
            "result_contract": "final-or-checkpoint",
            "close_protocol": "explicit-cancel-or-terminal-close",
            "late_result_policy": "not-applicable",
            "timeout_policy": non_advisory_timeout_policy,
            "allowed_close_reasons": list(strong_close_reasons),
        }
    if agent_id == "verification-worker":
        return {
            "blocking_class": "semi-blocking",
            "result_contract": "final-or-checkpoint",
            "close_protocol": "explicit-cancel-or-terminal-close",
            "late_result_policy": "merge-if-relevant",
            "timeout_policy": non_advisory_timeout_policy,
            "allowed_close_reasons": list(strong_close_reasons),
        }
    return {
        "blocking_class": "advisory",
        "result_contract": "preliminary-or-final",
        "close_protocol": "explicit-cancel-or-terminal-close",
        "late_result_policy": "merge-if-relevant",
        "timeout_policy": advisory_timeout_policy,
        "allowed_close_reasons": list(strong_close_reasons),
    }


def _sandbox_for_agent(agent_id: str, sandbox_overrides: dict[str, str]) -> str:
    return sandbox_overrides.get(agent_id, "read-only")


def _role_for_codex_builtin(agent_key: str) -> str:
    if agent_key == "worker":
        return "implementer"
    if agent_key == "explorer":
        return "explorer"
    return "reviewer"


def _repo_tools_for_helper(agent_key: str) -> list[str]:
    if agent_key == "worker":
        return ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
    return ["Read", "Grep", "Glob"]


def _bootstrap_repo_agents(repo_root: Path, registry_root: Path) -> None:
    (
        _required_helper_agent_ids,
        _planning_role_ids,
        _documentation_only_builtins,
        sandbox_overrides,
        expected_reasoning_effort,
        _helper_close,
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
            codex_reasoning_effort=expected_reasoning_effort,
            codex_sandbox_mode=_sandbox_for_agent(agent_id, sandbox_overrides),
            orchestration=_existing_orchestration(registry_root, agent_id),
            instructions=_strip_generated_notice(body),
        )


def _bootstrap_codex_builtins(
    repo_root: Path,
    registry_root: Path,
    builtin_profiles: list[CodexBuiltinProfile] | None = None,
) -> None:
    (
        required_helper_agent_ids,
        _planning_role_ids,
        _documentation_only_builtins,
        _sandbox_overrides,
        _expected_reasoning_effort,
        helper_close,
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
            orchestration=_existing_orchestration(registry_root, agent_key)
            or (
                _default_helper_orchestration(agent_key, helper_close)
                if is_required_helper
                else None
            ),
            instructions=profile.developer_instructions,
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
        "structure-planner": {
            "role": "reviewer",
            "description": "Plan cohesive file/module splits before large refactors or boundary changes.",
            "instructions": """너는 structure-planner다.

핵심 임무
- 큰 변경을 안전한 slice와 모듈 경계로 분해한다.
- 무엇을 유지하고 어디를 나눌지 구조 기준으로 제안한다.

규칙
- diff budget, 파일 책임, 경계 안정성을 기준으로 판단한다.
- 구현 세부보다 분해 순서와 검증 포인트를 우선한다.

출력 포맷
1. 핵심결론
2. 근거 (구조 분해 근거)
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


def _bootstrap_planning_roles(repo_root: Path, registry_root: Path) -> None:
    (
        _required_helpers,
        planning_role_ids,
        _documentation_only,
        _sandbox_overrides,
        _effort,
        _helper_close,
    ) = (
        _policy_lists(repo_root)
    )
    templates = _planning_role_templates()
    for agent_id in planning_role_ids:
        template = templates[agent_id]
        _write_registry_entry(
            registry_root,
            agent_id=agent_id,
            role=template["role"],
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


def bootstrap_from_current(repo_root: Path, registry_root: Path) -> None:
    _validate_planning_role_templates(repo_root)
    builtin_profiles = _load_codex_builtin_profiles(repo_root)
    _bootstrap_repo_agents(repo_root, registry_root)
    _bootstrap_codex_builtins(repo_root, registry_root, builtin_profiles)
    _bootstrap_planning_roles(repo_root, registry_root)
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
