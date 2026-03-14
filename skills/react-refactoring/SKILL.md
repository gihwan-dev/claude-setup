---
name: react-refactoring
description: >
  Critically evaluate React/TypeScript refactoring requests before changing code. React 컴포넌트
  경로와 문제점이 주어지면 먼저 문제를 검증하고, 계획과 승인 후 실행한다. 상세 분석 모드와
  프롬프트는 `references/analysis-modes.md`, 평가 기준은 `references/evaluation-criteria.md`를 사용한다.
---

# React Refactoring

사용자 제안을 그대로 수용하지 않고, "수정하기 좋은 코드" 기준으로 실제 개선 가치가 있는지 먼저 검증한다.

## Trigger

- `리팩토링`
- `개선하고 싶어`
- `코드 구조 변경`
- `훅 분리`
- `응집도`
- `결합도`
- React/TypeScript 컴포넌트 경로와 구체 문제점이 함께 주어진 요청

## Required Inputs

- 대상 component/file path
- 사용자 문제점 또는 제안 목록
- 분석 범위가 넓어질 때 참고할 imports, hooks, types, 형제 파일

## Core Flow

1. 대상 파일과 직접 의존성을 읽고 현재 구조를 간단히 요약한다.
2. `references/evaluation-criteria.md` 기준으로 각 문제점이 실제로 수정 가치가 있는지 검증한다.
3. 문제 수와 복잡도에 따라 Standard 또는 Multi-Perspective 분석 모드를 선택한다. 세부 질문과 프롬프트는 `references/analysis-modes.md`를 따른다.
4. 각 문제점에 대해 `수용`, `수정`, `기각` 중 하나로 판단하고, 불확실한 의도나 비즈니스 컨텍스트가 있으면 먼저 확인한다.
5. 판단 결과를 바탕으로 작은 단위의 리팩토링 계획을 작성하고 사용자 승인을 받는다.
6. 승인 후 계획 순서대로 리팩토링하고 필요한 타깃 검증과 관련 테스트 업데이트를 수행한다.

## Guardrails

- 분석 없이 바로 코드 수정하지 않는다.
- "일반적으로 좋은 패턴"이라는 이유만으로 변경을 강요하지 않는다.
- 기존 코드베이스 스타일과 팀 컨벤션을 우선한다.
- 판단 근거와 트레이드오프를 명시한다.
- 큰 변경을 한 번에 밀어 넣지 않고 점진적 실행 계획으로 쪼갠다.

## References

- 평가 기준: `references/evaluation-criteria.md`
- 분석 모드, 3관점 프롬프트, 합의 규칙, React/TypeScript 체크리스트: `references/analysis-modes.md`

## Validation

- 리팩토링 후에는 변경 범위에 맞는 타깃 검증을 우선 실행한다.
- 동작/계약이 바뀌면 관련 테스트를 함께 확인하거나 갱신한다.
