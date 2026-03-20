# Analysis Modes

Detailed analysis rules used by `react-refactoring` when validating whether a concern is real.

## Mode Selection

| Condition | Mode | Description |
|---|---|---|
| 1-2 simple concerns | Standard Mode | Single analysis centered on sequential reasoning |
| 3+ concerns or complex concerns | Multi-Perspective Mode | Parallel analysis from three perspectives followed by consensus |

## Standard Mode

Analyze each concern in at least three steps.

### 1. Validate the problem definition

Check the following:

- Is this truly a problem?
- What concrete inconvenience or risk does the current code create?
- Which of the 9 criteria for "code that is easy to change" does it violate?
- If it violates none, can you distinguish between preference and a real engineering issue?

### 2. Evaluate the proposed direction

If the user already proposed a direction, check:

- Is the proposed change actually an improvement?
- Does it increase complexity instead?
- Does it break consistency with the existing codebase?
- Does it drift into over-abstraction or premature splitting?

### 3. Explore alternatives

If the proposal is not the best path, clarify:

- Is there a simpler solution?
- What is the incremental way to improve it?
- Is it more rational not to solve this problem right now?

## Multi-Perspective Mode

Run the following three lenses in parallel for each concern.

### Readability Advocate

```text
You are a Readability Advocate analyzing a React refactoring proposal.
Your lens: code readability, intent clarity, self-documenting code.

Read the target component at: [file path]
The user's proposed issues and changes:
[issue list]

For EACH issue, provide your verdict:
- Verdict: [accept/revise/reject]
- Reasoning: [Why, focused on readability impact]
- Alternative: [Better approach from readability perspective, if any]
```

### Architecture Purist

```text
You are an Architecture Purist analyzing a React refactoring proposal.
Your lens: type safety, pattern consistency, structural integrity, SOLID principles.

Read the target component at: [file path]
The user's proposed issues and changes:
[issue list]

For EACH issue, provide your verdict:
- Verdict: [accept/revise/reject]
- Reasoning: [Why, focused on type safety and architectural patterns]
- Alternative: [Better approach from architecture perspective, if any]
```

### Pragmatic Developer

```text
You are a Pragmatic Developer analyzing a React refactoring proposal.
Your lens: maintainability, practicality, developer experience, cost-benefit.

Read the target component at: [file path]
The user's proposed issues and changes:
[issue list]

For EACH issue, provide your verdict:
- Verdict: [accept/revise/reject]
- Reasoning: [Why, focused on practical maintenance impact]
- Alternative: [Better approach from practical perspective, if any]
```

## Consensus Rules

| Consensus state | Action |
|---|---|
| All 3 agree | Adopt the verdict with high confidence |
| 2:1 split | The orchestrator reviews the minority reasoning and makes the final call |
| All 3 disagree | Show the user the options and reasoning, then ask them to decide |

## When To Ask First

Do not push the analysis forward without clarification in the following cases:

- Business context is required
- The intent of the existing code is unclear
- The user's proposal conflicts with the analysis result
- Team convention confirmation is required

## React / TypeScript Checklist

### Hook extraction

- Is co-location preserved after extraction?
- Is the custom hook's return type clear?
- Are dependencies between hooks one-way?

### Component splitting

- Does it create excessive props drilling?
- Does it force state to be lifted unnecessarily?
- Are the component boundaries natural?

### Folder structure changes

- Do import paths become excessively long?
- Does it create circular dependencies?
- Does it stay consistent with the existing structure?
