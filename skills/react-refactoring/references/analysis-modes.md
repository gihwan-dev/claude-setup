# Analysis Modes

`react-refactoring`에서 실제 문제를 검증할 때 사용하는 상세 분석 규칙이다.

## Mode Selection

| 조건 | 모드 | 설명 |
|---|---|---|
| 1-2개 단순 문제점 | Standard Mode | sequential thinking 중심의 단일 분석 |
| 3개 이상 또는 복잡한 문제점 | Multi-Perspective Mode | 3관점 병렬 분석 후 합의 |

## Standard Mode

각 문제점마다 최소 3단계로 분석한다.

### 1. 문제 정의 검증

다음을 확인한다.

- 이 문제가 정말 문제인가?
- 현재 코드가 실제로 어떤 불편/위험을 초래하는가?
- "수정하기 좋은 코드" 9가지 기준 중 무엇을 위반하는가?
- 위반이 없다면 취향 문제인지 실질 문제인지 구분할 수 있는가?

### 2. 제안된 방향 평가

사용자가 방향을 제시했다면 다음을 확인한다.

- 제안된 변경이 실제로 개선인가?
- 복잡성을 오히려 증가시키지 않는가?
- 기존 코드베이스의 일관성을 해치지 않는가?
- 과한 추상화나 성급한 분리로 흐르지 않는가?

### 3. 대안 탐색

제안된 방향이 최선이 아니라면 다음을 정리한다.

- 더 단순한 해결책이 있는가?
- 점진적으로 개선할 수 있는 방법은 무엇인가?
- 지금 이 문제를 해결하지 않는 것이 더 합리적인가?

## Multi-Perspective Mode

각 문제점에 대해 아래 3관점 분석을 병렬 실행한다.

### Readability Advocate

```text
You are a Readability Advocate analyzing a React refactoring proposal.
Your lens: code readability, intent clarity, self-documenting code.

Read the target component at: [파일 경로]
The user's proposed issues and changes:
[문제점 목록]

For EACH issue, provide your verdict:
- Verdict: [수용/수정/기각]
- Reasoning: [Why, focused on readability impact]
- Alternative: [Better approach from readability perspective, if any]
```

### Architecture Purist

```text
You are an Architecture Purist analyzing a React refactoring proposal.
Your lens: type safety, pattern consistency, structural integrity, SOLID principles.

Read the target component at: [파일 경로]
The user's proposed issues and changes:
[문제점 목록]

For EACH issue, provide your verdict:
- Verdict: [수용/수정/기각]
- Reasoning: [Why, focused on type safety and architectural patterns]
- Alternative: [Better approach from architecture perspective, if any]
```

### Pragmatic Developer

```text
You are a Pragmatic Developer analyzing a React refactoring proposal.
Your lens: maintainability, practicality, developer experience, cost-benefit.

Read the target component at: [파일 경로]
The user's proposed issues and changes:
[문제점 목록]

For EACH issue, provide your verdict:
- Verdict: [수용/수정/기각]
- Reasoning: [Why, focused on practical maintenance impact]
- Alternative: [Better approach from practical perspective, if any]
```

## Consensus Rules

| 합의 상황 | 행동 |
|---|---|
| 3개 일치 | 높은 확신으로 해당 판단 채택 |
| 2:1 | 소수 의견의 근거를 검토한 뒤 오케스트레이터가 최종 결정 |
| 3개 상이 | 사용자에게 선택지와 근거를 보여 주고 판단을 요청 |

## When To Ask

아래 경우에는 분석을 밀어붙이지 않고 먼저 확인한다.

- 비즈니스 컨텍스트가 필요한 경우
- 기존 코드 의도가 불명확한 경우
- 사용자 제안과 분석 결과가 충돌하는 경우
- 팀 컨벤션 확인이 필요한 경우

## React / TypeScript Checklist

### 훅 분리

- 분리 후에도 co-location이 유지되는가?
- 커스텀 훅의 반환 타입이 명확한가?
- 훅 간 의존성이 단방향인가?

### 컴포넌트 분리

- Props drilling이 과도해지지 않는가?
- 상태 끌어올리기가 필요해지지 않는가?
- 컴포넌트 경계가 자연스러운가?

### 폴더 구조 변경

- import 경로가 과도하게 길어지지 않는가?
- 순환 의존성이 생기지 않는가?
- 기존 구조와 일관적인가?
