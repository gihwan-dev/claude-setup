# Design Quality Rubric

Use this rubric at the `quality-gate` state. Score each criterion as `pass`, `weak`, or `fail`.
If any **critical** criterion is `fail`, return to the indicated state and resolve it before proceeding.

## Critical Criteria (must all pass)

### 1. Goal clarity

- **pass**: Goal is specific, measurable, and distinguishable from non-goals.
- **weak**: Goal is stated but vague or not measurable.
- **fail**: Goal is missing or indistinguishable from the solution.
- Return to: `frame`

### 2. Success criteria defined

- **pass**: Success criteria are concrete, testable, and directly tied to the goal.
- **weak**: Success criteria exist but are subjective or untestable.
- **fail**: No success criteria, or criteria are just restated goals.
- Return to: `frame`

### 3. System model explainability

- **pass**: The current system (or problem domain) is modeled clearly enough that a new team member could understand the relevant boundaries, data flow, and invariants.
- **weak**: Model exists but has gaps or uses undefined terms.
- **fail**: No system model, or model contradicts the evidence.
- Return to: `system-model`

### 4. Alternatives compared

- **pass**: At least 2 substantively different approaches were compared with explicit trade-offs.
- **weak**: Alternatives exist but comparison is superficial or one-sided.
- **fail**: Only one approach was considered, or alternatives were dismissed without analysis.
- Return to: `alternatives`

### 5. Decision reasoning

- **pass**: The chosen approach has a clear rationale tied to constraints and trade-offs. Rejected alternatives have documented reasons.
- **weak**: Decision is stated but rationale is thin or doesn't reference the trade-off analysis.
- **fail**: Decision is implicit or unjustified.
- Return to: `decision`

### 6. Failure modes identified

- **pass**: At least 3 concrete failure scenarios are documented with their impact and mitigation.
- **weak**: Failure modes are mentioned but vague or lack mitigation.
- **fail**: No failure mode analysis.
- Return to: `adversarial-review`

## Important Criteria (should pass, weak is acceptable)

### 7. Assumption ledger completeness

- **pass**: All assumptions are listed with their status (verified, likely, unverified) and source.
- **weak**: Assumptions are listed but statuses are missing or stale.
- **fail**: No assumption tracking.

### 8. Rollback strategy

- **pass**: A concrete rollback or undo plan exists for the chosen approach.
- **weak**: Rollback is mentioned but not detailed.
- **fail**: No rollback consideration.

### 9. Validation plan

- **pass**: The plan includes what to test, how to test it, and what signals indicate success or failure.
- **weak**: Validation plan exists but is incomplete.
- **fail**: No validation plan.

### 10. Open questions accountability

- **pass**: Remaining open questions are listed, each with a reason (external dependency, not thinking gap) and an owner or next step.
- **weak**: Open questions exist but lack owners or next steps.
- **fail**: Open questions are unacknowledged.

## Scoring

- **Proceed to done**: All 6 critical criteria pass. No important criterion is fail.
- **Proceed with advisory**: All 6 critical criteria pass. 1-2 important criteria are weak.
- **Return and fix**: Any critical criterion is fail, or 2+ important criteria are fail.

Record the score in the design document under `## Quality Gate Result` with the verdict and any required remediation.
