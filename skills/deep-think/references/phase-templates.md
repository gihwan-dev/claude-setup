# Phase Templates

Templates for each phase of the Deep Think workflow. All teammates and team-lead should follow these structures.

## Phase 1: Analysis (`01-analysis/analysis.md`)

Written by team-lead before spawning teammates.

```
# Problem Analysis

## Original Question
[Restate the question precisely]

## Problem Type
[coding | debugging | math | analysis | creative | hybrid]

## Complexity Assessment
[low | medium | high | extreme]
Reasoning: [why this level? → determines teammate count]

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

Written by team-lead before spawning teammates.

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

## Phase 3: Multi-Path (`03-paths/path-{persona}.md`)

Each teammate writes their solution following this structure:

```
# Approach: [Approach name]

## Core Idea
[One paragraph summary]

## Detailed Reasoning
[Step-by-step logic from this persona's perspective. Be thorough.]

## Concrete Solution
[Specific implementation, code, architecture, or recommendation]

## Potential Weaknesses
[Honest assessment of where this approach might fail]

## Confidence: [low/medium/high]
[Brief justification]
```

## Phase 4: Verification (`04-verification/verification.md`)

Written by verifier teammate after reading all paths.

```
# Verification Report

## Path-by-Path Evaluation

### path-first-principles
- Correctness: X/5
- Completeness: X/5
- Practicality: X/5
[Brief notes]

### path-pragmatist
[same structure]

[... for each path ...]

## Contradictions Found
[Where do paths disagree? Who is right and why?]

## Blind Spots
[What did ALL paths miss?]

## Devil's Advocate
[Strongest argument against the current best approach]
```

## Phase 5: Synthesis (`05-synthesis/synthesis.md`)

Written by verifier teammate.

```
# Synthesis

## Best Elements from Each Path
- From first-principles: [what to keep]
- From pragmatist: [what to keep]
- From adversarial: [what to keep]
- From optimizer: [what to keep]

## Integrated Solution
[Combine the best elements into one coherent answer]

## Trade-offs
[What was sacrificed and why it's worth it]

## Remaining Uncertainty
[What we still can't be sure about]
```

## Phase 6: Final Answer (`06-answer/answer.md`)

Written by verifier teammate.

```
# Final Answer

## TL;DR
[One-paragraph executive summary]

## Detailed Answer
[Complete, polished response. Include code, diagrams, etc. as needed.]

## Thought Process Summary
[2-3 paragraphs explaining:
 - What perspectives were considered
 - Where they agreed/disagreed
 - What was verified and what edge cases were checked
 - Why this answer was chosen over alternatives]

## Confidence Level
[Overall confidence + justification]
```