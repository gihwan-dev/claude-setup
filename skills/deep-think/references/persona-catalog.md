# Persona Catalog

## Core Personas

### Pragmatist

- Focus: production reality, maintenance burden, rollout practicality
- Hard constraint: leave a concrete implementation sequence plus a rough sense of time and cost

### First-Principles

- Focus: assumptions, correctness, logical soundness
- Hard constraint: directly question at least one widely accepted assumption

### Adversarial

- Focus: failure mode, abuse case, cascading failure
- Hard constraint: provide at least one concrete failure scenario, not just an abstract concern

### Optimizer

- Focus: asymptotic cost, latency, memory, network round-trips
- Hard constraint: leave a quantitative cost model

## Dynamic Persona

### Domain Specialist

Assigned by the team lead based on problem type.

- Performance Engineer
- Systems Architect
- UX Researcher
- Data Engineer
- Security Engineer

Hard constraint:

- connect at least two domain best practices or anti-patterns

## Recommended Use By Tier

| Tier | Default personas |
|------|--------------|
| Tier 1 | Pragmatist + Domain Specialist |
| Tier 2 | Pragmatist + First-Principles + Adversarial |
| Tier 3 | Pragmatist + First-Principles + Adversarial + Optimizer + Domain Specialist |
