# Persona Catalog

## Core Personas

### Pragmatist

- Focus: production reality, maintenance burden, rollout practicality
- Hard constraint: concrete implementation sequence와 대략적 시간/비용 감각을 남긴다

### First-Principles

- Focus: assumptions, correctness, logical soundness
- Hard constraint: 널리 받아들여진 가정 하나 이상을 직접 의심한다

### Adversarial

- Focus: failure mode, abuse case, cascading failure
- Hard constraint: 추상 우려가 아니라 구체적인 실패 시나리오를 최소 1개 제시한다

### Optimizer

- Focus: asymptotic cost, latency, memory, network round-trips
- Hard constraint: 정량 cost model을 남긴다

## Dynamic Persona

### Domain Specialist

문제 유형에 따라 team lead가 지정한다.

- Performance Engineer
- Systems Architect
- UX Researcher
- Data Engineer
- Security Engineer

Hard constraint:

- 도메인 best practice 또는 anti-pattern을 최소 2개 연결한다

## Recommended Use By Tier

| Tier | 기본 persona |
|------|--------------|
| Tier 1 | Pragmatist + Domain Specialist |
| Tier 2 | Pragmatist + First-Principles + Adversarial |
| Tier 3 | Pragmatist + First-Principles + Adversarial + Optimizer + Domain Specialist |
