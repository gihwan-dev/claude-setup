---
name: deep-think
description: >
  Adaptive multi-persona deep reasoning with tiered complexity (2-5 agents) and convergence-based synthesis.
  Deep Think v2 — Adaptive multi-persona reasoning with evidence-based depth.
  Uses tiered complexity (2-5 agents), targeted critique→reflect cycles,
  convergence shortcuts, and 3-pass PENCIL-inspired synthesis.
  Detects execution environment to choose between Agent Teams (normal mode)
  and Task Orchestration (plan mode).
  Use when the user prefixes with `deep think`, uses an equivalent phrase meaning
  "think deeply", or requests thorough analysis. Best for complex architecture,
  debugging, algorithmic, or multi-domain problems. NOT for simple lookups.
  Track A requires Agent Teams feature (Claude Code: CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1). Track B works on any platform.
---

# Deep Think v2

This is a reasoning workflow for complex problems using tier-based, multi-perspective analysis.

## Trigger

- `deep think`
- any equivalent request meaning "think deeply"
- problems that are hard to answer in a single pass, such as architecture, debugging, algorithms, or multi-domain trade-offs

Do not use this for simple lookups, short fact checks, or an obvious one-file edit.

## Track Routing

- If the system prompt contains `Plan mode is active`, use Track B.
  - Task Orchestration
  - Write the result to the plan file
- Otherwise, use Track A.
  - Agent Teams
  - Leave `.deep-think/05-answer/answer.md` and a report

Track A only prerequisite:

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

## Tier Routing

Score the problem from 0-2 on each of the four dimensions below.

- Solution Space Breadth
- Stakeholder Tension
- Uncertainty Level
- Impact Scope

| Tier | Score | Agents | Default meaning |
|------|-------|--------|-----------|
| Tier 1 | 0-2 | 2 | Focused comparison |
| Tier 2 | 3-5 | 3 | Standard deep dive |
| Tier 3 | 6-8 | 4-5 | Composite / high-risk |

See `references/persona-catalog.md` for persona details.

## Core Workflow

1. Phase 0: frame the problem and choose the tier and personas.
2. Phase 1: each persona writes an evidence-tagged path in parallel.
3. Phase 2: inspect convergence and decide whether to shorten the challenge round.
4. Phase 3:
   - all tiers: targeted critique
   - Tier 3: add pre-mortem and author reflection
5. Phase 4: run the `Extract -> Reconcile -> Compose` three-pass synthesis.
6. Phase 5: produce the final answer with structured confidence and dissent.

## Path Contract

Each path must contain at least the following.

1. Core Thesis
2. Evidence Chain
   - tag every claim with one of `[CODE]`, `[BENCH]`, `[PATTERN]`, `[REASON]`, or `[ASSUME]`
3. Implementation Sequence
4. Risk Register
5. What This Path Uniquely Offers

`[ASSUME]` items must be surfaced explicitly in the final answer as unverified assumptions.

## Guardrails

- Critique must include concrete scenarios. Drop vague critique during synthesis.
- If convergence is strong, skip the challenge round to save time.
- If the tier is ambiguous, bias one level higher.
- Do not concatenate raw path text into the final answer. Rewrite it from the synthesis result.
- End with a blind-spot check.

## References

- persona definitions: `references/persona-catalog.md`
- tier/track playbook: `references/tier-playbook.md`
- phase templates: `references/phase-templates.md`
- reasoning patterns by problem type: `references/reasoning-patterns.md`
- execution scripts:
  - `scripts/deep_think.py`
  - `scripts/evaluate_paths.py`
