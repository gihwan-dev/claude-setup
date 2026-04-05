# Bundle Rules

Defines the 8-axis signal model and the conditional document bundle that is
selected from it. The main agent evaluates signals in plan mode, then applies
the conditions below to derive the candidate bundle.

## 8 Axes and Their Signals

Each signal is `true | false | unknown`. Unknown signals become clarification
questions to the user.

| Axis | Signal key | What it means |
|------|-----------|---------------|
| Problem clarity | `has_user_problem` | The user has named a concrete pain or gap |
| Problem clarity | `scope_clarity` | The scope boundary is already stated |
| Interaction | `has_ui` | Work produces or modifies a user interface |
| Interaction | `has_user_interaction` | End users interact with the result (CLI, API, chat ok) |
| Interaction | `public_facing` | External users, not only internal staff |
| Contract | `exposes_api` | Work ships an HTTP/RPC/library API |
| Contract | `changes_contract` | Work modifies an existing consumed contract |
| Architecture | `touches_multiple_services` | Work spans service boundaries |
| Architecture | `new_service` | Work introduces a new deployable unit |
| Architecture | `data_flow_changes` | Data movement, storage, or ownership shifts |
| Architecture | `has_nontrivial_decision` | At least one choice has real trade-offs |
| Sensitivity | `handles_pii` | Personal or confidential data is touched |
| Sensitivity | `auth_changes` | AuthN/AuthZ surface changes |
| Sensitivity | `compliance_required` | Regulation or policy applies (GDPR, SOC2, etc.) |
| Measurement | `requires_measurement` | Success depends on metrics collected post-launch |
| Measurement | `pm_dashboard_needed` | PM/stakeholder wants a live view |
| Scale | `perf_sensitive` | Latency or throughput budgets exist |
| Scale | `scale_sensitive` | Load pattern may change 10× |
| Scale | `new_deployable` | A new production surface appears |
| Work mode | `work_mode` | `architecture \| bugfix \| refactor \| feature` (enum, not bool) |

## Work Mode Classification

Infer `work_mode` from task description before selecting the bundle. It
determines the `mode-playbook` used during flesh mode.

| work_mode | Signals |
|-----------|---------|
| architecture | new_service OR touches_multiple_services OR data_flow_changes, scale/sensitivity axes loaded |
| bugfix | task describes symptom, reproduction, or incident; no new functionality |
| refactor | behavior preservation language ("extract", "reorganize", "clean up"), no new feature |
| feature | user-facing capability described, outcome framed in user terms |

If two modes seem to apply, pick the one that carries more docs in its
bundle (architecture > feature > refactor > bugfix by doc count). Record
the decision in `_state.yaml.work_mode`.

## Bundle Conditions

```yaml
docs:
  prd-lite:
    always: true
    rationale: "Every non-trivial task needs problem, goal, success criteria."

  ux-flow:
    when: "has_user_interaction OR has_ui"
    rationale: "User interacts with the result."

  architecture-context:
    when: "touches_multiple_services OR new_service OR data_flow_changes"
    rationale: "Cross-boundary work needs a drawn system context."

  adr:
    when: "has_nontrivial_decision OR work_mode == architecture OR work_mode == refactor"
    rationale: "Decisions with trade-offs deserve an append-only record."
    note: "Create adr/ subdir. Each decision = one ADR-NNNN file."

  api-contract:
    when: "exposes_api OR changes_contract"
    rationale: "Contracts must be written before implementation."

  nfr-checklist:
    when: "perf_sensitive OR scale_sensitive OR compliance_required"
    rationale: "Non-functional budgets need explicit targets."

  security-privacy:
    when: "handles_pii OR auth_changes"
    rationale: "Threat model + data handling before touching sensitive paths."

  accessibility:
    when: "has_ui AND public_facing"
    rationale: "WCAG criteria apply to public UI."

  analytics:
    when: "requires_measurement OR pm_dashboard_needed"
    rationale: "Event taxonomy must exist before instrumentation."

  ops-runbook:
    when: "new_deployable"
    rationale: "On-call needs diagnostic paths and escalation."
```

## Evaluation Procedure

1. Parse task description into candidate signals.
2. Dispatch `docs-researcher` in parallel for each `unknown` signal with a
   narrow search scope (see `agent-dispatch-guide.md` for payload shape).
3. Merge researcher findings. Any signal still `unknown` → ask the user.
4. Evaluate each `when` condition. Produce:
   - `included`: docs whose condition is satisfied
   - `skipped`: docs whose condition is `false` (record rationale)
   - `uncertain`: docs whose condition has `unknown` signals (ask user)
5. Present the bundle with per-doc rationale. Accept user overrides
   (add-doc, remove-doc). Freeze into `_state.yaml.bundle`.

## App Prototype Default Bundle

If the task description matches "app prototype", "prototype", "MVP app",
or similar, seed the bundle with these before evaluating signals:

- prd-lite (always)
- ux-flow (interaction inferred)
- architecture-context (new deployable inferred)
- adr (decisions will arise)
- accessibility (if public)
- analytics (if growth/validation matters)

This is a heuristic starting point, not a prescription. Signal evaluation
still runs; the user can drop any doc.

## Anti-patterns

- **Don't add a doc just to be thorough.** If the signal says `false`,
  skip with rationale.
- **Don't ask every unknown signal.** Batch ≤3 per turn. Prefer signals
  that swing 2+ docs in the bundle.
- **Don't silently expand bundle later.** If refine discovers a new
  axis activated, re-enter plan mode for that one doc and log it.
