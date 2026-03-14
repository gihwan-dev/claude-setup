# UX Behavior & Accessibility

## Interaction Model

- run list와 graph/timeline selection은 단일 selection source를 공유한다.
- node/edge 선택은 동시에 유지하지 않고 최근 선택만 drawer에 반영한다.
- detail drawer는 기본 auto-open이며 pin 상태를 지원한다.

## Keyboard + Focus Contract

- Focus order는 run list -> graph/timeline -> drawer actions 순서를 유지한다.
- overlay drawer가 닫히면 focus는 마지막 active trigger로 돌아간다.
- keyboard shortcuts: next error jump, expand longest gap, drawer toggle을 지원한다.

## Accessibility Contract

- status는 color 외에 chip shape/text/icon으로도 구분한다.
- focus ring은 고대비 외곽선으로 항상 visible 상태를 유지한다.
- graph node, gap chip, icon button은 최소 24x24 target을 유지한다.

## Live Update Semantics

- 사용자가 과거 이벤트를 보고 있으면 auto-follow를 멈추고 paused badge를 노출한다.
- watch disconnect 시 stale badge와 reconnect CTA를 노출한다.
- partial parse failure는 전체 run fatal이 아니라 degraded row/state로 표현한다.

## State Matrix + Fixture Strategy

- State matrix: default, loading, empty, error, permission, success, paused-live, degraded, responsive fallback.
- Fixture strategy: nominal, first-failure, longest-gap, reconnect, partial-parse-failure fixture를 유지한다.
- Mock strategy: `SLICE-2`에서 local state와 fixture payload로 edge state를 검증한다.

## Large-run Degradation Rules

- lane 8개 초과 시 inactive lane은 collapse 후보가 된다.
- event 500개 초과 시 row virtualization을 고려하고 transfer edge는 aggregate edge로 묶는다.
- selected path 외 컨텍스트는 dim/fade 처리한다.

## Microcopy + Information Expression Rules

- 상태 copy는 `Blocked by permission`, `Waiting on reviewer-2`, `Resume required`처럼 원인 포함 형태를 사용한다.
- 시간 표기는 `12m 04s`를 기본으로 하고 absolute time hover/focus 보조 정보를 허용한다.
- unknown/redacted payload는 명시적인 fallback copy를 사용한다.

## Task-based Approval Criteria

- fixture A에서 30초 안에 first failure를 찾을 수 있다.
- fixture B에서 last handoff를 한 번에 설명할 수 있다.
- keyboard만으로 run 선택 -> error jump -> drawer 확인이 가능하다.
- 1024px overlay 모드에서도 focus loss 없이 동일 과업이 가능하다.
