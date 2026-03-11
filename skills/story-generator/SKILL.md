---
name: story-generator
description: >
  Auto-generate Storybook story files for component screenshot comparison.
  스크린샷 비교용 Story 파일 자동 생성. "/story-gen", "스토리 생성" 등의 요청 시 사용
---

# Story Generator

스크린샷 캡처와 디자인 비교에 쓸 Storybook Story를 빠르게 만든다.

## Trigger

- `/story-gen`
- `스토리 생성`
- screenshot 비교용 Story가 아직 없거나, 기존 Story를 screenshot 전용으로 분리해야 할 때

## Required Input

- 컴포넌트 파일 경로
- 필요하면 목표 width 또는 참조할 기존 Story 위치

## Core Flow

1. 컴포넌트 경로에서 이름, 레이어, import 경로를 추출한다.
2. export, props, dependency를 읽고 렌더링 요구를 분류한다.
3. 기존 Story가 있으면 args/decorators/parameters를 최대한 재사용한다.
4. screenshot Story를 `__screenshots__/{ComponentName}.stories.tsx`에 만든다.
5. title, render root, import alias, wrapper width를 검증한다.

## Guardrails

- Story 규칙은 `../_shared/storybook-screenshot-guidelines.md`를 따른다.
- 기본 틀은 `../_shared/storybook-screenshot-template.tsx`를 출발점으로 삼는다.
- title은 `Screenshots/{Layer}/{ComponentName}` 형식을 유지한다.
- render는 단일 루트 엘리먼트를 반환해야 한다.
- import는 `@/` alias를 사용한다.
- width는 캡처 목적에 맞게 주고, height는 특별한 이유가 없으면 강제하지 않는다.
- 기존 screenshot Story가 있으면 덮어쓰기 전에 확인한다.

## Classification

| 분류 | 조건 | 기본 대응 |
|------|------|-----------|
| Simple | props만 필요 | 직접 렌더링 |
| MSW-dependent | API 호출/useQuery 등 | MSW handler 추가 |
| Provider-dependent | Context/Store 의존 | decorator로 Provider 래핑 |

## References

- 공통 Storybook/screenshot 규칙: `../_shared/storybook-screenshot-guidelines.md`
- 공통 Story template: `../_shared/storybook-screenshot-template.tsx`
