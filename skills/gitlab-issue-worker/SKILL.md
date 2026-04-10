---
name: gitlab-issue-worker
description: >
  GitLab 이슈 기반 코드 작업 워크플로우. glab CLI로 이슈를 조회·분석하고
  코드 변경을 수행한다. 이슈 번호가 없으면 목록을 보여주고 선택받는다.
  모호한 이슈는 사용자에게 구체적 질문으로 범위를 좁힌다.
  Use when the user says "이슈 작업해줘", "이슈 처리해줘", "#123 작업",
  "gitlab issue", or mentions a GitLab issue number.
  Do not use when the project has no GitLab remote or glab is not installed.
---

# GitLab Issue Worker

glab CLI로 GitLab 이슈를 조회·분석하고 코드 작업을 수행한다.

## 전제 조건

```bash
glab auth status
git remote -v
```

- 인증 안 됨 → `! glab auth login` 안내.
- GitLab remote 없음 → 스킬 사용 불가, 사용자에게 알림.

## Workflow

### 1. 이슈 특정

**이슈 번호 있음:**

```bash
glab issue view <번호> --comments
```

**이슈 번호 없음:**

```bash
glab issue list --assignee=@me -P 10
glab issue list --assignee=none -P 10
```

- 두 명령을 병렬 실행하여 **본인 할당 이슈 + 미할당 이슈**를 모두 수집한다.
- 중복 제거 후 번호·제목·라벨·할당자 포함 목록을 보여주고 사용자에게 선택받는다.
- 두 조회 모두 결과가 없으면 `glab issue list -P 10`으로 전체 조회.

### 2. 모호성 판단

이슈의 제목·본문·라벨·코멘트를 읽고 판단한다.

**명확** — 아래를 모두 충족:
- 변경 대상(파일, 컴포넌트, API 등)이 특정 가능
- 기대 동작 또는 수정 사항이 구체적

**모호** — 하나라도 해당:
- "성능 개선", "UX 개선" 등 범위가 넓음
- 변경 대상을 특정할 수 없음
- 여러 해석이 가능

모호한 경우 사용자에게 구체적 질문을 던져 범위를 좁힌다:

```
이슈 #42: "로그인 UX 개선"
→ 다음 중 어떤 작업을 의미하나요?
  1. 로그인 폼 UI 리디자인
  2. 에러 메시지 개선
  3. 소셜 로그인 추가
  4. 기타 (직접 설명)
```

### 3. 작업 브랜치 생성

```bash
git checkout -b <prefix>/<이슈번호>-<슬러그>
```

라벨 기반 prefix: `bug` → `fix/`, `enhancement`/`feature` → `feat/`, `documentation` → `docs/`. 기본값 `feat/`.
해당 브랜치가 이미 있으면 checkout만 수행.

### 4. 구현

- 코드베이스를 탐색하여 변경 대상 파일을 파악한다.
- 이슈 요구사항에 맞게 코드를 수정/추가한다.
- 구현 중 이슈 내용과 맞지 않는 부분이 발견되면 사용자에게 확인한다.

### 5. 완료 보고

- 변경 파일 목록과 변경 요약
- 이슈 요구사항 대비 구현 내용 매핑

커밋, MR 생성, 이슈 클로즈는 사용자가 명시적으로 요청할 때만 수행.
