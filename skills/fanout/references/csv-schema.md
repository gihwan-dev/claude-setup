# Deprecated: CSV Schema Removed

`fanout` no longer uses `work-items.csv`.

## Why

CSV execution plans over-emphasized pipeline mechanics and parallel fan-out,
while under-serving the real goals of multi-agent execution:

1. Context isolation for broad, ambiguous work
2. Independent progress on long-running tasks
3. Independent review to reduce author self-bias

## Replacement

Use `tasks/<slug>/BRIEF.md` as the source of truth with:

- `Orchestration Strategy`
- per-milestone `helper-plan`
- explicit approval gates before long-running execution

See:

- `skills/plan/SKILL.md`
- `skills/build/SKILL.md`
