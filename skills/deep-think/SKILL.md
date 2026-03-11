---
name: deep-think
description: >
  Adaptive multi-persona deep reasoning with tiered complexity (2-5 agents) and convergence-based synthesis.
  Deep Think v2 — Adaptive multi-persona reasoning with evidence-based depth.
  Uses tiered complexity (2-5 agents), targeted critique→reflect cycles,
  convergence shortcuts, and 3-pass PENCIL-inspired synthesis.
  Detects execution environment to choose between Agent Teams (normal mode)
  and Task Orchestration (plan mode).
  Use when the user prefixes with "deep think", "딥씽크", "깊게 생각해", or requests
  thorough analysis. Best for complex architecture, debugging, algorithmic, or
  multi-domain problems. NOT for simple lookups.
  Track A requires Agent Teams feature (Claude Code: CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1). Track B works on any platform.
---

# Deep Think v2

복잡한 문제를 tier 기반 다중 시각 분석으로 다루는 reasoning workflow다.

## Trigger

- `deep think`
- `딥씽크`
- `깊게 생각해`
- 아키텍처, 디버깅, 알고리즘, 다분야 trade-off처럼 단일 패스로 답하기 어려운 문제

단순 조회, 짧은 사실 확인, 명백한 한 파일 수정에는 쓰지 않는다.

## Track Routing

- System prompt에 `Plan mode is active`가 있으면 Track B를 사용한다.
  - Task Orchestration
  - 결과를 plan file에 쓴다
- 그렇지 않으면 Track A를 사용한다.
  - Agent Teams
  - `.deep-think/05-answer/answer.md`와 report를 남긴다

Track A only prerequisite:

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

## Tier Routing

문제를 4개 축으로 0-2점씩 평가한다.

- Solution Space Breadth
- Stakeholder Tension
- Uncertainty Level
- Impact Scope

| Tier | Score | Agents | 기본 의미 |
|------|-------|--------|-----------|
| Tier 1 | 0-2 | 2 | 집중 비교 |
| Tier 2 | 3-5 | 3 | 표준 심화 |
| Tier 3 | 6-8 | 4-5 | 복합/고위험 |

persona 상세는 `references/persona-catalog.md`를 본다.

## Core Workflow

1. Phase 0: 문제를 framing하고 tier와 persona를 정한다.
2. Phase 1: 각 persona가 evidence-tagged path를 병렬로 작성한다.
3. Phase 2: convergence 여부를 보고 challenge round를 줄일지 결정한다.
4. Phase 3:
   - 모든 tier: targeted critique
   - Tier 3: pre-mortem + author reflection 추가
5. Phase 4: `Extract -> Reconcile -> Compose` 3-pass synthesis를 수행한다.
6. Phase 5: structured confidence와 dissent를 포함해 최종 답변을 만든다.

## Path Contract

각 path는 최소한 아래를 포함한다.

1. Core Thesis
2. Evidence Chain
   - claim마다 `[CODE]`, `[BENCH]`, `[PATTERN]`, `[REASON]`, `[ASSUME]` 중 하나를 붙인다
3. Implementation Sequence
4. Risk Register
5. What This Path Uniquely Offers

`[ASSUME]`는 최종 답변에서 미검증 가정으로 따로 드러나야 한다.

## Guardrails

- critique는 구체적인 시나리오가 있어야 한다. vague critique는 synthesis에서 버린다.
- convergence가 강하면 challenge round를 생략해 시간을 줄인다.
- Tier가 애매하면 보수적으로 한 단계 올린다.
- final answer는 경로 원문을 이어붙이지 말고 synthesis 결과를 새로 작성한다.
- 마지막에는 blind spot check를 수행한다.

## References

- persona 정의: `references/persona-catalog.md`
- tier/track playbook: `references/tier-playbook.md`
- phase별 템플릿: `references/phase-templates.md`
- 문제 유형별 reasoning pattern: `references/reasoning-patterns.md`
- 실행 스크립트:
  - `scripts/deep_think.py`
  - `scripts/evaluate_paths.py`
