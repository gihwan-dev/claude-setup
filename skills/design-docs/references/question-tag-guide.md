# Question Tag Guide

Tags are structured markers embedded directly in doc bodies. They encode
unresolved items without fragmenting context across a separate questions file.
Refine mode scans for these tags, classifies them, and rewrites them in-place.

## Tag Syntax

```
[QUESTION][must-answer] <text>
[QUESTION][nice-to-have] <text>
[ASSUMPTION][candidate] <text>
[ASSUMPTION][confirmed] <text>
[DECISION-CANDIDATE] <option A> | <option B> | <option C>
[SPIKE][required] <assumption> — <test description>
[SPIKE][passed] <assumption> — <observed result>
[SPIKE][failed] <assumption> — <observed result>
```

### Regex

```
^\[(QUESTION|ASSUMPTION|DECISION-CANDIDATE|SPIKE)\](\[[a-z-]+\])?\s+(.+)$
```

The main agent uses this regex in refine mode to enumerate all tags across
every doc in the bundle.

## Tag Semantics

### `[QUESTION][must-answer]`

A question that **blocks implementation**. Used when the writer cannot draft a
section without this answer, and the answer cannot be safely assumed.

- Writer emits when: the information is domain knowledge the user has and
  cannot be inferred from code/docs/external sources.
- Refine triage: **user-required**. Batched ≤3 per turn to the user.
- On resolution: tag is **deleted** and replaced with prose. If the answer
  reveals a decision with trade-offs, an ADR entry is created.

Example:
```
[QUESTION][must-answer] What is the maximum acceptable downtime for the
data migration?
```

### `[QUESTION][nice-to-have]`

A question that **refines but does not block**. Implementation can proceed
with a reasonable default.

- Writer emits when: the section has a workable default but a user answer
  would tighten it.
- Refine triage: **deferred**. Moved to the doc's `## Open Questions`
  section with the reason "refinement only, not blocker".
- Never asked to the user during refine.

Example:
```
[QUESTION][nice-to-have] Should the success toast auto-dismiss after 3s or
stay until user closes it?
```

### `[ASSUMPTION][candidate]`

An assumption the writer made in the absence of an answer. Not yet validated.

- Writer emits when: the writer had to fill a section and chose a reasonable
  default rather than leaving it blank.
- Refine triage: try to self-resolve via `docs-researcher`. If resolved, the
  tag flips to `[ASSUMPTION][confirmed]`. If contradicted, it becomes a
  `must-answer` for the user.
- On confirm: record in the doc's `## Assumptions` section with source.

Example:
```
[ASSUMPTION][candidate] Users are authenticated before reaching this flow,
so no login handling is needed here.
```

### `[ASSUMPTION][confirmed]`

An assumption that has been validated with a source.

- Writer does not emit this directly; refine produces it by promoting
  `[ASSUMPTION][candidate]`.
- Lives in the doc until implementation. Never deleted.

Example:
```
[ASSUMPTION][confirmed] Users are authenticated before reaching this flow
(verified: routes in src/app/router.tsx:42 wrap this in <RequireAuth>).
```

### `[DECISION-CANDIDATE]`

Two or more live options that together form a trade-off. Signals a decision
that needs to be made and recorded.

- Writer emits when: the section could reasonably go two ways and the
  choice affects downstream docs.
- Refine triage: **user-required** if impact is high. Always produces an
  ADR entry once resolved.
- On resolution: replaced with prose referencing the ADR number.

Example:
```
[DECISION-CANDIDATE] store tokens in httpOnly cookie | localStorage | in-memory only
```

### `[SPIKE][required]`

A runtime-only assumption that **must be validated by executing code** before
full design production. Cannot be resolved by reading files or asking the user.

- Plan mode emits when: the assumption depends on external platform behavior,
  API semantics, runtime timing, or other properties that are only observable
  through execution.
- Spike mode resolves: execute the test, record result as `[SPIKE][passed]`
  or `[SPIKE][failed]`.
- **Blocks flesh mode** until resolved. This is the key difference from
  `[ASSUMPTION][candidate]` — candidates can be validated later, spikes
  cannot.
- On pass: replaced with `[SPIKE][passed]` + observation.
- On fail: design must be revised (return to plan) or risk explicitly accepted.

Example:
```
[SPIKE][required] Stop hook fires once per session exit, not per-turn —
Test: add Stop hook that appends timestamp to /tmp/spike-stop.log,
run 1 session with 3 turns, count lines in log file.
Expected: 1 line. If 3 lines → assumption false.
```

### `[SPIKE][passed]` / `[SPIKE][failed]`

Resolved spike. Carries the observed result as evidence.

Example:
```
[SPIKE][passed] sessions-index.json updates before Stop hook fires —
Observed: messageCount=6 at Stop time matches final session count.
```
```
[SPIKE][failed] Stop hook fires once per session — Observed: 3 lines
in log for 3-turn session. Stop fires per-turn, not per-session.
```

## Refine Triage Rules

During refine mode, every tag is placed into exactly one bucket:

| Bucket | Tag types | Action |
|--------|-----------|--------|
| self-resolvable | `[ASSUMPTION][candidate]` with a citation-shaped target | Dispatch `docs-researcher`; promote to `[ASSUMPTION][confirmed]` on evidence |
| user-required | `[QUESTION][must-answer]`, `[DECISION-CANDIDATE]` (high impact) | Batch ≤3 per turn, prefix with question type from `question-taxonomy.md` |
| deferred | `[QUESTION][nice-to-have]`, `[DECISION-CANDIDATE]` (low impact, no blocker) | Move to `## Open Questions` with reason |

### High-impact vs low-impact DECISION-CANDIDATE

A `[DECISION-CANDIDATE]` is **high-impact** (user-required) if any of:
- It affects ≥2 docs in the bundle.
- The options have different operational/rollback profiles.
- The options have different security or compliance implications.

Otherwise it is **low-impact** (deferred).

## Writing Guidance for Flesh-mode Writers

When a flesh-mode Agent fills a template and hits a gap:

1. **Prefer `[ASSUMPTION][candidate]`** if a reasonable default exists. The
   default keeps the doc flowing and refine can validate cheaply.
2. **Use `[QUESTION][must-answer]`** only when no safe default is possible.
3. **Use `[DECISION-CANDIDATE]`** when exactly one of a small enumerated
   set is right, but the writer cannot decide.
4. **Never leave a section blank**. Either fill it, tag it, or mark it
   `N/A` with a reason.
5. **Limit tags per doc**. A single doc with >6 `must-answer` tags is a
   smell: either the writer lacked context (refine interview answers first)
   or the doc is too broad (split it).

## Refine-mode Rewrites

When refine resolves a tag, the rewrite is **in-place** and **complete**:

- `[QUESTION][must-answer]` → prose answer inline, plus ADR entry if
  decision-shaped.
- `[ASSUMPTION][candidate]` → `[ASSUMPTION][confirmed]` with source, OR
  `[QUESTION][must-answer]` if contradicted.
- `[DECISION-CANDIDATE]` → prose referencing `adr/ADR-NNNN-*.md`.
- `[QUESTION][nice-to-have]` → moved to `## Open Questions` with reason.

After rewrite, update `_state.yaml.bundle[].open_questions` counts.
