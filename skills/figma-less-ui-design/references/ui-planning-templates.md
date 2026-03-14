# UI Planning Templates

`figma-less-ui-design`이 packet skeleton이나 handoff 문장을 빠르게 맞출 때만 이 파일을 읽는다.

## UI Planning Packet Skeleton

```md
# UX Specification

## Goal/Audience/Platform
- Goal:
- Audience:
- Platform:

## Visual Direction + Anti-goals
- Direction:
- Anti-goals:

## Reference Pack (adopt/avoid)
- Adopt:
- Avoid:

## Layout/App-shell Contract
- Shell:
- Navigation:
- Primary panes:

## Token + Primitive Contract
- Token source path:
- Primitive/component source:
- Styling constraints:

## Screen/Flow/State Coverage
- Screens:
- Flows:
- State matrix:
- Mock strategy:
- Edge states:

## Review Loop
- Reviewers:
- Evidence:
- Approval gate:

## Implementation Prompt/Handoff
- `SLICE-1` reads:
- `SLICE-2` reads:
- `SLICE-3+` waits for:
```

## Handoff Wording

- `SLICE-1 reads Layout/App-shell Contract, Token + Primitive Contract, Review Loop.`
- `SLICE-2 reads Screen/Flow/State Coverage state matrix, mock plan, edge states.`
- `If an existing design system or Figma exists, record reuse + delta before proposing net-new style work.`
