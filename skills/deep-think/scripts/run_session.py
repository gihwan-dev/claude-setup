#!/usr/bin/env python3
"""
Deep Think — Full Session Runner
Orchestrates a complete deep think session end-to-end.

Usage:
  python scripts/run_session.py "Your complex question here" [options]

This is the simplest way to run a full deep think session.
The orchestrator (parent Claude) handles Phase 1-2, then delegates
Phase 3-6 to independent sub-agents.
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Import sibling scripts
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from deep_think import init_session, start_phase, end_phase, finalize
from parallel_paths import run_parallel_paths
from verify_synthesize import run_verify_and_synthesize


COMPLEXITY_TO_PATHS = {
    "low": 2,
    "medium": 3,
    "high": 4,
    "extreme": 5,
}


def run_full_session(
    question: str,
    complexity: str = "high",
    workspace: str = ".deep-think",
    model: str = "",
    extra_context: str = "",
    num_paths: int = 0,
):
    """Run a complete deep think session."""
    print("=" * 60)
    print("🧠 DEEP THINK SESSION")
    print("=" * 60)
    print(f"\n📝 Question: {question[:100]}{'...' if len(question) > 100 else ''}")
    print(f"⚙️  Complexity: {complexity}")
    print()

    total_start = time.time()

    # Initialize
    init_session(workspace, question, complexity)

    # Determine number of paths
    n_paths = num_paths or COMPLEXITY_TO_PATHS.get(complexity, 3)

    # ── Phase 1 & 2: Analysis & Decomposition ──
    # These are done by the PARENT agent (the Claude that invokes this script).
    # The parent should write analysis.md and decomposition.md BEFORE calling
    # parallel paths. But if this script is run standalone, we note that.
    print("\n" + "─" * 40)
    print("📋 Phase 1-2: Analysis & Decomposition")
    print("─" * 40)
    print("   ℹ️  These phases should be completed by the orchestrator agent")
    print("   ℹ️  before running parallel paths.")

    ws = Path(workspace)
    analysis_exists = (ws / "01-analysis" / "analysis.md").exists()
    decomp_exists = (ws / "02-decomposition" / "decomposition.md").exists()

    if not analysis_exists:
        print("   ⚠️  No analysis.md found — sub-agents will work without it")
    else:
        print("   ✅ analysis.md found")

    if not decomp_exists:
        print("   ⚠️  No decomposition.md found — sub-agents will work without it")
    else:
        print("   ✅ decomposition.md found")

    # ── Phase 3: Parallel Path Exploration ──
    print("\n" + "─" * 40)
    print(f"🔀 Phase 3: Parallel Path Exploration ({n_paths} agents)")
    print("─" * 40)

    start_phase(workspace, "03-paths")
    results = run_parallel_paths(
        workspace=workspace,
        num_paths=n_paths,
        model=model,
        extra_context=extra_context,
    )
    end_phase(workspace, "03-paths")

    success_count = sum(1 for r in results if r["success"])
    if success_count == 0:
        print("\n❌ All agents failed. Cannot continue.")
        sys.exit(1)

    # ── Phase 4-6: Verify, Synthesize, Final Answer ──
    print("\n" + "─" * 40)
    print("🔍 Phase 4-6: Verification → Synthesis → Final Answer")
    print("─" * 40)

    start_phase(workspace, "04-verification")
    run_verify_and_synthesize(workspace=workspace, model=model)
    end_phase(workspace, "04-verification")

    # Mark remaining phases as tracked
    start_phase(workspace, "05-synthesis")
    end_phase(workspace, "05-synthesis")
    start_phase(workspace, "06-answer")
    end_phase(workspace, "06-answer")

    # ── Finalize ──
    finalize(workspace)

    total_elapsed = time.time() - total_start

    # ── Summary ──
    print("\n" + "=" * 60)
    print("🧠 DEEP THINK COMPLETE")
    print("=" * 60)
    print(f"   ⏱️  Total wall time: {total_elapsed:.1f}s")
    print(f"   🤖 Agents used: {n_paths} path + 1 verifier + 1 final = {n_paths + 2}")
    print(f"   📁 Workspace: {workspace}")
    print(f"   📄 Report: {workspace}/REPORT.md")
    print(f"   💡 Answer: {workspace}/06-answer/answer.md")


def main():
    parser = argparse.ArgumentParser(
        description="Run a complete Deep Think session",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_session.py "Design a caching strategy for our API"
  python scripts/run_session.py "Debug this race condition" -c extreme -n 5
  python scripts/run_session.py "Optimize React rendering" -c high --context ./code.tsx
        """,
    )
    parser.add_argument("question", help="The question or task to think deeply about")
    parser.add_argument("--complexity", "-c", choices=["low", "medium", "high", "extreme"], default="high")
    parser.add_argument("--workspace", "-w", default=".deep-think")
    parser.add_argument("--model", "-m", default="", help="Model override for sub-agents")
    parser.add_argument("--paths", "-n", type=int, default=0, help="Override number of paths (default: auto from complexity)")
    parser.add_argument("--context", default="", help="Extra context file or string")

    args = parser.parse_args()

    extra = ""
    if args.context:
        ctx_path = Path(args.context)
        if ctx_path.exists():
            extra = ctx_path.read_text(encoding="utf-8")
        else:
            extra = args.context

    run_full_session(
        question=args.question,
        complexity=args.complexity,
        workspace=args.workspace,
        model=args.model,
        extra_context=extra,
        num_paths=args.paths,
    )


if __name__ == "__main__":
    main()