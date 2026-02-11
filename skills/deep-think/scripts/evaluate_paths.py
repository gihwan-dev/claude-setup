#!/usr/bin/env python3
"""
Deep Think v2 — Path Evaluator
Reads multiple reasoning paths and generates a structured comparison matrix
with evidence quality scoring and convergence detection.
"""

import argparse
import re
import sys
from pathlib import Path


EVIDENCE_TAGS = ["CODE", "BENCH", "PATTERN", "REASON", "ASSUME"]

# Evidence quality weights: higher = stronger evidence
EVIDENCE_WEIGHTS = {
    "CODE": 5,
    "BENCH": 4,
    "PATTERN": 3,
    "REASON": 2,
    "ASSUME": 0,
}


def extract_core_thesis(content: str) -> str:
    """Extract the Core Thesis section from a path file."""
    match = re.search(
        r"##\s+Core Thesis\s*\n(.+?)(?=\n##|\Z)",
        content,
        re.DOTALL,
    )
    if match:
        return match.group(1).strip()
    # Fallback: first non-header line
    for line in content.split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            return line
    return ""


def count_evidence_tags(content: str) -> dict[str, int]:
    """Count evidence tags in content."""
    counts = {}
    for tag in EVIDENCE_TAGS:
        counts[tag] = len(re.findall(rf"\[{tag}\]", content))
    return counts


def compute_evidence_quality(counts: dict[str, int]) -> str:
    """Compute overall evidence quality from tag counts.
    HIGH: majority code/bench evidence
    MEDIUM: majority pattern/reason evidence
    LOW: majority assumptions or no tags
    """
    total = sum(counts.values())
    if total == 0:
        return "LOW"

    strong = counts.get("CODE", 0) + counts.get("BENCH", 0)
    medium = counts.get("PATTERN", 0) + counts.get("REASON", 0)
    weak = counts.get("ASSUME", 0)

    if strong >= total * 0.5:
        return "HIGH"
    elif (strong + medium) >= total * 0.5:
        return "MEDIUM"
    else:
        return "LOW"


def compute_evidence_score(counts: dict[str, int]) -> float:
    """Compute weighted evidence score (0-5 scale)."""
    total_weight = 0
    total_count = 0
    for tag, count in counts.items():
        total_weight += EVIDENCE_WEIGHTS.get(tag, 0) * count
        total_count += count
    if total_count == 0:
        return 0.0
    return round(total_weight / total_count, 1)


def simple_similarity(text_a: str, text_b: str) -> float:
    """Simple word-overlap similarity between two texts (Jaccard-like).
    Returns 0.0-1.0.
    """
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def compute_convergence(theses: list[str]) -> dict:
    """Compute pairwise convergence scores between core theses.
    Returns convergence info including whether strong convergence is detected.
    """
    n = len(theses)
    if n < 2:
        return {"converged": True, "score": 1.0, "pairs": []}

    pairs = []
    total_sim = 0.0
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            sim = simple_similarity(theses[i], theses[j])
            pairs.append({"a": i, "b": j, "similarity": round(sim, 3)})
            total_sim += sim
            count += 1

    avg_sim = total_sim / count if count > 0 else 0.0

    # Strong convergence: average similarity > 0.4 (adjusted for natural language variance)
    return {
        "converged": avg_sim > 0.4,
        "score": round(avg_sim, 3),
        "pairs": sorted(pairs, key=lambda p: p["similarity"]),
    }


def check_required_sections(content: str) -> list[str]:
    """Check which required path sections are present."""
    required = ["Core Thesis", "Evidence Chain", "Implementation Sequence", "Risk Register", "What This Path Uniquely Offers"]
    missing = []
    for section in required:
        pattern = rf"#{{1,4}}\s+.*{re.escape(section)}"
        if not re.search(pattern, content, re.IGNORECASE):
            missing.append(section)
    return missing


def evaluate_paths(workspace: str) -> None:
    """Read all path files and generate an evaluation with evidence quality and convergence."""
    ws = Path(workspace)
    paths_dir = ws / "03-paths"

    if not paths_dir.exists():
        print("❌ No paths directory found. Run multi-path exploration first.")
        sys.exit(1)

    path_files = sorted(
        f for f in paths_dir.glob("path-*.md")
        if "-reflected" not in f.name and "-revised" not in f.name
    )
    if not path_files:
        print("❌ No path files found in 03-paths/")
        sys.exit(1)

    print(f"📊 Found {len(path_files)} reasoning paths\n")

    paths = []
    theses = []
    for pf in path_files:
        content = pf.read_text(encoding="utf-8").strip()
        name = pf.stem.replace("path-", "")
        thesis = extract_core_thesis(content)
        evidence = count_evidence_tags(content)
        quality = compute_evidence_quality(evidence)
        score = compute_evidence_score(evidence)
        missing_sections = check_required_sections(content)

        paths.append({
            "name": name,
            "file": str(pf),
            "thesis": thesis,
            "evidence": evidence,
            "quality": quality,
            "score": score,
            "missing_sections": missing_sections,
        })
        theses.append(thesis)

        print(f"  📄 {name}")
        print(f"     Thesis: {thesis[:80]}{'...' if len(thesis) > 80 else ''}")
        print(f"     Evidence: {quality} (score: {score}/5.0)")
        if missing_sections:
            print(f"     ⚠️ Missing: {', '.join(missing_sections)}")

    # Compute convergence
    convergence = compute_convergence(theses)
    print(f"\n📐 Convergence: {'STRONG' if convergence['converged'] else 'WEAK'} (score: {convergence['score']})")
    if convergence["converged"]:
        print("   → Challenge round may be skipped (strong convergence detected)")

    # Generate evaluation template
    eval_lines = [
        "# 🔍 Path Evaluation Matrix (v2)\n",
        "## Paths Under Evaluation\n",
    ]

    for i, p in enumerate(paths, 1):
        eval_lines.append(f"{i}. **{p['name']}**: {p['thesis'][:100]}")

    eval_lines.extend([
        "",
        "## Evidence Quality\n",
        "| Path | [CODE] | [BENCH] | [PATTERN] | [REASON] | [ASSUME] | Quality | Score |",
        "|------|--------|---------|-----------|----------|----------|---------|-------|",
    ])
    for p in paths:
        e = p["evidence"]
        eval_lines.append(
            f"| {p['name']} | {e['CODE']} | {e['BENCH']} | {e['PATTERN']} "
            f"| {e['REASON']} | {e['ASSUME']} | {p['quality']} | {p['score']}/5.0 |"
        )

    eval_lines.extend([
        "",
        "## Convergence Analysis\n",
        f"**Overall: {'STRONG' if convergence['converged'] else 'WEAK'}** (score: {convergence['score']})\n",
    ])
    if convergence["pairs"]:
        eval_lines.append("| Pair | Similarity |")
        eval_lines.append("|------|-----------|")
        for pair in convergence["pairs"]:
            a_name = paths[pair["a"]]["name"]
            b_name = paths[pair["b"]]["name"]
            eval_lines.append(f"| {a_name} ↔ {b_name} | {pair['similarity']} |")

    if convergence["converged"]:
        eval_lines.extend([
            "",
            "> **Recommendation:** Strong convergence detected. Consider skipping challenge round",
            "> and proceeding directly to synthesis with high-confidence note.",
        ])
    else:
        # Find max-disagreement pairs for targeted critique
        if convergence["pairs"]:
            min_pair = convergence["pairs"][0]  # sorted ascending
            a_name = paths[min_pair["a"]]["name"]
            b_name = paths[min_pair["b"]]["name"]
            eval_lines.extend([
                "",
                f"> **Max disagreement:** {a_name} ↔ {b_name} (similarity: {min_pair['similarity']})",
                "> Prioritize this pair for targeted critique.",
            ])

    eval_lines.extend([
        "",
        "## Section Completeness\n",
    ])
    for p in paths:
        if p["missing_sections"]:
            eval_lines.append(f"- ⚠️ **{p['name']}**: missing {', '.join(p['missing_sections'])}")
        else:
            eval_lines.append(f"- ✅ **{p['name']}**: all sections present")

    eval_lines.extend([
        "",
        "## Contradictions & Conflicts\n",
        "<!-- List any contradictions found between paths -->\n",
        "## Blind Spots\n",
        "<!-- What did ALL paths miss? -->\n",
        "## Verdict\n",
        "<!-- Which path (or combination) is best and why? -->\n",
    ])

    eval_dir = ws / "04-synthesis"
    eval_dir.mkdir(exist_ok=True)
    eval_path = eval_dir / "evaluation-matrix.md"
    eval_path.write_text("\n".join(eval_lines), encoding="utf-8")
    print(f"\n✅ Evaluation generated: {eval_path}")


def main():
    parser = argparse.ArgumentParser(description="Deep Think v2 Path Evaluator")
    parser.add_argument("--workspace", "-w", default=".deep-think", help="Workspace directory")
    args = parser.parse_args()
    evaluate_paths(args.workspace)


if __name__ == "__main__":
    main()
