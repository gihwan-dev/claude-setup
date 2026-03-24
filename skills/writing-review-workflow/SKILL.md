---
name: writing-review-workflow
description: >
  Review an existing draft with three parallel read-only reviewers, then rewrite it
  into a stronger final version. Use when the user wants structure, reader experience,
  and accuracy reviewed separately before producing the final rewrite. Do not use for
  new writing from scratch (use writing-best-practices instead) or for code review.
allowed-tools: Read, Agent, Edit, Write
---

# Writing Review Workflow

Do not stop at a single direct pass over the draft.
Always run three read-only sub-agents in parallel, collect their perspective-specific reviews, then have the main agent interpret those results and rewrite the final version.

## Core Dependency

- Read `${SKILLS_ROOT}/writing-best-practices/SKILL.md` first so all reviewers share the same writing and quality baseline.
- If that file cannot be read, this workflow loses its standard. Report the missing dependency briefly and stop.

## Hard Rules

- Use this skill only when a draft already exists. If the user provides only a topic, use `writing-best-practices` first.
- Always run exactly three parallel read-only sub-agents.
- Only the main agent may perform the actual rewrite and compose the final sentences.
- If the runtime cannot support parallel multi-agent review, do not collapse this into a single-agent flow. Report that the requirement cannot be met and stop.
- If the user does not specify another language, default to Korean.
- Unless the user explicitly asks otherwise, return only the final revised draft.

## Workflow

### 1) Organize the draft and request constraints

- Read the full draft and identify the writing goal, likely audience, medium, length, and tone constraints.
- Ask one brief follow-up question only if a missing detail would materially change the result.
- If the user specified a format or length, treat that constraint as higher priority than later stylistic preferences.

### 2) Launch three reviewers in parallel

- Launch three read-only sub-agents at the same time.
- Use `${SKILL_DIR}/references/reviewer-prompts.md` for the role cards.
- Give each reviewer the same draft, the same user constraints, and the same output template.
- Each reviewer should review in the draft's actual language, unless the user explicitly requested another language.
- Each reviewer should prioritize must-fix issues from its own perspective over broad rewrite ideas outside its role.

Recommended role split:

- structure reviewer: sentence structure, paragraph focus, sequencing, and transitions
- reader reviewer: reading speed, naturalness, translation tone, cliches, and tonal smoothness
- accuracy reviewer: exaggeration, empty claims, unsupported statements, information density, and polished-but-thin writing

Execution rules:

- Prefer the built-in `explorer` as the read-only base agent when possible, then layer the role through the prompt.
- Require each sub-agent to return only these four sections:
  - `Core Conclusion`
  - `Evidence`
  - `Required Revisions`
  - `Hold`

### 3) Synthesize the review results

After collecting the sub-agent outputs, have the main agent decide with these rules:

- 3/3 agreement: apply it directly.
- 2/1 majority: review the minority rationale, but follow the majority unless it conflicts with an explicit user constraint.
- 1/1/1 split: ask the user a short question only when the choice meaningfully changes the meaning or tone. Otherwise revise conservatively in favor of clarity.
- Do not add unsupported content. If needed, soften the wording or delete the sentence.
- Do not make uncertain factual claims stronger.

### 4) Rewrite the final version in the main agent

- Re-read the draft from the beginning and produce the final version using the synthesized review results.
- Apply the same writing and quality standard from `${SKILLS_ROOT}/writing-best-practices/SKILL.md`.
- Even when restructuring, preserve the draft's core claims and the user's explicit constraints.
- Do not list reviewer comments in the answer. Reflect the judgment in the revised result itself.

### 5) Keep the output format

- By default, return only the revised final draft.
- Add a concise diagnostic summary, revision points, or reviewer-perspective notes only when the user asks for them.
- If you explain the changes, compress them into the agreed essentials instead of dumping verbose review logs.

## Decision Guide

Handle these cases conservatively:

- If a sentence is awkward but mixed with factual judgment, do not broaden the meaning. Rewrite it into a simpler, safer sentence.
- If the tone is good but the information density is weak, trim ornament and move the core sentence earlier.
- If the facts are sound but the reading flow is slow, prioritize sentence splitting, paragraph reordering, and removal of unnecessary transitions.
- If reader friendliness and accuracy pull in different directions, keep the facts intact and rewrite into easier sentences.

## Output Contract

- The default output is only the final revised draft.
- If the user asks for diagnosis, summarize only the integrated revision points instead of dumping each reviewer's full log.
- Present the result immediately without greetings, padded intros, or self-explanation.

## Reference

- reviewer role cards: `${SKILL_DIR}/references/reviewer-prompts.md`
- shared writing baseline: `${SKILLS_ROOT}/writing-best-practices/SKILL.md`
