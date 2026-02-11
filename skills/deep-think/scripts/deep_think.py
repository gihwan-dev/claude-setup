#!/usr/bin/env python3
"""
Deep Think v2 — Session Utilities
Workspace initialization and report generation with adaptive tier system,
section-based validation, and evidence quality tracking.
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

PHASES = [
    {"id": "00-triage", "name": "Triage & Frame", "emoji": "🎯", "required_sections": ["Problem Frame", "Tier"]},
    {"id": "01-analysis", "name": "Problem Analysis", "emoji": "🔍", "required_sections": ["Original Question", "Why This Is Hard", "Constraints"]},
    {"id": "02-decomposition", "name": "Decomposition", "emoji": "🧩", "required_sections": ["Sub-Problems", "Attack Plan"]},
    {"id": "03-paths", "name": "Parallel Paths", "emoji": "🔀", "required_sections": ["Core Thesis", "Evidence Chain", "Implementation Sequence", "Risk Register", "What This Path Uniquely Offers"]},
    {"id": "03.5-challenges", "name": "Targeted Critique", "emoji": "⚔️", "required_sections": ["Findings", "Overall Rating"]},
    {"id": "04-synthesis", "name": "3-Pass Synthesis", "emoji": "🧬", "required_sections": []},
    {"id": "05-answer", "name": "Final Answer", "emoji": "💡", "required_sections": ["Confidence Assessment", "TL;DR"]},
]

COMPLEXITY_CONFIG = {
    "tier1": {"teammates": 2, "expected_time": "5-10 min", "personas": ["pragmatist", "domain-specialist"]},
    "tier2": {"teammates": 3, "expected_time": "10-20 min", "personas": ["pragmatist", "first-principles", "adversarial"]},
    "tier3": {"teammates": 5, "expected_time": "20-40 min", "personas": ["pragmatist", "first-principles", "adversarial", "optimizer", "domain-specialist"]},
}


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def check_sections(content: str, required_sections: list[str]) -> list[str]:
    """Check which required sections are present in the content.
    Returns list of missing sections.
    """
    missing = []
    for section in required_sections:
        # Check for section as markdown header (## or ###) or bold text
        pattern = rf"(#{{1,4}}\s+.*{re.escape(section)}|^\*\*{re.escape(section)})"
        if not re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
            missing.append(section)
    return missing


def init_session(workspace: str, question: str, complexity: str = "tier2") -> dict:
    """Initialize a new deep think workspace."""
    ws = Path(workspace)
    ws.mkdir(parents=True, exist_ok=True)

    config = COMPLEXITY_CONFIG.get(complexity, COMPLEXITY_CONFIG["tier2"])

    session = {
        "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "question": question,
        "tier": complexity,
        "workspace": str(ws),
        "created_at": datetime.now().isoformat(),
        "config": config,
    }

    # Create all phase directories
    for phase in PHASES:
        (ws / phase["id"]).mkdir(exist_ok=True)

    # Save session metadata
    with open(ws / "session.json", "w") as f:
        json.dump(session, f, indent=2, ensure_ascii=False)

    # Create initial question file
    with open(ws / "00-question.md", "w") as f:
        f.write("# Deep Think v2 Session\n\n")
        f.write(f"**Question/Task:**\n\n{question}\n\n")
        f.write(f"**Tier:** {tier}\n")
        f.write(f"**Teammates:** {config['teammates']}\n")
        f.write(f"**Personas:** {', '.join(config['personas'])}\n")
        f.write(f"**Expected time:** {config['expected_time']}\n")
        f.write(f"**Created:** {session['created_at']}\n")

    print(f"✅ Deep Think v2 workspace initialized: {ws}")
    print(f"   Tier: {tier}")
    print(f"   Teammates: {config['teammates']}")
    print(f"   Personas: {', '.join(config['personas'])}")
    print(f"   Expected time: {config['expected_time']}")
    print(f"\n📋 Next steps:")
    print(f"   1. Write triage & frame to {ws}/00-triage/frame.md")
    print(f"   2. Write analysis to {ws}/01-analysis/analysis.md")
    print(f"   3. Write decomposition to {ws}/02-decomposition/decomposition.md")
    print(f"   4. Spawn agent team per tier (see SKILL.md)")
    print(f"   5. Run convergence check after paths complete")
    return session


def generate_report(workspace: str) -> None:
    """Generate a summary report from completed session."""
    ws = Path(workspace)

    if not (ws / "session.json").exists():
        print(f"❌ No session found at {ws}")
        sys.exit(1)

    session = json.loads((ws / "session.json").read_text())

    report_lines = [
        "# 🧠 Deep Think v2 — Session Report",
        "",
        f"**Question:** {session['question']}",
        f"**Tier:** {session.get('tier', 'unknown')}",
        f"**Created:** {session['created_at']}",
        "",
    ]

    # Section completeness summary
    report_lines.append("## 📊 Section Completeness\n")
    for phase in PHASES:
        phase_dir = ws / phase["id"]
        if phase_dir.exists():
            md_files = list(phase_dir.glob("*.md"))
            if md_files:
                phase_words = sum(count_words(f.read_text(encoding="utf-8")) for f in md_files)
                # Check required sections
                all_missing = []
                for md_file in md_files:
                    content = md_file.read_text(encoding="utf-8")
                    missing = check_sections(content, phase.get("required_sections", []))
                    all_missing.extend(missing)
                status = "✅" if not all_missing else "⚠️"
                report_lines.append(f"- {status} **{phase['name']}**: {len(md_files)} file(s), {phase_words} words")
                if all_missing:
                    report_lines.append(f"  Missing sections: {', '.join(set(all_missing))}")
            else:
                report_lines.append(f"- ⬜ **{phase['name']}**: empty")
        else:
            report_lines.append(f"- ⬜ **{phase['name']}**: not created")

    report_lines.append("\n---\n")

    # Evidence quality summary
    report_lines.append("## 📋 Evidence Quality Summary\n")
    paths_dir = ws / "03-paths"
    if paths_dir.exists():
        evidence_counts = {"CODE": 0, "BENCH": 0, "PATTERN": 0, "REASON": 0, "ASSUME": 0}
        for pf in paths_dir.glob("path-*.md"):
            content = pf.read_text(encoding="utf-8")
            for tag in evidence_counts:
                evidence_counts[tag] += len(re.findall(rf"\[{tag}\]", content))
        total = sum(evidence_counts.values())
        if total > 0:
            for tag, count in evidence_counts.items():
                pct = round(count / total * 100)
                report_lines.append(f"- [{tag}]: {count} ({pct}%)")
            assume_pct = round(evidence_counts["ASSUME"] / total * 100) if total else 0
            if assume_pct > 30:
                report_lines.append(f"\n⚠️ High assumption rate ({assume_pct}%) — consider gathering more evidence")
        else:
            report_lines.append("- No evidence tags found in paths")
    report_lines.append("")

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
                        words = count_words(content)
                        report_lines.append(f"### {md_file.name} ({words} words)\n")
                        report_lines.append(content)
                        report_lines.append("")

    report = "\n".join(report_lines)
    report_path = ws / "REPORT.md"
    report_path.write_text(report, encoding="utf-8")

    print(f"✅ Report generated: {report_path}")


def status(workspace: str) -> None:
    """Show workspace status with section completeness."""
    ws = Path(workspace)

    if not (ws / "session.json").exists():
        print(f"❌ No session found at {ws}")
        sys.exit(1)

    session = json.loads((ws / "session.json").read_text())
    config = session.get("config", {})

    print(f"\n🧠 Deep Think v2 Session")
    print(f"   Question: {session['question'][:60]}...")
    print(f"   Tier: {session.get('tier', 'unknown')}")
    print(f"   Expected time: {config.get('expected_time', 'unknown')}")
    print()

    for phase in PHASES:
        phase_dir = ws / phase["id"]
        if phase_dir.exists():
            files = list(phase_dir.glob("*.md"))
            if files:
                phase_words = sum(count_words(f.read_text(encoding="utf-8")) for f in files)
                # Check sections
                all_missing = []
                for f in files:
                    missing = check_sections(f.read_text(encoding="utf-8"), phase.get("required_sections", []))
                    all_missing.extend(missing)
                status_icon = "✅" if not all_missing else "⚠️"
                print(f"   {status_icon} {phase['name']}: {len(files)} file(s), {phase_words} words")
                if all_missing:
                    print(f"      Missing: {', '.join(set(all_missing))}")
            else:
                print(f"   ⬜ {phase['name']}: empty")
        else:
            print(f"   ⬜ {phase['name']}: not created")


def validate(workspace: str) -> None:
    """Validate that all phases have required sections."""
    ws = Path(workspace)

    if not (ws / "session.json").exists():
        print(f"❌ No session found at {ws}")
        sys.exit(1)

    session = json.loads((ws / "session.json").read_text())

    print(f"\n🔍 Validating Deep Think v2 session...\n")

    issues = []

    # Check triage
    frame_file = ws / "00-triage" / "frame.md"
    if frame_file.exists():
        content = frame_file.read_text(encoding="utf-8")
        missing = check_sections(content, ["Problem Frame", "Tier"])
        if missing:
            issues.append(f"Triage missing sections: {', '.join(missing)}")
    else:
        issues.append("Missing: 00-triage/frame.md")

    # Check analysis
    analysis_file = ws / "01-analysis" / "analysis.md"
    if analysis_file.exists():
        content = analysis_file.read_text(encoding="utf-8")
        missing = check_sections(content, ["Original Question", "Why This Is Hard"])
        if missing:
            issues.append(f"Analysis missing sections: {', '.join(missing)}")
    else:
        issues.append("Missing: 01-analysis/analysis.md")

    # Check paths — required sections
    paths_dir = ws / "03-paths"
    required_path_sections = ["Core Thesis", "Evidence Chain", "Implementation Sequence", "Risk Register"]
    if paths_dir.exists():
        path_files = list(paths_dir.glob("path-*.md"))
        if not path_files:
            issues.append("No path files found in 03-paths/")
        for pf in path_files:
            if "-reflected" in pf.name:
                continue  # Reflected paths have different structure
            content = pf.read_text(encoding="utf-8")
            missing = check_sections(content, required_path_sections)
            if missing:
                issues.append(f"{pf.name} missing sections: {', '.join(missing)}")
            # Check for evidence tags
            has_evidence = bool(re.search(r"\[(CODE|BENCH|PATTERN|REASON|ASSUME)\]", content))
            if not has_evidence:
                issues.append(f"{pf.name}: no evidence tags found (need [CODE], [BENCH], [PATTERN], [REASON], or [ASSUME])")
    else:
        issues.append("Missing: 03-paths directory")

    # Check challenges
    challenges_dir = ws / "03.5-challenges"
    if challenges_dir.exists():
        challenge_files = list(challenges_dir.glob("critique-*.md"))
        for cf in challenge_files:
            content = cf.read_text(encoding="utf-8")
            missing = check_sections(content, ["Findings", "Overall Rating"])
            if missing:
                issues.append(f"{cf.name} missing sections: {', '.join(missing)}")
    # Challenges may be skipped due to convergence — not always an error

    # Check final answer
    answer_file = ws / "05-answer" / "answer.md"
    if answer_file.exists():
        content = answer_file.read_text(encoding="utf-8")
        missing = check_sections(content, ["Confidence Assessment", "TL;DR"])
        if missing:
            issues.append(f"Final answer missing sections: {', '.join(missing)}")
    else:
        issues.append("Missing: 05-answer/answer.md")

    if issues:
        print("❌ Issues found:\n")
        for issue in issues:
            print(f"   • {issue}")
        print()
        sys.exit(1)
    else:
        print("✅ All validations passed!")


def main():
    parser = argparse.ArgumentParser(description="Deep Think v2 Session Utilities")
    sub = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = sub.add_parser("init", help="Initialize workspace")
    p_init.add_argument("question", help="The question or task")
    p_init.add_argument("--workspace", "-w", default=".deep-think")
    p_init.add_argument("--complexity", "-c",
                       choices=["tier1", "tier2", "tier3"],
                       default="tier2")

    # report
    p_report = sub.add_parser("report", help="Generate summary report")
    p_report.add_argument("--workspace", "-w", default=".deep-think")

    # status
    p_status = sub.add_parser("status", help="Show workspace status")
    p_status.add_argument("--workspace", "-w", default=".deep-think")

    # validate
    p_validate = sub.add_parser("validate", help="Validate required sections")
    p_validate.add_argument("--workspace", "-w", default=".deep-think")

    args = parser.parse_args()

    if args.command == "init":
        init_session(args.workspace, args.question, args.complexity)
    elif args.command == "report":
        generate_report(args.workspace)
    elif args.command == "status":
        status(args.workspace)
    elif args.command == "validate":
        validate(args.workspace)


if __name__ == "__main__":
    main()
