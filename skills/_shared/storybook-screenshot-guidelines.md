# Storybook Screenshot Guidelines

`design-check`와 `story-generator`가 공통으로 따르는 Storybook/screenshot 규칙이다.

## Scope

- screenshot 비교용 Story를 만들거나 갱신할 때 사용한다.
- canonical source는 각 skill의 `SKILL.md`이지만, 공통 Story 규칙은 여기서 재사용한다.

## Story Placement

- 기본 위치: 컴포넌트 옆 `__screenshots__/{ComponentName}.stories.tsx`
- 기존 screenshot Story가 있으면 우선 재사용한다.
- 같은 이름 파일이 있으면 덮어쓰기 전에 확인한다.

## Title Rules

- 형식: `Screenshots/{Layer}/{ComponentName}`
- 중첩 경로가 있으면 `Screenshots/{Layer}/{SubPath}/{ComponentName}`
- Layer는 PascalCase를 사용한다.
- 예: `src/features/widget-builder/ui/ColumnHeader.tsx`
  - `Screenshots/Features/WidgetBuilder/ColumnHeader`

## Rendering Rules

- render는 반드시 단일 루트 엘리먼트를 반환한다.
- import 경로는 `@/` alias를 사용한다.
- wrapper는 screenshot 기준 컨테이너다.
- width는 Figma bbox나 명시된 캡처 폭을 기준으로 넣는다.
- height는 특별한 이유가 없으면 강제하지 않는다. 높이 차이는 실제 diff로 남겨야 한다.

## Classification

| 분류 | 조건 | 기본 대응 |
|------|------|-----------|
| Simple | props만 필요 | 직접 렌더링 |
| MSW-dependent | API 호출/useQuery 등 | MSW handler 추가 |
| Provider-dependent | Context/Store 의존 | decorator로 Provider 래핑 |

기존 Story가 있으면 args, decorators, parameters 패턴을 최대한 재사용한다.

## Capture Contract

- Storybook 캡처용 Story는 `#storybook-root > *` 선택자 기준으로 안정적으로 렌더링돼야 한다.
- 새 Story를 만든 직후 캡처하면 `--rebuild`를 기본값으로 본다.
- Figma 기반 비교에서는 `bbox.width`를 `--container-width`에 연결한다.

## Validation Checklist

- TypeScript 구문 오류가 없는가
- title이 `Screenshots/...` 규칙을 따르는가
- import가 `@/` alias를 사용하는가
- render가 단일 루트 엘리먼트를 반환하는가
- wrapper width가 캡처 목적과 맞는가
