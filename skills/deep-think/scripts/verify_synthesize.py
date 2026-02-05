#!/usr/bin/env python3
"""
Deep Think — Independent Verifier & Synthesizer
Spawns a fresh Claude agent to verify and synthesize multiple reasoning paths.
This agent has NO prior context about the paths — it sees them with fresh eyes.
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from textwrap import dedent


def build_verify_prompt(question: str, analysis: str, paths: list[dict]) -> str:
    """Build verification prompt with all paths included."""
    paths_block = ""
    for p in paths:
        paths_block += f"\n---\n## {p['name']}\n\n{p['content']}\n"

    return dedent(f"""\
    # Deep Think — Verification & Synthesis

    You are an independent verification agent. You are seeing these reasoning paths
    for the FIRST TIME. Your job is to:

    1. **Critically evaluate** each path for correctness, completeness, and quality
    2. **Find contradictions** between paths
    3. **Identify blind spots** that ALL paths missed
    4. **Play devil's advocate** against the strongest-looking path
    5. **Synthesize** the best elements into one optimal solution

    Be ruthlessly honest. If a path is wrong, say so. If all paths missed something, say so.

    ## Original Question
    {question}

    ## Problem Analysis
    {analysis}

    ## Reasoning Paths to Evaluate
    {paths_block}

    ---

    ## Your Output Format

    # Verification Report

    ## Path-by-Path Evaluation

    For each path, rate 1-5 on:
    - **Correctness**: Is the logic sound?
    - **Completeness**: Does it address the full problem?
    - **Practicality**: Is it implementable in the real world?
    - **Originality**: Does it bring unique value?

    [Evaluate each path]

    ## Contradictions Found
    [Where do paths disagree? Who is right and why?]

    ## Blind Spots
    [What did ALL paths miss?]

    ## Devil's Advocate
    [Strongest argument against the current best approach]

    ## Synthesized Solution

    ### The Best Answer
    [Combine the strongest elements from all paths into one coherent solution]

    ### What We Took From Each Path
    [Credit which ideas came from which paths]

    ### Trade-offs
    [What was sacrificed and why it's worth it]

    ### Remaining Uncertainty
    [What we still can't be sure about]

    ### Confidence: [low/medium/high]
    [Overall confidence in the synthesized answer]
    """)


def build_final_answer_prompt(question: str, synthesis: str) -> str:
    """Build the final answer generation prompt."""
    return dedent(f"""\
    # Deep Think — Final Answer Generation

    You have gone through a rigorous multi-path reasoning process. Below is the
    synthesized result from evaluating multiple independent reasoning paths.

    Your job: Write the **final, polished answer** to the user's original question.

    ## Original Question
    {question}

    ## Synthesized Analysis
    {synthesis}

    ## Output Format

    # Final Answer

    ## TL;DR
    [One-paragraph executive summary — the answer in a nutshell]

    ## Detailed Answer
    [Complete, well-structured, polished response. This is what the user reads.
     Include code, diagrams, architecture decisions, etc. as appropriate.
     Be thorough but not verbose.]

    ## Thought Process Summary
    [2-3 paragraph summary of HOW this conclusion was reached:
     - What perspectives were considered
     - Where they agreed/disagreed
     - What was verified and what edge cases were checked
     - Why this answer was chosen over alternatives
     This helps the user understand and trust the reasoning.]

    ## Confidence Level
    [Overall confidence + brief justification]
    """)


def run_agent(prompt: str, model: str = "", timeout: int = 600) -> str:
    """Run a single Claude agent and return its output."""
    cmd = ["claude", "-p", prompt, "--output-format", "text"]
    if model:
        cmd.extend(["--model", model])
    cmd.extend(["--max-turns", "1"])

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    if proc.returncode == 0 and proc.stdout.strip():
        return proc.stdout.strip()
    else:
        raise RuntimeError(f"Agent failed: {proc.stderr or 'empty output'}")


def run_verify_and_synthesize(workspace: str, model: str = "", skip_final: bool = False):
    """Run verification agent, then final answer agent."""
    ws = Path(workspace)

    # Load question
    session_file = ws / "session.json"
    question = ""
    if session_file.exists():
        session = json.loads(session_file.read_text())
        question = session.get("question", "")

    # Load analysis
    analysis_file = ws / "01-analysis" / "analysis.md"
    analysis = analysis_file.read_text(encoding="utf-8") if analysis_file.exists() else ""

    # Load all paths
    paths_dir = ws / "03-paths"
    path_files = sorted(paths_dir.glob("path-*.md"))
    if not path_files:
        print("❌ No path files found. Run parallel_paths.py first.")
        sys.exit(1)

    paths = []
    for pf in path_files:
        content = pf.read_text(encoding="utf-8").strip()
        if content and not content.startswith("# ❌") and not content.startswith("# ⏰"):
            paths.append({"name": pf.stem, "content": content})

    if not paths:
        print("❌ No valid path outputs found.")
        sys.exit(1)

    print(f"\n🔍 Starting independent verification of {len(paths)} paths...")

    # Phase 4+5: Verification & Synthesis (combined in one agent for efficiency)
    verify_prompt = build_verify_prompt(question, analysis, paths)

    start = time.time()
    try:
        verify_output = run_agent(verify_prompt, model=model, timeout=600)
    except Exception as e:
        print(f"❌ Verification agent failed: {e}")
        sys.exit(1)

    elapsed = time.time() - start
    print(f"   ✅ Verification complete ({elapsed:.1f}s)")

    # Save verification + synthesis
    verify_dir = ws / "04-verification"
    verify_dir.mkdir(exist_ok=True)
    (verify_dir / "verification.md").write_text(verify_output, encoding="utf-8")

    synth_dir = ws / "05-synthesis"
    synth_dir.mkdir(exist_ok=True)
    (synth_dir / "synthesis.md").write_text(verify_output, encoding="utf-8")

    if skip_final:
        print("   ⏭️  Skipping final answer generation (--skip-final)")
        return

    # Phase 6: Final Answer (another fresh agent)
    print(f"\n💡 Generating final answer...")

    final_prompt = build_final_answer_prompt(question, verify_output)

    start = time.time()
    try:
        final_output = run_agent(final_prompt, model=model, timeout=600)
    except Exception as e:
        print(f"❌ Final answer agent failed: {e}")
        sys.exit(1)

    elapsed = time.time() - start
    print(f"   ✅ Final answer complete ({elapsed:.1f}s)")

    answer_dir = ws / "06-answer"
    answer_dir.mkdir(exist_ok=True)
    (answer_dir / "answer.md").write_text(final_output, encoding="utf-8")

    print(f"\n🧠 Done! Final answer: {answer_dir / 'answer.md'}")


def main():
    parser = argparse.ArgumentParser(description="Deep Think Verifier & Synthesizer")
    parser.add_argument("--workspace", "-w", default=".deep-think")
    parser.add_argument("--model", "-m", default="", help="Model override")
    parser.add_argument("--skip-final", action="store_true", help="Only verify, don't generate final answer")
    args = parser.parse_args()

    run_verify_and_synthesize(args.workspace, model=args.model, skip_final=args.skip_final)


if __name__ == "__main__":
    main()