---
name: socratic-debate
description: >
  소크라테스식 3인 팀 토론으로 계획·설계·의사결정을 다각도 검증한다.
  TeamCreate로 사회자(team lead) + advocate(socratic-partner) + skeptic(design-skeptic)
  팀을 구성하고, 라운드 기반 교차 반박으로 합의와 쟁점을 도출한다.
  "$debate", "/debate", "토론해줘", "소크라테스 토론", "죽음의 토론" 등
  사용자가 계획이나 설계에 대해 다각도 검증을 원할 때 사용한다.
  단순 질문, 코드 구현, 단일 리뷰에는 사용하지 않는다.
allowed-tools: Read, Grep, Glob, Agent, TeamCreate, SendMessage, TaskCreate, TaskUpdate, TaskList, TaskGet
---

# Socratic Debate

## Goal

사용자의 계획·설계·의사결정을 advocate와 skeptic의 구조화된 토론으로 검증하여
**합의사항 테이블 + 수정된 계획 + 품질 기준**을 도출한다.

## Hard Rules

1. **토론 대상 필수.** 대상이 없으면 "무엇에 대해 토론할까요?"로 물어본다. 대상 없이 진행하지 않는다.
2. **사회자 중계 필수.** advocate ↔ skeptic 직접 소통 금지. 모든 메시지는 사회자(team lead)를 경유한다.
3. **소크라테스식 반문.** 사회자는 상대의 논점을 전달할 때 반드시 1개 이상의 소크라테스식 질문을 추가한다.
4. **발언 제한.** 각 에이전트 발언은 200-250단어 이내.
5. **라운드 상한.** 최대 5라운드. 5라운드 후에도 합의 불가 시 양쪽 의견을 병렬 제시하고 사용자에게 결정을 맡긴다.
6. **코드 수정 금지.** 읽기 전용. 토론 결과물은 텍스트 아웃풋으로만 제공한다.
7. **raw 출력 금지.** 에이전트 응답을 그대로 사용자에게 보여주지 않는다. 반드시 합성·정리 후 전달한다.

## Invocation

```
$debate                          # 토론 대상을 물어봄
$debate <계획/설계 설명>          # 해당 내용으로 토론 시작
$debate <파일경로>               # 파일 내용을 토론 대상으로 사용
```

## Team Structure

```
TeamCreate("socratic-debate")
├── team-lead (사회자, 나): 중재 + 소크라테스 반문 + 합의/쟁점 정리
├── advocate (socratic-partner): 강점 논증 + 약점 인정 + 개선 방향
└── skeptic (design-skeptic): 약점 지적 + 실패 시나리오 + 대안 제시
```

### Advocate Spawn

```
Agent({
  name: "advocate",
  subagent_type: "socratic-partner",
  team_name: "socratic-debate",
  prompt: <Round 1 초기 프롬프트 — 아래 참조>
})
```

### Skeptic Spawn

```
Agent({
  name: "skeptic",
  subagent_type: "design-skeptic",
  team_name: "socratic-debate",
  prompt: <Round 1 초기 프롬프트 — 아래 참조>
})
```

## Round Protocol

### Round 1: 개진 (Opening)

**advocate와 skeptic을 동시(병렬) 스폰한다.**

Advocate 초기 프롬프트:
```
당신은 소크라테스식 토론의 advocate 역할이다.
아래 [토론 대상]에 대해 가장 강력한 3가지 강점을 논증해라.
맹목적 옹호가 아니라 약점도 인정하되, 각 강점에 대해 개선 방향을 함께 제시해라.

발언 구조 (필수):
- Claim: 주장
- Evidence: 근거 (코드, 도메인 지식, 구체적 사례)
- Hidden Assumption: 이 주장이 성립하려면 참이어야 하는 전제
- Failure Possibility: 이 주장이 무너지는 조건

200-250단어 이내로 작성한다. 한국어로 소통한다.
반드시 사회자(team lead)에게만 SendMessage로 응답한다.

---
[토론 대상]
{subject}
```

Skeptic 초기 프롬프트:
```
당신은 소크라테스식 토론의 skeptic 역할이다.
아래 [토론 대상]에 대해 가장 위험한 3가지 약점 또는 빠진 부분을 지적해라.
파괴가 목적이 아니라 강화가 목적이다. 각 약점에 대해 반드시 구체적 대안을 제시해라.

발언 구조 (필수):
- Attack: 가장 강한 주장부터 공격
- Failure Scenarios: 2-3개 구체적 실패 시나리오 (트리거 조건 명시)
- Rollback Difficulty: trivial / moderate / hard / catastrophic
- Counterexample: 이 설계가 잘못된 결과를 내는 현실적 상황

200-250단어 이내로 작성한다. 한국어로 소통한다.
반드시 사회자(team lead)에게만 SendMessage로 응답한다.

---
[토론 대상]
{subject}
```

**사회자 행동**: 양쪽 수신 후 → 충돌 지점 테이블 정리 → 사용자에게 표시

충돌 지점 테이블 형식:
```markdown
| # | 쟁점 | Advocate 입장 | Skeptic 입장 | 충돌 유형 |
|---|------|--------------|-------------|----------|
| 1 | ...  | ...          | ...         | 전제 충돌 / 우선순위 차이 / 해법 상이 |
```

### Round 2: 교차 반박 (Cross-Rebuttal)

각 에이전트에게 상대의 핵심 논점을 전달하면서 **소크라테스식 질문 1개를 추가**한다.

Advocate에게 보내는 메시지:
```
skeptic이 다음과 같이 반박했다:
{skeptic 핵심 논점 요약}

소크라테스 질문: {반문}

위 반박에 대해 교차 반박해라. 동의하는 부분은 인정하고,
반박할 부분은 Claim → Evidence → Hidden Assumption → Failure Possibility 구조로 응답해라.
200-250단어 이내. 사회자에게만 SendMessage로 응답한다.
```

Skeptic에게 보내는 메시지: (동일 구조, advocate 논점 전달)

**소크라테스 질문 생성 가이드**: See [references/socratic-questions.md](references/socratic-questions.md)

**사회자 행동**: 양쪽 수신 후 → 합의점과 남은 쟁점을 분리 정리 → 사용자에게 표시

```markdown
### 합의점
- ...

### 남은 쟁점
| # | 쟁점 | 핵심 분기점 |
|---|------|------------|
| 1 | ...  | ...        |
```

### Round 3: 수렴 (Convergence)

남은 쟁점에 대해 각자에게 **구체적 해법**을 요구한다.

```
다음 쟁점에 대해 구체적 해법을 제시해라.
"~하면 된다" 수준의 추상적 답변은 금지. 구현 수준의 구체성을 요구한다.

남은 쟁점:
{remaining_issues}

200-250단어 이내. 사회자에게만 SendMessage로 응답한다.
```

**사회자 행동**: 최종 합의사항 + 원래 계획 대비 변경사항 정리 → 사용자에게 표시

### Round 4-5: 추가 라운드 (Optional)

Round 3에서 합의 안 된 쟁점이 있으면 Round 4를 진행한다.
- 각 추가 라운드는 Round 2 형식(교차 반박 + 소크라테스 반문)을 따른다.
- Round 5 후에도 합의 불가 시: 양쪽 의견을 병렬 제시하고 사용자에게 결정을 맡긴다.

## Agent Liveness

- 에이전트가 idle 상태이면 SendMessage로 리마인드를 보낸다.
- 1회 리마인드 후에도 응답 없으면 사용자에게 알린다.
- idle은 정상 상태이다 — 메시지를 보내면 깨어난다.

## Output Format

토론 종료 후 다음 3가지를 정리하여 사용자에게 제공한다.

### 1. 합의사항 테이블

```markdown
| # | 항목 | 결정 | 근거 |
|---|------|------|------|
| 1 | ...  | 유지 / 변경 / 추가 / 삭제 | advocate·skeptic 공통 근거 |
```

### 2. 수정된 계획 (Diff)

원래 계획 대비 변경된 부분을 구체적으로 명시한다.

```markdown
#### 변경사항
- **[항목]**: (기존) ... → (변경) ...

#### 유지사항
- **[항목]**: 유지 이유
```

### 3. 품질 기준

토론에서 도출된, 이 설계가 만족해야 하는 검증 기준.

```markdown
| # | 기준 | 검증 방법 | 출처 라운드 |
|---|------|----------|-----------|
| 1 | ...  | ...      | Round N   |
```

## Shutdown

아웃풋 정리 후 advocate, skeptic에게 shutdown_request를 보낸다:

```
SendMessage({ to: "advocate", message: { type: "shutdown_request" } })
SendMessage({ to: "skeptic", message: { type: "shutdown_request" } })
```

## References

- [소크라테스 질문 가이드](references/socratic-questions.md) — 질문 유형별 예시와 생성 규칙
