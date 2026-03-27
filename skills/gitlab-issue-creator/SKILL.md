---
name: gitlab-issue-creator
description: >
  Create GitLab issues from natural-language requirements with preview-first
  confirmation and safe metadata selection. Use when the user says
  "GitLab 이슈 만들어줘", "issue 생성해줘", "이 요구사항으로 이슈 등록해줘",
  or asks to run `glab issue create`. Resolve the target repo explicitly,
  fetch project labels/users/milestones/templates before drafting, and only
  create after the user confirms the preview. Do not use when glab auth is
  unavailable for the target host or when the target is not a GitLab project.
allowed-tools: Bash, Read, Grep, Glob
---

# GitLab Issue Creator

Create GitLab issues from a requirement brief without guessing repo metadata.
Always preview the final title, body, labels, assignee, and milestone before
running `glab issue create`.

## Workflow

### 1. Preflight

Run auth and target resolution first.

```bash
glab auth status
python3 ${SKILL_DIR}/scripts/project_context.py --repo "<optional repo or GitLab URL>"
```

Hard rules:
- If the target host is unauthenticated, stop and tell the user the exact command:
  `glab auth login --hostname <host>`.
- If `--repo` is omitted, trust only GitLab remotes discovered from `git remote -v`.
  If no GitLab remote exists, stop and ask for `group/project` or a full GitLab URL.
- Do not assume the current repo host is GitLab. This workspace may have a GitHub remote.

### 2. Fetch Project Context

Use the helper output as the source of truth for metadata.

```bash
python3 ${SKILL_DIR}/scripts/project_context.py --repo "<optional repo or GitLab URL>" > /tmp/gitlab-issue-context.json
```

The helper returns:
- resolved host and project path
- project info and a stable `repo_selector` for `glab -R`
- current `glab` user
- existing labels
- assignable project users
- active milestones
- issue templates

If the helper fails, surface the blocker instead of guessing.

### 3. Draft Title And Check Duplicates

Create a short, concrete title from the requirement, then search for existing issues before drafting the body.

```bash
REPO_SELECTOR="$(python3 - <<'PY'
import json
print(json.load(open('/tmp/gitlab-issue-context.json'))['target']['repo_selector'])
PY
)"
glab issue list -R "$REPO_SELECTOR" --search "<title or tight keyword query>" --in title,description -O json
```

- Show close matches first if the result is non-empty.
- If a likely duplicate exists, ask the user whether to create a new issue anyway.

### 4. Draft The Body

Template precedence:
1. If there is exactly one issue template, fetch and fill it.
2. If there are multiple templates, show the names and ask the user to choose.
3. If there is no template, use the fallback structure below.

Fetch a template when needed:

```bash
python3 - <<'PY'
import json
ctx = json.load(open('/tmp/gitlab-issue-context.json'))
print(ctx['target']['host'])
print(ctx['target']['project_path_encoded'])
print(ctx['issue_templates'][0]['key'])
PY

glab api --hostname "<host>" "projects/<encoded_project>/templates/issues/<template_key>"
```

Fallback body structure:

```md
## Summary
- what should change

## Problem or Goal
- why this is needed

## Scope
- in scope
- out of scope

## Acceptance Criteria
- [ ] concrete user-visible outcomes

## Context
- constraints, links, screenshots, related issues

## Open Questions
- unresolved decisions, or `None`
```

### 5. Metadata Rules

Use only project metadata returned by the helper.

- Labels: choose only from the existing project labels list. If a requested label does not exist, omit it and mention that omission in the preview. Never create labels implicitly.
- Assignee: if the user did not specify one, default to the current `glab` username only when that username exists in the project users list. Otherwise ask.
- Milestone: set it only on exact or very high-confidence match against active milestones. If ambiguous, leave it unset and say so in the preview.
- Epic: support only an explicit numeric epic ID passed by the user. Do not infer epics from titles.
- Optional overrides: pass through explicit `due date`, `confidential`, and `weight` only when the user supplied them.

### 6. Preview First

Before creation, show this preview and wait for confirmation.

```text
Repo: <repo_selector>
Title: <title>
Labels: <comma-separated labels or none>
Assignee: <username or none>
Milestone: <title or none>
Due date: <YYYY-MM-DD or none>
Confidential: <true|false>
Weight: <number or none>

Body:
<full issue body>
```

Do not run `glab issue create` until the user confirms.

### 7. Create The Issue

After confirmation, create the issue with the previewed values only.

```bash
BODY="$(cat /tmp/gitlab-issue-body.md)"
glab issue create \
  -R "$REPO_SELECTOR" \
  -t "$TITLE" \
  -d "$BODY" \
  -a "$ASSIGNEE" \
  -l "$LABEL_ONE" \
  -l "$LABEL_TWO" \
  -m "$MILESTONE" \
  --due-date "$DUE_DATE" \
  -w "$WEIGHT" \
  --yes
```

Rules:
- Omit unset flags instead of passing empty strings.
- Add `--confidential` only when the issue should be confidential.
- Return the created issue URL and IID, plus the final metadata summary.
