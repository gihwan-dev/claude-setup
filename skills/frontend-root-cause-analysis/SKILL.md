---
name: frontend-root-cause-analysis
description: >
  Evidence-based root cause analysis for frontend bugs using Five Whys and Socratic questioning.
  Use when debugging frontend issues with flaky UI behavior, async timing, stale state, hydration mismatch,
  focus problems, race conditions, event ordering, rendering glitches, or performance regressions, especially
  when the user wants root cause analysis instead of a quick patch. Do not use when the fix is already obvious,
  when the task is a simple type/syntax/lint error, or when planning a new feature.
---

# Frontend Root Cause Analysis

프론트엔드 버그를 증상 중심이 아니라 근본 원인 중심으로 분석하고 해결안을 제시한다.

## Language Rule

- Always respond in the user's language.
- Keep code identifiers, file paths, APIs, and commands in their original language.

## Workflow

1. Capture `symptom`, `expected behavior`, `actual behavior`, `repro steps`, and `severity` first.
2. Inspect available evidence: relevant code, recent diffs, stack traces, logs, test failures, and network behavior.
3. Build a why-chain up to five levels deep; stop early if a root cause is already supported by evidence.
4. Label every statement as exactly one of: `Fact`, `Inference`, `Assumption`.
5. Rank the most likely root-cause candidates by confidence and evidence strength.
6. Recommend:
   - the smallest high-confidence fix
   - a structural fix when the issue indicates deeper design problems
7. Define regression tests and concrete verification steps.
8. Warn explicitly when a proposed patch treats only the symptom while the cause is elsewhere.

## Stop Condition

- Stop and avoid definitive fix claims when evidence is insufficient to support a root cause.
- Treat evidence as insufficient when the top candidate is not backed by at least two independent `Fact` items.
- Ask a small number of decisive follow-up questions (max 3) and specify the exact artifact needed (log line, repro video, trace, failing test output, network capture).

## Questioning Rule

- Prefer 1 to 3 high-leverage Socratic questions that materially change diagnosis.
- Do not ask broad discovery questions that do not reduce uncertainty.
- Each question must target one unresolved assumption in the current why-chain.

## Required Output Format

Use the exact section order below:

1. Symptom Summary
2. Evidence
3. Five Whys Chain
4. Root Cause Candidates
5. Recommended Fix
6. Structural Follow-up
7. Regression Tests
8. Verification Steps

## Output Constraints

- In `Evidence` and `Five Whys Chain`, prefix each bullet with one label: `[Fact]`, `[Inference]`, or `[Assumption]`.
- In `Root Cause Candidates`, provide ranked candidates with a confidence level and linked evidence references.
- In `Recommended Fix`, present the smallest high-confidence change first.
- In `Structural Follow-up`, describe the deeper correction when architecture/state ownership/timing model is the real issue.

## Example Invocations

- `$frontend-root-cause-analysis 모달이 가끔 닫히지 않는 버그가 있는데 race condition인지 근본 원인까지 Five Whys로 분석해줘.`
- `$frontend-root-cause-analysis hydration mismatch 경고가 간헐적으로 발생해. 증상 패치 말고 근거 기반으로 원인 후보를 순위화해줘.`
- `$frontend-root-cause-analysis 입력 포커스가 랜덤하게 튀는 현상을 Socratic 질문으로 좁혀가며 원인과 회귀 테스트까지 제시해줘.`
