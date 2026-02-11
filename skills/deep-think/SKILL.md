---
name: deep-think
description: >
  Deep Think v2 — Adaptive multi-persona reasoning with evidence-based depth.
  Uses tiered complexity (2-5 agents), targeted critique→reflect cycles,
  convergence shortcuts, and 3-pass PENCIL-inspired synthesis.
  Detects execution environment to choose between Agent Teams (normal mode)
  and Task Orchestration (plan mode).
  Use when the user prefixes with "deep think", "딥씽크", "깊게 생각해", or requests
  thorough analysis. Best for complex architecture, debugging, algorithmic, or
  multi-domain problems. NOT for simple lookups.
  Requires: CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 (Track A only)
---

# Deep Think v2

Adaptive multi-phase reasoning with **evidence-based depth**, **targeted critique→reflect cycles**, **convergence shortcuts**, and **3-pass synthesis**. Agent count scales with problem complexity (2-5).

## Prerequisites

```bash
# Track A (Agent Teams) only — Track B works without this
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

## Execution Track Detection

Before starting, detect which track to use:

```
System prompt contains "Plan mode is active"?
  → Yes: Track B (Task Orchestration) — output to plan file
  → No:  Track A (Agent Teams) — output to .deep-think/06-answer/answer.md
```

---

## Personas

### Core Personas (always available)

**Pragmatist**
Focus: What works in production at 3am when things break.
Hard Constraint: Must include a concrete implementation sequence with time estimates.
Consider: maintenance burden, onboarding, debugging at scale.
Favor battle-tested over novel. Ask: "Will this still make sense in 2 years?"

**First-Principles**
Focus: Derive from fundamentals. Question every assumption.
Hard Constraint: Must question at least one widely-accepted assumption.
Don't accept "best practices" — ask WHY they're best. Maybe they're not.
Focus on correctness and logical soundness above all else.

**Adversarial**
Focus: Everything will fail. Find out how.
Hard Constraint: Must provide at least one specific failure scenario (no abstract concerns).
Consider: malicious input, race conditions, resource exhaustion, cascading failures.
Your job is to BREAK every approach. Be paranoid. Be concrete.

**Optimizer**
Focus: Think in O(n), cache lines, memory bandwidth, network round-trips.
Hard Constraint: Must include a quantitative cost model (even if estimated).
Quantify EVERYTHING. Don't say "faster" — say "3x faster because..."
Profile before you optimize. Know your bottlenecks.

### Dynamic Persona

**Domain Specialist** (replaces fixed Innovator)
Assigned by team lead in Phase 0 based on problem type:
- Performance → "Performance Engineer"
- Architecture → "Systems Architect"
- UX decisions → "UX Researcher"
- DB design → "Data Engineer"
- Security → "Security Engineer"
Hard Constraint: Must reference at least 2 established best practices or anti-patterns from the domain.

### Tier-based Persona Assignment

| Tier | Personas |
|------|----------|
| Tier 1 (집중) | Pragmatist + Domain Specialist |
| Tier 2 (표준) | Pragmatist + First-Principles + Adversarial |
| Tier 3 (복합) | Pragmatist + First-Principles + Adversarial + Optimizer + Domain Specialist |

---

## Architecture

```
You (Team Lead)
├── Phase 0: Triage & Frame (you — classify, assign tier)
├── Phase 1: Parallel Paths (2-5 agents, evidence-based depth)
│   └── Personas assigned per tier
├── Phase 2: Convergence Check (you — shortcut if aligned)
├── Phase 3a: Targeted Critique (max-disagreement pairs)
├── Phase 3b: Author Reflection (Tier 3 only)
├── Phase 4: 3-Pass Synthesis (Extract → Reconcile → Compose)
└── Phase 5: Final Answer (structured confidence)
```

---

## Workflow

### Phase 0: Triage & Frame (Team Lead)

**Evaluate the problem on 4 dimensions (0-2 each):**

| Dimension | 0 | 1 | 2 |
|-----------|---|---|---|
| Solution Space Breadth | One correct answer | Few approaches | Many paradigms |
| Stakeholder Tension | None | Some trade-offs | Fundamental tensions |
| Uncertainty Level | Known problem | Some unknowns | Exploratory/uncharted |
| Impact Scope | Local | Module-level | System-wide |

**Tier assignment:**

| Tier | Score | Agents | Challenge |
|------|-------|--------|-----------|
| Tier 1 (집중) | 0-2 | 2 | Mutual critique ×1 |
| Tier 2 (표준) | 3-5 | 3 | Targeted critique |
| Tier 3 (복합) | 6-8 | 4-5 | Critique → Reflect |

**Phase 0 Output:**

```markdown
## Problem Frame
- Question: [one sentence]
- Type: [architecture / optimization / design / debugging / knowledge]
- Dimensions: Space=[X] Tension=[X] Uncertainty=[X] Scope=[X]
- Tier: [1/2/3] (score: X/8)
- Key Constraints: [list]
- Success Criteria: [what a good answer looks like]
- Persona Assignments: [who gets which focus question]
- Domain Specialist Role: [specific role name, if Tier 1 or 3]
```

**Pre-Mortem (Tier 3 only):**

After framing, add:

```markdown
## Pre-Mortem
Imagine 3 months from now, our chosen approach has failed badly.
- What went wrong? (3 scenarios)
- What early warning signs should we watch for?
- Which assumptions, if wrong, would invalidate the entire approach?
```

Pre-mortem scenarios become mandatory evaluation criteria for all paths.

**Initialize workspace (Track A only):**

```bash
python scripts/deep_think.py init "your question" -c tier2 -w .deep-think
```

### Phase 1: Parallel Paths

**Track A (Agent Teams):**
```
Create agent team "deep-think".

Each assigned persona:
- Read .deep-think/00-triage/frame.md
- Write solution to .deep-think/03-paths/path-{name}.md
- Follow the structured path template (see phase-templates.md)
- When done, message team-lead with Core Thesis + key differentiator
```

**Track B (Task Orchestration):**
```
For each assigned persona, launch a Task agent:
- Task(name="{persona}", prompt="[problem frame] + [persona instructions] + [path template]")
- Collect returned text from each Task
```

**Path Structure (replaces word count minimum):**

Each path MUST include these sections:
1. Core Thesis (1-2 sentences)
2. Evidence Chain (each claim tagged: [CODE] [BENCH] [PATTERN] [REASON] [ASSUME])
3. Implementation Sequence (dependency-ordered steps)
4. Risk Register (table: risk / likelihood / impact / mitigation)
5. What This Path Uniquely Offers (1-2 things other paths won't surface)

`[ASSUME]`-tagged claims are treated as hypotheses in synthesis. They appear as unverified assumptions in the final answer.

### Phase 2: Convergence Check (Team Lead)

After all paths complete, read each path's Core Thesis.

```
If (N-1) or more of N paths converge on the same core recommendation:
  → Skip challenge round
  → Proceed to synthesis with note: "Strong convergence detected — high confidence in common recommendation"
  → Record minority opinion in "Dissenting Views"
Otherwise:
  → Proceed to Phase 3a
```

**Expected effect:** 40-50% time savings on strong models (Opus 4.6) for convergent problems.

### Phase 3a: Targeted Critique

**Assignment: max-disagreement pairs** (NOT round-robin).
Team lead assigns each critic to the path they most disagree with.

**Critique quality rules:**
All critiques MUST include specific scenarios. Critiques without concrete scenarios are ignored in synthesis.

```
Weak: "This approach may have performance issues at scale"
Strong: "With 1,650 cells + 30 columns, the O(n*m²) algorithm executes
        49,500 array traversals per render, causing ~110ms interaction delay"
```

**Critique rating scale (3-level):**
- **SOUND**: No significant gaps found
- **HAS-GAPS**: Specific issues identified but approach is viable with fixes
- **FUNDAMENTALLY-FLAWED**: Core thesis is broken

**Targeted critique question examples:**
- First-Principles → Pragmatist: "What practical constraints does this path underestimate?"
- Adversarial → Optimizer: "In what specific production scenario does this optimization fail?"
- Pragmatist → Adversarial: "Which of these risk assessments confuse actual probability with worst-case?"

**Track A:** Each critic reads the target path file and writes to `.deep-think/03.5-challenges/`.
**Track B:** Team lead passes the target path's full text into the critic Task's prompt.

### Phase 3b: Author Reflection (Tier 3 only)

After receiving critique, each path author:
- Accepted points → revised approach
- Rejected points → counter-argument with evidence
- Updated self-assessment: SOUND / HAS-GAPS

**Track A:** Send critique via message, author writes `path-{name}-reflected.md`.
**Track B:** Launch new Task with original path + critique in prompt, collect reflected version.

### Phase 4: 3-Pass Synthesis

Replaces weighted accumulation with distillation-based synthesis (PENCIL-inspired):

**Pass 1: Extract**
From each path, extract ONLY:
- (a) Core thesis
- (b) Unique contributions
- (c) HIGH-confidence recommendations
Discard everything else.

**Pass 2: Reconcile**
Using the disagreement map:
- Factual disagreements → resolve by evidence
- Preference disagreements → present as explicit trade-offs (with recommended choice)
- Scope disagreements → "depends on context" + context guide for each

**Pass 3: Compose**
Write the final answer fresh from reconciled materials. **No text copying from original paths.** This forces genuine integration.

**Blind Spot Check (all tiers):**
Before finalizing, ask: "What question did NO path address that a domain expert would ask?"

### Phase 5: Final Answer

Write the final answer with structured confidence (see phase-templates.md for full template).

**Structured Confidence (replaces X/10):**

```markdown
## Confidence Assessment

### Convergence: [Y of N paths recommended this approach]
### Evidence Quality: HIGH (code-based) / MEDIUM (pattern-based) / LOW (reasoning only)
### Risk Level: [from adversarial analysis]

### High-Confidence Recommendations (all paths agree, evidence-backed)
- ...

### Medium-Confidence Recommendations (majority agree, some caveats)
- ...

### Low-Confidence Recommendations (exploratory, needs validation)
- ...
```

### Shutdown

**Track A:**
```
Shutdown the deep-think team. Wait for all teammates to finish.
```
Then generate report:
```bash
python scripts/deep_think.py report -w .deep-think
```

**Track B:**
Write final plan to plan file → `ExitPlanMode` for user approval.

---

## Tier Workflows Summary

### Tier 1 (집중, ~60% of use)
```
Phase 0: Triage & Frame → Tier 1
Phase 1: 2 agents parallel paths
Phase 2: Convergence check → if aligned, skip to synthesis
Phase 3a: Mutual critique ×1 (if not converged)
Phase 4: 3-pass synthesis
Phase 5: Final answer
Agents: 2 (+ team lead)
```

### Tier 2 (표준, ~30% of use)
```
Phase 0: Triage & Frame → Tier 2, focus questions assigned
Phase 1: 3 agents parallel paths (structured requirements)
Phase 2: Convergence check
Phase 3a: Targeted critique (specific scenarios required)
Phase 4: 3-pass synthesis + blind spot check
Phase 5: Final answer (structured confidence)
Agents: 3 (+ team lead)
```

### Tier 3 (복합, ~10% of use)
```
Phase 0: Triage & Frame + Pre-Mortem → Tier 3
Phase 1: 4-5 agents parallel paths (evidence anchoring)
Phase 2: Convergence check
Phase 3a: Targeted critique (specific scenarios required)
Phase 3b: Author reflection (accept/rebut critique)
Phase 4: 3-pass synthesis + blind spot check
Phase 5: Final answer (structured confidence + disagreement tracking)
Agents: 4-5 (+ team lead)
```

---

## Output Structure

### Track A (Agent Teams)
```
.deep-think/
├── 00-triage/frame.md                  # Problem frame + tier assignment
├── 01-analysis/analysis.md             # Detailed analysis
├── 02-decomposition/decomposition.md   # Sub-problems
├── 03-paths/
│   ├── path-pragmatist.md              # Structured evidence-based paths
│   ├── path-first-principles.md
│   ├── path-{persona}.md
│   └── path-{name}-reflected.md        # Tier 3: post-critique reflection
├── 03.5-challenges/
│   ├── critique-{from}-vs-{to}.md      # Targeted critiques
│   └── ...
├── 04-synthesis/
│   ├── pass1-extract.md                # Extracted elements
│   ├── pass2-reconcile.md              # Disagreement resolution
│   └── pass3-compose.md                # Fresh composition
├── 05-answer/answer.md                 # Final polished answer
├── session.json
└── REPORT.md
```

### Track B (Plan Mode)
Output goes to plan file:
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
[Concrete implementation steps]

## Confidence Assessment
[Structured confidence]

## Dissenting Views
[Minority opinions]

## Verification
[Test/validation methods]
```
→ Then `ExitPlanMode` for user approval.

---

## Troubleshooting

**Paths lacking evidence tags?**
→ Message: "Tag each claim with [CODE], [BENCH], [PATTERN], [REASON], or [ASSUME]."

**Critiques too vague?**
→ Message: "Provide a specific scenario with numbers. Vague critiques are ignored in synthesis."

**Convergence check unclear?**
→ Compare Core Thesis sentences. If they recommend the same fundamental approach (even with different details), that's convergence.

**Tier seems wrong?**
→ Re-evaluate dimensions. When in doubt, tier up (Tier 2 → Tier 3) rather than down.
