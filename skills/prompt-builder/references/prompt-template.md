# Prompt Template

아래 템플릿을 그대로 채워 최종 프롬프트를 만든다.

```markdown
You are an AI agent working in <workspace>.

## Objective
- <사용자가 원하는 최종 결과를 1-2문장으로 명확히>

## Deliverables
- <산출물 1>
- <산출물 2>

## Context Plan
Must Read:
- <필수 파일/문서 경로>

Optional Read:
- <필요할 때만 볼 경로>

Do Not Read:
- <무관한 경로/대용량 파일/제외 대상>

## Constraints
- <기술/정책/시간/성능 제약>
- <변경 금지 조건>

## Edge Cases
- Case 1: <상황> -> Action: <대응>
- Case 2: <상황> -> Action: <대응>
- Case 3: <상황> -> Action: <대응>

## Validation Checklist
- <검증 항목 1>
- <검증 항목 2>
- <검증 항목 3>

## Output Format
- <응답 형식과 섹션>

## Assumptions
- <확정되지 않은 가정>

## Open Questions (max 3)
- <필요시 질문>
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
