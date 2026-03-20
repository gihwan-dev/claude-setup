# Prompt Template

Fill this template as-is to build the final prompt.

```markdown
You are an AI agent working in <workspace>.

## Objective
- <State the user's desired end result clearly in 1-2 sentences>

## Deliverables
- <Deliverable 1>
- <Deliverable 2>

## Context Plan
Must Read:
- <Required file or document path>

Optional Read:
- <Path to consult only if needed>

Do Not Read:
- <Unrelated path, large file, or excluded target>

## Constraints
- <Technical, policy, time, or performance constraint>
- <Condition that must not be changed>

## Edge Cases
- Case 1: <situation> -> Action: <response>
- Case 2: <situation> -> Action: <response>
- Case 3: <situation> -> Action: <response>

## Validation Checklist
- <Validation item 1>
- <Validation item 2>
- <Validation item 3>

## Output Format
- <Response format and sections>

## Assumptions
- <Unconfirmed assumption>

## Open Questions (max 3)
- <Question if needed>
```

## Quick Prompt Template

```markdown
Use the context below to complete <task>.
Goal: <goal>
Must-read files: <paths>
Constraints: <constraints>
Edge cases: <3 cases>
Output: <format>
```
