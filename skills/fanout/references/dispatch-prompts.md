# Dispatch Prompts

Prompt templates for sub-agents dispatched in Phase 1 (Read) and Phase 3
(Review). The main agent fills placeholders from `work-items.csv` columns.

## Dispatch Prompt Contract

Each sub-agent prompt contains exactly these items and nothing else:

1. **Task target** — `target_paths` + `instruction` from the CSV row
2. **Scope boundary** — what is in scope and out of scope for this agent
3. **Return shape** — the expected output format from `phase-contract.md`

Do not include: references to SKILL.md, orchestration rules, budget info,
other rows' data, or pipeline state.

## Phase 1: Read Agent Prompt

```markdown
## Task

{instruction}

## Target

Explore these paths:
{target_paths}

## Scope

- In scope: files and patterns within the target paths relevant to the task
- Out of scope: files outside target paths, code modifications, unrelated modules

## Return Shape

Return your findings in this exact format:

### Summary
{Short paragraph of key findings}

### Evidence
- {file_path}:{line} — {what was found}

### Target Paths
- {paths relevant to downstream work}

### Confidence
{high / medium / low}
```

## Phase 3: Review Agent Prompt

```markdown
## Task

{instruction}

## Target

Review these paths for changes made during implementation:
{target_paths}

## Scope

- In scope: verify correctness, completeness, and quality of recent changes
- Out of scope: pre-existing issues unrelated to the current changes, code modifications

## Acceptance Criteria

{acceptance}

## Return Shape

Return your findings in this exact format:

### Findings
- [{severity}] {file_path}:{line} — {description}
  Tag: {correctness / test-gap / maintainability}

### Summary
{Short paragraph of observations}

### Confidence
{high / medium / low}
```

## Placeholder Rules

- `{instruction}` — from the `instruction` column of the CSV row
- `{target_paths}` — from the `target_paths` column, formatted as a list
- `{acceptance}` — from the `acceptance` column; omit the section if empty
- Referencing a missing column resolves to an empty string

## Agent Type Selection Guide

### Phase 1 (Read) Agent Types

| Situation | Recommended agent |
|-----------|-------------------|
| Codebase structure and patterns | `explorer` |
| External documentation or APIs | `web-researcher` |
| Type contracts and interfaces | `type-specialist` |
| Architecture and boundaries | `architecture-reviewer` |

### Phase 3 (Review) Agent Types

| Situation | Recommended agent |
|-----------|-------------------|
| General correctness verification | `verification-worker` |
| Test coverage and quality | `test-engineer` |
| Structural complexity | `structure-reviewer` |
| Type safety | `type-specialist` |
| React state correctness | `react-state-reviewer` |
| Visual regression | `browser-explorer` |
