# Codex API Contract

API usage rules for the Codex `spawn_agents_on_csv` and `report_agent_job_result` calls used by Figma Codex Pipeline.

## spawn_agents_on_csv

### Phase 2: Execute (Generate Component Code)

```python
spawn_agents_on_csv(
    csv_path="components.csv",
    instruction=EXECUTOR_PROMPT,        # Uses {column_name} placeholders
    id_column="row_id",
    output_schema={
        "component_path": "string",     # Actual generated file path
        "exports": "string",            # Exported symbols, comma-separated
        "tokens_used": "string",        # Design tokens used, comma-separated
        "dependencies": "string",       # Imported packages or components, comma-separated
        "warnings": "string"            # Warning messages
    },
    max_concurrency=6,
    max_runtime_seconds=300
)
```

### Phase 4: Verify

```python
spawn_agents_on_csv(
    csv_path="verification.csv",
    instruction=VERIFIER_PROMPT,        # Uses {column_name} placeholders
    id_column="row_id",
    output_schema={
        "pass": "boolean",              # Whether the check passed
        "severity": "string",           # "none" | "minor" | "major" | "critical"
        "findings": "string",           # Description of findings
        "artifact_paths": "string"      # Generated artifact paths, comma-separated
    },
    max_concurrency=6,
    max_runtime_seconds=180
)
```

## Instruction Placeholder Rules

Within the `instruction` parameter, `{column_name}` references a CSV column value.

- `{row_id}` -> replaced with that row's `row_id` value
- `{component_name}` -> replaced with that row's `component_name` value
- Referencing a column that does not exist in the CSV resolves to an empty string
- Placeholders may appear anywhere inside the instruction text

## report_agent_job_result

Each worker calls this exactly once when the job is complete.

```python
report_agent_job_result(
    row_id="{row_id}",
    status="success" | "failed",
    output={
        # Fields defined in output_schema
    }
)
```

### Rules

- Call exactly once per worker. No duplicate calls.
- Even when `status="failed"`, include as much error information as possible in `output`.
- If a worker exits without calling this, it is treated as a timeout after `max_runtime_seconds`.

## Failure Recovery Strategy

### Phase 2 (Execute) Failure Recovery

1. After `spawn_agents_on_csv` completes, collect rows with `status=failed` from the output CSV
2. Append error context to `acceptance_criteria` for the failed rows using a note like `[RETRY] Previous error: {error}. Try a different approach`
3. Generate `components_retry.csv` with only the failed rows
4. Retry once with the same `spawn_agents_on_csv` call
5. If a row fails twice, mark it as `skipped`

### Phase 4 (Verify) Failure Recovery

1. If a Critical issue is found, fix it in Phase 3
2. Generate a verification CSV containing only the affected component
3. Repeat up to 2 rounds

### Stop Conditions

- If the overall Phase 2 success rate is below 50%, stop the pipeline and ask the user to revisit decomposition
- If Phase 4 Critical issues remain unresolved after 3 rounds, ask the user for manual intervention

## Concurrency Guidelines

| Parameter | Phase 2 | Phase 4 | Rationale |
|----------|---------|---------|------|
| `max_concurrency` | 6 | 6 | Stays within the Codex default limits |
| `max_runtime_seconds` | 300 | 180 | Code generation takes longer than verification |

If there are 6 or fewer components, run them all concurrently. If there are more, dispatch them through the queue.

## Independent Output Principle

- Each worker creates or modifies files only at its own `target_path`
- No cross-worker file references, imports, or direct dependencies
- Shared context is accessed only through `shared_context.json`, which is read-only
- Integration work that needs outputs from multiple workers is handled by the main agent in Phase 3
