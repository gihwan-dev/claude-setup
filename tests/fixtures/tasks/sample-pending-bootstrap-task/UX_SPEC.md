# UX Specification

## Goal/Audience/Platform

- Goal: Codex long-running task execution을 timeline-first UI로 빠르게 분석한다.
- Audience: 작업 상태를 추적하는 power user와 maintainer.
- Platform: desktop-first web app, mobile fallback 포함.

## Visual Direction + Anti-goals

- Direction: timeline-first, dense-but-readable, status-aware.
- Anti-goals: dashboard card maze, 과한 marketing hero, 시각 장식 중심 layout.

## Reference Pack (adopt/avoid)

- Adopt: linear activity timeline, split-pane detail, subdued status color coding.
- Avoid: widget-heavy admin chrome, modal-first drilldown, decorative empty state.

## Layout/App-shell Contract

- `SCR-001`은 좌측 filter rail + 중앙 timeline + 우측 detail preview shell을 사용한다.
- `SCR-002`는 selected item 기준으로 thread detail과 related event context를 묶는다.
- `FLOW-001`은 Overview -> Detail drilldown 흐름을 유지한다.

## Token + Primitive Contract

- Token source path candidate: `src/ui/tokens/timeline.css`.
- Primitive/component source: existing app primitives + task-specific timeline row only.
- Reuse boundary: badge, panel, tabs, empty state primitive를 우선 재사용한다.

## Screen/Flow/State Coverage

- Screens: `SCR-001` Overview, `SCR-002` Thread detail.
- Flows: `FLOW-001` Overview -> Detail drilldown.
- State matrix: default, loading, empty, error, permission, success, responsive fallback.
- Mock strategy: `SLICE-2`에서 local state와 fixture payload로 edge state를 검증한다.
- Edge states: long label truncation, missing avatar, stale timeline item, permission denial.

## Review Loop

- Reviewers: task owner + UX reviewer.
- Evidence: static screenshot, state matrix walkthrough, keyboard navigation spot check.
- Approval gate: `SLICE-1` shell 승인 후에만 `SLICE-2`로 진행한다.

## Implementation Prompt/Handoff

- `SLICE-1` reads `Layout/App-shell Contract`, `Token + Primitive Contract`, `Review Loop`.
- `SLICE-2` reads `Screen/Flow/State Coverage` state matrix, mock plan, edge states.
- `SLICE-3+` waits for `SLICE-2` local state approval and real ingestion contract.
