#!/usr/bin/env python3
"""Claude Code history.jsonl에서 특정 날짜의 활동을 추출하고,
각 프로젝트 디렉토리의 git log를 수집하여 구조화된 텍스트로 출력한다."""

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

KST = timezone(timedelta(hours=9))
HISTORY_FILE = Path.home() / ".claude" / "history.jsonl"
SKIP_PREFIXES = ("/clear", "/compact")
MIN_DISPLAY_LENGTH = 10
MAX_ITEMS_PER_PROJECT = 15


def parse_args():
    parser = argparse.ArgumentParser(description="Extract Claude Code daily activity")
    parser.add_argument(
        "--date",
        type=str,
        default=datetime.now(KST).strftime("%Y-%m-%d"),
        help="Target date in YYYY-MM-DD format (default: today)",
    )
    return parser.parse_args()


def parse_history(target_date: str) -> dict[str, list[dict]]:
    """history.jsonl을 스트리밍 파싱하여 날짜별 프로젝트별 요청을 그룹화한다."""
    projects = defaultdict(list)

    if not HISTORY_FILE.exists():
        print(f"# history.jsonl not found: {HISTORY_FILE}", file=sys.stderr)
        return projects

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            display = entry.get("display", "")
            timestamp_ms = entry.get("timestamp")
            project = entry.get("project", "")

            if not display or not timestamp_ms or not project:
                continue

            # 필터: /clear, /compact, 10자 미만
            if any(display.strip().startswith(p) for p in SKIP_PREFIXES):
                continue
            if len(display.strip()) < MIN_DISPLAY_LENGTH:
                continue

            # 타임스탬프 → KST 날짜 변환
            dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=KST)
            if dt.strftime("%Y-%m-%d") != target_date:
                continue

            project_name = Path(project).name
            projects[project_name].append(
                {
                    "time": dt.strftime("%H:%M"),
                    "display": display.strip().split("\n")[0][:120],
                    "project_path": project,
                }
            )

    # 시간순 정렬
    for name in projects:
        projects[name].sort(key=lambda x: x["time"])

    return projects


def get_git_log(project_path: str, target_date: str) -> list[str]:
    """프로젝트 디렉토리에서 해당 날짜의 git commit 목록을 가져온다."""
    if not os.path.isdir(project_path):
        return []

    try:
        result = subprocess.run(
            [
                "git",
                "log",
                f"--since={target_date} 00:00:00",
                f"--until={target_date} 23:59:59",
                "--oneline",
                "--no-merges",
            ],
            capture_output=True,
            text=True,
            cwd=project_path,
            timeout=10,
        )
        if result.returncode != 0:
            return []
        lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
        return lines
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return []


def format_output(projects: dict[str, list[dict]], target_date: str) -> str:
    """프로젝트별 활동을 구조화된 텍스트로 포매팅한다."""
    if not projects:
        return "활동 없음"

    sections = []

    for project_name, entries in sorted(projects.items()):
        project_path = entries[0]["project_path"]
        time_range = f"{entries[0]['time']} - {entries[-1]['time']}"

        lines = [f"## {project_name} ({time_range})"]

        # 사용자 요청
        lines.append("### 사용자 요청")
        display_entries = entries[:MAX_ITEMS_PER_PROJECT]
        for e in display_entries:
            lines.append(f"- {e['time']}: {e['display']}")
        if len(entries) > MAX_ITEMS_PER_PROJECT:
            lines.append(f"- ... 외 {len(entries) - MAX_ITEMS_PER_PROJECT}건")

        # Git Commits
        commits = get_git_log(project_path, target_date)
        if commits:
            lines.append("### Git Commits")
            for c in commits[:MAX_ITEMS_PER_PROJECT]:
                lines.append(f"- {c}")
            if len(commits) > MAX_ITEMS_PER_PROJECT:
                lines.append(f"- ... 외 {len(commits) - MAX_ITEMS_PER_PROJECT}건")

        sections.append("\n".join(lines))

    return "\n\n".join(sections)


def main():
    args = parse_args()
    target_date = args.date

    # 날짜 형식 검증
    try:
        datetime.strptime(target_date, "%Y-%m-%d")
    except ValueError:
        print(f"Error: Invalid date format '{target_date}'. Use YYYY-MM-DD.", file=sys.stderr)
        sys.exit(1)

    projects = parse_history(target_date)
    output = format_output(projects, target_date)
    print(output)


if __name__ == "__main__":
    main()
