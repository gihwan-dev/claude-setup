---
name: pm-spec-from-code
description: >
  Convert implemented code into a PM-style spec focused on user-visible behavior and rules.
  Use when the user wants a concise feature spec derived from code, with behaviors, rules, constraints,
  exceptions, and non-goals captured in product language rather than implementation detail.
---

# PM Spec from Code

## Goal

- Produce a product-behavior spec based on the implemented code.
- Prefer short, declarative rule sentences over long explanations.

## Output Format

Write the result in Markdown using this structure.

```md
# <Feature Name> Spec

## Purpose
- <The user problem this feature solves>

## Core Behavior
- <User-visible behavior 1>
- <User-visible behavior 2>

## Detailed Rules
- <A rule in condition -> outcome form>
- <Priority or conflict-resolution rule>

## Constraints And Exceptions
- <Minimum / maximum / disallowed condition>
- <Boundary-case handling>

## Non-goals
- <Scope not covered by this feature>

## Open Questions
- <Policy question that cannot be confirmed from code alone>
```

## Writing Rules

- Put exactly one rule in each bullet.
- End each bullet with a single sentence.
- Avoid vague wording such as "appropriately," "flexibly," or "when possible."
- Do not describe implementation details such as function names, variable names, file paths, state management choices, or library names.
- If the code does not support a conclusion, do not guess. Record it under `Open Questions`.

## Workflow

1. Read the relevant code and extract user-visible behavior.
2. Rewrite the behavior as rule sentences that make the condition and outcome explicit.
3. Separate constraints, exceptions, and non-goals into their own sections.
4. Tighten the wording and remove duplicate rules.

## Example Style

Request: `Create a spec for the table resize feature`

Rule sentence examples:
- Columns without a fixed size share the available width evenly.
- When a column is resized, the columns to its right shrink to absorb the change.
