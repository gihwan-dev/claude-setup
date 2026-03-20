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

Lock down MVP or prototype product UI clearly enough to implement without Figma, and leave reusable UX source-of-truth documents in `UX_SPEC.md` and `UX_BEHAVIOR_ACCESSIBILITY.md`.

## Hard Rules

- Always produce exactly 2 documents: `UX_SPEC.md` and `UX_BEHAVIOR_ACCESSIBILITY.md`.
- Keep the `UI Planning Packet` section order inside `UX_SPEC.md` exactly as follows.
  - `Goal/Audience/Platform`
  - `30-Second Understanding Checklist`
  - `Visual Direction + Anti-goals`
  - `Reference Pack (adopt/avoid)`
  - `Glossary + Object Model`
  - `Layout/App-shell Contract`
  - `Token + Primitive Contract`
  - `Screen + Flow Coverage`
  - `Implementation Prompt/Handoff`
- Keep the `UX_BEHAVIOR_ACCESSIBILITY.md` section order exactly as follows.
  - `Interaction Model`
  - `Keyboard + Focus Contract`
  - `Accessibility Contract`
  - `Live Update Semantics`
  - `State Matrix + Fixture Strategy`
  - `Large-run Degradation Rules`
  - `Microcopy + Information Expression Rules`
  - `Task-based Approval Criteria`
- If an existing design system, shipped UI, brand guide, or Figma exists, record `reuse + delta`.
- Do not invent a new visual language when an existing style source already exists.
- Keep saved file paths and adopt or avoid reasons together in `Reference Pack`.
- Do not hand off without `30-Second Understanding Checklist`, `Glossary + Object Model`, `Interaction Model`, `Accessibility Contract`, `Live Update Semantics`, and `Task-based Approval Criteria`.
- This skill is advisory planning only. Long-running public-surface execution still belongs to `design-task` and `implement-task`.

## Required References

- Use `${SKILL_DIR}/references/official-patterns.md` when product UI patterns or `reuse + delta` judgment are needed.
- Use `${SKILL_DIR}/references/ui-planning-templates.md` when packet skeletons or handoff phrasing are needed.

## Workflow

1. Investigate whether the current repo already has shipped UI, a design system, a component library, brand artifacts, or Figma.
2. If `DESIGN_REFERENCES/manifest.json` and `shortlist.md` exist, read them first and use the saved references as evidence for `Reference Pack`.
3. If an existing baseline exists, start with `reuse + delta` and minimize unnecessary change.
4. Lock the product-understanding contract first through `Goal/Audience/Platform`, `30-Second Understanding Checklist`, `Visual Direction + Anti-goals`, and `Glossary + Object Model`.
5. Lock the structural and visual contract for `SLICE-1` through `Layout/App-shell Contract`, `Token + Primitive Contract`, and `Screen + Flow Coverage`.
6. Lock the behavior contract for `SLICE-2` and beyond through `Interaction Model`, `Keyboard + Focus Contract`, `Accessibility Contract`, `Live Update Semantics`, `State Matrix + Fixture Strategy`, `Large-run Degradation Rules`, `Microcopy + Information Expression Rules`, and `Task-based Approval Criteria`.
7. In `Implementation Prompt/Handoff`, explicitly connect which documents and sections `SLICE-1` and `SLICE-2` must read.

## Output Contract

Use the exact heading order below in `UX_SPEC.md`.

## Goal/Audience/Platform

Record goal, audience, platform, and success impression as one line each.

## 30-Second Understanding Checklist

Record the core questions a user should answer within 30 seconds, plus the expected answer criteria.

## Visual Direction + Anti-goals

Record 2 to 4 visual directions and 2 to 4 anti-goals.

## Reference Pack (adopt/avoid)

Summarize saved file paths, source URLs, and adopt or avoid reasons from `DESIGN_REFERENCES/manifest.json`.

## Glossary + Object Model

Record key term definitions and major object relationships so implementation, copy, filters, and schema language all stay aligned.

## Layout/App-shell Contract

Record app shell, navigation, pane or layout hierarchy, and screen ownership.

## Token + Primitive Contract

Record candidate token source paths, primitive or component sources, and styling constraints.

## Screen + Flow Coverage

Record screen IDs, flow IDs, primary journeys, and screen ownership.

## Implementation Prompt/Handoff

Explicitly state that `SLICE-1` reads `30-Second Understanding Checklist`, `Layout/App-shell Contract`, `Token + Primitive Contract`, and `Screen + Flow Coverage`, while `SLICE-2` reads the behavior, accessibility, live-update, and state sections of `UX_BEHAVIOR_ACCESSIBILITY.md`.

Use the exact heading order below in `UX_BEHAVIOR_ACCESSIBILITY.md`.

## Interaction Model

Record selection, pane sync, drawer or pin behavior, filter persistence, resize rules, and pointer or keyboard parity.

## Keyboard + Focus Contract

Record focus order, focus return, focus visibility, overlay or drawer focus traps, and keyboard shortcuts.

## Accessibility Contract

Record non-color status cues, focus-ring behavior, contrast, target size, reduced motion, and hover or focus parity.

## Live Update Semantics

Record rules for auto-follow, paused mode, reconnect or stale badges, partial parse failure, and running-to-done transitions.

## State Matrix + Fixture Strategy

Record the state matrix, fixture strategy, edge states, and mock plan.

## Large-run Degradation Rules

Record thresholds and rules for lanes, events, edge cases, collapse, aggregation, fade, and virtualization.

## Microcopy + Information Expression Rules

Record status naming, time formatting, ID truncation, and unknown or redacted fallback copy.

## Task-based Approval Criteria

Record 30-second tasks, keyboard-only tasks, overlay focus retention, and per-fixture success criteria.
