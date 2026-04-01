# Phase Contract

Data contracts and execution rules for each phase of the fanout pipeline.

## Phase 1: Read Fan-out

### Execution

1. Filter `phase=read` rows from `work-items.csv`
2. Resolve `depends_on` — rows without dependencies dispatch first
3. Dispatch up to `max_helpers_per_fanout` agents in parallel
4. If more rows than budget, batch: dispatch batch 1, wait, dispatch batch 2
5. Write each agent's result to its `output_ref` path

### Agent Return Shape

Read agents return this shape. If unable, report `blocked` with a reason.

```markdown
## Summary
{Short paragraph of key findings}

## Evidence
- {file_path}:{line} — {what was found}
- ...

## Target Paths
- {paths relevant to the write phase}

## Confidence
{high / medium / low}
```

### Result Handling

| Agent Signal | Action |
|---|---|
| confidence: high | Write findings to `output_ref`, mark `success` |
| confidence: medium | Write findings, mark `success`, flag for user awareness |
| confidence: low | Write findings, mark `success` with caveat in output |
| blocked | Mark `failed`, retry once with narrower scope |
| timeout | Mark `failed`, retry once |

## Phase 2: Write Lane

### Execution

1. Filter `phase=write` rows, sort by topological order of `depends_on`
2. For each row sequentially:
   a. Read all `output_ref` files from `depends_on` rows
   b. Execute the `instruction` — the main agent performs all edits
   c. Record changes made in `output_ref`
   d. Update `status`

### Write Output Shape

After each write, record in `output_ref`:

```markdown
## Changes
- {file_path}: {what changed}
- ...

## Decisions
- {decision made and why, informed by read findings}

## Status
{success / failed}

## Error (if failed)
{error description}
```

### Dependency Resolution

- A write row cannot start until all rows in its `depends_on` are `success`
- If a dependency is `failed` or `skipped`, the dependent write is also
  `skipped` unless the dependency is optional (noted in `acceptance`)

## Phase 3: Review Fan-out

### Execution

1. Filter `phase=review` rows from `work-items.csv`
2. Dispatch review agents in parallel, up to `max_helpers_per_fanout`
3. Each agent reviews the files modified in Phase 2
4. Write results to `output_ref`

### Agent Return Shape

Review agents return this shape:

```markdown
## Findings
- [{severity}] {file_path}:{line} — {finding description}
  Tag: {correctness / test-gap / maintainability}
- ...

## Summary
{Short paragraph of key observations}

## Confidence
{high / medium / low}
```

### Severity Levels

- **critical** — blocks completion; must fix before proceeding
- **major** — should fix; quality or correctness risk
- **minor** — nice to fix; style or minor improvement
- **info** — observation only

### Result Handling

| Review Signal | Action |
|---|---|
| No critical findings | Mark `success`, report summary |
| Critical findings | Mark `success` (review itself passed), surface findings to user |
| blocked | Mark `failed`, note gap in synthesis |

## Failure Recovery

### Per-Row Recovery

1. On first failure, retry once:
   - Append `[RETRY] Previous error: {error}` to the instruction
   - Narrow the scope if the error suggests the task was too broad
2. On second failure, mark `skipped` and continue

### Phase-Level Stop Conditions

- If success rate within a phase drops below 50%, stop the pipeline
- Report which rows failed and their errors
- Suggest the user re-scope or simplify the decomposition

### Budget Exhaustion

- Track fanout count against `max_total_fanouts_per_session`
- Each Phase 1 and Phase 3 dispatch counts as one fanout
- If budget exhausted, report `blocked` and suggest continuing in a new session

## Cross-Phase Data Flow

```
Phase 1 (Read)
  └─ output_ref files ─→ Phase 2 reads these before writing
                            │
Phase 2 (Write)             │
  └─ output_ref files ─→ Phase 3 reads these to know what changed
                            │
Phase 3 (Review)            │
  └─ output_ref files ─→ Synthesis reads all for final report
```

Each phase only reads output from prior phases. No backward data flow.
