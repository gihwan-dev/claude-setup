#!/usr/bin/env python3
"""
Deep Think — Parallel Path Explorer
Spawns independent Claude sub-agents to explore multiple reasoning paths simultaneously.
Each agent runs in a separate process with its own context, eliminating anchoring bias.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from textwrap import dedent

# Default personas — each brings a genuinely different lens
DEFAULT_PERSONAS = [
    {
        "id": "first-principles",
        "name": "First Principles Thinker",
        "system": (
            "You are a rigorous first-principles thinker. "
            "Break every assumption down to its foundation. "
            "Don't accept conventional wisdom — derive everything from scratch. "
            "Question 'best practices' and ask WHY they are best. "
            "Focus on correctness and logical soundness above all."
        ),
    },
    {
        "id": "pragmatist",
        "name": "Pragmatic Engineer",
        "system": (
            "You are a pragmatic senior engineer who has shipped many production systems. "
            "You care about what actually works in practice, not theoretical elegance. "
            "Consider maintenance burden, team velocity, onboarding cost, and real-world constraints. "
            "Favor battle-tested approaches over novel ones. "
            "Always ask: 'Will this still make sense 6 months from now?'"
        ),
    },
    {
        "id": "adversarial",
        "name": "Adversarial Reviewer",
        "system": (
            "You are a skeptical adversarial reviewer. "
            "Your job is to find the WORST case scenarios, edge cases, and failure modes. "
            "Assume Murphy's Law applies everywhere. "
            "Think about what happens under load, with bad input, during failures, "
            "with malicious actors, and at scale. "
            "Propose the most defensive and robust approach."
        ),
    },
    {
        "id": "innovator",
        "name": "Creative Innovator",
        "system": (
            "You are a creative innovator who looks for unconventional solutions. "
            "Draw analogies from other domains. Consider approaches that might seem unusual. "
            "Ask 'What if we did the opposite?' or 'What would this look like in 5 years?' "
            "Don't be constrained by current conventions. "
            "Propose approaches others might not consider."
        ),
    },
    {
        "id": "optimizer",
        "name": "Performance Optimizer",
        "system": (
            "You are a performance optimization specialist. "
            "You think in terms of time complexity, space complexity, cache behavior, "
            "network round-trips, rendering cycles, and resource utilization. "
            "Quantify everything — don't say 'faster', say HOW MUCH faster and WHY. "
            "Consider the full system: CPU, memory, I/O, network."
        ),
    },
]


def build_path_prompt(
    question: str,
    analysis: str,
    decomposition: str,
    persona: dict,
    path_index: int,
    total_paths: int,
    extra_context: str = "",
) -> str:
    """Build the prompt for a single path exploration agent."""
    prompt = dedent(f"""\
    # Deep Think — Path {path_index}/{total_paths}: {persona['name']}

    ## Your Role
    {persona['system']}

    ## Task
    You are one of {total_paths} independent thinkers working on the same problem.
    Each thinker has a different perspective. Your perspective is: **{persona['name']}**.

    Provide a thorough, well-reasoned solution from YOUR unique angle.
    Do NOT try to be balanced or cover all perspectives — that's what the other agents are for.
    Go DEEP into your specialty.

    ## The Question
    {question}

    ## Problem Analysis (from Phase 1)
    {analysis}

    ## Problem Decomposition (from Phase 2)
    {decomposition}
    """)

    if extra_context:
        prompt += f"\n## Additional Context\n{extra_context}\n"

    prompt += dedent("""\

    ## Output Format
    Write your response in this structure:

    # Approach: [Your approach name]

    ## Core Idea
    [One paragraph summary of your approach]

    ## Detailed Reasoning
    [Step-by-step reasoning from your perspective. Be thorough.]

    ## Concrete Solution
    [Specific implementation, code, architecture, or recommendation]

    ## Potential Weaknesses
    [Honest assessment of where this approach might fail]

    ## Confidence: [low/medium/high]
    [Brief justification for your confidence level]
    """)

    return prompt


def run_single_agent(
    prompt: str,
    output_path: str,
    persona_name: str,
    model: str = "",
    max_turns: int = 1,
) -> dict:
    """Run a single Claude sub-agent and capture its output."""
    start_time = time.time()
    result = {"persona": persona_name, "output_path": output_path, "success": False}

    try:
        cmd = ["claude", "-p", prompt, "--output-format", "text"]
        if model:
            cmd.extend(["--model", model])
        cmd.extend(["--max-turns", str(max_turns)])

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout per agent
        )

        elapsed = time.time() - start_time

        if proc.returncode == 0 and proc.stdout.strip():
            Path(output_path).write_text(proc.stdout.strip(), encoding="utf-8")
            result["success"] = True
            result["elapsed"] = elapsed
            result["length"] = len(proc.stdout)
        else:
            error_msg = proc.stderr or "Empty output"
            Path(output_path).write_text(
                f"# ❌ Agent Error: {persona_name}\n\n```\n{error_msg}\n```",
                encoding="utf-8",
            )
            result["error"] = error_msg
            result["elapsed"] = elapsed

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        Path(output_path).write_text(
            f"# ⏰ Agent Timeout: {persona_name}\n\nExceeded 600s limit.",
            encoding="utf-8",
        )
        result["error"] = "timeout"
        result["elapsed"] = elapsed

    except Exception as e:
        elapsed = time.time() - start_time
        Path(output_path).write_text(
            f"# ❌ Agent Error: {persona_name}\n\n```\n{str(e)}\n```",
            encoding="utf-8",
        )
        result["error"] = str(e)
        result["elapsed"] = elapsed

    return result


def run_parallel_paths(
    workspace: str,
    num_paths: int = 3,
    model: str = "",
    extra_context: str = "",
    personas_override: list = None,
) -> list:
    """Run multiple path agents in parallel."""
    ws = Path(workspace)

    # Load previous phase outputs
    question_file = ws / "00-question.md"
    analysis_file = ws / "01-analysis" / "analysis.md"
    decomp_file = ws / "02-decomposition" / "decomposition.md"

    question = question_file.read_text(encoding="utf-8") if question_file.exists() else ""
    analysis = analysis_file.read_text(encoding="utf-8") if analysis_file.exists() else "(no analysis yet)"
    decomposition = decomp_file.read_text(encoding="utf-8") if decomp_file.exists() else "(no decomposition yet)"

    # Also load from session.json for the raw question
    session_file = ws / "session.json"
    if session_file.exists():
        session = json.loads(session_file.read_text())
        raw_question = session.get("question", "")
        if raw_question:
            question = raw_question

    # Select personas
    personas = personas_override or DEFAULT_PERSONAS
    selected = personas[:num_paths]

    # Ensure paths dir exists
    paths_dir = ws / "03-paths"
    paths_dir.mkdir(exist_ok=True)

    print(f"\n🔀 Launching {num_paths} parallel sub-agents...")
    for i, p in enumerate(selected, 1):
        print(f"   🤖 Agent {i}: {p['name']}")

    # Build prompts
    tasks = []
    for i, persona in enumerate(selected, 1):
        prompt = build_path_prompt(
            question=question,
            analysis=analysis,
            decomposition=decomposition,
            persona=persona,
            path_index=i,
            total_paths=num_paths,
            extra_context=extra_context,
        )
        output_path = str(paths_dir / f"path-{i}.md")
        tasks.append((prompt, output_path, persona["name"], model))

    # Run in parallel
    start_time = time.time()
    results = []

    with ProcessPoolExecutor(max_workers=num_paths) as executor:
        futures = {
            executor.submit(run_single_agent, t[0], t[1], t[2], t[3]): t[2]
            for t in tasks
        }

        for future in as_completed(futures):
            persona_name = futures[future]
            try:
                result = future.result()
                results.append(result)
                status = "✅" if result["success"] else "❌"
                elapsed = result.get("elapsed", 0)
                print(f"   {status} {persona_name} ({elapsed:.1f}s)")
            except Exception as e:
                print(f"   ❌ {persona_name}: {e}")
                results.append({"persona": persona_name, "success": False, "error": str(e)})

    total_elapsed = time.time() - start_time
    success_count = sum(1 for r in results if r["success"])

    print(f"\n   🏁 All agents complete: {success_count}/{num_paths} succeeded ({total_elapsed:.1f}s wall time)")

    # Save run metadata
    meta = {
        "num_paths": num_paths,
        "wall_time": total_elapsed,
        "results": [
            {
                "persona": r["persona"],
                "success": r["success"],
                "elapsed": r.get("elapsed", 0),
                "length": r.get("length", 0),
            }
            for r in results
        ],
    }
    (paths_dir / "_parallel_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return results


def main():
    parser = argparse.ArgumentParser(description="Deep Think Parallel Path Explorer")
    parser.add_argument("--workspace", "-w", default=".deep-think", help="Workspace directory")
    parser.add_argument("--paths", "-n", type=int, default=3, help="Number of parallel paths (2-5)")
    parser.add_argument("--model", "-m", default="", help="Model override for sub-agents (e.g. claude-sonnet-4-20250514)")
    parser.add_argument("--context", "-c", default="", help="Extra context to pass to agents (file path or string)")

    args = parser.parse_args()
    num = max(2, min(5, args.paths))

    extra = ""
    if args.context:
        ctx_path = Path(args.context)
        if ctx_path.exists():
            extra = ctx_path.read_text(encoding="utf-8")
        else:
            extra = args.context

    run_parallel_paths(
        workspace=args.workspace,
        num_paths=num,
        model=args.model,
        extra_context=extra,
    )


if __name__ == "__main__":
    main()