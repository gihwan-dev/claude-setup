# Design Quality Rubric

Used by `design-evaluator` at the refine-mode completion gate. Score each
criterion as `pass`, `weak`, or `fail`. If any **critical** criterion is
`fail`, return to the indicated mode + doc and resolve it before proceeding
to `done`.

## Critical Criteria (must all pass)

### 1. Goal clarity

- **pass**: Goal in PRD is specific, measurable, distinguishable from non-goals.
- **weak**: Goal stated but vague or not measurable.
- **fail**: Goal missing or indistinguishable from the solution.
- Return to: `flesh`, doc=`prd-lite`

### 2. Success criteria defined

- **pass**: Success criteria are concrete, testable, tied to the goal.
- **weak**: Criteria exist but subjective or untestable.
- **fail**: No criteria, or criteria are just restated goals.
- Return to: `flesh`, doc=`prd-lite`

### 3. System model explainability

- **pass**: Architecture-context (or equivalent) models boundaries, data
  flow, and invariants clearly enough for a new team member.
- **weak**: Model exists but has gaps or uses undefined terms.
- **fail**: No system model, or model contradicts the evidence. (Only
  enforced when `architecture-context` is in the bundle.)
- Return to: `flesh`, doc=`architecture-context`

### 4. Alternatives compared

- **pass**: Every ADR has ≥2 substantively different options with explicit
  trade-offs.
- **weak**: ADRs exist but comparisons are superficial or one-sided.
- **fail**: ADRs missing for decisions that obviously had options, or only
  one option considered. (Only enforced when `adr` is in the bundle.)
- Return to: `refine`, bucket=decision-candidates

### 5. Decision reasoning

- **pass**: Chosen path in each ADR has rationale tied to constraints and
  trade-offs. Rejected alternatives have documented reasons.
- **weak**: Decision stated but rationale thin or doesn't reference trade-offs.
- **fail**: Decision implicit or unjustified.
- Return to: `refine`, bucket=decision-candidates

### 6. Failure modes identified

- **pass**: ≥3 concrete failure scenarios documented across the bundle with
  impact and mitigation. (Typically in nfr-checklist, security-privacy, or
  ops-runbook.)
- **weak**: Failure modes mentioned but vague or lack mitigation.
- **fail**: No failure mode analysis.
- Return to: `flesh`, doc=`nfr-checklist` or `security-privacy`

## Important Criteria (should pass, weak is acceptable)

### 7. Assumption ledger completeness

- **pass**: All `[ASSUMPTION][confirmed]` entries have a source. No
  `[ASSUMPTION][candidate]` remains unresolved.
- **weak**: Assumptions tracked but sources missing or stale.
- **fail**: Candidates still present, no refine pass done.

### 8. Rollback strategy

- **pass**: A concrete rollback/undo plan exists for each deployed change.
- **weak**: Rollback mentioned but not detailed.
- **fail**: No rollback consideration.

### 9. Validation plan

- **pass**: PRD or ops-runbook names what to test, how, and what signals
  success/failure.
- **weak**: Validation plan exists but incomplete.
- **fail**: No validation plan.

### 10. Open questions accountability

- **pass**: Remaining open questions listed per doc with reason (external
  dependency, not thinking gap) and owner or next step.
- **weak**: Open questions exist but lack owners or next steps.
- **fail**: Open questions unacknowledged or still look like `[must-answer]`
  tags.

## Scoring

- **Proceed to done**: All 6 critical criteria pass. No important criterion
  is fail.
- **Proceed with advisory**: All 6 critical criteria pass. 1-2 important
  criteria are weak.
- **Return and fix**: Any critical criterion is fail, OR 2+ important
  criteria are fail.

Record the evaluator verdict at the top of `tasks/<slug>/design/PRD.md`
under `## Quality Gate Result` with the verdict, per-criterion scores, and
any required remediation.
