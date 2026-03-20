---
name: change-architecture-doc
description: >
  Analyze git changes and generate/update architecture documentation with Mermaid diagrams.
  Analyze git changes in the current branch/worktree and create or update an
  architecture-centered change note. Prefer an existing documentation folder
  inside the project (`docs`, `packages/docs`, `guides`, `documentation`, `doc`);
  if none fits, create a markdown file at the project root. Use this when you need
  to document system boundaries, module interactions, data/event flow, and impact
  scope with Mermaid diagrams rather than implementation detail.
---

# Change Architecture Doc

Document the structural changes in the current working branch quickly and clearly.

## Core Principles

- Explain system flow and structure rather than implementation detail.
- Do not simply list changed files; record why the structure changed first.
- Include at least two Mermaid diagrams.
- Prefer an existing documentation folder, and fall back to the repo root only if needed.

## Workflow

### 1) Inspect the change scope

- At the worktree root, check the working tree status with `git status --short`.
- Check the branch name with `git branch --show-current`.
- Collect the change scope in a readable way.

```bash
git status --short
git diff --name-status
git diff --stat
```

- If you need a common-ancestor baseline, inspect an additional merge-base diff.

```bash
BASE_REF=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/@@')
[ -z "$BASE_REF" ] && BASE_REF="origin/main"
MERGE_BASE=$(git merge-base HEAD "$BASE_REF" 2>/dev/null || true)
[ -n "$MERGE_BASE" ] && git diff --name-status "$MERGE_BASE"...HEAD
```

### 2) Choose the target documentation folder

- Auto-discover the documentation folder with the script below.

```bash
python3 ${SKILL_DIR}/scripts/find_doc_target.py
```

- If `target_kind` is `docs`, use `target_path`.
- If `target_kind` is `root`, write the document at the project root.
- Even when multiple documentation folders exist, prefer the one closest to the current change scope.

### 3) Update an existing doc first, otherwise create a new one

- In the target folder, search first for docs matching these name patterns.
  - `*architecture*.md*`
  - `*design*.md*`
  - `*overview*.md*`
  - `*change*.md*`
- If a relevant doc exists, update its architecture/structure/flow section.
- If not, create a new file.
  - Filename rule: `architecture-change-<branch>-<YYYY-MM-DD>.md`
  - Replace `/` in the branch name with `-`.

### 4) Write the architecture-centered document

- Use `${SKILL_DIR}/references/doc-template.md` as the default structure.
- Choose context-appropriate Mermaid patterns from `${SKILL_DIR}/references/mermaid-patterns.md`.
- Include at least two Mermaid diagrams.
  - One for system/module structure, such as a flowchart or C4 component view.
  - One for request/data/event flow, such as a sequence diagram.
- Keep implementation detail such as function-level logic or tiny type changes under 20% of the document.

### 5) Pass the quality gate

- Make sure the document includes all of the following.
  - Background for the change and why it happened
  - A before/after structure explanation
  - At least two Mermaid diagrams
  - Impact scope and risks
  - Follow-up work or open questions
- Check that the diagrams are renderable and free of syntax errors.
- Verify that the changed-file scope and the documented impact scope are logically connected.

## Output Rules

- Write the first paragraph as a 3-5 sentence structural summary of the change.
- Keep the tone explanatory instead of ending with checklist fragments only.
- At the end of the document, record the document timestamp and the analyzed git range.
- If the user gives extra context, patch the existing document instead of recreating it from scratch.

## Reference Files

- Document template: `${SKILL_DIR}/references/doc-template.md`
- Mermaid patterns: `${SKILL_DIR}/references/mermaid-patterns.md`
- Doc-target discovery script: `${SKILL_DIR}/scripts/find_doc_target.py`
