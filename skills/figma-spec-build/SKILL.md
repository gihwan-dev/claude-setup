---
name: figma-spec-build
description: >
  Extract spec text from Figma frame "Description" side panels via the installed
  Figma MCP, propose codebase component mappings for each spec row, and produce
  structured spec files with component mappings. Use when the user provides one
  or more Figma frame URLs containing a "Description" panel and asks to turn
  them into an implementation plan (e.g. "Figma Description으로 구현해줘",
  "이 기획서 링크들 스펙 뽑아서 작업해줘", "$figma-spec-build",
  "figma-spec-build"). Do not use for pure design-to-code translation (that is
  figma:figma-implement-design) or for writing back to Figma.
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, Skill, AskUserQuestion
---

# Figma Spec Build

Turn Figma "Description" side panels into machine-readable spec files and map
each numbered section to candidate codebase components. The user decides how to
proceed with the output (create issues, feed to Codex, etc.).

## When this skill fires

- User shares one or more `figma.com/design/...` URLs AND mentions extracting
  specs, "Description", "스펙", "설명 영역", or asks to build from them.
- User writes `$figma-spec-build` or `figma-spec-build` verbatim.

## When NOT to use

- Pure pixel design-to-code with no textual spec → use
  `figma:figma-implement-design`.
- User wants to push code INTO Figma → use `figma:figma-generate-design` +
  `figma:figma-use`.
- `mcp__plugin_figma_figma__*` tools are unavailable (Figma MCP not installed)
  → stop and report.
- URL is `figma.com/board/...` (FigJam) → not supported.

## Hard Rules

1. **Read-only toward Figma**: only `get_metadata`, `get_design_context`,
   `get_screenshot` are allowed. Never call `use_figma` from this skill.
2. **Scope MCP calls to Description nodes**, not whole frames.
   Whole-frame `get_design_context` produces 100KB+ output; per-Description
   calls are ~8KB. Whole-frame `get_metadata` is fine (only ID/name/position).
3. **Scripts do heavy parsing.** Claude reads only clean markdown outputs
   (`tasks/<slug>/specs/*.md`), never raw XML/JSX.
4. **Checkpoint at every phase.** Never jump from extraction to
   implementation without user approval.
5. **No FIGMA_TOKEN needed.** Reuse the installed Figma MCP.
6. **"Description" frame name is hardcoded.** `x=1920` is the fallback hint.
7. **This skill produces specs and mappings, not code.** Implementation is
   the user's decision (Codex, manual, etc.).

## Workflow Phases

```
Phase 0: Bootstrap  — verify MCP, collect URLs, create slug
Phase 1: Extract    — per URL: find Description nodes, get JSX+screenshot, convert to markdown
Phase 2: Map        — per section: suggest candidates via grep, user confirms
Phase 3: Brief      — synthesize tasks/<slug>/BRIEF.md from specs + mappings
Phase 4: Handoff    — present artifacts and suggest next steps
```

Each phase ends with a checkpoint. User replies with one of:
`[1] Approve and continue` `[2] Modify` `[3] Add context` `[4] Stop here`.

### Phase 0: Bootstrap

1. Verify Figma MCP tools exist (attempt a minimal `get_metadata` on first
   URL, or check `mcp__plugin_figma_figma__*` is in the available tools list).
2. Collect all URLs from user. Accept one per line or comma-separated.
3. Derive a kebab-case slug (≤4 words) from a user-provided task name. Ask
   if missing.
4. Create workspace:
   ```
   tasks/<slug>/
     figma/urls.txt
     figma/raw/          (get_metadata XML, get_design_context JSX dumps)
     figma/screenshots/  (frame PNGs)
     specs/              (clean markdown)
   ```

**Checkpoint**: "Found N URLs. Slug is `<slug>`. Proceed with extraction?"

### Phase 1: Extract

For each URL in `tasks/<slug>/figma/urls.txt`, sequentially:

1. Parse URL:
   ```bash
   python3 ${SKILL_DIR}/scripts/parse_url.py "<url>"
   ```
   Captures `fileKey`, `nodeId`, `fileName`.

2. Fetch metadata (lightweight XML, text content NOT included):
   ```
   mcp__plugin_figma_figma__get_metadata(fileKey, nodeId)
   ```
   Save raw output to `tasks/<slug>/figma/raw/metadata_<nodeId>.xml`.

3. Find Description nodes:
   ```bash
   python3 ${SKILL_DIR}/scripts/find_description_nodes.py \
     --metadata tasks/<slug>/figma/raw/metadata_<nodeId>.xml
   ```
   Returns JSON: `[{node_id, parent_node_id, parent_name, x, y, ...}]`.

4. For each Description node:
   - Call `get_design_context(fileKey, <desc_node_id>, excludeScreenshot=true)`
     and save JSX to `tasks/<slug>/figma/raw/dc_<desc_node_id>.jsx`.
   - Convert JSX to markdown:
     ```bash
     python3 ${SKILL_DIR}/scripts/jsx_to_spec.py \
       tasks/<slug>/figma/raw/dc_<desc_node_id>.jsx \
       > tasks/<slug>/specs/<parent_node_id>__<desc_node_id>.md
     ```

5. Capture screenshot of the PARENT frame (not Description):
   ```
   mcp__plugin_figma_figma__get_screenshot(fileKey, <parent_node_id>)
   ```
   Save to `tasks/<slug>/figma/screenshots/<parent_node_id>.png`.

**Output**: `specs/*.md` (clean markdown), `screenshots/*.png`.

**Checkpoint**: list frames + section counts + spec paths. Ask to proceed to
mapping.

### Phase 2: Map

For each spec file under `tasks/<slug>/specs/`:

1. Determine target repo path. Default: current working directory. Ask user
   if ambiguous (monorepo, frontend subdir, etc).

2. Run mapping suggester:
   ```bash
   python3 ${SKILL_DIR}/scripts/suggest_mappings.py \
     --spec tasks/<slug>/specs/<file>.md \
     --repo <repo_path> \
     --top-n 5
   ```

3. For each section with candidates, present via `AskUserQuestion`:
   - Label each option: `<path> (score X.XX, <reason>)`
   - Include: `[new component: <suggested name>]` option
   - Include: `[skip this section]` option
   - Maximum 4 options per AskUserQuestion (1 is "Other" implicit); if there
     are 5 candidates, show top-3 + "new component" + fall through to "Other".

4. Save to `tasks/<slug>/mappings.json`:
   ```json
   {
     "<frame_node_id>": {
       "spec_path": "specs/<id>.md",
       "screenshot_path": "figma/screenshots/<id>.png",
       "sections": [
         {"id": "1", "title": "Date 설정 드롭다운",
          "mapping": {"type": "existing", "path": "src/..."}},
         {"id": "2", "title": "좌측 정보 영역",
          "mapping": {"type": "new", "proposed_name": "LeftInfoPanel"}}
       ]
     }
   }
   ```

**Checkpoint**: summary ("N sections mapped: X existing, Y new, Z skipped").
Ask to synthesize BRIEF.

### Phase 3: Brief

Draft `tasks/<slug>/BRIEF.md` with sections:
`Goal / Context / Scope / Success Criteria / Phases / Decisions / Risks /
References / Status / Log`.

**Phase decomposition rules**:
- Group mappings by target file. One BRIEF phase per target file, or per new
  component.
- "New components" come first (so existing files can depend on them).
- Each BRIEF phase's **Inputs** lists: spec markdown path, screenshot path,
  target code file path, section IDs within the spec that drive this phase.
- Each phase's **Done when** copies the section bullets verbatim as
  behavioral acceptance criteria.
- **Verification** defaults to the project's usual lint+build+test commands
  if detectable; otherwise leaves a `# TODO: verification command` stub.

**References** section includes the Figma URLs (source of truth).

**Checkpoint**: present the BRIEF phase list. Ask: "N phases drafted. Approve
or modify?"

### Phase 4: Handoff

1. Print artifact summary:
   ```
   tasks/<slug>/
     BRIEF.md
     mappings.json
     specs/        (N files)
     figma/screenshots/ (N images)
   ```
2. Suggest next steps: create issues, feed to Codex, or proceed manually.

## Cooperation With Existing Skills

| Skill | Relation |
|-------|----------|
| `figma:figma-implement-design` | Complementary. That skill does pixel-fidelity code-gen for whole designs. This skill extracts **textual spec** for structured implementation planning. |
| `architect` | Use before this skill to explore design trade-offs. This skill handles Figma-specific extraction; architect handles design reasoning. |
| `figma:figma-use` | Not used. We only read from Figma. |

## Session Resumption

Each phase writes `tasks/<slug>/figma/state.json`:
```json
{"phase": "extract|map|brief|done",
 "urls": [...],
 "completed_frames": [...],
 "pending_frames": [...]}
```
On re-invocation, read this file to resume from the last completed phase.

## Examples

### Example invocation

User:
```
$figma-spec-build

https://www.figma.com/design/0CWIMb3Apd7wAiy66OqURb/Analysis?node-id=19030-97432&m=dev
https://www.figma.com/design/0CWIMb3Apd7wAiy66OqURb/Analysis?node-id=19030-98200
```

Claude responses (phase by phase):
1. "Found 2 URLs. What slug should I use?" → user: "sql-detail-spec"
2. "Workspace created at tasks/sql-detail-spec/. Proceed?" → user: "[1]"
3. [extracts 6 Descriptions across 2 frames] → "Review specs under
   tasks/sql-detail-spec/specs/. Proceed to mapping?" → "[1]"
4. [presents candidates per section] → user confirms each
5. [drafts BRIEF.md] → "N phases drafted. Approve?" → "[1]"
6. "Ready. Create issues or feed to Codex?"
