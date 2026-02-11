# Phase Templates v2

Templates for Deep Think v2 workflow phases.

---

## Phase 0: Triage & Frame (`00-triage/frame.md`)

Written by team lead. Determines tier and persona assignments.

```markdown
# Problem Frame

## Question
[Restate with ALL nuances. Don't simplify.]

## Type
[architecture / optimization / design / debugging / knowledge]

## Complexity Dimensions

| Dimension | Score (0-2) | Justification |
|-----------|-------------|---------------|
| Solution Space Breadth | | |
| Stakeholder Tension | | |
| Uncertainty Level | | |
| Impact Scope | | |

**Total: X/8 → Tier [1/2/3]**

## Key Constraints
- [constraint 1 — source]
- [constraint 2 — source]

## Success Criteria
[What a good answer looks like — be specific]

## Persona Assignments

| Persona | Focus Question |
|---------|---------------|
| Pragmatist | [specific angle to explore] |
| [other persona] | [specific angle to explore] |
```

---

## Phase 0 Extension: Pre-Mortem (Tier 3 only)

Appended to frame.md for Tier 3 problems.

```markdown
## Pre-Mortem

Imagine 3 months from now, our chosen approach has failed badly.

### Failure Scenario 1: [Name]
- What went wrong:
- Early warning signs:
- Probability: [LOW / MEDIUM / HIGH]

### Failure Scenario 2: [Name]
- What went wrong:
- Early warning signs:
- Probability: [LOW / MEDIUM / HIGH]

### Failure Scenario 3: [Name]
- What went wrong:
- Early warning signs:
- Probability: [LOW / MEDIUM / HIGH]

### Critical Assumptions
If any of these are wrong, the entire approach is invalidated:
1. [assumption]
2. [assumption]
```

---

## Phase 1: Analysis (`01-analysis/analysis.md`)

Written by team lead after framing.

```markdown
# Problem Analysis

## Original Question
[Restate with ALL nuances. Don't simplify.]

## Why This Is Hard
[What makes this non-trivial?]

## Constraints (Explicit)
- [constraint 1 — source]

## Constraints (Implicit/Assumed)
- [assumption 1 — what if it's wrong?]

## What "Perfect" Looks Like
[Ideal output]

## What "Good Enough" Looks Like
[Minimum viable answer]

## Known Unknowns
[What we don't know]
```

---

## Phase 1: Decomposition (`02-decomposition/decomposition.md`)

Written by team lead.

```markdown
# Problem Decomposition

## Sub-Problems

### 1. [Sub-problem A]
- Why it matters:
- Difficulty: [low/medium/high]
- Dependencies: [what must be solved first]

### 2. [Sub-problem B]
[same structure]

## Dependency Graph
A → B → D
    ↘ C ↗

## Hardest Parts
[Which sub-problems are trickiest and why?]

## Attack Plan
1. First: [X] because [reason]
2. Then: [Y] because [reason]
```

---

## Phase 1: Path (`03-paths/path-{persona}.md`)

Each persona writes their solution. **No word count minimum — structural sections required.**

```markdown
# Path: [Descriptive Name]

## Core Thesis
[1-2 sentences: the fundamental approach and why]

## Evidence Chain

### Recommendation 1: [Title]
1. Claim: "[specific recommendation]"
2. Evidence: [CODE] reference to specific code/pattern
   — OR [BENCH] benchmark data
   — OR [PATTERN] established industry pattern
   — OR [REASON] logical derivation (show reasoning)
   — OR [ASSUME] unverified assumption (will be flagged in final answer)
3. Confidence: HIGH / MEDIUM / LOW

### Recommendation 2: [Title]
[same structure]

### Recommendation 3: [Title]
[same structure]

[Continue as needed...]

## Implementation Sequence
Steps in dependency order:

1. **[Step]** (depends on: nothing)
   - What: [specific action]
   - Why: [rationale]

2. **[Step]** (depends on: Step 1)
   - What: [specific action]
   - Why: [rationale]

[Continue...]

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| [risk 1] | LOW/MED/HIGH | LOW/MED/HIGH | [mitigation] |
| [risk 2] | LOW/MED/HIGH | LOW/MED/HIGH | [mitigation] |

## What This Path Uniquely Offers
1. [Thing that other approaches won't surface]
2. [Another unique contribution]

## Self-Assessment: [SOUND / HAS-GAPS]
[If HAS-GAPS, identify what's missing]
```

---

## Phase 3a: Targeted Critique (`03.5-challenges/critique-{from}-vs-{to}.md`)

Each critic evaluates one path. **Specific scenarios required.**

```markdown
# Critique: {from} → {to}

## Their Core Thesis
[1-2 sentences summarizing their approach]

## Focused Question
[The specific question assigned by team lead for this pairing]

## Findings

### Finding 1: [Title]
**Severity: [SOUND / HAS-GAPS / FUNDAMENTALLY-FLAWED]**

Specific scenario:
> [Concrete example with numbers/specifics]
> Example: "With 1,650 cells + 30 columns, the O(n*m²) algorithm
>  executes 49,500 array traversals per render, causing ~110ms delay"

Impact: [what happens if this is not addressed]
Suggested fix: [concrete alternative]

### Finding 2: [Title]
[same structure]

## Evidence Audit
- Claims tagged [CODE]: [verified / not checked]
- Claims tagged [ASSUME]: [how many, which are risky]
- Missing evidence for: [any untagged claims]

## Blind Spots
- [What they didn't consider]

## Overall Rating: [SOUND / HAS-GAPS / FUNDAMENTALLY-FLAWED]

Recommendation: [specific action — "No revision needed" / "Address findings 1,2" / "Rethink core approach"]
```

---

## Phase 3b: Author Reflection (Tier 3 only) (`03-paths/path-{name}-reflected.md`)

Each path author responds to their critique.

```markdown
# Reflection: [Persona] responding to [Critic]

## Accepted Points
### [Finding title from critique]
- Original approach: [what I said]
- Revised approach: [how I'm changing it]
- Evidence for revision: [why the critic was right]

## Rejected Points
### [Finding title from critique]
- Critic's claim: [what they said]
- Counter-argument: [why I disagree]
- Supporting evidence: [CODE/BENCH/PATTERN/REASON]

## Updated Self-Assessment: [SOUND / HAS-GAPS]
[If changed from original, explain why]

## Revised Core Thesis (if changed)
[Updated 1-2 sentences, or "No change to core thesis"]
```

---

## Phase 4: 3-Pass Synthesis

### Pass 1: Extract (`04-synthesis/pass1-extract.md`)

```markdown
# Synthesis Pass 1: Extraction

## Path Summaries

### [Persona 1]
- Core Thesis: [1-2 sentences]
- Unique Contributions: [what only this path surfaced]
- HIGH-confidence recommendations:
  1. [recommendation] — evidence: [tag]
  2. [recommendation] — evidence: [tag]
- Discarded: [what was LOW-confidence or redundant]

### [Persona 2]
[same structure]

[Continue for each path...]
```

### Pass 2: Reconcile (`04-synthesis/pass2-reconcile.md`)

```markdown
# Synthesis Pass 2: Reconciliation

## Disagreement Map

### Factual Disagreements
| Topic | Path A says | Path B says | Resolution | Basis |
|-------|-------------|-------------|------------|-------|
| [topic] | [claim] | [claim] | [resolved to...] | [evidence that decided it] |

### Preference Disagreements
| Topic | Path A prefers | Path B prefers | Trade-off |
|-------|---------------|---------------|-----------|
| [topic] | [option] | [option] | [Recommended: X, because Y. Choose Z if condition.] |

### Scope Disagreements
| Topic | Path A scope | Path B scope | Context Guide |
|-------|-------------|-------------|---------------|
| [topic] | [narrow] | [broad] | [When to use narrow: ..., When to use broad: ...] |

## Blind Spot Check
What question did NO path address that a domain expert would ask?
- [question 1]: [brief answer or "needs investigation"]
- [question 2]: [brief answer or "needs investigation"]
```

### Pass 3: Compose (`04-synthesis/pass3-compose.md`)

Written fresh — no copy-paste from original paths.

```markdown
# Synthesis Pass 3: Integrated Solution

[Write the complete integrated solution here.
This must be composed from scratch using the reconciled materials.
Do NOT copy text from any original path.]
```

---

## Phase 5: Final Answer (`05-answer/answer.md`)

### Track A (Agent Teams) Format

```markdown
# Final Answer

## TL;DR
[One paragraph executive summary]

## Detailed Answer

### [Section 1]
[Thorough explanation]

### [Section 2]
[Thorough explanation]

[Continue as needed...]

## Implementation Notes
[Concrete next steps, code if relevant]

## Confidence Assessment

### Convergence: [Y of N paths recommended this approach]
### Evidence Quality: [HIGH (code-based) / MEDIUM (pattern-based) / LOW (reasoning only)]
### Risk Level: [from adversarial analysis — LOW/MEDIUM/HIGH]

### High-Confidence Recommendations (all paths agree, evidence-backed)
- [recommendation 1]
- [recommendation 2]

### Medium-Confidence Recommendations (majority agree, some caveats)
- [recommendation 1] — caveat: [what to watch for]

### Low-Confidence Recommendations (exploratory, needs validation)
- [recommendation 1] — validate by: [how to test this]

## Unverified Assumptions
[All [ASSUME]-tagged claims that survived into the final answer]
- [assumption 1]: impact if wrong — [consequence]
- [assumption 2]: impact if wrong — [consequence]

## Dissenting Views
[Minority opinions that weren't adopted but remain valid]
- [Persona X] argued [alternative] because [reason].
  Not adopted because [reason], but valid if [conditions].

## Thought Process Summary
[2-3 paragraphs:
 - Which perspectives contributed what
 - Key disagreements and how they were resolved
 - Why this synthesis beats any individual path]
```

### Track B (Plan Mode) Format

Written to plan file:

```markdown
# [Topic] Implementation Plan

## Context
[Deep-think analysis summary: why this change is needed]
[How many personas participated, convergence/divergence status]

## Approach
[Recommended approach from synthesis]
[Which persona's perspective was adopted and why]

## Changes
| # | Change | Files |
|---|--------|-------|
| 1 | [change description] | [file paths] |

[Detailed implementation steps for each change]

## Confidence Assessment

### Convergence: [Y of N]
### Evidence Quality: [HIGH/MEDIUM/LOW]

### High-Confidence Changes
- [change]

### Medium-Confidence Changes
- [change] — caveat: [note]

### Low-Confidence Changes
- [change] — validate by: [test]

## Unverified Assumptions
- [assumption]: impact if wrong — [consequence]

## Dissenting Views
- [persona] argued [alternative] because [reason]

## Verification
- [test/validation method 1]
- [test/validation method 2]
```

→ Then `ExitPlanMode` for user approval.
