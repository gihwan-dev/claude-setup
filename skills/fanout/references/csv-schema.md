# CSV Schema

Schema definition for `work-items.csv`, the single data contract used across
all three phases of the fanout pipeline.

## work-items.csv

| Column | Required | Type | Description |
|--------|----------|------|-------------|
| `row_id` | Y | string | Unique ID with phase prefix: `read-001`, `write-001`, `review-001`. 3-digit zero-padded |
| `phase` | Y | string | `read` / `write` / `review` |
| `agent_type` | Y | string | Agent from registry (`explorer`, `verification-worker`, etc.) or `main` for write rows |
| `target_paths` | Y | string | Files or directories to focus on, comma-separated |
| `instruction` | Y | string | Specific task instruction for the agent |
| `depends_on` | N | string | Prerequisite `row_id` list, comma-separated. Write rows depend on read rows; review rows depend on write rows |
| `output_ref` | Y | string | Result file path: `.fanout-cache/{row_id}.md` |
| `acceptance` | N | string | Completion criteria for verification |
| `status` | N | string | `pending` / `running` / `success` / `failed` / `skipped`. Default: `pending` |

## Constraints

- `row_id` must be unique within the CSV
- `row_id` prefix must match `phase` value (`read-*`, `write-*`, `review-*`)
- Write rows must have `agent_type=main` (main agent executes directly)
- Read and review rows must use a valid agent from the agent registry
- `target_paths` must not be empty
- `output_ref` must be unique per row to prevent file collisions

## Phase Ordering

Rows are executed in phase order: all `read` rows first, then `write`, then
`review`. Within a phase:

- **read**: independent rows run in parallel; rows with `depends_on` wait
- **write**: rows execute sequentially in topological order of `depends_on`
- **review**: independent rows run in parallel

## Example

```csv
row_id,phase,agent_type,target_paths,instruction,depends_on,output_ref,acceptance,status
read-001,read,explorer,"src/auth/**",Analyze current auth middleware structure and identify all session handling patterns,,".fanout-cache/read-001.md",Auth patterns documented,pending
read-002,read,explorer,"src/api/routes/**",Map all API routes that depend on auth middleware,,".fanout-cache/read-002.md",Route dependency map complete,pending
read-003,read,web-researcher,,Research JWT best practices for session token compliance,,".fanout-cache/read-003.md",Compliance requirements listed,pending
write-001,write,main,"src/auth/middleware.ts",Refactor session token storage to use encrypted HTTP-only cookies,"read-001,read-003",".fanout-cache/write-001.md",Middleware uses secure cookies,pending
write-002,write,main,"src/auth/session.ts",Update session manager to work with new cookie-based tokens,"read-001,write-001",".fanout-cache/write-002.md",Session manager updated,pending
write-003,write,main,"src/api/routes/auth.ts",Update auth routes to use new session flow,"read-002,write-002",".fanout-cache/write-003.md",Auth routes working,pending
review-001,review,verification-worker,"src/auth/**",Verify auth middleware changes compile and pass existing tests,write-001,".fanout-cache/review-001.md",No type errors or test failures,pending
review-002,review,test-engineer,"src/auth/**,src/api/routes/auth.ts",Check test coverage for new session handling logic,"write-001,write-002,write-003",".fanout-cache/review-002.md",Critical paths have tests,pending
```

## Output Ref Convention

All output files go under `.fanout-cache/` in the project root:

- `.fanout-cache/read-001.md` — exploration findings
- `.fanout-cache/write-001.md` — change summary and decisions
- `.fanout-cache/review-001.md` — review findings

This directory is ephemeral. Suggest cleanup after the pipeline completes.
