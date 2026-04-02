# Multi-Agent Wave Contract

Use this contract when executing helper-based milestones from `BRIEF.md`.

## Wave 1: Discovery (Read)

### Purpose

Contain uncertainty and avoid context pollution by assigning narrow scopes to
parallel read helpers.

### Required Inputs

- lane name
- bounded scope (paths/questions)
- expected output

### Return Shape

```markdown
## Summary
<key findings>

## Evidence
- <path:line> — <finding>

## Unknowns
- <open question>

## Confidence
<high|medium|low>
```

## Wave 2: Implementation (Build)

### Purpose

Execute bounded slices independently so long-running tasks can progress without
one giant, decaying context window.

### Required Inputs

- slice scope (what this worker may change)
- acceptance criteria
- dependencies from prior wave outputs

### Return Shape

```markdown
## Changes
- <file>: <what changed>

## Decisions
- <decision + rationale>

## Risks
- <known risk or "none">

## Status
<success|failed|blocked>
```

## Wave 3: Independent Review

### Purpose

Counter author bias with reviewer helpers that did not implement the slice.

### Required Inputs

- reviewed scope
- review focus (correctness/tests/architecture/types)
- acceptance criteria

### Return Shape

```markdown
## Findings
- [<critical|major|minor|info>] <path:line> — <finding>

## Summary
<overall quality + risk>

## Confidence
<high|medium|low>
```

## Failure Recovery

1. Retry once with narrower scope and explicit error context.
2. On second failure, mark lane `blocked` and report why.
3. If multiple lanes block and progress is unclear, stop and replan with user.

## Stop/Replan Triggers

- Discovery invalidates core assumptions
- Integration conflicts erase slice boundaries
- Review reports unresolved critical findings

When triggered, pause and present a revised helper plan for approval.
