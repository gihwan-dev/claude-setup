#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1"
DEFAULT_BASELINE_MIN_SESSIONS = 5
DEFAULT_DECAY_HALF_LIFE_DAYS = 7
DEFAULT_TREND_THRESHOLD = 0.15
DEFAULT_BASELINE_PATH = "~/.claude/hyperagent/baseline.json"
REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class SessionSample:
    entity_type: str
    entity_id: str
    session_id: str
    timestamp: datetime | None
    count: int
    turn_count: int
    complexity_score: float
    negative_factor: float
    dimensions: dict[str, float]
    composite: float
    negative_total: float
    touched_files: set[str] = field(default_factory=set)


@dataclass
class EntityScore:
    entity_type: str
    entity_id: str
    score: float
    dimensions: dict[str, float]
    score_breakdown: dict[str, dict[str, float]]
    sessions: int
    invocations: int
    evidence_sessions: list[str]
    session_scores: list[float]
    session_ids: list[str]
    touched_files: set[str]
    trend: dict[str, Any]
    baseline: dict[str, Any] | None
    suggestions: list[dict[str, Any]]
    commit_adoption_rate: dict[str, Any]


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def expand_input_path(raw_path: str) -> Path:
    if raw_path.startswith("~/.claude"):
        suffix = raw_path.removeprefix("~/.claude").lstrip("/")
        return claude_home() / suffix
    return Path(raw_path).expanduser()


def claude_home() -> Path:
    configured = os.environ.get("CLAUDE_HOME")
    if configured:
        return Path(configured).expanduser()
    return Path("~/.claude").expanduser()


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def rounded(value: float) -> float:
    return round(clamp(value), 4)


def entity_key(entity_type: str, entity_id: str) -> str:
    return f"{entity_type}:{entity_id}"


def session_weight(turn_count: int) -> float:
    return max(math.log(max(turn_count, 0) + 1), 0.1)


def decay_weight(timestamp: datetime | None, reference: datetime, half_life_days: int) -> float:
    if timestamp is None:
        return 1.0
    days_ago = max((reference - timestamp).total_seconds() / 86400, 0.0)
    return 2 ** (-days_ago / max(half_life_days, 1))


def weighted_average(rows: list[tuple[float, float]]) -> float:
    total_weight = sum(weight for _, weight in rows)
    if total_weight <= 0:
        return 0.0
    return sum(value * weight for value, weight in rows) / total_weight


def load_report(args: argparse.Namespace) -> tuple[dict[str, Any], str]:
    raw_source = args.input or args.report
    if raw_source:
        path = expand_input_path(raw_source)
        try:
            return json.loads(path.read_text(encoding="utf-8")), str(path)
        except FileNotFoundError:
            raise SystemExit(f"report not found: {path}") from None
        except json.JSONDecodeError as exc:
            raise SystemExit(f"invalid report JSON: {exc}") from None

    if sys.stdin.isatty():
        raise SystemExit("no input report supplied; use --input PATH or pipe JSON on stdin")
    try:
        return json.load(sys.stdin), "stdin"
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid report JSON from stdin: {exc}") from None


def validate_report(report: dict[str, Any]) -> None:
    if not isinstance(report, dict):
        raise SystemExit("invalid report JSON: top-level value must be an object")
    if str(report.get("schema_version")) != SCHEMA_VERSION:
        raise SystemExit("invalid report JSON: schema_version must be \"1\"")
    signals = report.get("signals")
    if not isinstance(signals, dict):
        raise SystemExit("invalid report JSON: missing signals object")
    by_session = signals.get("by_session")
    aggregated = signals.get("aggregated")
    if not isinstance(by_session, list):
        raise SystemExit("invalid report JSON: signals.by_session must be a list")
    if not isinstance(aggregated, dict):
        raise SystemExit("invalid report JSON: signals.aggregated must be an object")


def validate_metadata_paths(registry: Path, skills: Path) -> None:
    missing = [str(path) for path in (registry, skills) if not path.exists() or not path.is_dir()]
    if missing:
        print("missing metadata path(s):", file=sys.stderr)
        for path in missing:
            print(f"  {path}", file=sys.stderr)
        raise SystemExit(3)


def count_tool_failures(session: dict[str, Any]) -> int:
    failures = session.get("tool_failures")
    if not isinstance(failures, list):
        return 0
    total = 0
    for row in failures:
        if isinstance(row, dict):
            total += int(row.get("count") or row.get("failure_count") or 0)
    return total


def session_id_for(session: dict[str, Any]) -> str:
    return str(session.get("session_id") or "unknown-session")


def entity_rows(session: dict[str, Any], key_name: str, count_name: str) -> list[tuple[str, int]]:
    rows = session.get(key_name)
    if not isinstance(rows, list):
        return []
    parsed: list[tuple[str, int]] = []
    name_field = "skill" if key_name == "skill_invocations" else "agent"
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = row.get(name_field)
        if not isinstance(name, str) or not name:
            continue
        parsed.append((name, max(int(row.get(count_name) or 1), 1)))
    return parsed


def complexity_values(session: dict[str, Any]) -> tuple[float, float]:
    complexity = session.get("complexity")
    if not isinstance(complexity, dict):
        return 0.0, 1.0
    score = clamp(float(complexity.get("score") or 0.0))
    factor = complexity.get("negative_signal_weight_factor")
    if isinstance(factor, (int, float)):
        return score, clamp(float(factor), 0.7, 1.0)
    return score, clamp(1.0 - (score * 0.3), 0.7, 1.0)


def touched_files(session: dict[str, Any]) -> set[str]:
    raw = session.get("files_touched") or session.get("touched_files")
    if not isinstance(raw, list):
        return set()
    return {str(item) for item in raw if isinstance(item, str) and item}


def negative_signal_total(session: dict[str, Any]) -> int:
    return (
        int(session.get("user_corrections") or 0)
        + int(session.get("repeated_instructions") or 0)
        + count_tool_failures(session)
    )


def skill_dimensions(session: dict[str, Any], count: int) -> tuple[dict[str, float], float, float]:
    corrections = int(session.get("user_corrections") or 0)
    repeated = int(session.get("repeated_instructions") or 0)
    positives = int(session.get("positive_feedback") or 0)
    failures = count_tool_failures(session)
    turn_count = max(int(session.get("turn_count") or 0), 1)
    _, negative_factor = complexity_values(session)
    denominator = max(count, 1)

    adjusted_corrections = corrections * negative_factor
    adjusted_repeated = repeated * negative_factor
    adjusted_failures = failures * negative_factor
    negative_total = adjusted_corrections + adjusted_repeated + adjusted_failures
    implicit_accepts = denominator if positives == 0 and negative_total == 0 else 0

    dimensions = {
        "acceptance_rate": clamp((positives + implicit_accepts) / denominator),
        "modification_freq": clamp(adjusted_corrections / denominator),
        "completion_rate": clamp(1.0 - (negative_total / max(turn_count, denominator))),
        "rework_rate": clamp(adjusted_repeated / denominator),
        "usage_frequency": clamp(denominator / max(turn_count, denominator)),
    }
    composite = (
        0.35 * dimensions["acceptance_rate"]
        + 0.25 * (1.0 - dimensions["modification_freq"])
        + 0.25 * dimensions["completion_rate"]
        + 0.15 * (1.0 - dimensions["rework_rate"])
    )
    return dimensions, clamp(composite), negative_total


def agent_dimensions(session: dict[str, Any], count: int) -> tuple[dict[str, float], float, float]:
    corrections = int(session.get("user_corrections") or 0)
    repeated = int(session.get("repeated_instructions") or 0)
    failures = count_tool_failures(session)
    _, negative_factor = complexity_values(session)
    denominator = max(count, 1)

    adjusted_corrections = corrections * negative_factor
    adjusted_repeated = repeated * negative_factor
    adjusted_failures = failures * negative_factor
    false_positive_rate = clamp((adjusted_repeated + (0.5 * adjusted_corrections)) / denominator)
    dimensions = {
        "accuracy": clamp(1.0 - (adjusted_corrections / denominator)),
        "relevance": clamp(1.0 - ((adjusted_repeated + (0.5 * adjusted_failures)) / denominator)),
        "false_positive_rate": false_positive_rate,
        "usage_frequency": clamp(denominator / max(int(session.get("turn_count") or 1), denominator)),
    }
    composite = (
        0.4 * dimensions["accuracy"]
        + 0.4 * dimensions["relevance"]
        + 0.2 * (1.0 - dimensions["false_positive_rate"])
    )
    return dimensions, clamp(composite), adjusted_corrections + adjusted_repeated + adjusted_failures


def orchestration_dimensions(session: dict[str, Any], count: int) -> tuple[dict[str, float], float, float]:
    corrections = int(session.get("user_corrections") or 0)
    repeated = int(session.get("repeated_instructions") or 0)
    failures = count_tool_failures(session)
    _, negative_factor = complexity_values(session)
    assignments = max(count, 1)

    adjusted_corrections = corrections * negative_factor
    adjusted_repeated = repeated * negative_factor
    adjusted_failures = failures * negative_factor
    dimensions = {
        "dispatch_accuracy": clamp(1.0 - (adjusted_corrections / assignments)),
        "fanout_efficiency": clamp(1.0 - (adjusted_failures / assignments)),
        "routing_relevance": clamp(1.0 - (adjusted_repeated / assignments)),
    }
    composite = statistics.mean(dimensions.values())
    return dimensions, clamp(composite), adjusted_corrections + adjusted_repeated + adjusted_failures


def build_samples(report: dict[str, Any]) -> list[SessionSample]:
    samples: list[SessionSample] = []
    for session in report["signals"]["by_session"]:
        if not isinstance(session, dict):
            continue
        session_id = str(session.get("session_id") or "unknown-session")
        timestamp = parse_timestamp(session.get("timestamp"))
        turn_count = max(int(session.get("turn_count") or 0), 0)
        complexity_score, negative_factor = complexity_values(session)
        files = touched_files(session)

        for skill, count in entity_rows(session, "skill_invocations", "count"):
            dimensions, composite, negative_total = skill_dimensions(session, count)
            samples.append(
                SessionSample(
                    entity_type="skill",
                    entity_id=skill,
                    session_id=session_id,
                    timestamp=timestamp,
                    count=count,
                    turn_count=turn_count,
                    complexity_score=complexity_score,
                    negative_factor=negative_factor,
                    dimensions=dimensions,
                    composite=composite,
                    negative_total=negative_total,
                    touched_files=files,
                )
            )

        agent_counts = entity_rows(session, "agent_dispatches", "count")
        for agent, count in agent_counts:
            dimensions, composite, negative_total = agent_dimensions(session, count)
            samples.append(
                SessionSample(
                    entity_type="agent",
                    entity_id=agent,
                    session_id=session_id,
                    timestamp=timestamp,
                    count=count,
                    turn_count=turn_count,
                    complexity_score=complexity_score,
                    negative_factor=negative_factor,
                    dimensions=dimensions,
                    composite=composite,
                    negative_total=negative_total,
                    touched_files=files,
                )
            )

        if agent_counts:
            total_dispatches = sum(count for _, count in agent_counts)
            dimensions, composite, negative_total = orchestration_dimensions(session, total_dispatches)
            samples.append(
                SessionSample(
                    entity_type="orchestration",
                    entity_id="global",
                    session_id=session_id,
                    timestamp=timestamp,
                    count=total_dispatches,
                    turn_count=turn_count,
                    complexity_score=complexity_score,
                    negative_factor=negative_factor,
                    dimensions=dimensions,
                    composite=composite,
                    negative_total=negative_total,
                    touched_files=files,
                )
            )
    return samples


def aggregate_entity_scores(
    samples: list[SessionSample],
    baseline_data: dict[str, Any],
    reference_time: datetime,
    half_life_days: int,
    trend_threshold: float,
) -> list[EntityScore]:
    grouped: defaultdict[str, list[SessionSample]] = defaultdict(list)
    for sample in samples:
        grouped[entity_key(sample.entity_type, sample.entity_id)].append(sample)

    scores: list[EntityScore] = []
    baselines = baseline_data.get("entities") if isinstance(baseline_data.get("entities"), dict) else {}
    for key, entity_samples in sorted(grouped.items()):
        entity_type = entity_samples[0].entity_type
        entity_id = entity_samples[0].entity_id
        dimension_names = sorted({name for sample in entity_samples for name in sample.dimensions})
        dimension_values: dict[str, float] = {}
        for name in dimension_names:
            dimension_values[name] = weighted_average(
                [
                    (
                        sample.dimensions.get(name, 0.0),
                        session_weight(sample.turn_count)
                        * decay_weight(sample.timestamp, reference_time, half_life_days)
                        * max(sample.count, 1),
                    )
                    for sample in entity_samples
                ]
            )

        if entity_type == "skill":
            composite = (
                0.35 * dimension_values.get("acceptance_rate", 0.0)
                + 0.25 * (1.0 - dimension_values.get("modification_freq", 0.0))
                + 0.25 * dimension_values.get("completion_rate", 0.0)
                + 0.15 * (1.0 - dimension_values.get("rework_rate", 0.0))
            )
        elif entity_type == "agent":
            composite = (
                0.4 * dimension_values.get("accuracy", 0.0)
                + 0.4 * dimension_values.get("relevance", 0.0)
                + 0.2 * (1.0 - dimension_values.get("false_positive_rate", 0.0))
            )
        else:
            composite = statistics.mean(
                [
                    dimension_values.get("dispatch_accuracy", 0.0),
                    dimension_values.get("fanout_efficiency", 0.0),
                    dimension_values.get("routing_relevance", 0.0),
                ]
            )

        score = rounded(composite)
        baseline = baseline_for_entity(baselines, key)
        trend = trend_for_entity(baseline, [sample.composite for sample in entity_samples], trend_threshold)
        suggestions = suggestions_for_entity(entity_type, entity_id, score, dimension_values, trend)
        evidence_sessions = evidence_for_entity(entity_samples)
        touched = set().union(*(sample.touched_files for sample in entity_samples)) if entity_samples else set()
        adoption_rate = compute_commit_adoption_rate(entity_id, touched, REPO_ROOT)
        scores.append(
            EntityScore(
                entity_type=entity_type,
                entity_id=entity_id,
                score=score,
                dimensions={name: rounded(value) for name, value in dimension_values.items()},
                score_breakdown=score_breakdown(entity_type, dimension_values),
                sessions=len({sample.session_id for sample in entity_samples}),
                invocations=sum(sample.count for sample in entity_samples),
                evidence_sessions=evidence_sessions,
                session_scores=[rounded(sample.composite) for sample in entity_samples],
                session_ids=sorted({sample.session_id for sample in entity_samples}),
                touched_files=touched,
                trend=trend,
                baseline=baseline,
                suggestions=suggestions,
                commit_adoption_rate=adoption_rate,
            )
        )
    return scores


def score_breakdown(entity_type: str, dimensions: dict[str, float]) -> dict[str, dict[str, float]]:
    weights = {
        "skill": {
            "acceptance_rate": 0.35,
            "modification_freq": -0.25,
            "completion_rate": 0.25,
            "rework_rate": -0.15,
            "usage_frequency": 0.0,
        },
        "agent": {
            "accuracy": 0.4,
            "relevance": 0.4,
            "false_positive_rate": -0.2,
            "usage_frequency": 0.0,
        },
        "orchestration": {
            "dispatch_accuracy": 1 / 3,
            "fanout_efficiency": 1 / 3,
            "routing_relevance": 1 / 3,
        },
    }
    rows: dict[str, dict[str, float]] = {}
    for name, weight in weights[entity_type].items():
        raw = clamp(dimensions.get(name, 0.0))
        weighted = raw * weight if weight >= 0 else (1.0 - raw) * abs(weight)
        rows[name] = {"raw": round(raw, 4), "weighted": round(weighted, 4)}
    return rows


def evidence_for_entity(samples: list[SessionSample]) -> list[str]:
    ordered = sorted(samples, key=lambda sample: (-sample.negative_total, sample.session_id))
    evidence = [sample.session_id for sample in ordered if sample.negative_total > 0]
    if not evidence:
        evidence = [sample.session_id for sample in ordered[:3]]
    return list(dict.fromkeys(evidence))[:5]


def baseline_for_entity(baselines: dict[str, Any], key: str) -> dict[str, Any] | None:
    row = baselines.get(key)
    if not isinstance(row, dict):
        return None
    return {
        "baseline_score": row.get("baseline_score"),
        "baseline_sessions": row.get("baseline_sessions"),
        "established_at": row.get("established_at"),
    }


def trend_for_entity(
    baseline: dict[str, Any] | None,
    recent_scores: list[float],
    threshold: float,
) -> dict[str, Any]:
    if not baseline or not isinstance(baseline.get("baseline_score"), (int, float)):
        return {
            "direction": "new",
            "magnitude": 0.0,
            "confidence": min(1.0, len(recent_scores) / 10),
            "period_sessions": len(recent_scores),
        }
    if len(recent_scores) < 3:
        return {
            "direction": "stable",
            "magnitude": 0.0,
            "confidence": 0.3,
            "period_sessions": len(recent_scores),
        }
    baseline_score = float(baseline["baseline_score"])
    recent_avg = statistics.mean(recent_scores)
    magnitude = (recent_avg - baseline_score) / max(baseline_score, 0.01)
    if magnitude > threshold:
        direction = "improving"
    elif magnitude < -threshold:
        direction = "degrading"
    else:
        direction = "stable"
    return {
        "direction": direction,
        "magnitude": round(magnitude, 4),
        "confidence": round(min(1.0, len(recent_scores) / 10), 4),
        "period_sessions": len(recent_scores),
    }


def suggestions_for_entity(
    entity_type: str,
    entity_id: str,
    score: float,
    dimensions: dict[str, float],
    trend: dict[str, Any],
) -> list[dict[str, Any]]:
    suggestions: list[dict[str, Any]] = []
    issue, description = weakest_dimension(entity_type, dimensions)
    priority = priority_for(score, trend.get("direction"))
    if score < 0.8 or trend.get("direction") == "degrading":
        suggestions.append(
            {
                "type": issue,
                "target": target_for(entity_type, entity_id),
                "description": description,
                "priority": priority,
            }
        )
    return suggestions


def weakest_dimension(entity_type: str, dimensions: dict[str, float]) -> tuple[str, str]:
    if entity_type == "skill":
        candidates = {
            "acceptance_rate": dimensions.get("acceptance_rate", 0.0),
            "modification_freq": 1.0 - dimensions.get("modification_freq", 0.0),
            "completion_rate": dimensions.get("completion_rate", 0.0),
            "rework_rate": 1.0 - dimensions.get("rework_rate", 0.0),
        }
        weakest = min(candidates, key=candidates.get)
        descriptions = {
            "acceptance_rate": "수용률이 낮습니다. 입력 조건, 성공 기준, 산출물 형식을 더 명확히 고정하는 개선이 우선입니다.",
            "modification_freq": "수정 요청 비율이 높습니다. 자주 보정되는 요구사항을 스킬 지침에 체크리스트로 반영하는 편이 좋습니다.",
            "completion_rate": "완료율이 낮습니다. 실패 종료 조건과 검증 명령을 스킬 흐름에 더 선명하게 넣는 개선이 필요합니다.",
            "rework_rate": "재작업율이 높습니다. 반복 지시가 발생한 세션의 공통 패턴을 스킬 초반 질문 또는 실행 순서에 반영하세요.",
        }
        return weakest, descriptions[weakest]
    if entity_type == "agent":
        candidates = {
            "accuracy": dimensions.get("accuracy", 0.0),
            "relevance": dimensions.get("relevance", 0.0),
            "false_positive_rate": 1.0 - dimensions.get("false_positive_rate", 0.0),
        }
        weakest = min(candidates, key=candidates.get)
        descriptions = {
            "accuracy": "정확도 신호가 약합니다. 근거 확인, 파일 참조, 불확실성 표기 규칙을 에이전트 지침에 강화하세요.",
            "relevance": "관련성 신호가 약합니다. 에이전트의 작업 수락 조건과 제외 범위를 더 좁혀 라우팅 품질을 높이세요.",
            "false_positive_rate": "거부 또는 무시된 제안 비율이 높습니다. 주장 강도를 낮추고 증거가 있는 지적만 보고하도록 조정하세요.",
        }
        return weakest, descriptions[weakest]
    candidates = {
        "dispatch_accuracy": dimensions.get("dispatch_accuracy", 0.0),
        "fanout_efficiency": dimensions.get("fanout_efficiency", 0.0),
        "routing_relevance": dimensions.get("routing_relevance", 0.0),
    }
    weakest = min(candidates, key=candidates.get)
    descriptions = {
        "dispatch_accuracy": "에이전트 배정 정확도가 낮습니다. 작업 유형별 라우팅 기준과 중단 조건을 더 명확히 하세요.",
        "fanout_efficiency": "fan-out 효율이 낮습니다. 병렬 실행 대상을 독립적인 증거 수집 또는 검증 업무로 제한하세요.",
        "routing_relevance": "라우팅 관련성이 낮습니다. 에이전트 교체가 필요한 신호를 초기에 확인하는 게 좋습니다.",
    }
    return weakest, descriptions[weakest]


def priority_for(score: float, trend_direction: Any) -> str:
    if score < 0.5 or trend_direction == "degrading":
        return "high"
    if score < 0.7:
        return "medium"
    return "low"


def target_for(entity_type: str, entity_id: str) -> str:
    if entity_type == "skill":
        return f"skills/{entity_id}/SKILL.md"
    if entity_type == "agent":
        return f"agent-registry/{entity_id}/instructions.md"
    return "orchestration-policy"


def compute_commit_adoption_rate(entity_id: str, files: set[str], repo_path: Path) -> dict[str, Any]:
    if not files:
        return {
            "available": False,
            "rate": None,
            "method": "git_blame",
            "reason": "analysis report does not include touched files for this entity",
        }
    committed_lines = 0
    total_lines = 0
    considered_files: list[str] = []
    for raw_file in sorted(files):
        path = Path(raw_file)
        if path.is_absolute():
            try:
                relative = path.resolve().relative_to(repo_path.resolve())
            except ValueError:
                continue
        else:
            relative = path
        candidate = repo_path / relative
        if not candidate.exists() or not candidate.is_file():
            continue
        result = subprocess.run(
            ["git", "blame", "--line-porcelain", "--", str(relative)],
            cwd=repo_path,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode != 0:
            continue
        considered_files.append(str(relative))
        for line in result.stdout.splitlines():
            if not line or line.startswith("\t"):
                continue
            parts = line.split()
            if len(parts) >= 4 and len(parts[0]) >= 8:
                total_lines += 1
                if set(parts[0]) != {"0"}:
                    committed_lines += 1
    if total_lines == 0:
        return {
            "available": False,
            "rate": None,
            "method": "git_blame",
            "reason": "no blameable lines found for touched files",
            "files_considered": considered_files,
            "entity_id": entity_id,
        }
    return {
        "available": True,
        "rate": round(committed_lines / total_lines, 4),
        "method": "git_blame",
        "committed_lines": committed_lines,
        "total_lines": total_lines,
        "files_considered": considered_files,
        "entity_id": entity_id,
    }


def load_or_create_baseline(
    path: Path,
    samples: list[SessionSample],
    min_sessions: int,
    half_life_days: int,
    trend_threshold: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    path = path.expanduser()
    status: dict[str, Any] = {
        "path": str(path),
        "min_sessions": min_sessions,
        "decay_half_life_days": half_life_days,
        "trend_threshold": trend_threshold,
        "state": "loaded",
        "created": False,
        "updated": False,
        "entities_established": [],
        "entities_pending": [],
    }
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"invalid baseline JSON: {path}: {exc}") from None
        if not isinstance(data, dict):
            raise SystemExit(f"invalid baseline JSON: {path}: top-level value must be an object")
        if not isinstance(data.get("entities"), dict):
            data["entities"] = {}
    else:
        data = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
            "config": {
                "baseline_min_sessions": min_sessions,
                "decay_half_life_days": half_life_days,
                "trend_threshold": trend_threshold,
            },
            "entities": {},
        }
        status["state"] = "created"
        status["created"] = True

    changed = establish_missing_baselines(data, samples, min_sessions, status)
    if status["created"] or changed:
        data["updated_at"] = utc_now_iso()
        data["config"] = {
            "baseline_min_sessions": min_sessions,
            "decay_half_life_days": half_life_days,
            "trend_threshold": trend_threshold,
        }
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            tmp.replace(path)
            status["updated"] = True
        except OSError as exc:
            status["state"] = "write_failed"
            status["write_error"] = str(exc)
            warn(f"could not write baseline file {path}: {exc}")
    return data, status


def establish_missing_baselines(
    data: dict[str, Any],
    samples: list[SessionSample],
    min_sessions: int,
    status: dict[str, Any],
) -> bool:
    grouped: defaultdict[str, list[SessionSample]] = defaultdict(list)
    for sample in samples:
        grouped[entity_key(sample.entity_type, sample.entity_id)].append(sample)

    changed = False
    baselines: dict[str, Any] = data.setdefault("entities", {})
    for key, entity_samples in sorted(grouped.items()):
        if key in baselines:
            continue
        session_ids = sorted({sample.session_id for sample in entity_samples})
        if len(session_ids) < min_sessions:
            status["entities_pending"].append(
                {
                    "entity_key": key,
                    "sessions": len(session_ids),
                    "needed": min_sessions,
                }
            )
            continue
        baseline_score = statistics.median(sample.composite for sample in entity_samples)
        baselines[key] = {
            "entity_type": entity_samples[0].entity_type,
            "entity_id": entity_samples[0].entity_id,
            "baseline_score": round(baseline_score, 4),
            "baseline_sessions": len(session_ids),
            "established_at": utc_now_iso(),
            "source_session_ids": session_ids,
        }
        status["entities_established"].append(key)
        changed = True
    return changed


def improvements_from_scores(scores: list[EntityScore]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for score in scores:
        if score.invocations <= 0:
            continue
        if not score.suggestions:
            continue
        baseline_delta = None
        if score.baseline and isinstance(score.baseline.get("baseline_score"), (int, float)):
            baseline_delta = round(score.score - float(score.baseline["baseline_score"]), 4)
        suggestion = score.suggestions[0]
        rows.append(
            {
                "entity_type": score.entity_type,
                "entity_id": score.entity_id,
                "score": score.score,
                "priority": suggestion["priority"],
                "reason": suggestion["type"],
                "suggestion": suggestion["description"],
                "target": suggestion["target"],
                "trend": score.trend,
                "baseline_delta": baseline_delta,
                "evidence_sessions": score.evidence_sessions,
            }
        )
    priority_rank = {"high": 0, "medium": 1, "low": 2}
    rows.sort(key=lambda row: (priority_rank.get(str(row["priority"]), 9), row["score"], row["entity_type"], row["entity_id"]))
    for index, row in enumerate(rows, 1):
        row["rank"] = index
    return rows


def tool_failure_labels(session: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    failures = session.get("tool_failures")
    if not isinstance(failures, list):
        return labels
    for failure in failures:
        if not isinstance(failure, dict):
            continue
        tool = failure.get("tool")
        pattern = failure.get("error_pattern")
        if isinstance(tool, str) and tool:
            labels.append(tool)
        if isinstance(pattern, str) and pattern:
            labels.append(pattern)
    return labels


def coverage_pattern_for(session: dict[str, Any]) -> str:
    labels = " ".join(tool_failure_labels(session)).lower()
    if "docker compose" in labels or "docker-compose" in labels or "compose" in labels:
        return "Docker Compose 관련 작업"
    if "gitlab" in labels or "glab" in labels:
        return "GitLab 관련 작업"
    if "github" in labels or "gh " in labels:
        return "GitHub 관련 작업"
    if "figma" in labels:
        return "Figma 관련 작업"
    if "test" in labels or "pytest" in labels or "unittest" in labels:
        return "테스트 실패 조사 작업"
    if int(session.get("repeated_instructions") or 0) > 0:
        return "반복 지시가 있었지만 에이전트 없이 수행된 작업"
    complexity = session.get("complexity")
    if isinstance(complexity, dict) and isinstance(complexity.get("grade"), str):
        return f"{complexity['grade']} 복잡도 작업"
    return "에이전트 없이 수행된 작업"


def add_grouped_gap(
    grouped: dict[str, dict[str, Any]],
    pattern: str,
    session_id: str,
    frequency: int,
    suggestion_type: str,
) -> None:
    row = grouped.setdefault(
        pattern,
        {
            "pattern": pattern,
            "sessions": [],
            "frequency": 0,
            "suggestion_type": suggestion_type,
        },
    )
    if session_id not in row["sessions"]:
        row["sessions"].append(session_id)
    row["frequency"] += max(frequency, 1)


def gap_analysis_for_report(report: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    sessions = report.get("signals", {}).get("by_session", [])
    if not isinstance(sessions, list):
        sessions = []

    missing_coverage: dict[str, dict[str, Any]] = {}
    repeated_patterns: dict[str, dict[str, Any]] = {}
    agent_totals: defaultdict[str, set[str]] = defaultdict(set)
    agent_negative: defaultdict[str, set[str]] = defaultdict(set)

    for session in sessions:
        if not isinstance(session, dict):
            continue
        session_id = session_id_for(session)
        agent_counts = entity_rows(session, "agent_dispatches", "count")
        negative_total = negative_signal_total(session)
        repeated_count = int(session.get("repeated_instructions") or 0)
        turn_count = int(session.get("turn_count") or 0)

        if not agent_counts and (negative_total > 0 or turn_count >= 3):
            add_grouped_gap(
                missing_coverage,
                coverage_pattern_for(session),
                session_id,
                max(negative_total, turn_count, 1),
                "new_agent",
            )

        if repeated_count > 0:
            repeated_pattern = "반복 지시가 재발한 작업"
            if not session.get("skill_invocations"):
                repeated_pattern = "반복 지시가 있었지만 스킬 없이 수행된 작업"
            add_grouped_gap(
                repeated_patterns,
                repeated_pattern,
                session_id,
                repeated_count,
                "new_skill_or_hook",
            )

        for agent, _ in agent_counts:
            agent_totals[agent].add(session_id)
            if negative_total > 0:
                agent_negative[agent].add(session_id)

    misfit_agents: list[dict[str, Any]] = []
    for agent, total_sessions in sorted(agent_totals.items()):
        negative_sessions = sorted(agent_negative.get(agent, set()))
        if not total_sessions or not negative_sessions:
            continue
        negative_rate = round(len(negative_sessions) / len(total_sessions), 4)
        if negative_rate < 0.5:
            continue
        misfit_agents.append(
            {
                "agent": agent,
                "negative_rate": negative_rate,
                "sessions": negative_sessions[:5],
                "suggestion_type": "new_specialized_agent",
            }
        )
    misfit_agents.sort(key=lambda row: (-row["negative_rate"], row["agent"]))

    return {
        "missing_coverage": sorted(
            missing_coverage.values(),
            key=lambda row: (-row["frequency"], row["pattern"]),
        )[:10],
        "repeated_patterns": sorted(
            repeated_patterns.values(),
            key=lambda row: (-row["frequency"], row["pattern"]),
        )[:10],
        "misfit_agents": misfit_agents[:10],
    }


def entity_to_json(score: EntityScore) -> dict[str, Any]:
    return {
        "entity_type": score.entity_type,
        "entity_id": score.entity_id,
        "score": score.score,
        "score_breakdown": score.score_breakdown,
        "dimensions": score.dimensions,
        "sessions": score.sessions,
        "invocations": score.invocations,
        "trend": score.trend,
        "baseline": score.baseline,
        "suggestions": [
            {
                **suggestion,
                "evidence_sessions": score.evidence_sessions,
            }
            for suggestion in score.suggestions
        ],
        "commit_adoption_rate": score.commit_adoption_rate,
        "evidence_sessions": score.evidence_sessions,
    }


def build_output(
    report: dict[str, Any],
    report_source: str,
    baseline_data: dict[str, Any],
    baseline_status: dict[str, Any],
    scores: list[EntityScore],
) -> dict[str, Any]:
    agents = [entity_to_json(score) for score in scores if score.entity_type == "agent"]
    skills = [entity_to_json(score) for score in scores if score.entity_type == "skill"]
    orchestration = [entity_to_json(score) for score in scores if score.entity_type == "orchestration"]
    improvements = improvements_from_scores(scores)
    gap_analysis = gap_analysis_for_report(report)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now_iso(),
        "report_source": report_source,
        "input_summary": {
            "report_generated_at": report.get("generated_at"),
            "sessions_analyzed": report.get("sessions_analyzed", 0),
            "sessions_skipped": report.get("sessions_skipped", 0),
            "date_range": report.get("date_range"),
        },
        "baseline_status": baseline_status,
        "entities": {
            "agents": agents,
            "skills": skills,
            "orchestration": orchestration,
        },
        "scores": {
            "agents": agents,
            "skills": skills,
            "orchestration": orchestration,
        },
        "improvements": improvements,
        "gap_analysis": gap_analysis,
        "global_suggestions": [
            {
                "type": "improvement_candidate",
                "description": row["suggestion"],
                "priority": row["priority"],
                "entity_type": row["entity_type"],
                "entity_id": row["entity_id"],
                "evidence_pattern": row["reason"],
                "evidence_sessions": row["evidence_sessions"],
            }
            for row in improvements[:5]
        ],
        "diagnostics": {
            "baseline_entities": len(baseline_data.get("entities", {})) if isinstance(baseline_data.get("entities"), dict) else 0,
            "scored_entities": len(scores),
            "decay_half_life_days": baseline_status["decay_half_life_days"],
            "trend_threshold": baseline_status["trend_threshold"],
        },
    }


def print_text_report(output: dict[str, Any]) -> None:
    print(f"Performance Scorer report (schema v{output['schema_version']})")
    print(f"Generated at: {output['generated_at']}")
    print(f"Scored entities: {output['diagnostics']['scored_entities']}")
    print(f"Baseline: {output['baseline_status']['state']} ({output['baseline_status']['path']})")
    if output["improvements"]:
        print("Top improvements:")
        for row in output["improvements"][:5]:
            print(f"- {row['entity_type']}:{row['entity_id']} score={row['score']} priority={row['priority']}")
    else:
        print("Top improvements: none")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score HyperAgent performance from Session Analyzer JSON.")
    parser.add_argument("--input", help="Path to analysis-report.json. Omit to read JSON from stdin.")
    parser.add_argument("--report", help="Alias for --input, kept for API-CONTRACT compatibility.")
    parser.add_argument("--registry", default=str(REPO_ROOT / "agent-registry"), help="Agent registry root.")
    parser.add_argument("--skills", default=str(REPO_ROOT / "skills"), help="Skills directory root.")
    parser.add_argument("--baseline", default=DEFAULT_BASELINE_PATH, help="Baseline JSON path.")
    parser.add_argument("--json", action="store_true", help="Print structured JSON to stdout.")
    parser.add_argument("--baseline-min-sessions", type=int, default=DEFAULT_BASELINE_MIN_SESSIONS)
    parser.add_argument("--decay-half-life-days", type=int, default=DEFAULT_DECAY_HALF_LIFE_DAYS)
    parser.add_argument("--trend-threshold", type=float, default=DEFAULT_TREND_THRESHOLD)
    args = parser.parse_args(argv)
    if args.input and args.report:
        parser.error("--input and --report cannot be used together")
    if args.baseline_min_sessions < 1:
        parser.error("--baseline-min-sessions must be >= 1")
    if args.decay_half_life_days < 1:
        parser.error("--decay-half-life-days must be >= 1")
    if args.trend_threshold < 0:
        parser.error("--trend-threshold must be >= 0")
    return args


def run(argv: list[str]) -> int:
    args = parse_args(argv)
    validate_metadata_paths(expand_input_path(args.registry), expand_input_path(args.skills))
    report, report_source = load_report(args)
    validate_report(report)

    samples = build_samples(report)
    timestamps = [sample.timestamp for sample in samples if sample.timestamp is not None]
    reference_time = max(timestamps) if timestamps else datetime.now(timezone.utc)
    baseline_data, baseline_status = load_or_create_baseline(
        expand_input_path(args.baseline),
        samples,
        args.baseline_min_sessions,
        args.decay_half_life_days,
        args.trend_threshold,
    )
    scores = aggregate_entity_scores(
        samples,
        baseline_data,
        reference_time,
        args.decay_half_life_days,
        args.trend_threshold,
    )
    output = build_output(report, report_source, baseline_data, baseline_status, scores)
    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_text_report(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
