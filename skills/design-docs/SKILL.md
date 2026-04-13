---
name: design-docs
description: >
  Document bundle orchestrator that selects a minimum-sufficient set of design
  docs (PRD, UX flow, architecture, ADR, etc.) based on task risk signals,
  drafts them with inline question tags, and refines them to implementation-ready
  through subagent dispatch. Invoke only when the user explicitly writes
  "design-docs", "$design-docs", or asks to plan/flesh-out/refine a design
  bundle for a task before implementation. Do not use for single-decision
  discussions, code generation, or direct implementation.
allowed-tools: Read, Grep, Glob, Write, Edit, Agent
---

# Design Docs

## Goal

Produce a minimum-sufficient design-doc bundle for a task. Reach the
**implementation-ready** state with all critical questions answered, assumptions
confirmed, and decisions recorded — so the downstream `$plan` or `$build`
skill does not have to guess what or why.

The bundle is a set of files under `tasks/<slug>/design/`, not a single document.
Each file has a status and a confidence level, and carries its own open
questions inline until refine resolves them.

## Hard Rules

1. **No fixed checklist.** Select the bundle from risk signals, not from a
   template. Skipped docs are explicitly logged as `skipped: <reason>`.
2. **No code edits.** Read-only exploration + writes to `tasks/<slug>/design/`
   only. Never touch source files, config, or tests.
3. **Questions live inside documents.** Use `[QUESTION][must-answer]`,
   `[QUESTION][nice-to-have]`, `[ASSUMPTION][candidate]`, `[ASSUMPTION][confirmed]`,
   `[DECISION-CANDIDATE]` tags in the doc body. Do not create a separate
   questions file.
4. **Batch questions to the user.** Never ask more than 3 `must-answer`
   questions in one turn. Prefer the highest-leverage question first.
5. **Never surface raw subagent output.** Synthesize all dispatched agent
   results before speaking to the user.
6. **Decisions belong in ADRs.** Every non-trivial choice made during refine
   (by the main agent or by the user) becomes an `adr/ADR-NNNN-*.md` entry.
7. **Leave CLAUDE.md alone.** Project-wide always-on rules go there, not here.
8. **State file is the single source of truth.** Read `_state.yaml` on entry,
   update it after every write. Do not guess phase from memory.
9. **Mode argument wins.** When `$1 ∈ {plan, flesh, refine}` is given, jump to
   that phase and append a log entry. Otherwise use `_state.yaml.phase`.
10. **Completion gate = must-answer count 0 AND design-evaluator verdict OK.**
    Nothing else marks the bundle done.

## Invocation

```
$design-docs                          # resume from _state.yaml, or ask for slug if missing
$design-docs <task description>       # start new bundle in plan mode
$design-docs plan <task description>  # force plan mode (re-derive bundle)
$design-docs flesh                    # force flesh mode on current bundle
$design-docs refine                   # force refine mode on current bundle
```

**Slug resolution**: derive a kebab-case slug from the task description
(≤4 words). If `tasks/<slug>/` already exists, reuse it. If the user provides
`--slug=<name>`, use that verbatim.

## Mode State Machine

```
plan → spike → flesh → refine → done
  ↑      ↓       ↑        ↓
  └──────┘       └────────┘
  (spike failure    (refine may demote
   revises plan)     docs back to flesh)
```

- **plan**: classify task on 9 axes → select bundle → identify runtime assumptions → create placeholder files → freeze bundle with user approval
- **spike**: validate runtime-only assumptions with minimal executable tests → block flesh until all spikes pass or design adjusts
- **flesh**: conduct abstract interview → dispatch per-doc writers in parallel → fill templates + leave question tags
- **refine**: scan tags → 3-way triage → dispatch researchers for self-resolve → batch must-answer to user → run evaluator gate
- **done**: all docs refined, no must-answer remaining, all spikes passed, evaluator verdict = implementation-ready

## Required References

Load at session start:
- `${SKILL_DIR}/references/bundle-rules.md` — 8-axis signal → doc condition mapping
- `${SKILL_DIR}/references/interview-axes.md` — abstract interview questions for flesh mode
- `${SKILL_DIR}/references/question-tag-guide.md` — tag syntax + refine triage rules

Load on mode entry:
- `${SKILL_DIR}/references/mode-playbooks.md` — per-mode checklist × 4 work modes (arch/bugfix/refactor/feature)

Load before each agent dispatch:
- `${SKILL_DIR}/references/agent-dispatch-guide.md` — which agent per doc-type per mode
- `${SKILL_DIR}/references/question-taxonomy.md` — 6 question types when writing ADRs or refine questions

Load at refine completion:
- `${SKILL_DIR}/references/design-rubric.md` — evaluator gate criteria
- `${SKILL_DIR}/references/failure-patterns.md` — session-level anti-patterns to watch for

## 8-Axis Signal Model

Signals are inferred in plan mode from task description + `docs-researcher`
dispatch against the existing codebase. Each signal is `true | false | unknown`.
Unknown signals become plan-mode clarification questions to the user.

See `${SKILL_DIR}/references/bundle-rules.md` for the full axis → doc mapping.
Summary:

| Axis | Documents it can require |
|------|--------------------------|
| Problem clarity | prd-lite (always) |
| Interaction | ux-flow, accessibility |
| Contract | api-contract |
| Architecture | architecture-context, adr |
| Sensitivity | security-privacy |
| Measurement | analytics |
| Scale | nfr-checklist, ops-runbook |
| **Feasibility** | **spike tests (plan→spike gate)** |
| Work mode | determines mode-playbook (arch/bugfix/refactor/feature) |

## Consultation Loop

Every substantive action during flesh or refine follows this 5-step cycle:

1. **Assess** — read `_state.yaml`, identify the next gap (missing draft,
   unresolved tag, failed rubric criterion).
2. **Select** — pick which doc(s) and which agent to dispatch using
   `agent-dispatch-guide.md`.
3. **Dispatch** — send structured payloads (see Dispatch Payload Shape below).
   Parallelize independent dispatches in one message.
4. **Collect** — receive structured summaries. Do not show raw output to user.
5. **Write** — update target doc(s), update `_state.yaml`, decide next step.

### Dispatch Payload Shape

Every Agent dispatch includes these fields in the prompt:

- `mode`: plan | spike | flesh | refine
- `doc_type`: prd-lite | ux-flow | architecture-context | adr | api-contract | nfr-checklist | security-privacy | accessibility | analytics | ops-runbook
- `doc_path`: absolute path to the target file
- `template_path`: absolute path to the source template
- `task_description`: original user request
- `interview_answers`: k/v pairs from flesh interview (flesh mode only)
- `bundle_context`: names of sibling docs in the bundle
- `question_tag_spec`: inlined snippet from `question-tag-guide.md`

## Mode Workflows

### plan mode

1. If no `tasks/<slug>/design/` exists, create it + `adr/` subdir.
2. Infer 9-axis signals from task description.
3. Dispatch `docs-researcher` in parallel to search the codebase for each
   `unknown` signal. Use the 5-field payload from
   `agent-dispatch-guide.md` for each.
4. For unresolved signals, ask user ≤3 axis questions.
5. Evaluate `bundle-rules.md` conditions → candidate bundle list.
6. **Identify runtime assumptions** — scan signals and task description for
   assumptions that cannot be verified by reading code/docs alone (external
   platform behavior, API semantics, runtime timing, etc.). For each, emit
   a `[SPIKE][required]` tag with a concrete test description (≤10 lines).
7. Present the bundle + spike list to user with per-doc rationale. Accept
   additions / removals. Freeze.
8. Create placeholder files from templates in `assets/`. Write `_state.yaml`
   with `phase: plan`, each doc `status: placeholder`, `confidence: low`,
   and `spikes` list with `status: pending`.
9. Append log entry.
   - If spikes exist: suggest `$design-docs spike` as next step.
   - If no spikes: suggest `$design-docs flesh` as next step.

### spike mode

Validate runtime-only assumptions before committing to full document
production. design-docs is read-only, so it **generates** test scripts and
**asks the user to execute** them (or runs them via Bash if permitted).

1. Read `_state.yaml`. Verify `phase == plan` and `spikes` list is non-empty.
   If no spikes, skip to flesh.
2. For each spike with `status: pending`:
   a. Present the spike description and test script to the user.
   b. Execute the test via Bash (a simple echo/log script, ≤10 lines).
      If Bash is not available or the test requires interactive use
      (e.g. "open a Claude session and check behavior"), ask the user to
      run it manually and report the result.
   c. Record the result in `_state.yaml`: `status: passed | failed`,
      `result: "<observation>"`.
3. After all spikes are resolved:
   - **All passed**: set `phase: spike`, append log, suggest
     `$design-docs flesh`.
   - **Any failed**: present the failure to the user with options:
     a. **Revise plan** — go back to plan mode to adjust the approach
        (remove the failing assumption, pick a different mechanism).
     b. **Accept risk** — proceed to flesh despite the failure, recording
        it as `[ASSUMPTION][candidate]` with `spike_failed: true`.
     c. **Abort** — stop design-docs entirely.
4. If the user chose "revise plan", return to plan mode. Remove or adjust
   the affected signals, bundle docs, and spikes. Log the revision reason.

**Spike test guidelines:**
- Maximum 10 lines of executable code.
- Must produce observable output (file creation, log line, exit code).
- Must complete in under 60 seconds.
- Test the **smallest possible claim** — not the full feature, just the
  assumption (e.g. "does Stop fire per-turn or per-session?").

### flesh mode

1. Read `_state.yaml`. Verify `phase ∈ {plan, spike}` or user forced flesh.
   If spikes exist and any has `status: pending`, warn and suggest spike first.
2. Load `interview-axes.md`. Run abstract interview: 6-8 axes, one question
   per turn. Update interview_answers map in `_state.yaml` after each answer.
3. Once interview is complete, dispatch one Agent call **per doc in bundle**
   in parallel. Each dispatch:
   - reads its template
   - fills known sections from interview_answers
   - emits question tags for gaps
   - writes the target file
   - returns `{filled_sections, tags_left, confidence}`
4. Collect summaries. Update `_state.yaml` — set each doc `status: drafted`,
   record `open_questions.must_answer` and `nice_to_have` counts, update
   `confidence`.
5. Set `phase: refine`, append log, report bundle-level summary to user:
   "N docs drafted. M must-answer questions + K candidate assumptions.
   Run `$design-docs refine` to resolve them."

### refine mode

1. Read `_state.yaml` + scan all bundle docs for question tags with the
   regex from `question-tag-guide.md`.
2. Build triage buckets:
   - **self-resolvable**: tags that name a code/doc/config the agent can read
   - **user-required**: `must-answer` tags + `DECISION-CANDIDATE` with impact
   - **deferred**: `nice-to-have` tags with no blocker
3. Dispatch `docs-researcher` in parallel for self-resolvable items. Each
   returns evidence → main agent rewrites the tag in-place to
   `[ASSUMPTION][confirmed] ...` with a source citation, and appends an
   ADR entry if the resolution was a real decision.
4. Dispatch `design-skeptic` once against the full bundle for adversarial
   review. Collect failure scenarios + rollback ratings.
5. Batch user-required questions ≤3 per turn, prefixed with their question
   type from `question-taxonomy.md`. Record answers → rewrite tags in-place.
6. Move deferred `nice-to-have` tags to each doc's `## Open Questions`
   section with reason.
7. Dispatch `design-evaluator` with the full bundle + `design-rubric.md`.
   Collect verdict.
8. **Completion gate**: if verdict ∈ {proceed, proceed-with-advisory} AND
   must-answer count == 0, set `phase: done`. Otherwise return to the
   failing criterion's mode (plan if scope issue, flesh if draft gap).
9. Append log. Report final bundle summary.

## State File Schema

`tasks/<slug>/design/_state.yaml`:

```yaml
slug: <kebab-case>
work_mode: architecture | bugfix | refactor | feature
phase: plan | spike | flesh | refine | done | blocked
signals:
  has_user_problem: true | false | unknown
  has_ui: true | false | unknown
  # ... all 9 axes (including feasibility)
spikes:
  - id: spike-1
    assumption: "<what must be true>"
    test: "<≤10 line executable test>"
    status: pending | passed | failed
    result: "<observation or null>"
  # empty list if no runtime assumptions identified
interview_answers:
  users_and_jobs: "..."
  success_criteria: "..."
  # populated during flesh
bundle:
  - name: prd-lite
    path: tasks/<slug>/design/PRD.md
    status: placeholder | drafted | refined | skipped
    confidence: low | medium | high
    open_questions:
      must_answer: 0
      nice_to_have: 0
      decision_candidate: 0
    rationale: "<why included, from bundle-rules eval>"
next_action: "<1-line hint>"
log:
  - "2026-04-05T10:00:00Z: phase=plan, bundle frozen with 5 docs"
references:
  socratic_design: docs/design/<slug>.md   # only if present
  brief: tasks/<slug>/BRIEF.md             # only if present
```

See `${SKILL_DIR}/assets/_state.schema.yaml` for the canonical schema +
initial values.

## Completion Gate

A bundle is **implementation-ready** when all of the following hold:

- `phase == done` in `_state.yaml`
- For every doc in bundle: `status == refined` OR `status == skipped`
- Total `must_answer` across bundle == 0
- All spikes: `status == passed` OR `status == failed` with user-accepted risk
- `design-evaluator` returned `proceed` or `proceed-with-advisory`
- Every `DECISION-CANDIDATE` has been either resolved (in an ADR) or
  explicitly deferred with an Open Question reason

Record the final evaluator verdict at the top of the PRD under
`## Quality Gate Result`.

## Session Resumption

On any invocation:

1. Resolve slug (from `$2+` or prompt user).
2. If `tasks/<slug>/design/_state.yaml` does not exist, enter plan mode.
3. Otherwise read it. If `$1` is a mode name, jump to that phase + log
   the forced jump. Otherwise continue from `next_action` under the
   current `phase`.
4. If `phase == done`, report the current bundle and ask whether the user
   wants to re-open any doc (which demotes it back to `flesh`).
