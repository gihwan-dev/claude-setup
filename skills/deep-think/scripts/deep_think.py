#!/usr/bin/env python3
"""
Deep Think Session Orchestrator
Manages structured multi-phase reasoning sessions.
Creates workspace, tracks phases, measures time, and produces final output.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

PHASES = [
    {"id": "01-analysis", "name": "Problem Analysis", "emoji": "🔍"},
    {"id": "02-decomposition", "name": "Decomposition", "emoji": "🧩"},
    {"id": "03-paths", "name": "Multi-Path Exploration", "emoji": "🔀"},
    {"id": "04-verification", "name": "Self-Verification", "emoji": "✅"},
    {"id": "05-synthesis", "name": "Synthesis", "emoji": "🧬"},
    {"id": "06-answer", "name": "Final Answer", "emoji": "💡"},
]

COMPLEXITY_LEVELS = {
    "low": {"description": "Simple factual or straightforward task", "target_paths": 2, "depth": "shallow"},
    "medium": {"description": "Multi-step reasoning or moderate complexity", "target_paths": 3, "depth": "moderate"},
    "high": {"description": "Complex architecture, debugging, or multi-domain", "target_paths": 4, "depth": "deep"},
    "extreme": {"description": "Novel problem requiring creative multi-angle approach", "target_paths": 5, "depth": "exhaustive"},
}


def init_session(workspace: str, question: str, complexity: str = "auto") -> dict:
    """Initialize a new deep think session."""
    ws = Path(workspace)
    ws.mkdir(parents=True, exist_ok=True)

    session = {
        "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "question": question,
        "complexity": complexity,
        "workspace": str(ws),
        "started_at": datetime.now().isoformat(),
        "phases": {},
        "status": "initialized",
    }

    # Create phase directories
    for phase in PHASES:
        phase_dir = ws / phase["id"]
        phase_dir.mkdir(exist_ok=True)

    # Save session metadata
    with open(ws / "session.json", "w") as f:
        json.dump(session, f, indent=2, ensure_ascii=False)

    # Create initial prompt file for analysis phase
    with open(ws / "00-question.md", "w") as f:
        f.write(f"# Deep Think Session\n\n")
        f.write(f"**Question/Task:**\n\n{question}\n\n")
        f.write(f"**Complexity:** {complexity}\n")
        f.write(f"**Started:** {session['started_at']}\n")

    print(f"✅ Deep Think session initialized: {ws}")
    print(f"   Session ID: {session['id']}")
    print(f"   Complexity: {complexity}")
    print(f"   Workspace: {ws}")
    return session


def start_phase(workspace: str, phase_id: str) -> None:
    """Mark a phase as started."""
    ws = Path(workspace)
    session = _load_session(ws)

    phase_info = next((p for p in PHASES if p["id"] == phase_id), None)
    if not phase_info:
        print(f"❌ Unknown phase: {phase_id}")
        sys.exit(1)

    session["phases"][phase_id] = {
        "started_at": datetime.now().isoformat(),
        "status": "in_progress",
    }
    session["status"] = f"phase:{phase_id}"
    _save_session(ws, session)

    print(f"\n{phase_info['emoji']} Phase: {phase_info['name']} — started")


def end_phase(workspace: str, phase_id: str) -> None:
    """Mark a phase as completed and report elapsed time."""
    ws = Path(workspace)
    session = _load_session(ws)

    if phase_id not in session["phases"]:
        print(f"⚠️  Phase {phase_id} was not started, marking complete anyway")
        session["phases"][phase_id] = {"started_at": datetime.now().isoformat()}

    started = datetime.fromisoformat(session["phases"][phase_id]["started_at"])
    elapsed = (datetime.now() - started).total_seconds()

    session["phases"][phase_id]["ended_at"] = datetime.now().isoformat()
    session["phases"][phase_id]["elapsed_seconds"] = elapsed
    session["phases"][phase_id]["status"] = "completed"
    _save_session(ws, session)

    phase_info = next((p for p in PHASES if p["id"] == phase_id), None)
    name = phase_info["name"] if phase_info else phase_id
    print(f"   ✅ {name} completed ({elapsed:.1f}s)")


def finalize(workspace: str) -> None:
    """Finalize the session and produce a summary report."""
    ws = Path(workspace)
    session = _load_session(ws)

    session["ended_at"] = datetime.now().isoformat()
    started = datetime.fromisoformat(session["started_at"])
    total_elapsed = (datetime.now() - started).total_seconds()
    session["total_elapsed_seconds"] = total_elapsed
    session["status"] = "completed"
    _save_session(ws, session)

    # Build summary report
    report_lines = [
        "# 🧠 Deep Think — Session Report",
        "",
        f"**Question:** {session['question']}",
        f"**Complexity:** {session['complexity']}",
        f"**Total Time:** {_format_time(total_elapsed)}",
        "",
        "## Phase Timeline",
        "",
    ]

    for phase in PHASES:
        pid = phase["id"]
        if pid in session["phases"]:
            p = session["phases"][pid]
            elapsed = p.get("elapsed_seconds", 0)
            status = "✅" if p.get("status") == "completed" else "⏳"
            report_lines.append(
                f"- {status} **{phase['name']}**: {_format_time(elapsed)}"
            )
        else:
            report_lines.append(f"- ⏭️ **{phase['name']}**: skipped")

    report_lines.extend(["", "---", ""])

    # Collect content from each phase
    report_lines.append("## Thinking Artifacts\n")
    for phase in PHASES:
        phase_dir = ws / phase["id"]
        if phase_dir.exists():
            md_files = sorted(phase_dir.glob("*.md"))
            if md_files:
                report_lines.append(f"### {phase['emoji']} {phase['name']}\n")
                for md_file in md_files:
                    content = md_file.read_text(encoding="utf-8").strip()
                    if content:
                        report_lines.append(content)
                        report_lines.append("")

    report = "\n".join(report_lines)
    report_path = ws / "REPORT.md"
    report_path.write_text(report, encoding="utf-8")

    print(f"\n🧠 Deep Think session completed!")
    print(f"   Total time: {_format_time(total_elapsed)}")
    print(f"   Report: {report_path}")


def status(workspace: str) -> None:
    """Print current session status."""
    ws = Path(workspace)
    session = _load_session(ws)

    print(f"\n🧠 Deep Think Session Status")
    print(f"   Question: {session['question'][:80]}...")
    print(f"   Status: {session['status']}")
    print(f"   Complexity: {session['complexity']}")

    for phase in PHASES:
        pid = phase["id"]
        if pid in session["phases"]:
            p = session["phases"][pid]
            elapsed = p.get("elapsed_seconds", "...")
            status_icon = "✅" if p.get("status") == "completed" else "⏳"
            print(f"   {status_icon} {phase['name']}: {elapsed}s")
        else:
            print(f"   ⬜ {phase['name']}")


def _load_session(ws: Path) -> dict:
    session_file = ws / "session.json"
    if not session_file.exists():
        print(f"❌ No session found at {ws}")
        sys.exit(1)
    with open(session_file) as f:
        return json.load(f)


def _save_session(ws: Path, session: dict) -> None:
    with open(ws / "session.json", "w") as f:
        json.dump(session, f, indent=2, ensure_ascii=False)


def _format_time(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}m {secs:.0f}s"


def main():
    parser = argparse.ArgumentParser(description="Deep Think Session Orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = sub.add_parser("init", help="Initialize a new session")
    p_init.add_argument("question", help="The question or task to think deeply about")
    p_init.add_argument("--workspace", "-w", default=".deep-think", help="Workspace directory")
    p_init.add_argument("--complexity", "-c", choices=["auto", "low", "medium", "high", "extreme"], default="auto")

    # start-phase
    p_start = sub.add_parser("start-phase", help="Start a phase")
    p_start.add_argument("phase_id", choices=[p["id"] for p in PHASES])
    p_start.add_argument("--workspace", "-w", default=".deep-think")

    # end-phase
    p_end = sub.add_parser("end-phase", help="End a phase")
    p_end.add_argument("phase_id", choices=[p["id"] for p in PHASES])
    p_end.add_argument("--workspace", "-w", default=".deep-think")

    # finalize
    p_fin = sub.add_parser("finalize", help="Finalize session and generate report")
    p_fin.add_argument("--workspace", "-w", default=".deep-think")

    # status
    p_status = sub.add_parser("status", help="Show session status")
    p_status.add_argument("--workspace", "-w", default=".deep-think")

    args = parser.parse_args()

    if args.command == "init":
        init_session(args.workspace, args.question, args.complexity)
    elif args.command == "start-phase":
        start_phase(args.workspace, args.phase_id)
    elif args.command == "end-phase":
        end_phase(args.workspace, args.phase_id)
    elif args.command == "finalize":
        finalize(args.workspace)
    elif args.command == "status":
        status(args.workspace)


if __name__ == "__main__":
    main()