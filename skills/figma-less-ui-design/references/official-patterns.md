# Official Patterns

`figma-less-ui-design`이 product UI 방향을 고정할 때만 이 파일을 읽는다.

## Reuse + Delta First

- existing design system, shipped screen, brand guide, Figma가 있으면 새 style invention 대신 `reuse + delta`
- `reuse`: 그대로 따를 shell, token, primitive, spacing, motion
- `delta`: 이번 MVP/prototype에서 추가/변형할 화면, interaction, token override

## Reference Pack Rules

- `adopt`: product fit가 높고 바로 구현 가능한 패턴만 남긴다.
- `avoid`: 복잡도, brand mismatch, information scent 저하를 만드는 패턴을 남긴다.
- reference는 visual moodboard가 아니라 shell, hierarchy, state handling 근거로 사용한다.

## App-shell Priorities

- MVP/prototype는 novelty보다 orientation을 우선한다.
- 첫 화면에서 navigation, primary work area, detail context가 한눈에 보여야 한다.
- shell contract는 `SLICE-1`에서 구현 가능한 수준으로 구체적이어야 한다.

## Token + Primitive Bias

- token은 적게, primitive는 명확하게 고정한다.
- typography, spacing, surface, border, status color의 source를 먼저 적는다.
- primitive source는 design system, component library, custom layer 중 하나로 제한한다.

## State Coverage Minimum

- default
- loading
- empty
- error
- permission
- success
- responsive or density fallback

state는 `SLICE-2` mock 검증에 바로 연결될 수 있어야 한다.
