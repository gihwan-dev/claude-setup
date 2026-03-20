# UI Planning Templates

Read this file only when `figma-less-ui-design` needs to align packet skeletons or handoff wording quickly.

## `UX_SPEC.md` Skeleton

```md
# UX Specification

## Goal/Audience/Platform
- Goal:
- Audience:
- Platform:

## 30-Second Understanding Checklist
- Users should answer:

## Visual Direction + Anti-goals
- Direction:
- Anti-goals:

## Reference Pack (adopt/avoid)
- Adopt:
- Avoid:

## Glossary + Object Model
- Glossary:
- Object model:

## Layout/App-shell Contract
- Shell:
- Navigation:
- Primary panes:

## Token + Primitive Contract
- Token source path:
- Primitive/component source:
- Styling constraints:

## Screen + Flow Coverage
- Screens:
- Flows:
- Ownership:

## Implementation Prompt/Handoff
- `SLICE-1` reads:
- `SLICE-2` reads:
```

## `UX_BEHAVIOR_ACCESSIBILITY.md` Skeleton

```md
# UX Behavior & Accessibility

## Interaction Model
- Selection/sync:
- Drawer/overlay:
- Filter persistence:

## Keyboard + Focus Contract
- Focus order:
- Focus return:
- Keyboard shortcuts:

## Accessibility Contract
- Non-color status cues:
- Focus ring:
- Target size / motion:

## Live Update Semantics
- Auto-follow:
- Paused/stale/reconnect:
- Partial failure:

## State Matrix + Fixture Strategy
- State matrix:
- Fixture strategy:
- Mock plan:

## Large-run Degradation Rules
- Collapse threshold:
- Virtualization / aggregation:
- Fade / minimap:

## Microcopy + Information Expression Rules
- Status copy:
- Time formatting:
- Unknown/redacted fallback:

## Task-based Approval Criteria
- Fixture A:
- Fixture B:
- Keyboard-only:
```

## Handoff Wording

- `SLICE-1 reads UX_SPEC.md 30-Second Understanding Checklist, Layout/App-shell Contract, Token + Primitive Contract, Screen + Flow Coverage, plus UX_BEHAVIOR_ACCESSIBILITY.md Interaction Model, Accessibility Contract, Microcopy + Information Expression Rules.`
- `SLICE-2 reads UX_BEHAVIOR_ACCESSIBILITY.md Keyboard + Focus Contract, Live Update Semantics, State Matrix + Fixture Strategy, Large-run Degradation Rules, Task-based Approval Criteria.`
- `If an existing design system or Figma exists, record reuse + delta before proposing net-new style work.`
