---
name: prompt-builder
description: >
  Transform rough task requests into high-quality structured prompts for AI agents.
  Use when the user wants a request clarified into an execution-ready prompt with goals, completion
  criteria, required context, non-goals, constraints, and edge cases clearly organized.
---

# Prompt Builder

Turn an incomplete user request into a ready-to-run prompt.

## Goal

- Make the goal and completion criteria explicit so the task is less ambiguous.
- Limit context to only what the agent actually needs to read.
- Include high-risk edge cases and response rules directly in the prompt.

## Workflow

### 1) Compress the request into a problem statement

- Restate the user's request in one or two sentences.
- Check which of these fields are still missing:
  - deliverable type
  - completion criteria
  - constraints such as time, performance, policy, or compatibility
  - input data or source location

### 2) Run a two-round Q&A

- Do not ask everything at once. Ask only the most important questions each round.
- Ask at most three questions per round by default.
- Use `${SKILL_DIR}/references/question-flow.md` for question candidates.

Round A (goal alignment):

- What is the exact final deliverable?
- How should success be judged?
- What must be included or excluded?

Round B (risk and exceptions):

- Which conditions or edge cases are most likely to break?
- What fallback or partial-completion outcome is acceptable if something fails?
- What compatibility risks exist with the current system?

### 3) Minimize the context scope

- Prioritize the smallest useful reading list.
- Explicitly list paths or files that should not be read.
- If a path is unclear, do not guess. Ask one short follow-up question.

Use this context instruction format:

- `Must Read`: only files or documents that are required
- `Optional Read`: candidates to read only if needed
- `Do Not Read`: excluded paths, large files, or unrelated documents

### 4) Assemble the final prompt

- Use `${SKILL_DIR}/references/prompt-template.md` as the template.
- Keep the section order:
  - Objective
  - Deliverables
  - Context Plan
  - Constraints
  - Edge Cases
  - Validation Checklist
  - Output Format

### 5) Pass the quality gate

Before returning the final output, check these items:

- Did you remove vague words such as "well," "appropriately," or "if possible"?
- Are the completion criteria measurable?
- Are non-goals stated explicitly?
- Did you include at least three edge cases and response rules?
- Is missing information separated under `Assumptions`?

## Output Rules

- Always provide two versions:
  - `Production Prompt`: a complete version that is ready to run
  - `Quick Prompt`: a short summary version
- Leave at most three items under `Open Questions` at the end.
- If the user provides more answers, update the existing prompt incrementally instead of rebuilding it from scratch.
- Because the prompt may be executed in another worktree, write all paths as project-root-relative paths.

## References

- question catalog: `${SKILL_DIR}/references/question-flow.md`
- prompt template: `${SKILL_DIR}/references/prompt-template.md`
