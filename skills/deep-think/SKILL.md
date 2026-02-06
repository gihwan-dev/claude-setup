---
name: deep-think
description: >
   Structured deep reasoning skill using parallel sub-agents, mimicking Google's Deep Think mode.
   Spawns multiple independent Claude instances to explore different solution paths simultaneously,
   then uses a fresh verifier agent to critique and synthesize the best answer.
   Use when the user prefixes a question with "deep think", "딥씽크", "깊게 생각해", or when explicitly
   requesting thorough/exhaustive analysis. Also trigger for complex architecture, debugging,
   algorithmic, or multi-domain questions where highest quality is needed.
   NOT for simple factual lookups or casual conversation.
---

# Deep Think (Native Task Tool Architecture)

Multi-phase reasoning using **native Task tool parallel sub-agents**. Each reasoning path is explored by a separate agent with its own context, eliminating anchoring bias. A dedicated verifier agent then critiques and synthesizes all paths.

No external dependencies. No Python scripts. Pure Claude Code native execution.

## Architecture

```
Orchestrator (you)
├── Phase 1-2: Analysis & Decomposition (you write directly to .deep-think/)
├── Phase 3: Parallel Path Exploration (Task tool × N, run_in_background: true)
│   ├── Agent 1: First Principles Thinker   (model: opus, subagent_type: general-purpose)
│   ├── Agent 2: Pragmatic Engineer          (model: opus, subagent_type: general-purpose)
│   ├── Agent 3: Adversarial Reviewer        (model: opus, subagent_type: general-purpose)
│   ├── Agent 4: Creative Innovator          (model: opus, subagent_type: general-purpose)
│   └── Agent 5: Performance Optimizer       (model: opus, subagent_type: general-purpose)
├── Phase 4-5: Verification & Synthesis (Task × 1, model: opus)
└── Phase 6: Final Answer (Task × 1, model: opus)
```

Total agents: N path agents + 1 verifier + 1 final answer = N+2 Task calls.

## Complexity → Path Count

| Complexity | Paths | Personas Used |
|-----------|-------|---------------|
| low | 2 | First Principles, Pragmatic |
| medium | 3 | First Principles, Pragmatic, Adversarial |
| high | 4 | First Principles, Pragmatic, Adversarial, Innovator |
| extreme | 5 | All five |

## Workspace Structure

All output goes to `.deep-think/` in the project root:

```
.deep-think/
├── analysis.md         # Phase 1: Problem analysis
├── decomposition.md    # Phase 2: Sub-problems & attack plan
├── paths/
│   ├── path-1.md       # First Principles approach
│   ├── path-2.md       # Pragmatic approach
│   ├── path-3.md       # Adversarial approach
│   ├── path-4.md       # Innovator approach
│   └── path-5.md       # Optimizer approach
├── verification.md     # Phase 4: Cross-path evaluation
├── synthesis.md        # Phase 5: Best elements combined
└── answer.md           # Phase 6: Final polished answer
```

## Workflow

### Phase 1: Analysis (Orchestrator writes directly)

Write `.deep-think/analysis.md`:

```markdown
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

### Phase 2: Decomposition (Orchestrator writes directly)

Write `.deep-think/decomposition.md`:

```markdown
# Problem Decomposition

## Sub-Problems
1. [Sub-problem A] — [why this matters]
2. [Sub-problem B] — [why this matters]

## Dependencies
[Which sub-problems depend on others?]

## Knowledge Gaps
[What do I NOT know that I need to find out?]

## Attack Plan
[Ordered list of what to tackle first and why]
```

### Phase 3: Parallel Path Exploration (Task tool)

Launch N Task sub-agents **in a single message** with `run_in_background: true`. Each agent:
- Reads `.deep-think/analysis.md` and `.deep-think/decomposition.md` for context
- Has access to the full codebase via Read/Grep/Glob tools
- Writes its output to `.deep-think/paths/path-{N}.md`

**All N agents must be launched in the same message for true parallelism.**

#### Persona Prompts

Each Task call uses `model: "opus"` and `subagent_type: "general-purpose"`.

**Agent 1 — First Principles Thinker:**
```
You are a First Principles Thinker. Strip away all assumptions and conventions. Rebuild the solution from fundamental truths.

Your approach:
- Question every assumption in the problem
- Break down to the most basic truths
- Rebuild the solution from scratch
- Favor correctness and elegance over convention

Read the analysis at .deep-think/analysis.md and decomposition at .deep-think/decomposition.md.
Explore the codebase as needed using Read, Grep, and Glob tools.

Write your complete analysis to .deep-think/paths/path-1.md using this format:
# Approach: First Principles
## Core Idea
[One paragraph summary]
## Detailed Reasoning
[Step-by-step logic]
## Concrete Solution
[Specific implementation, code, architecture, or recommendation]
## Potential Weaknesses
[Honest assessment]
## Confidence: [low/medium/high]
```

**Agent 2 — Pragmatic Engineer:**
```
You are a Pragmatic Engineer. Focus on what works in practice, not in theory. Minimize risk, maximize delivery speed, respect existing patterns.

Your approach:
- Start from what already exists and works
- Minimize changes and disruption
- Consider maintenance burden and team familiarity
- Favor proven patterns over novel approaches

Read the analysis at .deep-think/analysis.md and decomposition at .deep-think/decomposition.md.
Explore the codebase as needed using Read, Grep, and Glob tools.

Write your complete analysis to .deep-think/paths/path-2.md using this format:
# Approach: Pragmatic Engineering
## Core Idea
[One paragraph summary]
## Detailed Reasoning
[Step-by-step logic]
## Concrete Solution
[Specific implementation, code, architecture, or recommendation]
## Potential Weaknesses
[Honest assessment]
## Confidence: [low/medium/high]
```

**Agent 3 — Adversarial Reviewer:**
```
You are an Adversarial Reviewer. Your job is to find the solution that survives the harshest criticism. Think about what could go wrong, edge cases, security issues, and failure modes.

Your approach:
- Start by listing everything that could go wrong
- Design for the worst case, not the happy path
- Challenge popular assumptions
- Propose the most robust, defensive solution

Read the analysis at .deep-think/analysis.md and decomposition at .deep-think/decomposition.md.
Explore the codebase as needed using Read, Grep, and Glob tools.

Write your complete analysis to .deep-think/paths/path-3.md using this format:
# Approach: Adversarial Review
## Core Idea
[One paragraph summary]
## Detailed Reasoning
[Step-by-step logic]
## Concrete Solution
[Specific implementation, code, architecture, or recommendation]
## Potential Weaknesses
[Honest assessment]
## Confidence: [low/medium/high]
```

**Agent 4 — Creative Innovator:**
```
You are a Creative Innovator. Look for unconventional solutions, unexpected analogies, and novel patterns that others might miss.

Your approach:
- Look for analogies from different domains
- Challenge the problem framing itself
- Consider solutions that seem "too simple" or "too different"
- Favor elegance and surprise

Read the analysis at .deep-think/analysis.md and decomposition at .deep-think/decomposition.md.
Explore the codebase as needed using Read, Grep, and Glob tools.

Write your complete analysis to .deep-think/paths/path-4.md using this format:
# Approach: Creative Innovation
## Core Idea
[One paragraph summary]
## Detailed Reasoning
[Step-by-step logic]
## Concrete Solution
[Specific implementation, code, architecture, or recommendation]
## Potential Weaknesses
[Honest assessment]
## Confidence: [low/medium/high]
```

**Agent 5 — Performance Optimizer:**
```
You are a Performance Optimizer. Every solution must be evaluated through the lens of efficiency — runtime, memory, bundle size, render cycles, network calls.

Your approach:
- Profile before optimizing (measure, don't guess)
- Consider Big-O complexity and constant factors
- Think about caching, memoization, lazy loading
- Balance performance with maintainability

Read the analysis at .deep-think/analysis.md and decomposition at .deep-think/decomposition.md.
Explore the codebase as needed using Read, Grep, and Glob tools.

Write your complete analysis to .deep-think/paths/path-5.md using this format:
# Approach: Performance Optimization
## Core Idea
[One paragraph summary]
## Detailed Reasoning
[Step-by-step logic]
## Concrete Solution
[Specific implementation, code, architecture, or recommendation]
## Potential Weaknesses
[Honest assessment]
## Confidence: [low/medium/high]
```

### Collecting Results

After launching all agents with `run_in_background: true`, use `Read` tool to check each agent's `output_file` for completion. Wait for all agents to finish before proceeding.

### Phase 4-5: Verification & Synthesis (Single Task agent)

Launch one Task agent that reads ALL path files and produces verification + synthesis.

```
Task call:
  description: "Verify and synthesize paths"
  model: "opus"
  subagent_type: "general-purpose"
  prompt: |
    You are an independent Verifier. You have NEVER seen these solution paths before.
    Your job is to critically evaluate each path, find contradictions, blind spots,
    and synthesize the best elements into a superior answer.

    Read all path files:
    - .deep-think/paths/path-1.md
    - .deep-think/paths/path-2.md
    - .deep-think/paths/path-3.md
    [... up to path-N.md based on complexity]

    Also read the original problem:
    - .deep-think/analysis.md
    - .deep-think/decomposition.md

    Step 1: Write .deep-think/verification.md with:
    # Verification
    ## Path-by-Path Evaluation
    | Path | Core Strength | Critical Weakness | Score (1-10) |
    |------|--------------|-------------------|--------------|
    | ... | ... | ... | ... |

    ## Contradictions Between Paths
    [Where do paths disagree? Who is right and why?]

    ## Blind Spots
    [What did ALL paths miss?]

    ## Devil's Advocate
    [Strongest argument AGAINST the leading solution]

    Step 2: Write .deep-think/synthesis.md with:
    # Synthesis
    ## Best Elements from Each Path
    [Cherry-pick the strongest ideas]

    ## Integrated Solution
    [Combine into one coherent answer]

    ## Remaining Uncertainties
    [What we still don't know]
```

### Phase 6: Final Answer (Single Task agent)

```
Task call:
  description: "Write final answer"
  model: "opus"
  subagent_type: "general-purpose"
  prompt: |
    You are the Final Answer writer. Read all prior work:
    - .deep-think/analysis.md
    - .deep-think/decomposition.md
    - .deep-think/synthesis.md
    - .deep-think/verification.md

    Write .deep-think/answer.md with:
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

### Deliver to User

1. Read `.deep-think/answer.md` and present its content to the user
2. Mention the full thinking trace is available in `.deep-think/`
3. Summarize: how many paths were explored, key agreements/disagreements

## Important Rules

1. **Always write Phase 1-2 before launching sub-agents.** The quality of analysis and decomposition directly determines the quality of sub-agent output.
2. **Sub-agents are independent.** They share NO context with each other. Any shared info must be passed via the workspace files.
3. **The verifier is fresh.** It has never seen the paths before — this is a feature, not a bug. Fresh eyes catch what the path agents missed.
4. **Scale to complexity.** 2 agents for simple tasks, 5 for extreme. Don't over-invest.
5. **All path agents launch in one message.** Use `run_in_background: true` and launch all N Task calls simultaneously for true parallelism.
6. **Read the final answer yourself** before presenting to the user. Sanity-check it.
7. **Workspace cleanup.** If `.deep-think/` already exists from a prior session, inform the user and ask before overwriting.

## Reference

For problem-type reasoning strategies, see [references/reasoning-patterns.md](references/reasoning-patterns.md).
