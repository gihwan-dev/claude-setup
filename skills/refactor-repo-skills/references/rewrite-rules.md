# Rewrite Rules

This document defines the criteria that `refactor-repo-skills` follows when compressing local skills.

## Official Snapshot

Snapshot date: 2026-03-14

- OpenAI instruction guide: keep the main instruction text short and improve hierarchy plus scanability.
- OpenAI skill-creator: keep only the core workflow in `SKILL.md`, and move details into `references/` or `scripts/`.
- OpenAI Codex prompting guide: prefer clear goals, boundaries, and execution rules over long upfront ceremony.
- Anthropic Claude Code memory guidance: keep root memory thin and structure it with `@import` or split files.

## Compression Rules

### 1. Frontmatter Description

- Lead with triggers and target scope.
- State when to use the skill, the main deliverable, and any excluded scope briefly.
- Omit long background explanation, implementation philosophy, and repetitive examples.

### 2. `SKILL.md` Body

- Keep workflow, selection logic, guardrails, and the validation entrypoint.
- Remove rationale, long background, and detailed catalogs that are not required for execution.
- Move large tables, variant-specific branching, and long examples into `references/`.

### 3. References Split

- Move variants, rubrics, templates, and decision matrices into `references/`.
- In `SKILL.md`, keep only when and why each reference should be read.
- Keep the reference depth to one level and make it clear that files should be read only when needed.

### 4. Scripts Over Repetition

- Move repeated calculations, smell scoring, file selection, and deterministic transforms into `scripts/`.
- If a script exists, keep only the execution point and arguments in `SKILL.md`.

### 5. Agents Metadata

- Add `agents/openai.yaml` only when explicit invocation is useful.
- Keep `display_name`, `short_description`, and `default_prompt` short enough for both people and models to parse quickly.
- Make the default prompt explicit about scope and the default batch rule.

### 6. What To Remove

- unnecessary fallback explanations
- duplicate checklists
- repeated `Hard Rules`, `Rules`, or `Checklist` sections that say the same thing
- historical rationale unrelated to execution
- procedures that demand extraneous docs

### 7. Repo-Specific Boundaries

- The canonical source is always `skills/`.
- Do not edit generated files directly. Use sync commands only.
- In v1, scope is limited to `skills/` and generated sync.
- `agent-registry` and non-skill repo infrastructure may be consulted, but not edited.

## Rewrite Checklist

- Is the frontmatter description trigger-focused?
- Is the `SKILL.md` body centered on workflow and guardrails?
- Were long detailed rules moved into `references/` or `scripts/`?
- Are generated updates handled only through sync commands?
- Are any newly created files directly necessary for the skill?
