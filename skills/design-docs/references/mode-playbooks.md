# Mode Playbooks

design-docs has two orthogonal mode dimensions:

- **Phase mode** (the state machine): `plan → flesh → refine → done`
- **Work mode** (the task category): `architecture | bugfix | refactor | feature`

This file describes what matters in each **phase × work-mode** cell. Load
the relevant row at each phase entry.

## Phase × Work-Mode Matrix

### Phase: plan

Common to all work modes: infer 8-axis signals, freeze the bundle, create
placeholders.

| Work mode | Plan-phase emphasis |
|-----------|---------------------|
| architecture | Lean heavily on `architecture-context` and `adr`. Likely signals: `touches_multiple_services`, `new_service`, `data_flow_changes`, `scale_sensitive`. Ask about quality attributes and operational boundaries. |
| bugfix | Often a 1-doc bundle: `prd-lite` (as incident summary) + `adr` (fix strategy). Likely signals mostly `false`. Skip ux-flow, nfr-checklist unless regression area demands it. |
| refactor | Signals: `changes_contract` (maybe), `data_flow_changes` (maybe). Bundle typically `prd-lite` + `architecture-context` (before/after) + `adr` (migration strategy). |
| feature | The "full bundle" case. Most axes probable. Use the app-prototype default seed if prompt matches, then trim via signal evaluation. |

### Phase: flesh

Common to all work modes: run abstract interview, dispatch per-doc writers.

| Work mode | Flesh-phase emphasis |
|-----------|---------------------|
| architecture | Interview axes 5-8 (reuse surface, data/integrations, quality attributes, future direction) are the critical ones. `[DECISION-CANDIDATE]` tags will dominate architecture-context and ADRs. |
| bugfix | Interview is short: axes 1-3 are usually already answered in the incident report. Jump to drafting. Focus on reproduction steps + invariant that broke + candidate fix. |
| refactor | Axes 3 (scope/non-scope) and 5 (reuse surface) are critical. The PRD section "what behavior must be preserved" must be exhaustive. Most tags will be `[ASSUMPTION][candidate]` about caller behavior. |
| feature | All 8 axes matter. This is where ux-flow gets the most tags; resist filling UI minutiae (button colors, exact copy) with `[QUESTION][must-answer]` — those are `[nice-to-have]`. |

### Phase: refine

Common to all work modes: scan tags, triage 3 ways, dispatch skeptic + evaluator.

| Work mode | Refine-phase emphasis |
|-----------|---------------------|
| architecture | `design-skeptic` should attack cascading failures, SPOFs, deployment coupling. Ask the user `risk` questions about 3am diagnosis. Every `[DECISION-CANDIDATE]` spawns an ADR. |
| bugfix | `design-skeptic` should attack the fix, not the design. Questions: "Is this the root cause or a symptom?" "What other paths share this assumption?" Regression test plan must exist before done. |
| refactor | `design-skeptic` attacks behavior-preservation claims. Every `[ASSUMPTION][candidate]` about caller behavior must be verified via `docs-researcher` against actual callers. |
| feature | `design-skeptic` attacks edge cases + abuse scenarios. UX flow + analytics doc must describe both happy path and error/empty states. |

### Phase: done

No work-mode variance. Evaluator verdict + final summary to user.

## Per Work-Mode Priority Questions

When the main agent is formulating a user-facing refine question, prefer
these question shapes for the current work mode.

### architecture

- `[constrain]` Which quality attributes are non-negotiable?
- `[clarify]` Where does ownership end for this service?
- `[falsify]` If service B is down for 5 minutes, what happens to service A?
- `[risk]` What does the on-call engineer need to diagnose this at 3am?
- `[compare]` Sync call vs event: which failure mode is more acceptable?

### bugfix

- `[clarify]` What is the exact sequence of actions that reproduces this?
- `[clarify]` When did this start? What changed around that time?
- `[falsify]` Is this the root cause, or a symptom of something deeper?
- `[falsify]` If we apply this fix, does the original invariant actually restore?
- `[risk]` What other code paths share this assumption and could break the same way?
- `[validate]` Does the regression test cover the exact reproduction scenario?

### refactor

- `[constrain]` Can we break any existing callers, or is full backward compatibility required?
- `[clarify]` What implicit behavior do callers depend on beyond the documented API?
- `[compare]` Incremental strangler fig vs clean rewrite: what's the risk/effort trade-off?
- `[falsify]` If we change this internal structure, does the public behavior actually stay identical?
- `[risk]` What happens if we need to roll back after 50% of callers have migrated?
- `[validate]` Does the existing test suite cover the behavior we claim to preserve?

### feature

- `[clarify]` What user problem does this solve? How will we know it's solved?
- `[constrain]` What is explicitly out of scope for the first release?
- `[clarify]` Walk through the user journey step by step. What happens at each decision point?
- `[falsify]` What happens when the user does the unexpected thing?
- `[compare]` Approach A is simpler for the user but harder to extend. Approach B is the reverse. Which trade-off aligns with the product direction?
- `[risk]` If this feature is used 10x more than expected, what breaks first?
- `[validate]` Do the acceptance criteria actually cover the user problem we stated?

## Mode Handoff Notes

- **plan → flesh**: Verify every signal is resolved (no `unknown`). If any
  remain, either ask one more question or mark the affected doc `skipped`
  with rationale.
- **flesh → refine**: Verify every doc in bundle has `status == drafted`.
  A doc stuck at placeholder means flesh failed for it — investigate before
  refining.
- **refine → done**: See `design-rubric.md` for the full gate. Shorthand:
  all critical pass + must-answer count 0.
