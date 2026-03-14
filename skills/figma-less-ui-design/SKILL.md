---
name: figma-less-ui-design
description: >
  Advisory skill for no-Figma MVP/prototype product UI planning. Use when `design-task`
  has `delivery_strategy=ui-first` but there is no Figma file and the team still needs a
  concrete `UI Planning Packet` inside `UX_SPEC.md`. If an existing design system, shipped
  UI, or Figma already exists, switch to `reuse + delta` and avoid inventing a new style.
---

# Workflow: Figma-less UI Design

## Goal

Figma 없이도 MVP/prototype product UI를 구현 가능한 수준으로 고정하고,
`UX_SPEC.md`에 재사용 가능한 `UI Planning Packet`을 남긴다.

## Hard Rules

- 산출물 이름은 항상 `UI Planning Packet`이다.
- 섹션 순서는 아래 순서를 그대로 유지한다.
  - `Goal/Audience/Platform`
  - `Visual Direction + Anti-goals`
  - `Reference Pack (adopt/avoid)`
  - `Layout/App-shell Contract`
  - `Token + Primitive Contract`
  - `Screen/Flow/State Coverage`
  - `Review Loop`
  - `Implementation Prompt/Handoff`
- 기존 design system, shipped UI, brand guide, Figma가 하나라도 있으면 `reuse + delta`로 기록한다.
- 기존 기준이 있는데 새 visual language를 invent하지 않는다.
- `Reference Pack`에는 따라갈 것(`adopt`)과 피할 것(`avoid`)을 모두 남긴다.
- `Layout/App-shell Contract`, `Token + Primitive Contract`, `Screen/Flow/State Coverage`, `Review Loop` 없이 handoff하지 않는다.
- 이 스킬은 advisory planning 전용이다. long-running public surface는 여전히 `design-task`, `implement-task`만 유지한다.

## Required References

- product UI 패턴이나 `reuse + delta` 판단이 필요할 때 `${SKILL_DIR}/references/official-patterns.md`
- packet skeleton과 handoff phrasing이 필요할 때 `${SKILL_DIR}/references/ui-planning-templates.md`

## Workflow

1. 현재 repo, shipped UI, design system, component library, brand artifact, Figma 존재 여부를 조사한다.
2. 기존 기준이 있으면 `reuse + delta`로 시작하고 변경 범위를 최소화한다.
3. `Goal/Audience/Platform`에서 product goal, primary audience, target platform을 한 줄씩 고정한다.
4. `Visual Direction + Anti-goals`에서 원하는 인상과 피해야 할 스타일을 함께 적는다.
5. `Reference Pack (adopt/avoid)`에 참고 사례, adopt 포인트, avoid 포인트를 이유와 함께 남긴다.
6. `Layout/App-shell Contract`에 navigation, pane/shell 구조, 주요 정보 위계를 고정한다.
7. `Token + Primitive Contract`에 token source candidate, primitive/component source, reuse boundary를 적는다.
8. `Screen/Flow/State Coverage`에 주요 screen, flow, state matrix, mock/edge state를 포함한다.
9. `Review Loop`에 who/when/how를 적고 screenshot/story/manual review 순서를 남긴다.
10. `Implementation Prompt/Handoff`에 `SLICE-1`과 `SLICE-2`가 읽어야 할 packet sections를 직접 연결한다.

## Output Contract

`UX_SPEC.md`에는 아래 heading 순서를 그대로 사용한다.

## Goal/Audience/Platform

goal, audience, platform, success impression을 한 줄씩 기록한다.

## Visual Direction + Anti-goals

visual direction 2~4개와 anti-goal 2~4개를 기록한다.

## Reference Pack (adopt/avoid)

adopt reference와 avoid reference를 이유와 함께 기록한다.

## Layout/App-shell Contract

app shell, navigation, pane/layout hierarchy, screen ownership을 기록한다.

## Token + Primitive Contract

token source path candidate, primitive/component source, styling constraints를 기록한다.

## Screen/Flow/State Coverage

screen ids, flow ids, state matrix, mock strategy, edge states를 기록한다.

## Review Loop

review cadence, screenshot/story/manual checks, approval gate를 기록한다.

## Implementation Prompt/Handoff

`SLICE-1`은 `Layout/App-shell Contract`, `Token + Primitive Contract`, `Review Loop`를 읽고,
`SLICE-2`는 `Screen/Flow/State Coverage`의 state matrix, mock plan, edge states를 읽는다고 명시한다.
