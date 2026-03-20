---
name: bootstrap-project-rules
description: >
  Post-design bootstrap workflow for greenfield or newly shaped work. Use after `design-task`
  and before `implement-task` when the task bundle is ready but the repo still needs implementation
  rules: repo baseline `docs/ai/ENGINEERING_RULES.md`, task supplement
  `tasks/{task-path}/IMPLEMENTATION_CONTRACT.md`, and optional managed links in root `README.md`.
  Lock only the core stack and architectural rules now; keep optional libraries as deferred decisions
  with explicit triggers.
---

# Workflow: Bootstrap Project Rules

## Goal

선택된 task bundle을 구현 가능한 계약으로 고정한다.
`design-task` 산출물을 읽고, repo baseline `docs/ai/ENGINEERING_RULES.md`와
task supplement `tasks/<task-path>/IMPLEMENTATION_CONTRACT.md`를 만들거나 갱신한 뒤
필요하면 root `README.md`의 managed link section을 맞춘다.
강화된 `UX_SPEC.md`, `UX_BEHAVIOR_ACCESSIBILITY.md`, `DESIGN_REFERENCES/manifest.json`은 UX source of truth로 유지하고,
bootstrap은 구현 스택/도구/경계만 잠근다.

## Hard Rules

- 코드, 설정, 테스트, 패키지 설치는 하지 않는다. 문서와 agent memory 계약만 갱신한다.
- `design-task` 이후 단계로만 사용한다. bundle `task.yaml`이 없으면 시작하지 않는다.
- path 후보가 2개 이상이면 자동 선택하지 않고 사용자 확인이 필요하다고 멈춘다.
- 현재 repo 사실(manifest, config, 기존 문서, 기존 AGENTS/CLAUDE)부터 탐색하고, 되돌리기 어려운 결정만 짧게 질의한다.
- dependency policy는 반드시 `Locked now`, `Deferred`, `Banned/Avoid` 세 분류로 기록한다.
- `Locked now`에는 runtime/language, framework, package manager, lint/format/typecheck/test stack, 기본 state/data fetching 전략, 기본 styling/design-system 방향, 폴더/모듈 경계를 포함한다.
- `Locked now`에는 styling stack, component source, Storybook/screenshot tooling, token source path도 포함한다.
- 선택 라이브러리는 scope가 아직 문서로 고정되지 않았으면 upfront으로 승인하지 않고 `Deferred`에 남긴다. 각 항목에는 재결정 trigger를 적는다.
- repo-level implementation rules는 `docs/ai/ENGINEERING_RULES.md`에만 기록한다.
- root global memory markdown은 만들거나 갱신하지 않는다.
- `README.md`는 human-facing 문서로 유지한다. `AI Workflow` 또는 `Engineering Rules` 링크 섹션만 짧게 추가한다.
- 기존 `README.md` 전체 overwrite를 금지한다. managed section만 갱신한다.
- `README.md` managed section marker는 아래 두 줄을 사용한다.
  - `<!-- bootstrap-project-rules:start -->`
  - `<!-- bootstrap-project-rules:end -->`
- `README.md`가 없으면 새로 장문 README를 만들지 않는다. advisory만 남기고 AI 문서만 작성한다.
- `SPEC_VALIDATION.md`에 bootstrap 관련 blocking issue 외 다른 blocker가 남아 있으면 이를 임의로 해소하지 않는다.
- 핵심 아키텍처 결정이 unresolved면 `IMPLEMENTATION_CONTRACT.md`를 부분 초안으로 남길 수는 있어도 bootstrap blocker는 해소하지 않는다.
- UX ownership은 계속 `UX_SPEC.md`와 `UX_BEHAVIOR_ACCESSIBILITY.md`에 남기고 bootstrap은 visual direction이나 behavior contract를 재정의하지 않는다.

## Required References

- 결정 분류와 defer 기준이 필요할 때만 `${SKILL_DIR}/references/decision-catalog.md`를 읽는다.
- 문서 skeleton과 managed section 형식은 `${SKILL_DIR}/references/doc-templates.md`를 읽는다.

## Inputs

- 선택된 `tasks/<task-path>/task.yaml`
- 같은 task의 `README.md`, `SPEC_VALIDATION.md`, `EXECUTION_PLAN.md`
- 존재하는 `PRD.md`, `UX_SPEC.md`, `UX_BEHAVIOR_ACCESSIBILITY.md`, `TECH_SPEC.md`, `ADRs/`, `ACCEPTANCE.feature`
- repo root의 `README.md`
- manifest/config (`package.json`, lockfile, `pyproject.toml`, `tsconfig.json`, `eslint`, formatter, CI/workflow 파일 등)

## Task Selection Rules

1. 사용자가 slug/path를 직접 지정하면 해당 task를 사용한다.
2. path가 없으면 active bundle 후보를 만든다.
3. 후보가 정확히 1개일 때만 자동 선택한다.
4. 후보가 2개 이상이면 자동 실행하지 않고 사용자 확인이 필요하다고 멈춘다.
5. legacy `PLAN.md` task에는 적용하지 않는다.

## Workflow

1. task path와 bundle mode를 판정한다.
2. `task.yaml`, `SPEC_VALIDATION.md`, `README.md`, source-of-truth design docs를 읽고 구현에 영향을 주는 불확실성을 추린다. `UX_SPEC.md`가 있으면 checklist/layout/token/screen-flow를, `UX_BEHAVIOR_ACCESSIBILITY.md`가 있으면 interaction/a11y/live/state/approval contract를 우선 확인한다.
3. repo root 문서와 manifest/config를 읽고 이미 고정된 사실을 `Fact`로 분류한다.
4. `${SKILL_DIR}/references/decision-catalog.md` 기준으로 결정을 분류한다.
   - `Locked now`
   - `Deferred`
   - `Banned/Avoid`
5. `Locked now`인데 repo 탐색으로 확정할 수 없는 항목만 high-leverage 질문으로 좁힌다.
6. `docs/ai/ENGINEERING_RULES.md`를 작성 또는 갱신한다. styling stack, component source, Storybook/screenshot tooling, token source path를 implementation-facing rule로 잠근다.
7. `tasks/<task-path>/IMPLEMENTATION_CONTRACT.md`를 작성 또는 갱신한다. `UX_SPEC.md`/`UX_BEHAVIOR_ACCESSIBILITY.md` ownership은 유지하고 slice가 읽어야 할 implementation guardrail만 추가한다.
8. `task.yaml.required_docs`에 `IMPLEMENTATION_CONTRACT.md`를 추가하고, `source_of_truth.implementation = IMPLEMENTATION_CONTRACT.md`를 기록한다.
9. task `README.md`의 document map과 key decisions를 implementation contract 관점으로 보강한다.
10. 존재하는 경우 root `README.md`의 managed section을 갱신한다.
11. `SPEC_VALIDATION.md`의 blocking issue 중 아래 조건을 동시에 만족하는 항목만 해소한다.
    - greenfield/new-project bootstrap 요구
    - `$bootstrap-project-rules` 실행 요구
    - 현재 문서로 실제로 해소됐음
12. 다른 blocker가 남아 있으면 `Proceed verdict`는 유지하고, bootstrap 이후에도 구현 시작 불가 상태를 명시한다.
13. 구현이나 패키지 설치는 시작하지 않고 `implement-task` handoff만 정리한다.

## Document Update Rules

- repo baseline은 `docs/ai/ENGINEERING_RULES.md` 하나를 SSOT로 둔다.
- task supplement는 `tasks/<task-path>/IMPLEMENTATION_CONTRACT.md` 하나를 SSOT로 둔다.
- root global memory markdown은 bootstrap 산출물에 포함하지 않는다.
- `README.md`는 사람이 읽는 목적/실행법/doc map을 유지하고 AI 문서는 링크만 건다.
- root README 갱신은 managed section 안에서만 수행한다.
- managed section이 없으면 파일 끝에 추가한다.
- managed section 밖 사용자 텍스트는 보존한다.
- UX direction, anti-goals, reference pack ownership은 계속 `UX_SPEC.md`에 남기고, interaction/a11y/live/approval ownership은 `UX_BEHAVIOR_ACCESSIBILITY.md`에 남긴다.

## Handoff Rules

- bootstrap 성공 후 다음 단계는 `implement-task`다.
- `source_of_truth.implementation`이 생긴 task는 이후 구현 단계에서 이를 선행 입력으로 읽어야 한다.
- unresolved architecture decision, missing validation command, conflicting source-of-truth가 남아 있으면 bootstrap blocker를 유지하고 `implement-task`로 넘어가지 않는다.
- `Deferred` 항목은 구현 slice에서 자동 승인하지 않는다. 문서에 적힌 trigger가 충족될 때만 재결정한다.
- `SLICE-1`/`SLICE-2` 구현자는 `UX_SPEC.md`와 `UX_BEHAVIOR_ACCESSIBILITY.md`를 먼저 읽고, bootstrap 문서는 그 구현 guardrail만 보강한다.

## Output Quality Checklist

- `docs/ai/ENGINEERING_RULES.md`가 fixed section order를 따르는가?
- `IMPLEMENTATION_CONTRACT.md`가 task bundle 입력과 task-specific 결정을 분리해 기록하는가?
- `Locked now` / `Deferred` / `Banned/Avoid`가 모두 채워졌는가?
- `Deferred` 항목마다 재결정 trigger가 있는가?
- `task.yaml.required_docs`와 `source_of_truth.implementation`이 반영됐는가?
- root `README.md`는 managed section만 갱신했는가?
- bootstrap 관련 blocking issue를 해소했거나, 해소하지 못한 이유를 남겼는가?
- 구현이나 패키지 설치 없이 문서 계약만 남겼는가?
- styling stack, component source, Storybook/screenshot tooling, token source path를 잠그되 UX ownership은 `UX_SPEC.md`/`UX_BEHAVIOR_ACCESSIBILITY.md`에 남겼는가?
