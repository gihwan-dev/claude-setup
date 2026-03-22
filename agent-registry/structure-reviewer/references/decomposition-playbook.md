# Structure Reviewer Decomposition Playbook

## Threshold Source

- The canonical source for quantitative thresholds is `policy/workflow.toml [structure_review]`.
- Do not place LOC thresholds, FAIL rules, or split-first procedure in the profile prompt.

## Structural Smells

- File bloat
- Responsibility mixing
- branch-heavy accretion
- Accumulation of repetitive stateful logic
- Public export sprawl
- Service or orchestration code leaking into component or view layers

## Role Taxonomy

- `component`
- `view`
- `hook`
- `provider`
- `view-model`
- `composable`
- `middleware`
- `service`
- `use-case`
- `repository`
- `controller`
- `util`
- `adapter`

## Notes

- Interpret exceptions such as generated files, route manifests, schema declarations, and migration snapshots according to policy.
- Use quantitative metrics as supporting evidence for design smells, not as the sole verdict.

## Hotspot Review Mode

- When orchestration passes `review_mode = diff+full-file-hotspots` and `diff+full-file-hotspots`, keep the diff review and hotspot full-file review distinct.
- Read every file in `hotspot_paths` as a maintenance boundary, not just the changed hunks.
- Keep hotspot scope capped by orchestration; if more files qualified than were passed in, mention that the cap may hide lower-severity follow-up work.
- Treat legacy oversized files that continue to grow as a stronger escalation than a newly oversized file.

## Required Outputs

- `maintainability_verdict`
- `reason_codes`
- `decomposition_boundary`
- `is_blocking`
