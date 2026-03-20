---
name: react-refactoring
description: >
  Critically evaluate React/TypeScript refactoring requests before changing code. When given a React component
  path and a list of concerns, validate whether those concerns are real first, then execute only after a plan
  and explicit approval. Use `references/analysis-modes.md` for detailed analysis modes and prompts, and
  `references/evaluation-criteria.md` for evaluation criteria.
---

# React Refactoring

Do not accept the user's proposal at face value. First verify whether it has real improvement value using the standard of "code that is easy to change."

## Trigger

- `refactor`
- `I want to improve this`
- `change the code structure`
- `extract a hook`
- `cohesion`
- `coupling`
- Requests that include both a React/TypeScript component path and specific concerns

## Required Inputs

- Target component / file path
- The user's list of concerns or proposed changes
- Related imports, hooks, types, and sibling files when the analysis scope must widen

## Core Flow

1. Read the target file and its direct dependencies, then summarize the current structure briefly.
2. Validate whether each concern is truly worth changing using `references/evaluation-criteria.md`.
3. Choose Standard or Multi-Perspective analysis mode based on the number and complexity of concerns. Follow `references/analysis-modes.md` for detailed prompts and questions.
4. For each concern, return one of `accept`, `revise`, or `reject`. If intent or business context is unclear, confirm that first.
5. Build a small-slice refactoring plan from the verdicts and get user approval.
6. After approval, refactor in plan order and run targeted validation plus any necessary test updates.

## Guardrails

- Do not modify code before analysis.
- Do not force changes just because they are "generally good patterns."
- Prioritize the existing codebase style and team conventions.
- State the reasoning and tradeoffs behind each judgment.
- Do not push a large change all at once; break it into incremental steps.

## References

- Evaluation criteria: `references/evaluation-criteria.md`
- Analysis modes, three-perspective prompts, consensus rules, and React/TypeScript checklist: `references/analysis-modes.md`

## Validation

- After refactoring, run targeted validation that matches the change scope.
- If behavior or contracts changed, review or update the related tests as well.
