#!/usr/bin/env python3
"""
Deep Think — Session Utilities
Workspace initialization and report generation for Agent Teams workflow.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

PHASES = [
    {"id": "01-analysis", "name": "Problem Analysis", "emoji": "🔍"},
    {"id": "02-decomposition", "name": "Decomposition", "emoji": "🧩"},
    {"id": "03-paths", "name": "Multi-Path Exploration", "emoji": "🔀"},
    {"id": "04-verification", "name": "Verification", "emoji": "✅"},
    {"id": "05-synthesis", "name": "Synthesis", "emoji": "🧬"},
    {"id": "06-answer", "name": "Final Answer", "emoji": "💡"},
]


def init_session(workspace: str, question: str, complexity: str = "high") -> dict:
    """Initialize a new deep think workspace."""
    ws = Path(workspace)
    ws.mkdir(parents=True, exist_ok=True)

    session = {
        "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "question": question,
        "complexity": complexity,
        "workspace": str(ws),
        "created_at": datetime.now().isoformat(),
    }

    # Create phase directories
    for phase in PHASES:
        (ws / phase["id"]).mkdir(exist_ok=True)

    # Save session metadata
    with open(ws / "session.json", "w") as f:
        json.dump(session, f, indent=2, ensure_ascii=False)

    # Create initial question file
    with open(ws / "00-question.md", "w") as f:
        f.write(f"# Deep Think Session\n\n")
        f.write(f"**Question/Task:**\n\n{question}\n\n")
        f.write(f"**Complexity:** {complexity}\n")
        f.write(f"**Created:** {session['created_at']}\n")

    print(f"✅ Deep Think workspace initialized: {ws}")
    print(f"   Complexity: {complexity}")
    print(f"\nNext steps:")
    print(f"   1. Write analysis to {ws}/01-analysis/analysis.md")
    print(f"   2. Write decomposition to {ws}/02-decomposition/decomposition.md")
    print(f"   3. Spawn agent team (see SKILL.md)")
    return session


def generate_report(workspace: str) -> None:
    """Generate a summary report from completed session."""
    ws = Path(workspace)

    if not (ws / "session.json").exists():
        print(f"❌ No session found at {ws}")
        sys.exit(1)

    session = json.loads((ws / "session.json").read_text())

    report_lines = [
        "# 🧠 Deep Think — Session Report",
        "",
        f"**Question:** {session['question']}",
        f"**Complexity:** {session['complexity']}",
        f"**Created:** {session['created_at']}",
        "",
        "---",
        "",
    ]

    # Collect content from each phase
    for phase in PHASES:
        phase_dir = ws / phase["id"]
        if phase_dir.exists():
            md_files = sorted(phase_dir.glob("*.md"))
            if md_files:
                report_lines.append(f"## {phase['emoji']} {phase['name']}\n")
                for md_file in md_files:
                    content = md_file.read_text(encoding="utf-8").strip()
                    if content:
                        report_lines.append(f"### {md_file.name}\n")
                        report_lines.append(content)
                        report_lines.append("")

    report = "\n".join(report_lines)
    report_path = ws / "REPORT.md"
    report_path.write_text(report, encoding="utf-8")

    print(f"✅ Report generated: {report_path}")


def status(workspace: str) -> None:
    """Show workspace status."""
    ws = Path(workspace)

    if not (ws / "session.json").exists():
        print(f"❌ No session found at {ws}")
        sys.exit(1)

    session = json.loads((ws / "session.json").read_text())

    print(f"\n🧠 Deep Think Session")
    print(f"   Question: {session['question'][:80]}...")
    print(f"   Complexity: {session['complexity']}")
    print()

    for phase in PHASES:
        phase_dir = ws / phase["id"]
        if phase_dir.exists():
            files = list(phase_dir.glob("*.md"))
            if files:
                print(f"   ✅ {phase['name']}: {len(files)} file(s)")
            else:
                print(f"   ⬜ {phase['name']}: empty")
        else:
            print(f"   ⬜ {phase['name']}: not created")


def main():
    parser = argparse.ArgumentParser(description="Deep Think Session Utilities")
    sub = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = sub.add_parser("init", help="Initialize workspace")
    p_init.add_argument("question", help="The question or task")
    p_init.add_argument("--workspace", "-w", default=".deep-think")
    p_init.add_argument("--complexity", "-c",
                       choices=["low", "medium", "high", "extreme"],
                       default="high")

    # report
    p_report = sub.add_parser("report", help="Generate summary report")
    p_report.add_argument("--workspace", "-w", default=".deep-think")

    # status
    p_status = sub.add_parser("status", help="Show workspace status")
    p_status.add_argument("--workspace", "-w", default=".deep-think")

    args = parser.parse_args()

    if args.command == "init":
        init_session(args.workspace, args.question, args.complexity)
    elif args.command == "report":
        generate_report(args.workspace)
    elif args.command == "status":
        status(args.workspace)


if __name__ == "__main__":
    main()