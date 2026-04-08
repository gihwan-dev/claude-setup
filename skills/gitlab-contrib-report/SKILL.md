---
name: gitlab-contrib-report
description: >
  GitLab 컨트리뷰션 월별 리포트 생성. glab CLI로 이벤트 데이터를 수집하고
  주/월/년 단위 추이 테이블 + AI 코멘트를 출력한다.
  Use when the user says "컨트리뷰션 리포트", "잔디 분석", "기여 추이",
  "gitlab-contrib-report", "$contrib", or wants to see their GitLab activity trends.
  Do not use when glab is not installed or not authenticated.
allowed-tools: Bash, Read, Grep, Glob, Write
---

# GitLab Contribution Report

glab CLI로 GitLab 컨트리뷰션 이벤트를 수집하여 주/월/년 추이 리포트 + AI 코멘트를 생성한다.

## 전제 조건

```bash
glab auth status
```

- glab 미설치 또는 인증 실패 시 → `! glab auth login` 안내 후 종료.

## Workflow

### 1. 사용자/호스트 식별

```bash
glab api /user --hostname <hostname>
```

- `glab auth status`에서 인증된 호스트를 자동 감지한다.
- 여러 호스트가 있으면 사용자에게 선택받는다.
- user id와 username을 확보한다.

### 2. 이벤트 데이터 수집

Python 스크립트를 `/tmp/claude/` 아래에 생성하여 실행한다.

**수집 범위**: 기본 최근 12개월. 사용자가 기간을 지정하면 그에 따른다.

**수집 방법**:
```
glab api "/users/{user_id}/events?per_page=100&page={page}&after={start_date}" --hostname {hostname}
```

- 페이지네이션으로 전체 이벤트를 수집한다 (최대 100페이지 안전 제한).
- 각 이벤트에서 `created_at`, `action_name`을 파싱한다.

**집계 항목**:
- `monthly_counts`: 월별 총 이벤트 수
- `weekly_counts`: 주별 총 이벤트 수 (ISO week)
- `yearly_counts`: 연도별 총 이벤트 수
- `monthly_by_action`: 월별 액션 유형 분해 (pushed to, pushed new, opened, commented on, closed, accepted, deleted, created 등)
- `daily_counts`: 일별 총 이벤트 수
- `quarterly_counts`: 분기별 총 이벤트 수

### 3. 리포트 출력

아래 형식의 마크다운 테이블을 **대화 출력**으로 제공한다. 파일로 저장하지 않는다.

#### 3-1. 전체 요약

| 항목 | 값 |
|------|-----|
| 분석 기간 | {start} ~ {end} |
| 총 이벤트 | N건 |
| 활동일 수 | N일 |
| 활동일 평균 | N.N건/일 |

#### 3-2. 월별 추이 테이블

| 월 | 총 | Push | MR | Comment | 전월 대비 |
|------|-----:|-----:|----:|--------:|--------:|
| 2025-01 | 64 | 48 | 5 | 10 | - |
| 2025-02 | 185 | 124 | 13 | 35 | +189% |

- **Push** = `pushed to` + `pushed new` 합산
- **MR** = `opened` (MR 오픈)
- **Comment** = `commented on`
- **전월 대비** = 전월 총 이벤트 대비 증감률

#### 3-3. 주별 추이 (최근 12주)

| 주 | 총 | 4주 이동평균 |
|----|---:|----------:|
| 2026-W10 | 72 | 87.8 |

#### 3-4. 연도별/분기별 요약

| 분기 | 건수 | 월 평균 |
|------|-----:|-------:|
| 2025-Q1 | 557 | 186 |

### 4. AI 코멘트

수집된 데이터를 분석하여 아래 관점의 코멘트를 작성한다:

#### 시기별 패턴 분석
- 데이터를 2~5개 Phase로 자연스럽게 구분한다.
- 각 Phase에 이름을 붙이고 (예: "웜업기", "폭발 성장기", "안정 순항기") 해당 기간의 특징을 설명한다.

#### 정량 인사이트
- **전반기 vs 후반기** 평균 비교 및 변화율
- **최근 4주 모멘텀**: 직전 4주 대비 증감률
- **Peak 기록**: 최고 월/주/일과 해당 수치
- **Push 비율 변화**: 초기 대비 최근의 push 비중 변화 → 코드 생산 vs 리뷰/협업 비중 해석

#### AI 시대 변화 해석
- Push 절대량 증가 + Push 비율 하락 패턴이 있으면: "AI로 코드 생산은 빨라지고, 사람은 리뷰·설계·소통에 집중하는 구조로 전환" 해석
- MR 수 증가 추이가 있으면: "더 작은 단위로 더 자주 배포하는 패턴" 해석
- 코멘트 비중 증가가 있으면: "리뷰어/멘토 역할 확대" 해석

### 5. 옵션

사용자가 추가 요청 시:
- **특정 기간**: `--from 2025-01 --to 2025-06` 형태로 범위 지정
- **팀 비교**: 여러 사용자 ID를 받아 비교 테이블 생성
- **프로젝트별**: 특정 프로젝트 필터링
- **파일 저장**: 사용자가 요청하면 마크다운 파일로 저장

## 주의사항

- 대화 출력 전용. 파일 저장은 사용자가 명시적으로 요청할 때만.
- API 호출이 많으므로 rate limit 주의. 실패 시 수집된 데이터까지만으로 리포트 생성.
- 이벤트 API는 최대 2년 전까지만 제공될 수 있음.
