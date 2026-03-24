# Agent Profile Architecture

Agent profiles stay operationally thin: they carry no workflows, output formats, thresholds, retries, or tool sequencing. That operational content lives in separate policy and reference layers.
Profiles should, however, be substantively rich in persona depth. A 3-line Identity that paints a vivid thinking style is thin (no operational content). A 1-line Identity that also specifies an output format is thick (operational content leaked in).
Repo-root `AGENTS.md` carries global main-thread behavior such as manager-lane read discipline; skill and policy layers carry the concrete orchestration contract.

## Four Layers

### Profile

- Purpose: lock in who the agent is and how it interprets problems.
- Contents: `identity`, `goal`, `expertise`, `domain_lens`, `preferred_quality`, `anti_pattern_sensitivity`, `collaboration_posture`
- Location: `agent-registry/<agent-id>/instructions.md`

### Orchestration

- Purpose: define when helpers are invoked, how they are combined, and which execution boundaries apply.
- Contents: helper selection, fan-out boundaries, review trigger, budget, termination
- Location: `AGENTS.md`, `policy/workflow.toml`, `scripts/workflow_contract.py`, `skills/multi-work`, `skills/multi-review`

### Task Contract

- Purpose: define the concrete inputs, constraints, and validation flow for a specific task.
- Contents: handoff schema, validation contract, shared file policy, browser evidence checklist
- Location: `skills/implement-task`, `skills/design-task`, related `references/`

### Schema/Eval

- Purpose: keep output structure and evaluation rules outside the natural-language persona.
- Contents: `input_schema`, `output_format`, `status_enum`, `retry_policy`, `thresholds`, `tool sequencing`, `validation command`
- Location: `scripts/validate_workflow_contracts.py`, tests, skill references

## Allowed Profile Elements

- `identity`: who the agent is
- `goal`: what the agent is trying to protect or improve
- `expertise`: the knowledge domain it works in
- `domain_lens`: the angle it uses to interpret problems
- `preferred_quality`: the quality bar and code/product taste it prefers
- `anti_pattern_sensitivity`: the smells it reacts to quickly
- `collaboration_posture`: how it works with the rest of the team

## Forbidden Profile Elements

- `input_schema`
- `output_format`
- `status_enum`
- `retry_policy`
- `thresholds`
- `tool sequencing`
- `validation command`

Profiles must not contain operational language such as input contracts, output formats, workflows, status values, retry counts, or threshold rules.

## Common Template

Every helper agent shares the same section order.

```md
## Identity

## Domain Lens

## Preferred Qualities

## Sensitive Smells

## Collaboration Posture
```

## Depth Guidance

Each section should contain 2-4 lines that give the agent a recognizable thinking style, judgment lens, and collaboration personality. A label like "architecture reviewer" tells the topic; a sentence like "reads dependency graphs the way a city planner reads zoning maps" tells the reasoning approach. Use metaphors, concrete judgment criteria, and explicit scope boundaries to make each agent immediately distinguishable from its neighbors.

## Heavy Agent Playbooks

These agents keep a separate playbook outside the profile.

- `agent-registry/structure-reviewer/references/decomposition-playbook.md`
- `agent-registry/test-engineer/references/test-review-playbook.md`
- `agent-registry/react-state-reviewer/references/state-anti-patterns.md`
- `skills/implement-task/SKILL.md` for built-in `worker` delegation rules
- `agent-registry/browser-explorer/references/observation-points.md`
- `agent-registry/browser-explorer/references/agent-browser-playbook.md`

## Research Basis

This structure was synthesized on March 20, 2026 from the references below.

- OpenAI Prompting: <https://platform.openai.com/docs/guides/prompting>
- Anthropic system prompts: <https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/system-prompts>
- OpenAI Structured Outputs: <https://openai.com/index/introducing-structured-outputs-in-the-api/>
- LangChain multi-agent: <https://docs.langchain.com/oss/python/langchain/multi-agent>
- CrewAI Agents: <https://docs.crewai.com/en/concepts/agents>
- AutoGen Agents: <https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/agents.html>
