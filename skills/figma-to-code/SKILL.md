---
name: figma-to-code
description: >
  Generate React component code from a Figma URL and target file path. Figma URL과 대상
  컴포넌트 파일 경로를 받아 디자인 데이터를 수집하고, 프로젝트 패턴과 토큰 규칙을 반영한
  React 코드를 만든다. 상세 토큰 매핑과 에러/출력 포맷은 `references/`를 사용한다.
---

# Figma to Code

Figma 디자인 데이터를 읽고, 프로젝트 패턴과 토큰 규칙에 맞는 React 컴포넌트 코드를 생성한다.

## Trigger

- `/figma-to-code`
- `피그마 구현`
- Figma URL과 대상 컴포넌트 파일 경로가 함께 주어진 요청

## Required Inputs

- Figma URL (`node-id` 포함)
- 대상 컴포넌트 파일 경로
- 대상 파일이 비어 있지 않을 때의 overwrite 여부

## Core Flow

1. Figma URL에서 `fileKey`와 `nodeId`를 추출하고, `.../branch/:branchKey/...` 형식이면 `branchKey`를 `fileKey`로 정규화한다. 대상 파일 경로에서 component name과 주변 맥락도 함께 정리한다.
2. `get_screenshot`, `get_design_context`, `get_variable_defs`를 `clientLanguages=typescript`, `clientFrameworks=react` 힌트와 함께 병렬 호출해 디자인 데이터를 수집한다.
3. 대상 디렉토리와 유사 컴포넌트를 읽어 `cn()`, export, props, alias 같은 로컬 패턴을 파악한다.
4. `references/token-mapping.md` 기준으로 토큰, 타이포, 레이아웃, 컴포넌트 매핑을 결정한다.
5. `@exem-fe/react` 우선, `@/` alias, named export, root `className` 합성 규칙을 지켜 React 코드를 생성한다.
6. `references/error-handling.md`의 output contract에 맞춰 결과를 요약하고, 변경 결과를 타깃 기준으로 검증한다.

## Guardrails

- `node-id`가 없는 URL은 중단하고 올바른 형식을 다시 요청한다.
- Figma 데이터 수집이 실패하면 Figma Desktop 앱과 대상 파일을 열어 달라고 안내한다.
- 대상 파일이 비어 있지 않으면 overwrite 확인 없이 덮어쓰지 않는다.
- 색상은 hex 하드코딩 대신 토큰 기반 Tailwind 클래스만 사용한다.
- 가능한 경우 raw HTML보다 `@exem-fe/react` 컴포넌트를 우선한다.
- 루트 요소에는 `className` prop을 연결하고 default export는 사용하지 않는다.

## References

- 토큰 매핑, 타이포 표, radius/shadow, 컴포넌트 인식 목록: `references/token-mapping.md`
- overwrite 정책, URL/MCP 오류 대응, 결과 요약 포맷, 예시 입력/출력: `references/error-handling.md`

## Validation

- 토큰 기반 Tailwind 클래스만 사용했는지 확인한다.
- import 경로가 `@/` alias를 따르는지 확인한다.
- class merge가 필요한 위치에 `cn()` 사용이 유지되는지 확인한다.
- named export와 적절한 컴포넌트 재사용을 확인한다.
