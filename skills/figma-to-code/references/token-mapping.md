# Token Mapping

`figma-to-code`에서 Figma 디자인 값을 React/Tailwind 코드로 옮길 때 사용하는 매핑 규칙이다.

## Color Mapping Priority

1. Figma 변수 바인딩이 있으면 그 이름을 직접 사용한다.
   - 예: `color/gray-05` -> `text-gray-05`
2. 시맨틱 토큰을 우선 사용한다.
   - text: `text-text-primary`, `text-text-secondary`, `text-text-tertiary`, `text-text-disabled`, `text-text-accent`, `text-text-critical`
   - surface: `bg-surface-primary-default`, `bg-elevation-elevation-0`
   - border: `border-border-primary`, `border-border-secondary`
   - icon: `text-icon-primary`, `text-icon-secondary`
3. 시맨틱 매칭이 안 되면 원시 색상 스케일을 사용한다.
   - `gray-00~10`, `red-00~10`, `blue-00~10`, `mono-white`, `mono-black`
4. 그래도 정확한 매칭이 없으면 가장 가까운 토큰을 사용하고 TODO를 남긴다.

## Typography

| Figma 크기 | Tailwind 클래스 |
|---|---|
| 28px/140% | `text-header-1` |
| 24px/140% | `text-header-2` |
| 20px/140% | `text-title-1` |
| 18px/140% | `text-title-2` |
| 16px/140% | `text-body-1` |
| 14px/140% | `text-body-2` |
| 12px/140% | `text-body-3` |
| 11px/140% | `text-caption` |

폰트 두께 매핑:

- 400 -> `font-regular`
- 500 -> `font-medium`
- 600 -> `font-semibold`
- 700 -> `font-bold`

## Radius And Shadow

- radius: `rounded-weak`, `rounded-medium`, `rounded-strong`, `rounded-circle`
- shadow: `shadow-weak`, `shadow-medium`, `shadow-strong`, `shadow-preview`

## Layout Mapping

- auto-layout direction -> `flex flex-row` / `flex flex-col`
- gap, padding -> 표준 spacing 우선, 없으면 arbitrary value 사용
- child sizing
  - fill -> `flex-1`
  - fixed -> `w-[Npx]`
  - hug -> `w-fit`

## Component Recognition

- Figma 컴포넌트 인스턴스는 먼저 `@exem-fe/react` 매핑을 찾는다.
  - 예: `Button`, `TextField`, `Select`, `Table`, `Tabs`, `Modal`, `Tooltip`, `Badge`, `Tag`, `Checkbox`, `Radio`, `Switch`
- 프로젝트 커스텀 UI가 더 가깝다면 `src/shared/ui/`의 유사 컴포넌트를 우선 참고한다.
  - 예: `Card`, `Form`, `DropdownMenu`, `Sheet`, `Popover`, `Skeleton`
- 아이콘은 `@exem-fe/icon`의 `{Name}{Variant}Icon` 패턴을 우선 찾는다.

## Code Generation Defaults

- import 순서: 외부 패키지 -> `@exem-fe/*` -> `@/` -> 상대 경로
- className 병합은 `@/shared/util`의 `cn()`을 사용한다.
- root element에는 항상 `className?: string` 합성 경로를 남긴다.
- 텍스트 노드는 string props, 반복 요소는 array/children props를 우선 검토한다.
- default export 대신 named export를 사용한다.
