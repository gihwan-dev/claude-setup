---
name: design-check
description: >
  Automated design verification comparing Figma designs vs implemented components with pixel-diff reports. Requires: component-screenshot skill.
  디자인 검증 자동화. Figma vs 구현 비교 리포트 생성. "/design-check", "디자인 검증" 등의 요청 시 사용
---

# Design Check

Figma 디자인과 구현된 컴포넌트를 비교해 screenshot artifacts와 Markdown 보고서를 만든다.

## Trigger

- `/design-check`
- `디자인 검증`
- Figma URL + 컴포넌트 경로를 함께 받아 시각 비교가 필요할 때

## Required Inputs

- Figma URL
  - `fileKey`와 `node-id`를 추출할 수 있어야 한다
- 구현 컴포넌트 경로
- `FIGMA_TOKEN`
- Storybook이 있는 프로젝트 환경

## Outputs

- `artifacts/screenshots/figma/{Name}.png`
- `artifacts/screenshots/figma/{Name}.meta.json`
- `artifacts/screenshots/impl/{Name}.png`
- `artifacts/screenshots/diff/{Name}.png`
- `artifacts/design-check/{Name}-report.md`
- 필요 시 `__screenshots__/{ComponentName}.stories.tsx`

## Core Flow

1. Figma URL에서 `fileKey`, `nodeId`, 대상 이름을 추출한다.
2. Figma screenshot + bbox metadata를 확보한다.
3. 디자인 context/token을 수집한다. 이 단계는 warning 허용이다.
4. 컴포넌트를 분석하고 screenshot Story를 준비한다.
   - Story 규칙은 `../_shared/storybook-screenshot-guidelines.md`
   - 공통 틀은 `../_shared/storybook-screenshot-template.tsx`
5. `bbox.width`만 Story wrapper와 캡처 옵션에 주입해 구현 screenshot을 만든다.
6. pixel diff를 계산하고 정성 비교를 수행한다.
7. 정량/정성 결과를 합쳐 보고서를 쓴다.

## Guardrails

- bbox를 얻지 못하면 중단한다. width contract 없이 비교를 진행하지 않는다.
- 디자인 context/token 수집 실패는 warning으로 남기고 나머지 흐름은 계속할 수 있다.
- screenshot Story는 단일 루트 render, `@/` import alias, `Screenshots/...` title 규칙을 지킨다.
- width는 Figma bbox 기준으로 맞추고 height는 특별한 이유가 없으면 강제하지 않는다.
- 기존 screenshot Story나 artifact를 덮어써야 하면 먼저 확인한다.
- report에는 최소한 diff ratio, severity별 발견사항, artifact 경로를 남긴다.

## References

- 상세 단계/명령: `references/workflow-details.md`
- 에러 처리: `references/error-handling.md`
- 공통 Storybook/screenshot 규칙: `../_shared/storybook-screenshot-guidelines.md`
- 공통 Story template: `../_shared/storybook-screenshot-template.tsx`
- 관련 스크립트:
  - `scripts/capture-figma-screenshot.ts`
  - `scripts/compare-screenshots.ts`
