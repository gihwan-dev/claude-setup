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
