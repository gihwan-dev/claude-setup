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

### 0. Pre-flight Check

Run all checks in parallel before proceeding. If any check fails, report the
specific blocker and stop.

```bash
# Run these in parallel
git branch --show-current          # Must not be main/master
git diff --cached --stat           # Warn if staged but uncommitted changes exist
git status --porcelain             # Warn if untracked/unstaged changes exist
git log @{upstream}..HEAD --oneline 2>/dev/null  # Must have commits ahead of upstream
```

| Check | Blocker action |
|-------|---------------|
| On main/master | Ask user to create a feature branch first |
| No commits ahead of upstream | Nothing to create an MR for — stop |
| Uncommitted changes exist | Warn user; ask whether to continue or commit first |

Detect the platform once and reuse throughout:
- `.gitlab-ci.yml` exists or remote URL contains `gitlab` → GitLab (`glab`)
- Otherwise → GitHub (`gh`)

Determine `<base>` branch: check upstream tracking branch, or fall back to `main`/`master`.

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

### 4. UI 변경 시 Before/After 스크린샷

If the diff touches UI code (components, styles, layouts, templates, CSS, HTML), capture
Before/After screenshots and attach them to the MR body.

**Detect UI changes:**
```bash
git diff <base>...HEAD --name-only | grep -iE '\.(tsx|jsx|vue|svelte|html|css|scss|sass|less|styled)\b'
```

**환경 확인 후 분기:**

1. `npx playwright --version` 성공 **and** dev server 기동 가능 → Playwright로 스크린샷 촬영:
   ```bash
   git worktree add /tmp/mr-before <base>
   # install deps & start dev server in /tmp/mr-before, then:
   npx playwright screenshot --wait-for-timeout=3000 <target-url> /tmp/mr-before-screenshot.png
   git worktree remove /tmp/mr-before
   # After screenshot from current branch:
   npx playwright screenshot --wait-for-timeout=3000 <target-url> /tmp/mr-after-screenshot.png
   ```
2. Playwright 미설치 또는 dev server 기동 불가 → **스크린샷을 건너뛰고** MR 본문의 Before/After 섹션에 다음을 기재:
   ```
   > ⚠️ Playwright 미설치 또는 dev server 기동 불가로 자동 스크린샷을 생략합니다.
   > 수동으로 스크린샷을 추가해 주세요.
   ```

스크린샷 촬영 실패가 MR 생성 자체를 막지 않는다.

### 5. Find Related Issue

**반드시 관련 이슈를 검색해서 찾는다.** 브랜치명 추측에 의존하지 않는다.

#### 5-1. 이슈 번호 힌트 수집

```bash
# 브랜치명에서 힌트 추출
git branch --show-current
# 커밋 메시지에서 힌트 추출
git log <base>...HEAD --oneline
```

#### 5-2. 이슈 검색

플랫폼에 맞는 CLI로 이슈를 직접 검색한다.

**GitLab:**
```bash
# 키워드로 검색 (MR의 핵심 주제/기능명 사용)
glab issue list --search "<키워드>" --per-page 10
# 브랜치명에서 번호가 추출되면 해당 이슈 확인
glab issue view <번호>
# 본인에게 할당된 열린 이슈도 확인
glab issue list --assignee=@me --per-page 10
```

**GitHub:**
```bash
gh issue list --search "<키워드>" --limit 10
gh issue view <번호>
gh issue list --assignee=@me --limit 10
```

#### 5-3. 이슈 매칭 및 삽입

1. 검색 결과에서 MR 변경 내용과 가장 관련 있는 이슈를 선택한다.
2. 매칭된 이슈가 있으면 MR 본문의 Related Issues 섹션에 `Closes #번호`를 삽입한다.
3. 후보가 여러 개이면 사용자에게 어떤 이슈를 연결할지 확인한다.
4. 관련 이슈를 찾지 못하면 Related Issues 섹션에 "None found"를 기재하고 MR 생성을 계속 진행한다. 이슈 미발견이 MR 생성을 막지 않는다.

### 6. Preview and Confirm

MR을 실제로 생성하기 전에 다음 항목을 사용자에게 보여주고 확인을 받는다:

- **Title**: 완성된 MR 제목
- **Type**: 분류된 변경 유형
- **Target branch**: base 브랜치
- **Body preview**: 본문 전체 (마크다운)
- **Related issue**: 연결할 이슈 번호 (있으면)

사용자가 수정을 요청하면 해당 부분만 반영한다. 확인을 받은 뒤 다음 단계로 진행한다.

### 7. Create the MR

1. Push the branch if needed: `git push -u origin <branch>`.
2. Create with composed title and body using the detected platform CLI. HEREDOC으로 body를 전달하여 서식을 보존한다:
   ```bash
   # GitLab
   glab mr create --title "<title>" --description "$(cat <<'EOF'
   <body>
   EOF
   )" --target-branch <base>

   # GitHub
   gh pr create --title "<title>" --body "$(cat <<'EOF'
   <body>
   EOF
   )"
   ```
3. Return the URL.

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

## Before / After
<!-- UI 변경 시 스크린샷. UI 변경 없으면 "N/A" -->
| Before | After |
|--------|-------|
| ![before]() | ![after]() |

## Related Issues
<!-- Closes #이슈번호 형식. 여러 이슈면 각각 Closes 붙인다. 없으면 "None found" -->

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
4. **Preview the complete MR and confirm with the user** before pushing or creating.
5. **MR titles in Korean** (except the type prefix).
6. **No emoji** in titles.
7. **스크린샷 실패는 블로킹하지 않는다** — Playwright 부재 또는 dev server 기동 불가 시 안내 문구를 남기고 MR 생성을 계속 진행한다.
8. **이슈 검색은 수행하되, 미발견 시 계속 진행한다** — `glab issue list --search` 또는 `gh issue list --search`로 관련 이슈를 직접 검색하고, 찾으면 `Closes #이슈번호`를 포함한다. 검색해도 못 찾으면 "None found"를 기재하고 MR 생성을 진행한다.
