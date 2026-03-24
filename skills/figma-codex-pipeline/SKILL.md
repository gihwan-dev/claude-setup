---
name: figma-codex-pipeline
description: >
  Page-level Figma-to-Code pipeline using Codex spawn_agents_on_csv. Decomposes
  a Figma page into semantic units, generates code for each component in parallel,
  then integrates and verifies the result. Use for page-level Figma work with
  multiple components. Do not use for single-component work (use figma-to-code instead).
allowed-tools: Bash, Read, Grep, Glob, Write, Agent
---

# Figma Codex Pipeline

A 4-phase pipeline that decomposes a Figma page into semantic units, generates component code in parallel, integrates the outputs, and verifies the result.
It uses Codex `spawn_agents_on_csv` to handle large page-level work without polluting context.

## Trigger

- `/figma-codex-pipeline`
- `implement a Figma page`
- Requests where the Figma URL points to a page-level design with multiple components and parallel generation is useful

## Required Inputs

- Figma URL including `node-id`, pointing to a page or large frame
- Target directory path, for example `src/features/dashboard/ui/`

## Existing Skill References

Reuse token mapping and error-handling rules from existing skills by path reference. Do not duplicate them.

- Token mapping: `skills/figma-to-code/references/token-mapping.md`
- Error handling: `skills/figma-to-code/references/error-handling.md`
- Screenshot capture: `skills/component-screenshot/scripts/capture-screenshot.ts`
- Figma screenshot capture: `skills/design-check/scripts/capture-figma-screenshot.ts`
- Screenshot comparison: `skills/design-check/scripts/compare-screenshots.ts`

## Phase 1: Decompose (Main Agent)

### Step 1-0: Setup Interview

On the first run, or whenever `shared_context.json` does not exist, collect project rules through a short interview.

**Required questions:**
1. Design system library, for example `@exem-fe/react`, `shadcn/ui`, `antd`, or none
2. CSS or styling approach, for example Tailwind + `cn()`, CSS Modules, or styled-components
3. Import alias convention, for example `@/`, `~/`, or relative paths
4. Export style, named vs default
5. Target directory path structure, for example `src/pages/{feature}/`

**Optional questions, depending on the project:**
- State management, routing, API layer, form library, and icon library patterns

Record the answers in the `design_system`, `code_rules`, and `project_patterns` sections of `shared_context.json`.
If `shared_context.json` already exists, show the current settings and ask only whether anything needs to change.

Detailed field rules live in `references/shared-context-spec.md`.

### Step 1-1: Collect Figma Data

1. Extract `fileKey` and `nodeId` from the Figma URL. If the URL uses `.../branch/:branchKey/...`, normalize `branchKey` into `fileKey`
2. Call `get_screenshot`, `get_design_context`, and `get_variable_defs` in parallel with the `clientLanguages=typescript` and `clientFrameworks=react` hints

### Step 1-2: Pre-fetch (Store All Node Data Files)

For each semantic node identified in `design_context`:
1. `get_screenshot(nodeId)` -> `.figma-cache/{nodeId}/screenshot.png`
2. `get_design_context(nodeId)` -> `.figma-cache/{nodeId}/context.json`
3. Page-level `get_variable_defs` -> `.figma-cache/variables.json`
4. Full-page screenshot -> `.figma-cache/page-screenshot.png`

Workers do not call MCP directly. They read only from these files.

### Step 1-3: Decompose into Semantic Units

1. Identify **semantic units** in `design_context`:
   - Independent layout units among the direct children of the top-level frame, such as hero, sidebar, card grid, or filter bar
   - Repeated instances of the same component are merged into a single row
   - Shared primitives like icons and buttons are recorded in `design_system_hint`
2. Fill the `tokens` and `layout` sections of `shared_context.json` using Figma data
3. Generate `components.csv`, recording `.figma-cache/{nodeId}/` in each row's `prefetched_data_dir`

CSV schema: `references/csv-schemas.md`

### Step 1-4: Approval Gate

Show the decomposition result and a `shared_context` summary to the user, then wait for approval.

Display:
- Component list with name, complexity, and `target_path`
- Project rule summary with design system, styling approach, and alias
- Expected token and layout information

**Branching rules:**
- If there is 1 or fewer semantic units, redirect to the existing `figma-to-code` skill and tell the user
- If there are more than 12 semantic units, suggest splitting the work into sub-pages

## Phase 2: Execute (`spawn_agents_on_csv`)

After approval, run parallel code generation using `components.csv` as input.

```python
spawn_agents_on_csv(
  csv_path = "components.csv",
  instruction = executor_prompt,        # See references/agent-prompts.md
  id_column = "row_id",
  output_schema = {
    component_path, exports, tokens_used, dependencies, warnings
  },
  max_concurrency = 6,
  max_runtime_seconds = 300
)
```

Each worker:
1. Reads `screenshot.png` and `context.json` from `prefetched_data_dir`
2. Loads global rules from `shared_context.json`
3. Generates a React component at `target_path`
4. Calls `report_agent_job_result` exactly once

**Independent output principle:** each worker writes only to its own `target_path`. Workers must not reference one another.

**Failure recovery:**
- Retry `status=failed` rows once after appending error context
- Mark rows as skipped after 2 failures
- Stop the pipeline if the overall success rate drops below 50%

Detailed API rules: `references/codex-api-contract.md`
Executor prompt skeleton: `references/agent-prompts.md`

## Phase 3: Integrate (Main Agent)

Read the successful components from the output CSV and integrate them.

1. Create the page root component: assemble layout, imports, and routing or state connections
2. Validate token consistency: reconcile token mismatches across workers
3. Normalize import paths and detect circular dependencies
4. Add responsive wrappers based on `shared_context.json` `layout.breakpoints`
5. Insert TODO placeholders for skipped components

Follow the integration order from `components.csv` `depends_on` relationships and the `parent_id` hierarchy.

## Phase 4: Verify (`spawn_agents_on_csv`)

The main agent creates `verification.csv` and fans out verification.

```python
spawn_agents_on_csv(
  csv_path = "verification.csv",
  instruction = verifier_prompt,        # See references/agent-prompts.md
  id_column = "row_id",
  output_schema = {
    pass, severity, findings, artifact_paths
  },
  max_concurrency = 6,
  max_runtime_seconds = 180
)
```

`check_type`: `lint`, `typecheck`, `screenshot`, `viewport`, `accessibility`

**Storybook fallback:** if Storybook is not available, skip `screenshot` and `viewport` checks, and run only `lint` and `typecheck`.

**Iteration loop:**
- If a Critical issue is found, fix it in Phase 3 and re-run verification, up to 2 rounds
- If Critical issues still remain after 2 rounds, ask the user for manual intervention

## Guardrails

- Stop if the URL has no `node-id`, and request the correct format
- If Figma data collection fails, tell the user to launch the Figma Desktop app. See `skills/figma-to-code/references/error-handling.md`
- Workers must not modify files outside `target_path`
- Use token-based classes instead of hardcoded hex colors. See `skills/figma-to-code/references/token-mapping.md`
- Pre-fetch caches are created per pipeline run. Suggest cleanup after completion

## Output

```text
Figma Codex Pipeline complete: {PageName}

[Phase 1] Decomposition:
- Semantic units: {N} components
- Project rules: {design_system}, {styling}, {alias}

[Phase 2] Code generation:
- Success: {N}/{Total}
- Skipped: {list or "none"}

[Phase 3] Integration:
- Root component: {page_root_path}
- Token reconciliations: {N}
- TODO placeholders: {N}

[Phase 4] Verification:
- lint: {pass/fail}
- typecheck: {pass/fail}
- screenshot: {pass/fail/skipped}
- Critical issues: {N}
```

## References

- CSV schemas: `references/csv-schemas.md`
- `shared_context.json` spec: `references/shared-context-spec.md`
- Codex API contract: `references/codex-api-contract.md`
- Executor and verifier prompt skeletons: `references/agent-prompts.md`
- Token mapping: `skills/figma-to-code/references/token-mapping.md`
- Error handling: `skills/figma-to-code/references/error-handling.md`

## Related Skills

| Skill | Relationship |
|------|------|
| `figma-to-code` | Used for a single component. Redirect here when there is 1 or fewer semantic units |
| `figma-design-pipeline` | Used for single-component implementation plus verification. This skill is for page-level work |
| `design-check` | Referenced for Phase 4 screenshot verification |
| `component-screenshot` | Referenced for Phase 4 implementation screenshot capture |
