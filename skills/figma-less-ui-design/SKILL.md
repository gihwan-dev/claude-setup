---
name: figma-less-ui-design
description: >
  Advisory skill for no-Figma MVP/prototype product UI planning. Use when `design-task`
  has `delivery_strategy=ui-first` and the team needs concrete UX planning docs from repo
  context plus saved task-local references. Produce `UX_SPEC.md` (`UI Planning Packet`) and
  `UX_BEHAVIOR_ACCESSIBILITY.md`, and fall back to `reuse + delta` when an existing design
  system, shipped UI, or Figma already exists.
---

# Workflow: Figma-less UI Design

## Goal

Figma 없이도 MVP/prototype product UI를 구현 가능한 수준으로 고정하고,
`UX_SPEC.md`와 `UX_BEHAVIOR_ACCESSIBILITY.md`에 재사용 가능한 UX source of truth를 남긴다.

## Hard Rules

- 산출물은 항상 `UX_SPEC.md`와 `UX_BEHAVIOR_ACCESSIBILITY.md` 두 문서다.
- `UX_SPEC.md` 안의 `UI Planning Packet` section order는 아래 순서를 그대로 유지한다.
  - `Goal/Audience/Platform`
  - `30-Second Understanding Checklist`
  - `Visual Direction + Anti-goals`
  - `Reference Pack (adopt/avoid)`
  - `Glossary + Object Model`
  - `Layout/App-shell Contract`
  - `Token + Primitive Contract`
  - `Screen + Flow Coverage`
  - `Implementation Prompt/Handoff`
- `UX_BEHAVIOR_ACCESSIBILITY.md` section order는 아래 순서를 그대로 유지한다.
  - `Interaction Model`
  - `Keyboard + Focus Contract`
  - `Accessibility Contract`
  - `Live Update Semantics`
  - `State Matrix + Fixture Strategy`
  - `Large-run Degradation Rules`
  - `Microcopy + Information Expression Rules`
  - `Task-based Approval Criteria`
- 기존 design system, shipped UI, brand guide, Figma가 하나라도 있으면 `reuse + delta`로 기록한다.
- 기존 기준이 있는데 새 visual language를 invent하지 않는다.
- `Reference Pack`에는 saved file 경로와 adopt/avoid 이유를 함께 남긴다.
- `30-Second Understanding Checklist`, `Glossary + Object Model`, `Interaction Model`, `Accessibility Contract`, `Live Update Semantics`, `Task-based Approval Criteria` 없이 handoff하지 않는다.
- 이 스킬은 advisory planning 전용이다. long-running public surface는 여전히 `design-task`, `implement-task`만 유지한다.

## Required References

- product UI 패턴이나 `reuse + delta` 판단이 필요할 때 `${SKILL_DIR}/references/official-patterns.md`
- packet skeleton과 handoff phrasing이 필요할 때 `${SKILL_DIR}/references/ui-planning-templates.md`

## Workflow

1. 현재 repo, shipped UI, design system, component library, brand artifact, Figma 존재 여부를 조사한다.
2. `DESIGN_REFERENCES/manifest.json`과 `shortlist.md`가 있으면 먼저 읽고, saved reference를 `Reference Pack`의 근거로 사용한다.
3. 기존 기준이 있으면 `reuse + delta`로 시작하고 변경 범위를 최소화한다.
4. `Goal/Audience/Platform`, `30-Second Understanding Checklist`, `Visual Direction + Anti-goals`, `Glossary + Object Model`로 제품 이해 계약을 먼저 고정한다.
5. `Layout/App-shell Contract`, `Token + Primitive Contract`, `Screen + Flow Coverage`로 `SLICE-1`의 구조/시각 계약을 고정한다.
6. `Interaction Model`, `Keyboard + Focus Contract`, `Accessibility Contract`, `Live Update Semantics`, `State Matrix + Fixture Strategy`, `Large-run Degradation Rules`, `Microcopy + Information Expression Rules`, `Task-based Approval Criteria`로 `SLICE-2` 이후 행동 계약을 고정한다.
7. `Implementation Prompt/Handoff`에는 `SLICE-1`과 `SLICE-2`가 읽어야 할 문서/섹션을 직접 연결한다.

## Output Contract

`UX_SPEC.md`에는 아래 heading 순서를 그대로 사용한다.

## Goal/Audience/Platform

goal, audience, platform, success impression을 한 줄씩 기록한다.

## 30-Second Understanding Checklist

사용자가 30초 안에 답할 수 있어야 하는 핵심 질문과 정답 기준을 bullet로 기록한다.

## Visual Direction + Anti-goals

visual direction 2~4개와 anti-goal 2~4개를 기록한다.

## Reference Pack (adopt/avoid)

`DESIGN_REFERENCES/manifest.json`의 saved file 경로, source URL, adopt/avoid 이유를 요약한다.

## Glossary + Object Model

핵심 용어 정의와 주요 객체 관계를 구현/카피/filter/schema가 동일한 뜻으로 쓰이게 기록한다.

## Layout/App-shell Contract

app shell, navigation, pane/layout hierarchy, screen ownership을 기록한다.

## Token + Primitive Contract

token source path candidate, primitive/component source, styling constraints를 기록한다.

## Screen + Flow Coverage

screen ids, flow ids, primary journeys, screen ownership을 기록한다.

## Implementation Prompt/Handoff

`SLICE-1`은 `30-Second Understanding Checklist`, `Layout/App-shell Contract`, `Token + Primitive Contract`, `Screen + Flow Coverage`를 읽고,
`SLICE-2`는 `UX_BEHAVIOR_ACCESSIBILITY.md`의 behavior/a11y/live/state sections를 읽는다고 명시한다.

`UX_BEHAVIOR_ACCESSIBILITY.md`에는 아래 heading 순서를 그대로 사용한다.

## Interaction Model

selection, pane sync, drawer/pin, filter persistence, resize, pointer/keyboard parity를 기록한다.

## Keyboard + Focus Contract

focus order, focus return, focus visibility, overlay/drawer focus trap, keyboard shortcuts를 기록한다.

## Accessibility Contract

non-color status rules, focus ring, contrast, hit target, reduced motion, hover/focus parity를 기록한다.

## Live Update Semantics

auto-follow, paused mode, reconnect/stale badge, partial parse failure, running-to-done transition 규칙을 기록한다.

## State Matrix + Fixture Strategy

state matrix, fixture strategy, edge state, mock plan을 기록한다.

## Large-run Degradation Rules

lane/event/edge threshold, collapse/aggregate/fade/virtualization 규칙을 기록한다.

## Microcopy + Information Expression Rules

status naming, time formatting, id truncation, unknown/redacted fallback copy를 기록한다.

## Task-based Approval Criteria

30초 과업, keyboard-only 과업, overlay focus 유지, fixture별 성공 조건을 기록한다.
