# Agent Dispatch Guide

Defines which existing agent to dispatch for each (phase, doc-type) pair,
and the context payload shape every dispatch must carry.

## Available Agents

| Agent | Role | Strength | Output shape |
|-------|------|----------|--------------|
| `docs-researcher` | researcher | Reads codebase + docs for evidence, reports found/not-found/confidence | Found / Relevant context / Not found / Confidence |
| `web-researcher` | researcher | External standards, benchmarks, compliance references | Sources / Key findings / Gaps |
| `design-skeptic` | reviewer | Generates counterexamples, failure scenarios, rollback ratings | Attack point / Failure scenarios / Rollback rating / Testability |
| `design-evaluator` | reviewer | Scores design bundle against rubric | Criterion scores / Verdict / Remediation |
| `socratic-partner` | design-partner | Deep reasoning, hidden-assumption surfacing, next-question proposal | Claim / Evidence / Hidden assumptions / Next question |

## Phase × Agent Matrix

### plan phase

| Sub-task | Primary agent | Optional | Purpose |
|---------|---------------|----------|---------|
| Signal inference | `docs-researcher` (parallel, 1 per unknown signal) | — | Find evidence for unknown signals in existing code |
| Work-mode classification | `socratic-partner` (once) | — | Analyze task description and recommend work mode |
| Bundle rationale | — | — | Main agent evaluates `bundle-rules.md` directly |
| External standards check | — | `web-researcher` | Only if user mentions compliance/standards by name |

### flesh phase

| Sub-task | Primary agent | Optional | Purpose |
|---------|---------------|----------|---------|
| Interview execution | — | — | Main agent asks axes directly to user |
| Per-doc writer dispatch | **inline Agent call** (not a named agent) | — | See Per-Doc Dispatch below |

Flesh uses **N parallel Agent calls**, one per doc in the bundle. Each call
is a task-scoped prompt (read template, fill, emit tags, write file) — it
does NOT name a sub-agent from `agents/`. The writer is the dispatched
Agent itself, acting as a template-filler.

### refine phase

| Sub-task | Primary agent | Optional | Purpose |
|---------|---------------|----------|---------|
| Tag enumeration | — | — | Main agent scans with regex |
| Self-resolve `[ASSUMPTION][candidate]` | `docs-researcher` (parallel, 1 per candidate) | — | Find source evidence in code/docs |
| External fact resolve | `web-researcher` | — | If tag references a standard/spec |
| Adversarial review | `design-skeptic` (once, full bundle) | — | Generate attacks on the drafted bundle |
| Completion gate | `design-evaluator` (once, full bundle) | `design-skeptic` rerun | Rubric verdict |
| User-question phrasing | `socratic-partner` | — | Only if user-required batch needs sharpening |

## Per-Doc Dispatch (flesh phase)

For each doc in `_state.yaml.bundle` with `status: placeholder`, dispatch an
Agent call with this prompt structure:

```
You are filling a design document template. You are not a subagent — you
are a task-scoped helper.

Inputs:
- mode: flesh
- doc_type: <prd-lite | ux-flow | architecture-context | adr | ...>
- doc_path: <absolute path>
- template_path: <absolute path to ${SKILL_DIR}/assets/<doc_type>.md>
- task_description: <original user request>
- interview_answers: <YAML block>
- bundle_context: <list of sibling doc names>
- question_tag_spec: <inlined content from question-tag-guide.md>

Instructions:
1. Read the template at template_path.
2. Fill each section using interview_answers + task_description.
3. When you cannot fill a section confidently:
   - Emit [ASSUMPTION][candidate] if a safe default exists
   - Emit [QUESTION][must-answer] if no safe default
   - Emit [DECISION-CANDIDATE] if 2+ options exist with trade-offs
4. Never leave a section blank. Tag or mark N/A with reason.
5. Write the filled template to doc_path.
6. Return JSON: {filled_sections: [...], tags_left: {...counts}, confidence: low|medium|high, notes: "..."}
```

Parallelize up to N dispatches in a single assistant turn (one per doc).

## Self-Resolve Dispatch (refine phase)

For each `[ASSUMPTION][candidate]` tag that references something searchable
(a component name, file path, config key, etc.), dispatch `docs-researcher`:

```
Verify this assumption against the codebase:

Assumption: "<text after tag>"
Context: found in <doc_path>, section "<section heading>"
Task context: <task_description>

Report:
- found: <code/doc paths that support the assumption>
- contradicts: <code/doc paths that contradict it>
- not_found: <true if no evidence either way>
- confidence: <low | medium | high>
- citation: <path:line if found>
```

If `found` is non-empty and confidence ≥ medium → promote to
`[ASSUMPTION][confirmed]` with the citation.
If `contradicts` is non-empty → demote to `[QUESTION][must-answer]` with
the contradiction surfaced.
If `not_found` → leave as `[ASSUMPTION][candidate]` but move to Open
Questions if low impact.

## Context Payload

Every non-writer dispatch (researchers, skeptic, evaluator, partner) must
carry these 5 fields in its prompt:

1. **phase**: plan | flesh | refine | done
2. **work_mode**: architecture | bugfix | refactor | feature
3. **bundle_summary**: doc names + statuses from `_state.yaml`
4. **specific_request**: the exact question this dispatch is answering
5. **doc_excerpt**: relevant section(s) from the target doc(s)

## Synthesis Rules

When combining dispatched agent results before writing to a doc or speaking
to the user:

1. **Single agent**: Use its output directly; rephrase in main-agent voice.
2. **`docs-researcher` + `design-skeptic`**: Researcher's findings become
   evidence; skeptic's attacks become risks. Combine into a single
   `[DECISION-CANDIDATE]` or must-answer question targeting the riskiest
   unverified assumption.
3. **`design-evaluator` standalone**: Summarize per-criterion scores to the
   user. If verdict is `return-and-fix`, identify the single highest-impact
   criterion and return to its mode.
4. **Conflict resolution**: If two agents disagree, surface both and frame
   as a `[compare]` question to the user.
5. **Never forward raw output.** The user sees synthesized insight only.

## Cost and Parallelization

| Situation | Dispatch pattern | Rationale |
|-----------|------------------|-----------|
| Plan-mode signal inference | parallel docs-researcher (1 per unknown, up to 6) | Independent searches |
| Flesh-mode per-doc writing | parallel Agent (1 per doc, up to 8) | Independent template fills |
| Refine-mode self-resolve | parallel docs-researcher (1 per candidate tag, up to 6) | Independent evidence hunts |
| Refine-mode skeptic | single dispatch (whole bundle) | Cross-doc attacks need full context |
| Refine-mode evaluator | single dispatch (whole bundle) | Rubric applies to bundle |
| Optional partner | skip unless complexity demands | Cost control |
