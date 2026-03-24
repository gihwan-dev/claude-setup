---
name: figma-less-ui-design
description: >
  Advisory skill for no-Figma MVP/prototype UI planning. Use when design-task has
  delivery_strategy=ui-first and the team needs UX planning docs without Figma.
  Produces UX_SPEC.md and UX_BEHAVIOR_ACCESSIBILITY.md. Falls back to reuse+delta
  when an existing design system or Figma exists. Do not invoke standalone outside
  of a design-task context.
allowed-tools: Read, Grep, Glob, Write, Agent
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

### `UX_SPEC.md` — use the exact heading order below

| Section | Key content |
|---------|------------|
| Goal/Audience/Platform | goal, audience, platform, success impression (one line each) |
| 30-Second Understanding Checklist | core questions a user answers within 30 seconds + expected criteria |
| Visual Direction + Anti-goals | 2-4 visual directions, 2-4 anti-goals |
| Reference Pack (adopt/avoid) | saved file paths, source URLs, adopt/avoid reasons from `manifest.json` |
| Glossary + Object Model | key terms, major object relationships for aligned implementation/copy/schema |
| Layout/App-shell Contract | app shell, navigation, pane hierarchy, screen ownership |
| Token + Primitive Contract | token source paths, primitive/component sources, styling constraints |
| Screen + Flow Coverage | screen IDs, flow IDs, primary journeys, screen ownership |
| Implementation Prompt/Handoff | SLICE-1 reads checklist/layout/token/screen-flow; SLICE-2 reads behavior/a11y/state sections |

### `UX_BEHAVIOR_ACCESSIBILITY.md` — use the exact heading order below

| Section | Key content |
|---------|------------|
| Interaction Model | selection, pane sync, drawer/pin, filter persistence, resize, pointer/keyboard parity |
| Keyboard + Focus Contract | focus order/return/visibility, overlay focus traps, keyboard shortcuts |
| Accessibility Contract | non-color cues, focus-ring, contrast, target size, reduced motion, hover/focus parity |
| Live Update Semantics | auto-follow, paused mode, reconnect/stale badges, parse failure, running-to-done |
| State Matrix + Fixture Strategy | state matrix, fixture strategy, edge states, mock plan |
| Large-run Degradation Rules | thresholds for lanes, events, collapse, aggregation, fade, virtualization |
| Microcopy + Information Expression Rules | status naming, time formatting, ID truncation, unknown/redacted fallback |
| Task-based Approval Criteria | 30-second tasks, keyboard-only tasks, overlay focus retention, per-fixture criteria |
