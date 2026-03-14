# Official Patterns

`figma-less-ui-design`이 product UI 방향을 고정할 때만 이 파일을 읽는다.

## Reuse + Delta First

- existing design system, shipped screen, brand guide, Figma가 있으면 새 style invention 대신 `reuse + delta`
- `reuse`: 그대로 따를 shell, token, primitive, spacing, motion, copy tone
- `delta`: 이번 MVP/prototype에서 추가/변형할 화면, interaction, a11y/live rules, degradation policy

## Reference Pack Rules

- `adopt`: product fit가 높고 바로 구현 가능한 패턴만 남긴다.
- `avoid`: 복잡도, brand mismatch, information scent 저하를 만드는 패턴을 남긴다.
- reference는 visual moodboard가 아니라 shell, hierarchy, live behavior, state handling, accessibility 근거로 사용한다.
- saved reference는 `DESIGN_REFERENCES/manifest.json` 경로와 함께 문서에 직접 연결한다.

## App-shell Priorities

- MVP/prototype는 novelty보다 orientation을 우선한다.
- 첫 화면에서 navigation, primary work area, detail context가 한눈에 보여야 한다.
- shell contract는 `SLICE-1`에서 구현 가능한 수준으로 구체적이어야 한다.
- `30-Second Understanding Checklist`와 `Glossary + Object Model`은 shell contract보다 먼저 고정한다.

## Token + Primitive Bias

- token은 적게, primitive는 명확하게 고정한다.
- typography, spacing, surface, border, status color의 source를 먼저 적는다.
- primitive source는 design system, component library, custom layer 중 하나로 제한한다.

## Behavior + Accessibility Minimum

- selection sync, drawer/overlay, filter persistence, keyboard focus order를 명시한다.
- 색상 외 구분, focus ring, target size, reduced motion, hover/focus parity를 명시한다.
- live update, stale/reconnect, partial failure, large-run degradation은 시각 방향과 별개로 별도 계약으로 고정한다.
