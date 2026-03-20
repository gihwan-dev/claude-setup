#!/usr/bin/env python3
"""Extract activity for a target date from AI agent history.jsonl and collect
git logs from each project directory, then print the result as structured text."""

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

KST = timezone(timedelta(hours=9))
HISTORY_FILE = Path(os.environ.get("AGENT_HISTORY_FILE", str(Path.home() / ".claude" / "history.jsonl")))
SKIP_PREFIXES = ("/clear", "/compact")
MIN_DISPLAY_LENGTH = 10
MAX_ITEMS_PER_PROJECT = 15


def parse_args():
    parser = argparse.ArgumentParser(description="Extract AI agent daily activity")
    parser.add_argument(
        "--date",
        type=str,
        default=datetime.now(KST).strftime("%Y-%m-%d"),
        help="Target date in YYYY-MM-DD format (default: today)",
    )
    return parser.parse_args()


def parse_history(target_date: str) -> dict[str, list[dict]]:
    """Stream-parse history.jsonl and group requests by date and project."""
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

            # Filters: /clear, /compact, shorter than the minimum display length
            if any(display.strip().startswith(p) for p in SKIP_PREFIXES):
                continue
            if len(display.strip()) < MIN_DISPLAY_LENGTH:
                continue

            # Convert the timestamp into a KST date
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

    # Sort chronologically
    for name in projects:
        projects[name].sort(key=lambda x: x["time"])

    return projects


def get_git_log(project_path: str, target_date: str) -> list[str]:
    """Return the git commits for the target date from a project directory."""
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
    """Format project activity into structured text."""
    if not projects:
        return "No activity"

    sections = []

    for project_name, entries in sorted(projects.items()):
        project_path = entries[0]["project_path"]
        time_range = f"{entries[0]['time']} - {entries[-1]['time']}"

        lines = [f"## {project_name} ({time_range})"]

        # User requests
        lines.append("### User Requests")
        display_entries = entries[:MAX_ITEMS_PER_PROJECT]
        for e in display_entries:
            lines.append(f"- {e['time']}: {e['display']}")
        if len(entries) > MAX_ITEMS_PER_PROJECT:
            lines.append(f"- ... and {len(entries) - MAX_ITEMS_PER_PROJECT} more")

        # Git Commits
        commits = get_git_log(project_path, target_date)
        if commits:
            lines.append("### Git Commits")
            for c in commits[:MAX_ITEMS_PER_PROJECT]:
                lines.append(f"- {c}")
            if len(commits) > MAX_ITEMS_PER_PROJECT:
                lines.append(f"- ... and {len(commits) - MAX_ITEMS_PER_PROJECT} more")

        sections.append("\n".join(lines))

    return "\n\n".join(sections)


def main():
    args = parse_args()
    target_date = args.date

    # Validate date format
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
