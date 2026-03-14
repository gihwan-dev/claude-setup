# UX Specification

## Goal/Audience/Platform

- Goal: Codex long-running task execution을 timeline-first UI로 빠르게 분석한다.
- Audience: 작업 상태를 추적하는 power user와 maintainer.
- Platform: desktop-first web app, mobile fallback 포함.

## 30-Second Understanding Checklist

- 몇 개 agent가 돌았는지 바로 설명할 수 있다.
- 지금 누가 waiting / blocked / failed 인지 말할 수 있다.
- 마지막 handoff가 어디서 어디로 갔는지 설명할 수 있다.
- 가장 긴 gap과 첫 실패 지점을 찾을 수 있다.
- 최종 artifact를 누가 만들었는지 답할 수 있다.

## Visual Direction + Anti-goals

- Direction: timeline-first, dense-but-readable, status-aware.
- Anti-goals: dashboard card maze, 과한 marketing hero, 시각 장식 중심 layout.

## Reference Pack (adopt/avoid)

- Adopt: `DESIGN_REFERENCES/curated/timeline-shell-adopt.svg`, `DESIGN_REFERENCES/curated/activity-density-adopt.svg`
- Avoid: `DESIGN_REFERENCES/curated/modal-heavy-avoid.svg`

## Glossary + Object Model

- `run`: 하나의 관측 대상 실행.
- `thread`: agent conversation lineage.
- `lane`: UI에서 보이는 실행 축.
- `handoff`: 제어권 이동.
- `artifact`: 실행 결과 산출물.

## Layout/App-shell Contract

- `SCR-001`은 좌측 run list + 중앙 graph/timeline + 우측 detail drawer의 3-pane shell을 사용한다.
- `SCR-002`는 selected item 기준으로 thread detail과 related event context를 묶는다.
- `FLOW-001`은 Overview -> Detail drilldown 흐름을 유지한다.

## Token + Primitive Contract

- Token source path candidate: `src/ui/tokens/timeline.css`.
- Primitive/component source: existing app primitives + task-specific timeline row only.
- Reuse boundary: badge, panel, tabs, empty state primitive를 우선 재사용한다.

## Screen + Flow Coverage

- Screens: `SCR-001` Overview, `SCR-002` Thread detail.
- Flows: `FLOW-001` Overview -> Detail drilldown, `FLOW-002` Error jump.
- Ownership: Overview는 orientation, Detail은 lineage/context, Drawer는 selected node/edge metadata를 담당한다.

## Implementation Prompt/Handoff

- `SLICE-1` reads `30-Second Understanding Checklist`, `Layout/App-shell Contract`, `Token + Primitive Contract`, `Screen + Flow Coverage`.
- `SLICE-2` reads `UX_BEHAVIOR_ACCESSIBILITY.md` keyboard/focus, live/state/degradation, task approval sections.
- `SLICE-3+` waits for `SLICE-2` local state approval and real ingestion contract.
