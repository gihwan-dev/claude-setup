# Sample Bundle Task

## Goal

Codex long-running task execution을 timeline-first UI로 분석한다.

## Document map

- Product: `PRD.md`
- UX Structure: `UX_SPEC.md` (`UI Planning Packet`)
- UX Behavior: `UX_BEHAVIOR_ACCESSIBILITY.md`
- Design References: `DESIGN_REFERENCES/` (`manifest.json`, `shortlist.md`, saved images)
- Architecture: `TECH_SPEC.md`
- Implementation: `IMPLEMENTATION_CONTRACT.md`
- Execution: `EXECUTION_PLAN.md`
- Validation: `SPEC_VALIDATION.md`
- Acceptance: `ACCEPTANCE.feature`

## Task continuity

- decision: create-new
- compared tasks: none
- reason: first bundle fixture
- chosen task path: `tasks/sample-bundle-task`

## Key decisions

- local-first index DB를 둔다.
- timeline-first UI를 기본 뷰로 둔다.
- UI-first delivery strategy를 사용한다.
- `UI Planning Packet`과 `UX_BEHAVIOR_ACCESSIBILITY.md`로 구조/행동 계약을 분리했다.
- `DESIGN_REFERENCES/manifest.json`으로 adopt 2개, avoid 1개 reference를 고정했다.
- greenfield bootstrap 이후 implementation contract를 source_of_truth에 추가한다.

## Validation gate status

- gate: blocking
- state: cleared
- bootstrap: `$bootstrap-project-rules` completed
- ux docs: complete
- reference pack: complete

## Implementation slices

- `SLICE-1` reads checklist/layout/token/screen-flow plus interaction/a11y/microcopy and ships static timeline overview UI shell
- `SLICE-2` reads keyboard/focus, live semantics, state matrix/fixture, degradation, task-based approval criteria and ships local interaction + mock states
- `SLICE-3` real ingestion/normalization integration
