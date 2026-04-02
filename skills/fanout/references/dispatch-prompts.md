# Helper Dispatch Prompts

Prompt templates for scoped discovery, bounded implementation, and independent
review lanes.

## Core Contract

Each helper prompt must contain only:

1. Task objective
2. Scope boundary (in/out)
3. Expected return shape

Never include orchestration internals, budget metadata, or unrelated lanes.

## Discovery Helper Prompt

```markdown
## Objective
<objective>

## Scope
In scope:
- <paths/questions>

Out of scope:
- code edits
- unrelated modules

## Return Shape
### Summary
<key findings>

### Evidence
- <path:line> — <finding>

### Unknowns
- <open question>

### Confidence
<high|medium|low>
```

## Implementation Helper Prompt

```markdown
## Objective
<implementation slice objective>

## Scope
In scope:
- <bounded files and change intent>

Out of scope:
- files outside slice
- unrelated refactors

## Acceptance
- <done criteria>

## Return Shape
### Changes
- <file>: <what changed>

### Decisions
- <decision + rationale>

### Risks
- <risk or "none">

### Status
<success|failed|blocked>
```

## Review Helper Prompt

```markdown
## Objective
<review objective>

## Scope
In scope:
- <files/concerns>

Out of scope:
- unrelated legacy issues
- code edits

## Focus
<correctness|tests|architecture|types>

## Return Shape
### Findings
- [<critical|major|minor|info>] <path:line> — <finding>

### Summary
<overall quality assessment>

### Confidence
<high|medium|low>
```

## Lane Design Guidance

- Split by risk boundary, not just by file count.
- Prefer narrow scopes with clear acceptance over broad generic prompts.
- Use separate reviewers when correctness risk is high.
