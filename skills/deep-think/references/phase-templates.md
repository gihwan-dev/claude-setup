# Phase Prompt Templates

Each phase writes its output to a markdown file in the workspace. These templates guide what to write.

## Phase 1: Analysis (`01-analysis/analysis.md`)

```
# Problem Analysis

## Original Question
[Restate the question precisely]

## Problem Type
[coding | debugging | math | analysis | creative | hybrid]

## Complexity Assessment
[low | medium | high | extreme]
Reasoning: [why this level?]

## Key Constraints
- [constraint 1]
- [constraint 2]

## Implicit Assumptions
- [assumption 1 — is it valid?]
- [assumption 2 — is it valid?]

## What Would a Perfect Answer Look Like?
[Describe the ideal output before attempting to produce it]
```

## Phase 2: Decomposition (`02-decomposition/decomposition.md`)

```
# Problem Decomposition

## Sub-Problems
1. [Sub-problem A] — [why this matters]
2. [Sub-problem B] — [why this matters]
3. [Sub-problem C] — [why this matters]

## Dependencies
[Which sub-problems depend on others? What order?]

## Knowledge Gaps
[What do I NOT know that I need to find out?]

## Attack Plan
[Ordered list of what to tackle first and why]
```

## Phase 3: Multi-Path (`03-paths/path-{N}.md`)

Each path is produced by an independent sub-agent with a unique persona. The sub-agent writes:

```
# Approach: [Approach name]

## Core Idea
[One paragraph summary]

## Detailed Reasoning
[Step-by-step logic from this persona's perspective]

## Concrete Solution
[Specific implementation, code, architecture, or recommendation]

## Potential Weaknesses
[Honest assessment of where this approach might fail]

## Confidence: [low/medium/high]
[Brief justification]
```

## Phase 4-5: Verification & Synthesis (via verify_synthesize.py)

These phases are handled by an independent sub-agent. The verifier agent automatically produces:
- Path-by-path evaluation with scores
- Contradictions and blind spots
- Devil's advocate arguments
- Synthesized best answer

Output: `04-verification/verification.md` and `05-synthesis/synthesis.md`

## Phase 6: Final Answer (via verify_synthesize.py)

Also handled by a sub-agent. Produces:

```
# Final Answer

## TL;DR
[One-paragraph executive summary]

## Detailed Answer
[Complete, polished response]

## Thought Process Summary
[How this conclusion was reached — perspectives considered,
agreements/disagreements, edge cases checked, why this over alternatives]

## Confidence Level
[Overall confidence + justification]
```

Output: `06-answer/answer.md`