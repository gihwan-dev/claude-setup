---
name: gitlab-issue-picker
description: >
  GitLab 이슈 우선순위 추천. glab CLI로 할당/미할당 이슈를 수집하고
  우선순위 라벨, 마감일, 가중치를 분석하여 작업할 이슈 Top 5를 추천한다.
  Use when the user says "이슈 추천해줘", "뭐 작업할까", "이슈 골라줘",
  "gitlab-issue-picker", "$pick", or wants help deciding which issue to work on.
  Do not use when glab is not installed or not authenticated.
allowed-tools: Bash, Read, Grep, Glob
---

# GitLab Issue Picker

glab CLI로 GitLab 이슈를 수집하고 우선순위를 분석하여 지금 작업할 이슈를 추천한다.

## 성공 기준

이 스킬의 실행이 성공으로 간주되려면 다음을 모두 충족해야 한다:
- glab 인증과 GitLab 리모트 확인을 통과했다.
- 최소 1개 이상의 이슈를 수집하여 우선순위 카드를 출력했다.
- 각 카드에 IID, 제목, 우선순위 근거, 복잡도 추정이 포함되어 있다.
- "작업할 이슈 번호를 알려주세요"로 후속 안내를 완료했다.

위 조건 중 하나라도 실패하면 실패 원인을 한 줄로 보고하고 종료한다.

## 전제 조건

```bash
glab auth status
git remote -v
```

- `glab auth status`가 비정상 종료하면 `glab auth login` 안내 후 **즉시 종료**. 이후 단계를 진행하지 않는다.
- `git remote -v` 출력에 GitLab 호스트가 없으면 스킬 사용 불가, 사용자에게 알리고 **즉시 종료**.
- glab 명령이 `unknown command`, `not found`, 또는 HTTP 4xx/5xx 에러를 반환하면 원인을 한 줄로 설명하고 **즉시 종료**.

## Workflow

### 1. 이슈 수집

두 명령을 **병렬 실행**하여 할당/미할당 이슈를 모두 수집한다.

```bash
glab issue list --assignee=@me -P 20 --output json 2>/dev/null
glab issue list --assignee=none -P 20 --output json 2>/dev/null
```

**수집 실패 처리**:
- 한쪽만 실패하면 성공한 쪽 결과만 사용한다.
- 둘 다 빈 결과(`[]` 또는 null)면 `glab issue list -P 20 --output json`으로 전체 조회 폴백.
- 전체 조회도 빈 결과면 "열린 이슈가 없습니다"를 출력하고 **즉시 종료**.
- JSON 파싱 실패(glab이 HTML이나 에러 메시지를 반환한 경우) 시 원본 출력 첫 3줄을 인용하며 "glab 응답이 JSON이 아닙니다"를 보고하고 **즉시 종료**.

**glab 명령 실행 시 주의**:
- `--output json` 결과가 빈 문자열이면 빈 배열(`[]`)로 취급한다.
- glab 명령의 exit code가 0이어도 stderr에 경고가 있을 수 있다 — stderr는 무시하고 stdout만 파싱한다.
- `--assignee=@me`가 실패하면(일부 GitLab 인스턴스에서 `@me` 미지원) `glab api user` 로 현재 사용자 username을 얻어 `--assignee={username}`으로 재시도한다.

중복 이슈는 IID 기준으로 제거한다.

### 2. 우선순위 분석

수집된 JSON에서 다음 신호를 종합하여 이슈별 우선순위를 판단한다.

| 신호 | 감지 방법 | 중요도 |
|------|----------|--------|
| 우선순위 라벨 | `labels[]`에서 `priority::1`, `priority::2`, `P1`, `P2`, `urgent`, `critical`, `high`, `medium`, `low` 등 | 최상 |
| 심각도 라벨 | `labels[]`에서 `severity::1`, `severity::critical`, `S1`, `S2` 등 | 상 |
| 마감일 | `due_date` — 오늘에 가까울수록 높음, 초과(overdue)면 최우선 | 상 |
| 가중치 | `weight` — 높을수록 중요 | 중 |
| 마일스톤 마감 | `milestone.due_date` — 근접 시 우선 | 중 |
| 생성일 | `created_at` — 오래된 이슈 약간 우선 | tiebreaker |

프로젝트에 우선순위/심각도 라벨이 없으면 마감일 → 가중치 → 생성일 순서로 판단한다.

라벨이 전혀 없고 마감일/가중치도 미설정인 이슈는 생성일 순으로 정렬하되, "우선순위 판단 근거 없음 — 라벨 또는 마감일 설정 권장"이라고 명시한다.

### 3. 추천 출력

카테고리별 Top 5를 카드 형태로 출력한다.

```
## 내게 할당된 이슈 (Top 5)

### 1. #142 — 로그인 페이지 비밀번호 재설정 버튼 미작동

| 항목 | 내용 |
|------|------|
| 요약 | 비밀번호 재설정 버튼 클릭 시 아무 동작 없는 버그 |
| 우선순위 근거 | priority::1, 마감 D-3 (2026-04-18) |
| 예상 복잡도 | 낮음 — 이벤트 핸들러 누락 가능성 |
| 라벨 | bug, priority::1, frontend |

---

### 2. #98 — ...

---

## 미할당 이슈 (Top 5)

### 1. #201 — ...
```

각 카드의 필드:

- **요약**: 이슈 제목이 아닌, 본문을 읽고 쉬운 한국어 한 줄로 설명. 본문이 비어 있거나 접근 불가하면 제목을 그대로 사용하고 "(본문 없음)"을 덧붙인다.
- **우선순위 근거**: 이 이슈가 왜 상위 랭크인지 (라벨, 마감일 등).
- **예상 복잡도**: 아래 규칙으로 추정.
- **라벨**: 이슈에 붙은 라벨 나열.

### 4. 복잡도 추정

| 신호 | 판단 |
|------|------|
| `size::S`, `size::XS`, weight ≤ 2 | 낮음 |
| `size::M`, weight 3~5 | 중간 |
| `size::L`, `size::XL`, weight ≥ 6 | 높음 |
| 설명이 짧고 변경 범위가 좁음 | 낮음 |
| 여러 파일/컴포넌트 언급 | 높음 |
| 판단 근거 부족 | "판단 불가 — 이슈 상세 확인 필요" |

### 5. 후속 안내

추천 목록 출력 후:

```
작업할 이슈 번호를 알려주세요.
선택하면 바로 작업을 시작할 수 있습니다.
```

카테고리가 하나만 결과가 있으면 해당 카테고리만 표시한다.
이슈가 5개 미만이면 있는 만큼만 표시한다.
