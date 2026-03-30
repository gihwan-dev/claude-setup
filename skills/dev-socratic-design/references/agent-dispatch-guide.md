# Agent Dispatch Guide

이 문서는 dev-socratic-design 세션에서 서브에이전트를 언제, 어떻게 디스패치하는지 정의한다.

## Agents Overview

| Agent | Role | Model (Claude/Codex) | Strength | Output Shape |
|-------|------|---------------------|----------|--------------|
| `socratic-partner` | design-partner | opus / gpt-5.4 xhigh | 깊은 설계 추론, 가정 발굴, 다음 질문 제안 | Claim / Evidence / Hidden assumptions / Failure possibility / Next question |
| `design-skeptic` | reviewer | sonnet / gpt-5.4 high | 반례 생성, 실패 시나리오, 롤백 난이도 평가 | Attack point / Failure scenarios / Rollback rating / Testability rating / Counterexample |
| `docs-researcher` | researcher | sonnet / gpt-5.4 medium | 코드·문서 증거 수집, 부재 보고 | Found / Relevant context / Not found / Confidence |
| `design-evaluator` | reviewer | sonnet / gpt-5.4 high | 루브릭 기반 설계 완성도 평가 | Criterion scores / Verdict / Remediation |

## Dispatch Matrix

각 FSM 상태별 primary(반드시 디스패치)와 optional(필요 시 추가) 에이전트를 정의한다.

### charter

- **Primary**: `socratic-partner` — 작업 분류와 모드 선택 근거를 분석하게 한다.
- **Prompt 예시**: "사용자가 이 작업을 요청했다: [요약]. architecture / bugfix-strategy / refactor / feature 중 어떤 모드가 맞는지 분석하고, 모드를 확정하기 위해 사용자에게 물어야 할 핵심 질문을 제안하라."

### frame

- **Primary**: `socratic-partner` — 목표, 제약, 비목표, 성공 기준의 완성도를 분석하게 한다.
- **Optional**: `docs-researcher` — 관련 코드나 기존 문서에서 제약 조건을 찾게 한다.
- **Prompt 예시 (partner)**: "현재 frame: [목표/제약/비목표/성공기준]. 빠진 것, 모호한 것, 숨어있는 가정을 분석하고 다음 질문을 제안하라."
- **Prompt 예시 (researcher)**: "[기능/모듈명]과 관련된 기존 코드, 설정, 문서를 찾아라. 특히 암묵적 제약이나 의존성에 집중하라."

### evidence-gap

- **Primary**: `docs-researcher` — 모르는 것을 코드베이스에서 조사하게 한다.
- **Optional**: `socratic-partner` — 수집된 증거를 해석하고 추가 조사 방향을 제안하게 한다.
- **Prompt 예시 (researcher)**: "이 설계에서 확인이 필요한 사항: [gap 목록]. 각각에 대해 코드베이스를 조사하고 found/not-found/confidence로 보고하라."

### system-model

- **Primary**: `docs-researcher` — 현재 시스템의 구조, 데이터 흐름, 경계를 조사하게 한다.
- **Optional**: `socratic-partner` — 조사 결과를 바탕으로 모델의 완성도를 평가하게 한다.
- **Prompt 예시 (researcher)**: "[대상 모듈/시스템]의 구조를 조사하라. 컴포넌트, 데이터 흐름, 책임 경계, invariant에 집중하라."

### alternatives

- **Primary**: `socratic-partner` — 대안을 생성하거나 기존 대안의 trade-off를 분석하게 한다.
- **Optional**: `docs-researcher` — 각 대안의 실현 가능성을 코드베이스에서 검증하게 한다.
- **Prompt 예시 (partner)**: "현재 대안: [A, B]. 각각의 강점/약점/trade-off를 분석하고, 빠진 대안이 있는지 검토하라. 사용자에게 trade-off를 명확히 드러낼 compare 질문을 제안하라."

### adversarial-review

- **Primary**: `design-skeptic` — 각 대안과 선호 방향을 공격하게 한다.
- **Optional**: `socratic-partner` — skeptic의 공격에 대한 방어 논리를 구성하게 한다.
- **Prompt 예시 (skeptic)**: "선호 대안: [X]. 이 대안의 가장 강한 주장을 먼저 공격하라. 최소 2개의 구체적 실패 시나리오, 롤백 난이도, 테스트 가능성, 반례를 제시하라."
- **Prompt 예시 (partner)**: "skeptic이 이 공격을 제기했다: [요약]. 이 공격이 타당한지, 완화할 수 있는지, 설계를 바꿔야 하는지 분석하라."

### decision

- **Primary**: `socratic-partner` — 선택과 기각 이유의 논리적 완결성을 점검하게 한다.
- **Prompt 예시**: "선택: [X], 기각: [Y, Z]. 선택 이유가 제약과 trade-off에 근거하는지 검토하라. 사용자에게 확인해야 할 validate 질문을 제안하라."

### plan

- **Primary**: `socratic-partner` — 검증 계획, 구현 전제조건, 롤백 전략의 빈틈을 분석하게 한다.
- **Optional**: `docs-researcher` — 검증 계획에 필요한 기존 테스트, 인프라, 도구를 조사하게 한다.
- **Prompt 예시 (partner)**: "현재 계획: [요약]. 빠진 검증 항목, 롤백 시나리오, 전제조건을 분석하고 risk 질문을 제안하라."

### quality-gate

- **Primary**: `design-evaluator` — 설계 문서를 루브릭으로 평가하게 한다.
- **Optional**: `design-skeptic` — 평가 결과에서 weak인 항목을 추가 공격하게 한다.
- **Prompt 예시 (evaluator)**: "이 설계 문서를 평가하라: [전체 문서 또는 핵심 섹션]. design-rubric.md의 10개 기준으로 pass/weak/fail 점수와 verdict를 제시하라."

### done / blocked

- 서브에이전트 디스패치 없음. 메인 에이전트가 직접 마무리한다.

## Context Payload

서브에이전트를 디스패치할 때 반드시 이 5개 필드를 프롬프트에 포함한다.

1. **state**: 현재 FSM 상태
2. **user_last_answer**: 사용자의 직전 응답 (첫 턴이면 원래 요청)
3. **assumption_ledger**: 현재 가정 목록 (번호, 내용, 상태)
4. **specific_question**: 이 에이전트에게 분석을 요청하는 구체적 질문
5. **design_doc_excerpt**: 설계 문서에서 현재 상태와 관련된 섹션

## Synthesis Rules

서브에이전트 결과를 사람에게 전달할 질문으로 합성할 때 따르는 규칙.

1. **단일 에이전트**: 에이전트의 "Next question" 제안을 기반으로 하되, 사용자 맥락에 맞게 재구성한다.
2. **partner + skeptic 병렬**: skeptic의 실패 시나리오로 partner의 추론을 보강한다. 질문은 가장 위험한 가정을 겨냥한다.
3. **partner + researcher 병렬**: researcher의 "Not found"가 있으면 그 부재 자체를 질문으로 전환한다. "Found"는 partner의 분석에 증거로 합류시킨다.
4. **evaluator 단독**: 스코어카드를 요약해서 fail 항목을 사용자에게 설명하고, 해당 상태로 돌아갈지 확인한다.
5. **충돌 시**: partner와 skeptic이 반대 결론이면, 양쪽 논거를 대비시키는 compare 질문을 만든다.

## Cost/Latency Guidance

| 상황 | 권장 에이전트 | 이유 |
|------|-------------|------|
| 깊은 추론이 필요한 상태 (charter, alternatives, decision) | `socratic-partner` (opus/xhigh) | 설계 품질에 직접 영향 |
| 증거 수집 (evidence-gap, system-model) | `docs-researcher` (sonnet/medium) | 빠른 탐색이 우선 |
| 공격적 검토 (adversarial-review) | `design-skeptic` (sonnet/high) | 구체적 반례 생성에 집중 |
| 최종 평가 (quality-gate) | `design-evaluator` (sonnet/high) | 루브릭 정밀 적용 |
| 빠른 보충이 필요할 때 | optional 에이전트 생략 | 불필요한 비용 절감 |
