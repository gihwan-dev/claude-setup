#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1"
DEFAULT_MIN_TURNS = 3
REPO_ROOT = Path(__file__).resolve().parents[2]

KNOWN_AGENTS = {
    "architecture-reviewer",
    "browser-explorer",
    "code-quality-reviewer",
    "design-evaluator",
    "design-skeptic",
    "docs-researcher",
    "react-state-reviewer",
    "socratic-partner",
    "structure-reviewer",
    "test-engineer",
    "type-specialist",
    "verification-worker",
    "web-researcher",
}

CORRECTION_PATTERNS = [
    r"아니[요]?\s",
    r"아닌데",
    r"그게\s*아니[라고]",
    r"아니야",
    r"틀렸[어는]",
    r"다시\s*(해|하|만들|작성|생성|수정)",
    r"다시\s*해\s*봐",
    r"그거\s*말고",
    r"[이그]렇게\s*말고",
    r"왜\s*(이렇게|그렇게|자꾸|계속|또)",
    r"제대로\s*(해|안|좀)",
    r"똑바로",
    r"잘못\s*(했|된|되)",
    r"빠[졌뜨트]",
    r"빠져\s*있",
    r"안\s*(했|됐|빠)",
    r"누락",
    r"빠[뜨트]렸",
    r"(?i)\b(no|not what i|wrong|incorrect|try again|i already said|again)\b",
]

REJECTION_PATTERNS = [
    r"다시\s*해\s*줘",
    r"처음부터\s*다시",
    r"리셋",
    r"취소",
    r"됐[어고].*말[어고]",
    r"하지\s*마",
    r"그만",
    r"필요\s*없",
    r"(?i)\b(cancel|stop|never mind|nevermind|do not|don't|reset)\b",
]

PRAISE_PATTERNS = [
    r"좋[아았]",
    r"완벽",
    r"잘\s*(했|됐|만들|나왔)",
    r"맞[아았]",
    r"그래\s*그거",
    r"오[케게]이",
    r"[ㅋk]{2,}",
    r"고마[워웠]",
    r"감사",
    r"딱\s*(이거|좋|맞)",
    r"훌륭",
    r"대박",
    r"ㅇㅇ",
    r"(?i)\b(good|great|perfect|thanks|thank you|exactly|nice|works)\b",
]

TOOL_ERROR_PATTERNS = [
    r"(?i)error",
    r"(?i)failed",
    r"(?i)exception",
    r"(?i)timeout",
    r"REDIRECT DETECTED",
    r"(?i)permission denied",
    r"(?i)not found",
    r"InputValidationError",
]

ROLLBACK_PATTERNS = [
    r"git\s+(revert|reset|checkout\s+--)",
    r"되돌[려리]",
    r"원래대로",
    r"롤백",
    r"복원",
    r"이전\s*버전",
]

FILE_PATH_PATTERNS = [
    re.compile(r"\b(?:[\w.-]+/)+[\w.-]+\.[A-Za-z0-9]+\b"),
    re.compile(r"\b/[^\s:'\"`]+/[^\s:'\"`]+\b"),
]

TOOL_NAME_ALIASES = {
    "Bash": "Bash",
    "Edit": "Edit",
    "MultiEdit": "MultiEdit",
    "Write": "Write",
    "Read": "Read",
    "Grep": "Grep",
    "Glob": "Glob",
    "Agent": "Agent",
    "Task": "Agent",
    "Skill": "Skill",
}


def load_known_skills() -> set[str]:
    skills_dir = REPO_ROOT / "skills"
    if not skills_dir.exists():
        return set()
    return {
        skill_dir.name
        for skill_dir in skills_dir.iterdir()
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists()
    }


KNOWN_SKILLS = load_known_skills()


@dataclass
class ToolCall:
    tool_id: str
    tool_name: str
    input_data: dict[str, Any] = field(default_factory=dict)
    caller_type: str = "direct"


@dataclass
class ToolResult:
    tool_use_id: str
    content: str
    is_error: bool


@dataclass
class StructuredMessage:
    uuid: str
    parent_uuid: str | None
    timestamp: datetime | None
    session_id: str
    msg_type: str
    content_text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)
    is_meta: bool = False
    cwd: str | None = None
    git_branch: str | None = None


@dataclass
class SessionAnalysis:
    session_id: str
    project: str
    timestamp: datetime | None
    turn_count: int
    session_duration_seconds: int
    user_corrections: int
    repeated_instructions: int
    tool_failures: Counter[str]
    tool_failure_patterns: Counter[tuple[str, str]]
    positive_feedback: int
    skill_invocations: Counter[str]
    agent_dispatches: Counter[str]
    tool_count: int
    unique_tools: set[str]
    files_touched: set[str]
    branch_switches: int
    complexity: dict[str, Any]


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        return datetime.fromisoformat(candidate)
    except ValueError:
        return None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def display_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.isoformat()
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def claude_home() -> Path:
    configured = os.environ.get("CLAUDE_HOME")
    if configured:
        return Path(configured).expanduser()
    return Path("~/.claude").expanduser()


def expand_input_path(raw_path: str) -> Path:
    if raw_path.startswith("~/.claude"):
        suffix = raw_path.removeprefix("~/.claude").lstrip("/")
        return claude_home() / suffix
    return Path(raw_path).expanduser()


def project_to_slug(project: str) -> str:
    expanded = expand_input_path(project)
    if expanded.exists() or project.startswith(("~", "/")):
        text = str(expanded.resolve())
    else:
        text = project
    if "/" not in text and "\\" not in text:
        return text
    return re.sub(r"[^A-Za-z0-9_-]", "-", text)


def extract_text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, str):
                chunks.append(item)
            elif isinstance(item, dict):
                item_type = item.get("type")
                if item_type in {"text", "tool_result"}:
                    chunks.append(extract_text_from_content(item.get("text") or item.get("content")))
        return "\n".join(chunk for chunk in chunks if chunk)
    if isinstance(content, dict):
        if content.get("type") == "text":
            return str(content.get("text", ""))
        return json.dumps(content, ensure_ascii=False, sort_keys=True)
    if content is None:
        return ""
    return str(content)


def parse_tool_calls(content: Any) -> list[ToolCall]:
    if not isinstance(content, list):
        return []
    calls: list[ToolCall] = []
    for item in content:
        if not isinstance(item, dict) or item.get("type") != "tool_use":
            continue
        caller = item.get("caller")
        caller_type = caller.get("type", "direct") if isinstance(caller, dict) else "direct"
        input_data = item.get("input")
        calls.append(
            ToolCall(
                tool_id=str(item.get("id") or ""),
                tool_name=str(item.get("name") or "unknown"),
                input_data=input_data if isinstance(input_data, dict) else {},
                caller_type=str(caller_type),
            )
        )
    return calls


def parse_tool_results(content: Any) -> list[ToolResult]:
    items: list[Any]
    if isinstance(content, list):
        items = content
    elif isinstance(content, dict):
        items = [content]
    else:
        return []

    results: list[ToolResult] = []
    for item in items:
        if not isinstance(item, dict) or item.get("type") != "tool_result":
            continue
        text = extract_text_from_content(item.get("content"))
        is_error = bool(item.get("is_error")) or matches_any(TOOL_ERROR_PATTERNS, text)
        results.append(
            ToolResult(
                tool_use_id=str(item.get("tool_use_id") or ""),
                content=text,
                is_error=is_error,
            )
        )
    return results


def normalize_message(raw: dict[str, Any]) -> StructuredMessage:
    message = raw.get("message")
    content: Any = raw.get("content")
    if isinstance(message, dict):
        content = message.get("content", content)
    msg_type = str(raw.get("type") or "")
    content_text = extract_text_from_content(content)

    tool_calls = parse_tool_calls(content) if msg_type == "assistant" else []
    tool_results = parse_tool_results(content) if msg_type == "user" else []

    return StructuredMessage(
        uuid=str(raw.get("uuid") or ""),
        parent_uuid=raw.get("parentUuid") if isinstance(raw.get("parentUuid"), str) else None,
        timestamp=parse_timestamp(raw.get("timestamp")),
        session_id=str(raw.get("sessionId") or ""),
        msg_type=msg_type,
        content_text=content_text,
        tool_calls=tool_calls,
        tool_results=tool_results,
        is_meta=bool(raw.get("isMeta")),
        cwd=raw.get("cwd") if isinstance(raw.get("cwd"), str) else None,
        git_branch=raw.get("gitBranch") if isinstance(raw.get("gitBranch"), str) else None,
    )


def parse_jsonl(path: Path) -> tuple[list[StructuredMessage], int]:
    messages: list[StructuredMessage] = []
    skipped_rows = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                raw = json.loads(stripped)
            except json.JSONDecodeError as exc:
                skipped_rows += 1
                warn(f"{path}:{line_number}: skipped unparsable JSONL row: {exc}")
                continue
            if not isinstance(raw, dict):
                skipped_rows += 1
                warn(f"{path}:{line_number}: skipped non-object JSONL row")
                continue
            messages.append(normalize_message(raw))
    messages.sort(key=lambda msg: msg.timestamp or datetime.min.replace(tzinfo=timezone.utc))
    return messages, skipped_rows


def matches_any(patterns: list[str], text: str) -> bool:
    return matched_pattern(patterns, text) is not None


def matched_pattern(patterns: list[str], text: str) -> str | None:
    for pattern in patterns:
        if re.search(pattern, text):
            return pattern
    return None


def detect_skill_invocations(message: StructuredMessage) -> list[str]:
    skills: list[str] = []
    if message.msg_type == "user" and message.content_text:
        for line in message.content_text.splitlines():
            slash_match = re.match(r"^\s*/([a-z][a-z0-9-]*)(?:\b|$)", line)
            if slash_match and slash_match.group(1) in KNOWN_SKILLS:
                skills.append(slash_match.group(1))
        for match in re.finditer(r"(?<![A-Za-z0-9_])\$([a-z][a-z0-9-]*)(?:\b|$)", message.content_text):
            if match.group(1) in KNOWN_SKILLS:
                skills.append(match.group(1))
    for call in message.tool_calls:
        if call.tool_name == "Skill":
            skill = call.input_data.get("skill") or call.input_data.get("name")
            if isinstance(skill, str) and skill:
                skills.append(skill)
    return skills


def detect_agent_dispatches(message: StructuredMessage) -> list[str]:
    agents: list[str] = []
    for call in message.tool_calls:
        if call.tool_name not in {"Agent", "Task", "spawn_agent"}:
            continue
        for key in ("subagent_type", "agent_type", "name"):
            value = call.input_data.get(key)
            if isinstance(value, str) and value:
                normalized = value.strip()
                if normalized in KNOWN_AGENTS or key != "name":
                    agents.append(normalized)
                break
    return agents


def extract_file_paths(text: str) -> set[str]:
    paths: set[str] = set()
    for pattern in FILE_PATH_PATTERNS:
        paths.update(match.group(0).rstrip(".,)") for match in pattern.finditer(text))
    return paths


def is_similar_instruction(previous: str, current: str) -> bool:
    prev_tokens = significant_tokens(previous)
    current_tokens = significant_tokens(current)
    if not prev_tokens or not current_tokens:
        return False
    overlap = len(prev_tokens & current_tokens)
    return overlap / max(len(prev_tokens), len(current_tokens)) >= 0.6


def significant_tokens(text: str) -> set[str]:
    lowered = text.lower()
    tokens = re.findall(r"[A-Za-z0-9가-힣_/-]{2,}", lowered)
    stopwords = {"the", "and", "that", "this", "with", "그리고", "근데", "다시", "해주세요", "해줘"}
    return {token for token in tokens if token not in stopwords}


def tool_name_for_result(tool_result: ToolResult, tool_call_by_id: dict[str, ToolCall]) -> str:
    call = tool_call_by_id.get(tool_result.tool_use_id)
    if not call:
        return "unknown"
    return TOOL_NAME_ALIASES.get(call.tool_name, call.tool_name)


def error_pattern_for_result(tool_result: ToolResult) -> str:
    return matched_pattern(TOOL_ERROR_PATTERNS, tool_result.content) or "is_error"


def compute_complexity(
    session_id: str,
    turn_count: int,
    unique_tools: set[str],
    entity_count: int,
    files_touched: set[str],
    branch_switches: int,
) -> dict[str, Any]:
    dimensions = {
        "turn_depth": min(turn_count / 30, 1.0),
        "tool_diversity": min(len(unique_tools) / 10, 1.0),
        "entity_count": min(entity_count / 8, 1.0),
        "file_scope": min(len(files_touched) / 20, 1.0),
        "branch_complexity": min(branch_switches / 5, 1.0),
    }
    weights = {
        "turn_depth": 0.25,
        "tool_diversity": 0.20,
        "entity_count": 0.20,
        "file_scope": 0.20,
        "branch_complexity": 0.15,
    }
    score = sum(dimensions[name] * weight for name, weight in weights.items())
    if score < 0.25:
        grade = "simple"
    elif score < 0.50:
        grade = "moderate"
    elif score < 0.75:
        grade = "complex"
    else:
        grade = "extreme"
    return {
        "session_id": session_id,
        "grade": grade,
        "score": round(score, 4),
        "dimensions": {name: round(value, 4) for name, value in dimensions.items()},
        "negative_signal_weight_factor": round(1.0 - (score * 0.3), 4),
    }


def analyze_session(path: Path, messages: list[StructuredMessage]) -> SessionAnalysis | None:
    if not messages:
        return None

    session_id = next((msg.session_id for msg in messages if msg.session_id), path.stem)
    timestamped = [msg.timestamp for msg in messages if msg.timestamp is not None]
    first_ts = min(timestamped) if timestamped else None
    last_ts = max(timestamped) if timestamped else None
    duration = int((last_ts - first_ts).total_seconds()) if first_ts and last_ts else 0

    user_messages = [msg for msg in messages if msg.msg_type == "user" and not msg.is_meta]
    direct_user_messages = [msg for msg in user_messages if msg.content_text and not msg.tool_results]
    turn_count = len(direct_user_messages)

    skill_invocations: Counter[str] = Counter()
    agent_dispatches: Counter[str] = Counter()
    tool_failures: Counter[str] = Counter()
    tool_failure_patterns: Counter[tuple[str, str]] = Counter()
    unique_tools: set[str] = set()
    files_touched: set[str] = set()
    tool_call_by_id: dict[str, ToolCall] = {}

    user_corrections = 0
    repeated_instructions = 0
    positive_feedback = 0
    previous_user_text = ""
    previous_branch: str | None = None
    branch_switches = 0

    for message in messages:
        if message.git_branch and previous_branch and message.git_branch != previous_branch:
            branch_switches += 1
        if message.git_branch:
            previous_branch = message.git_branch

        for call in message.tool_calls:
            unique_tools.add(TOOL_NAME_ALIASES.get(call.tool_name, call.tool_name))
            if call.tool_id:
                tool_call_by_id[call.tool_id] = call
            files_touched.update(extract_file_paths(json.dumps(call.input_data, ensure_ascii=False)))

        if message.content_text:
            files_touched.update(extract_file_paths(message.content_text))

        for skill in detect_skill_invocations(message):
            skill_invocations[skill] += 1
        for agent in detect_agent_dispatches(message):
            agent_dispatches[agent] += 1

        for result in message.tool_results:
            if not result.is_error:
                continue
            tool_name = tool_name_for_result(result, tool_call_by_id)
            pattern = error_pattern_for_result(result)
            tool_failures[tool_name] += 1
            tool_failure_patterns[(tool_name, pattern)] += 1

        if message not in direct_user_messages:
            continue
        text = message.content_text
        if matches_any(CORRECTION_PATTERNS, text) or matches_any(REJECTION_PATTERNS, text):
            user_corrections += 1
        if matches_any(PRAISE_PATTERNS, text):
            positive_feedback += 1
        if previous_user_text and (
            is_similar_instruction(previous_user_text, text) or matches_any(ROLLBACK_PATTERNS, text)
        ):
            repeated_instructions += 1
        previous_user_text = text

    entity_count = len(skill_invocations) + len(agent_dispatches)
    complexity = compute_complexity(
        session_id=session_id,
        turn_count=turn_count,
        unique_tools=unique_tools,
        entity_count=entity_count,
        files_touched=files_touched,
        branch_switches=branch_switches,
    )

    return SessionAnalysis(
        session_id=session_id,
        project=path.parent.name,
        timestamp=first_ts,
        turn_count=turn_count,
        session_duration_seconds=duration,
        user_corrections=user_corrections,
        repeated_instructions=repeated_instructions,
        tool_failures=tool_failures,
        tool_failure_patterns=tool_failure_patterns,
        positive_feedback=positive_feedback,
        skill_invocations=skill_invocations,
        agent_dispatches=agent_dispatches,
        tool_count=sum(1 for msg in messages for _ in msg.tool_calls),
        unique_tools=unique_tools,
        files_touched=files_touched,
        branch_switches=branch_switches,
        complexity=complexity,
    )


def in_date_range(session: SessionAnalysis, start: date, end: date) -> bool:
    if session.timestamp is None:
        return False
    session_date = session.timestamp.date()
    return start <= session_date <= end


def find_session_files(args: argparse.Namespace) -> tuple[list[Path], list[str]]:
    invalid: list[str] = []
    if args.sessions:
        paths = [expand_input_path(raw) for raw in args.sessions]
        missing = [str(path) for path in paths if not path.exists() or not path.is_file()]
        invalid.extend(missing)
        return [path for path in paths if path.exists() and path.is_file()], invalid

    projects_root = claude_home() / "projects"
    if not projects_root.exists():
        return [], [str(projects_root)]

    if args.project:
        project_dir = projects_root / project_to_slug(args.project)
        if not project_dir.exists() or not project_dir.is_dir():
            return [], [str(project_dir)]
        return sorted(project_dir.glob("*.jsonl")), []

    return sorted(projects_root.glob("*/*.jsonl")), []


def counter_items(counter: Counter[str], key_name: str, value_name: str) -> list[dict[str, Any]]:
    return [{key_name: key, value_name: value} for key, value in counter.most_common()]


def tool_failures_for_session(analysis: SessionAnalysis) -> list[dict[str, Any]]:
    rows = []
    for (tool, pattern), count in analysis.tool_failure_patterns.most_common():
        rows.append({"tool": tool, "error_pattern": pattern, "count": count})
    return rows


def session_to_json(analysis: SessionAnalysis) -> dict[str, Any]:
    return {
        "session_id": analysis.session_id,
        "project": analysis.project,
        "timestamp": display_iso(analysis.timestamp),
        "turn_count": analysis.turn_count,
        "session_duration_seconds": analysis.session_duration_seconds,
        "user_corrections": analysis.user_corrections,
        "repeated_instructions": analysis.repeated_instructions,
        "tool_failures": tool_failures_for_session(analysis),
        "positive_feedback": analysis.positive_feedback,
        "skill_invocations": counter_items(analysis.skill_invocations, "skill", "count"),
        "agent_dispatches": counter_items(analysis.agent_dispatches, "agent", "count"),
        "complexity": analysis.complexity,
    }


def aggregate(analyses: list[SessionAnalysis]) -> dict[str, Any]:
    total_turns = sum(item.turn_count for item in analyses)
    total_user_corrections = sum(item.user_corrections for item in analyses)
    total_repeated = sum(item.repeated_instructions for item in analyses)
    total_tool_failures = sum(sum(item.tool_failures.values()) for item in analyses)
    total_positive = sum(item.positive_feedback for item in analyses)

    failing_tools: Counter[str] = Counter()
    failing_sessions: defaultdict[str, set[str]] = defaultdict(set)
    skill_usage: Counter[str] = Counter()
    skill_sessions: defaultdict[str, set[str]] = defaultdict(set)
    agent_dispatches: Counter[str] = Counter()
    agent_sessions: defaultdict[str, set[str]] = defaultdict(set)
    complexity_distribution: Counter[str] = Counter()

    by_skill: defaultdict[str, Counter[str]] = defaultdict(Counter)
    by_agent: defaultdict[str, Counter[str]] = defaultdict(Counter)

    for analysis in analyses:
        complexity_distribution[analysis.complexity["grade"]] += 1
        for tool, count in analysis.tool_failures.items():
            failing_tools[tool] += count
            failing_sessions[tool].add(analysis.session_id)
        for skill, count in analysis.skill_invocations.items():
            skill_usage[skill] += count
            skill_sessions[skill].add(analysis.session_id)
            by_skill[skill]["invocations"] += count
            by_skill[skill]["sessions"] += 1
            by_skill[skill]["user_corrections"] += analysis.user_corrections
            by_skill[skill]["positive_feedback"] += analysis.positive_feedback
            by_skill[skill]["tool_failures"] += sum(analysis.tool_failures.values())
        for agent, count in analysis.agent_dispatches.items():
            agent_dispatches[agent] += count
            agent_sessions[agent].add(analysis.session_id)
            by_agent[agent]["dispatches"] += count
            by_agent[agent]["sessions"] += 1
            by_agent[agent]["user_corrections"] += analysis.user_corrections
            by_agent[agent]["positive_feedback"] += analysis.positive_feedback
            by_agent[agent]["tool_failures"] += sum(analysis.tool_failures.values())

    return {
        "total_user_corrections": total_user_corrections,
        "total_repeated_instructions": total_repeated,
        "total_tool_failures": total_tool_failures,
        "total_positive_feedback": total_positive,
        "correction_rate": round(total_user_corrections / total_turns, 4) if total_turns else 0.0,
        "tool_failure_rate": round(total_tool_failures / sum(item.tool_count for item in analyses), 4)
        if analyses and sum(item.tool_count for item in analyses)
        else 0.0,
        "top_failing_tools": [
            {
                "tool": tool,
                "failure_count": count,
                "sessions_affected": len(failing_sessions[tool]),
            }
            for tool, count in failing_tools.most_common()
        ],
        "top_skills_by_usage": [
            {
                "skill": skill,
                "invocations": count,
                "sessions": len(skill_sessions[skill]),
            }
            for skill, count in skill_usage.most_common()
        ],
        "top_agents_by_dispatch": [
            {
                "agent": agent,
                "dispatches": count,
                "sessions": len(agent_sessions[agent]),
            }
            for agent, count in agent_dispatches.most_common()
        ],
        "complexity_distribution": dict(sorted(complexity_distribution.items())),
        "by_skill": entity_breakdown(by_skill, "skill"),
        "by_agent": entity_breakdown(by_agent, "agent"),
    }


def entity_breakdown(stats_by_entity: dict[str, Counter[str]], name_key: str) -> list[dict[str, Any]]:
    rows = []
    for entity, stats in sorted(stats_by_entity.items()):
        denominator = max(stats["invocations"] or stats["dispatches"] or stats["sessions"], 1)
        row = {name_key: entity}
        row.update(dict(stats))
        row["correction_rate"] = round(stats["user_corrections"] / denominator, 4)
        row["positive_feedback_rate"] = round(stats["positive_feedback"] / denominator, 4)
        row["tool_failure_rate"] = round(stats["tool_failures"] / denominator, 4)
        rows.append(row)
    return rows


def build_report(
    analyses: list[SessionAnalysis],
    sessions_skipped: int,
    date_range: tuple[str, str] | None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now_iso(),
        "date_range": {"start": date_range[0], "end": date_range[1]} if date_range else None,
        "sessions_analyzed": len(analyses),
        "sessions_skipped": sessions_skipped,
        "signals": {
            "by_session": [session_to_json(analysis) for analysis in analyses],
            "aggregated": aggregate(analyses),
        },
    }


def print_text_report(report: dict[str, Any]) -> None:
    aggregated = report["signals"]["aggregated"]
    print(f"Session Analyzer report (schema v{report['schema_version']})")
    print(f"Generated at: {report['generated_at']}")
    print(f"Sessions analyzed: {report['sessions_analyzed']}")
    print(f"Sessions skipped: {report['sessions_skipped']}")
    print(f"User corrections: {aggregated['total_user_corrections']}")
    print(f"Repeated instructions: {aggregated['total_repeated_instructions']}")
    print(f"Tool failures: {aggregated['total_tool_failures']}")
    print(f"Positive feedback: {aggregated['total_positive_feedback']}")
    print(f"Correction rate: {aggregated['correction_rate']}")


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid ISO date: {value}") from exc


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze Claude session JSONL files for HyperAgent signals.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--sessions", nargs="+", help="Session JSONL paths to analyze.")
    source.add_argument("--date-range", nargs=2, metavar=("START", "END"), help="Inclusive ISO date range.")
    parser.add_argument("--project", help="Project path or slug to filter when using --date-range.")
    parser.add_argument("--json", action="store_true", help="Print structured JSON to stdout.")
    parser.add_argument("--min-turns", type=int, default=DEFAULT_MIN_TURNS, help="Minimum user turns to analyze.")
    args = parser.parse_args(argv)
    if args.min_turns < 0:
        parser.error("--min-turns must be >= 0")
    if args.date_range:
        start = parse_date(args.date_range[0])
        end = parse_date(args.date_range[1])
        if start > end:
            parser.error("--date-range START must be <= END")
        args.date_range_dates = (start, end)
    else:
        args.date_range_dates = None
    return args


def run(argv: list[str]) -> int:
    args = parse_args(argv)
    session_files, invalid_paths = find_session_files(args)
    if invalid_paths:
        print("invalid session path(s):", file=sys.stderr)
        for path in invalid_paths:
            print(f"  {path}", file=sys.stderr)
        return 1

    analyses: list[SessionAnalysis] = []
    sessions_skipped = 0
    for path in session_files:
        messages, skipped_rows = parse_jsonl(path)
        sessions_skipped += skipped_rows
        analysis = analyze_session(path, messages)
        if analysis is None:
            sessions_skipped += 1
            continue
        if args.date_range_dates and not in_date_range(analysis, *args.date_range_dates):
            continue
        if analysis.turn_count < args.min_turns:
            sessions_skipped += 1
            continue
        analyses.append(analysis)

    analyses.sort(key=lambda item: (item.timestamp or datetime.min.replace(tzinfo=timezone.utc), item.session_id))
    date_range = tuple(args.date_range) if args.date_range else None
    report = build_report(analyses, sessions_skipped, date_range)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_text_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
