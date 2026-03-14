# Inputs Read

- `task.yaml`
- `PRD.md`
- `UX_SPEC.md`
- `TECH_SPEC.md`
- `SPEC_VALIDATION.md`

# Task-Specific Decisions

- Timeline overview UI는 React 기반 local-first shell로 구현한다.
- ingestion/normalization pipeline은 local SQLite index DB 경계를 유지한다.
- initial slices는 `SLICE-1 -> SLICE-2 -> SLICE-3` 순서를 따른다.

# Allowed Core Libraries

- React
- TypeScript
- SQLite

# Deferred Decisions and Trigger

- charting library: 실제 overview metric 카드가 chart로 확정될 때 재결정
- virtualization helper: thread volume bottleneck이 fixture smoke check를 넘어서면 재결정

# Validation Overrides

- visual shell snapshot review
- mock interaction smoke check
- parser unit test

# Open Risks

- large JSONL payload volume이 fixture 수준을 넘으면 virtualization 여부를 다시 판단해야 한다.
