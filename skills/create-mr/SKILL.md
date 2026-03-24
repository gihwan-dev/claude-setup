---
name: create-mr
description: >
  Create a merge request (or pull request) with change-type analysis and
  project MR/PR template adherence. Use when the user asks to create an MR/PR,
  says "MR 만들어줘", "create-mr", "$create-mr", or "PR 생성해줘".
  Do not use for amending existing MRs, reviewing code, or committing changes.
---

# Create MR

Create a properly typed, template-adherent merge request or pull request.

## Workflow

### 1. Classify MR Type

Analyze the diff to determine the primary change type before writing anything.

```bash
git log <base>...HEAD --oneline
git diff <base>...HEAD --stat
git diff <base>...HEAD
```

| Type | Signal |
|------|--------|
| feature | New user-facing functionality |
| fix | Bug correction |
| refactor | Code restructure, no behavior change |
| chore | Tooling, config, deps, CI/CD |
| docs | Documentation only |
| perf | Performance improvement |
| test | Test addition/modification only |
| hotfix | Urgent production fix |

If multiple types, choose the dominant one and note secondary concerns in the body.

### 2. Find and Apply MR Template (MANDATORY)

**Never skip this step.** Always search for templates before writing the MR body.

1. Search these paths in the target repo:
   - `.gitlab/merge_request_templates/`
   - `.github/PULL_REQUEST_TEMPLATE/`
   - `.github/PULL_REQUEST_TEMPLATE.md`
   - `.github/pull_request_template.md`
   - `docs/mr_templates/`
2. Also run a glob search: `**/*{merge_request,pull_request,PULL_REQUEST,mr_template}*`
3. If multiple templates exist, pick the one matching the MR type (e.g. `feature.md` for features).
4. **Template found** → read it, fill every section. Mark inapplicable sections "N/A" with reason.
5. **No template found** → use the fallback below and inform the user.

### 3. Gather Context

```bash
git branch --show-current
git rev-parse --abbrev-ref @{upstream} 2>/dev/null
git status
```

Warn the user if unstaged changes or untracked files exist.

### 4. Create the MR

1. Push the branch if needed: `git push -u origin <branch>`.
2. Detect platform:
   - `.gitlab-ci.yml` exists or remote contains `gitlab` → `glab mr create`
   - Otherwise → `gh pr create`
3. Create with composed title and body. Return the URL.

## MR Title

Format: `<type>(<scope>): <Korean description>` — under 70 chars, no emoji.

Examples:
- `feat(auth): 소셜 로그인 연동 추가`
- `fix(api): 페이지네이션 오프셋 계산 오류 수정`
- `refactor(core): 에러 핸들링 구조 단순화`

## Fallback Template

Use when no project template is found:

```text
## Summary
<!-- what and why, 1-3 bullets -->

## Type
<!-- feature | fix | refactor | chore | docs | perf | test | hotfix -->

## Changes
<!-- key changes, bulleted -->

## Related Issues
<!-- links or "None" -->

## Test Plan
<!-- how these changes were tested -->

## Checklist
- [ ] Self-review completed
- [ ] Tests added/updated
- [ ] Documentation updated (if applicable)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## Hard Rules

1. **Never skip template search** — always run the search, even when you assume none exists.
2. **Never leave template sections empty** — fill every section or mark "N/A" with reason.
3. **Show MR type classification** to the user before creating.
4. **Confirm with the user** before pushing or creating the MR.
5. **MR titles in Korean** (except the type prefix).
6. **No emoji** in titles.
