---
name: refactor-repo-skills
description: >
  Repository-specific execution skill for refactoring verbose local skills. Audit `skills/*/SKILL.md`,
  score verbosity and structure smells, then rewrite only the top 1-3 candidates or a user-specified
  skill/path so the source of truth stays concise. Keep scope to `skills/` and generated skill index
  sync only; do not edit `agent-registry` or non-skill repo infrastructure.
---

# Refactor Repo Skills

Refactor `skills/` against the source-of-truth structure. The default mode is a batch run that audits everything, then edits only the top one to three candidates.

## Hard Rules

- Always start by auditing with `python3 ${SKILL_DIR}/scripts/audit_skills.py`.
- If the user provides a `skill name` or `path`, edit only that target.
- If no target is given, edit only the top one to three candidates from the audit.
- Do not edit generated files such as `skills/INDEX.md` or `skills/manifest.json` directly. Keep them in sync only through sync commands.
- In v1, the scope is limited to `skills/` plus generated sync. Do not edit `agent-registry` or non-skill repo infrastructure.
- Keep only workflow, selection logic, and guardrails in `SKILL.md`.
- Move variants, detailed criteria, examples, and long-form rationale into `references/`.
- Remove unnecessary fallback explanations, duplicate checklists, repeated explanations, and long non-goal sections.
- Do not create extraneous docs such as `README.md`, `CHANGELOG.md`, or `INSTALLATION_GUIDE.md`.
- In a single batch, edit at most three source-of-truth skills.

## Required References

- Read `${SKILL_DIR}/references/rewrite-rules.md` when you need the rewrite criteria.

## Workflow

1. Run `audit_skills.py` over the full scope or the requested target.
2. Review the scores and reasons, then choose the top one to three candidates.
3. Read the target skill's `SKILL.md` and, when needed, its `references/` and `agents/openai.yaml` to understand the source-of-truth structure.
4. Compress the frontmatter description around triggers, and keep only workflow and guardrails in the body.
5. If more detailed rules are needed, split them into the same skill's `references/`.
6. If `agents/openai.yaml` is missing and explicit invocation would help, add it.
7. Run `python3 scripts/sync_skills_index.py` and `python3 scripts/sync_skills_index.py --check` to sync generated outputs.
8. When needed, run `python3 scripts/install_assets.py --dry-run --target all` and any relevant tests, then summarize outcomes and residual risks.

## Targeting

- No explicit input: audit everything, then edit the top one to three candidates.
- If a `skill name` or `path` is given: edit only that target.
- If a candidate is already short and structurally clear, leave it unchanged and report only the audit result.

## Validation

- `python3 ${SKILL_DIR}/scripts/audit_skills.py --limit 5`
- `python3 scripts/sync_skills_index.py`
- `python3 scripts/sync_skills_index.py --check`
- `python3 scripts/install_assets.py --dry-run --target all`
