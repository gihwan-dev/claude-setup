# Tier Playbook

## Tier Selection

| Dimension | 0 | 1 | 2 |
|-----------|---|---|---|
| Solution Space Breadth | one answer | few approaches | many paradigms |
| Stakeholder Tension | none | moderate trade-offs | fundamental tension |
| Uncertainty Level | known problem | some unknowns | exploratory |
| Impact Scope | local | module-level | system-wide |

## Tier Workflow Summary

### Tier 1

- 2 agents
- one round of mutual critique or a convergence shortcut
- optimized for fast synthesis

### Tier 2

- 3 agents
- targeted critique
- include structured confidence

### Tier 3

- 4-5 agents
- pre-mortem
- author reflection after critique
- keep disagreement tracking in the final answer

## Track Output

### Track A

Store the frame, paths, critiques, synthesis, and final answer under `.deep-think/`.

### Track B

Leave the following in the plan file.

- Context
- Approach
- Changes
- Confidence Assessment
- Dissenting Views
- Verification

Then wait for approval with `ExitPlanMode`.

## Troubleshooting

- If a path has no evidence tags, make it rewrite the path.
- If a critique is vague, require numbers or a concrete scenario.
- If convergence is unclear, first check whether the recommendations match at the Core Thesis level.
- If the tier is ambiguous, prefer moving one level up rather than down.
