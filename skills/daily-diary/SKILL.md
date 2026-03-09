---
name: daily-diary
description: >
  Auto-generate daily diary from AI agent activity logs and Obsidian vault changes.
  매일 하루가 끝날 때 AI 에이전트 활동 히스토리와 Obsidian 볼트 변경사항을 기반으로
  자동 일기를 생성한다. "일기 써줘", "daily diary", "오늘 일기", "어제 일기" 등의 요청 시 사용.
---

# Daily Diary

AI 에이전트 활동 로그와 Obsidian 볼트 변경사항을 종합하여 Daily Notes에 일기를 자동 생성한다.

## 설정

```
VAULT_PATH=/Users/choegihwan/Documents/Projects/Obsidian-frontend-journey
DAILY_NOTES_DIR={VAULT_PATH}/Daily Notes
HISTORY_FILE=${AGENT_HISTORY_FILE:-~/.claude/history.jsonl}
SCRIPT_PATH=${SKILL_DIR}/scripts/extract_history.py
```

## 워크플로우

### 1단계: 날짜 결정

- 기본값: 오늘 날짜 (`YYYY-MM-DD`)
- 사용자가 "어제 일기", "2026-02-10 일기" 등 지정 시 해당 날짜 사용
- `DATE` 변수에 `YYYY-MM-DD` 형식으로 저장

### 2단계: 에이전트 활동 추출

Python 스크립트를 실행하여 해당 날짜의 에이전트 활동을 추출한다.

```bash
python3 ${SKILL_DIR}/scripts/extract_history.py --date {DATE}
```

이 스크립트는 다음을 수행한다:
- `${AGENT_HISTORY_FILE}`에서 해당 날짜의 사용자 요청을 필터링
- 프로젝트별로 그룹화하여 시간순 정렬
- 각 프로젝트 디렉토리에서 해당 날짜의 `git log`를 수집
- 결과를 구조화된 텍스트로 stdout에 출력

스크립트 출력이 비어있거나 "활동 없음"이면 → "오늘은 에이전트 작업이 없었습니다"로 처리.

### 3단계: Obsidian 볼트 변경사항 추출

Bash로 직접 실행한다.

```bash
cd "/Users/choegihwan/Documents/Projects/Obsidian-frontend-journey"

# 해당 날짜의 커밋 목록
COMMITS=$(git log --since="{DATE} 00:00:00" --until="{DATE} 23:59:59" --format="%h %s" 2>/dev/null)

if [ -n "$COMMITS" ]; then
  echo "$COMMITS"

  # 첫 커밋과 마지막 커밋 해시 추출
  FIRST=$(git log --since="{DATE} 00:00:00" --until="{DATE} 23:59:59" --format="%h" --reverse 2>/dev/null | head -1)
  LAST=$(git log --since="{DATE} 00:00:00" --until="{DATE} 23:59:59" --format="%h" 2>/dev/null | head -1)

  # 변경된 md 파일 통계 (.obsidian 제외)
  git diff --stat "${FIRST}^..${LAST}" -- '*.md' ':!.obsidian' 2>/dev/null
fi
```

커밋이 없으면 → 기록 활동 섹션을 생략한다.

### 4단계: 일기 작성

너는 하루의 활동 로그를 사람이 다시 읽고 싶어지는 일기이자,
나중에 이력서의 재료로 재사용할 수 있는 기록으로 바꾸는 편집자다.

목표는 로그를 나열하는 것이 아니라, 하루의 작업을
`왜 했는지 → 무엇을 했는지 → 무엇이 남았는지`
흐름으로 자연스럽게 정리하는 것이다.

#### 절대 하지 말 것
- 작성 과정, 판단 기준, 제약 조건을 본문에 쓰지 않는다.
- 아래 표현은 출력 금지:
  - 제공된 사실 데이터만 사용했다
  - 요청 범위가 한정되어
  - total requests
  - decision signals
  - 구조를 채웠다
  - 근거를 명시했다
  - 작성하기로 결정했다
  - 커밋 N건
  - 변경 md N건
- backup / wip / temp 류의 커밋 메시지를 본문 활동 설명으로 직접 쓰지 않는다.
- 파일 경로 나열로 본문을 대신하지 않는다.
- 확실하지 않은 사실은 만들지 않는다. 다만 파일명, 폴더명, 사용자 요청에서
  안전하게 일반화할 수 있는 수준의 상위 개념화는 허용한다.

#### 해석 규칙
1. 사용자 요청은 '의도'의 근거로 사용한다.
2. 생성/수정된 파일과 노트는 '산출물'의 근거로 사용한다.
3. git 기록은 '작업이 실제로 남았다는 증거'로만 사용한다.
4. 같은 주제를 가리키는 파일은 하나의 작업으로 묶는다.
5. 활동이 작아도 과장하지 말고, 다음 동사 위주로 보수적으로 표현한다:
   정리했다, 보강했다, 연결했다, 문서화했다, 다듬었다, 시각화했다, 유지했다.

#### 중요도 판단
다음 순서로 중요한 내용을 먼저 쓴다.
1. 새로 만든 결과물, 명확한 완료 작업
2. 구조 개선, 자동화, 문제 해결
3. 학습 노트 정리, 문서화, 시각화
4. 단순 백업, 형식 변경

#### 출력 규칙
- 한국어로 작성한다.
- 프로젝트당 핵심 bullet 2~4개만 작성한다.
- 각 bullet은 한 문장으로 쓰고,
  `무엇을 했다 + 왜/어떻게 했다 + 남은 결과` 흐름을 따른다.
- 불필요한 시간, 요청 수, 커밋 수는 쓰지 않는다.
- 템플릿 외 섹션은 추가하지 않는다.
- `### 🧾 커리어 자산`은 근거가 충분할 때만 1~3개 작성하고,
  근거가 약하면 생략한다.
- 회고는 1~2문장으로 쓴다.

#### 출력 템플릿

```markdown
---

## 📝 Daily Diary

### 🖥️ 개발 활동

#### {프로젝트명}
- ...
- ...

### 📓 기록 활동
- 새로 작성한 노트: [[...]]
- 수정한 노트: [[...]]

### 🧾 커리어 자산
- ...
- ...

### 💭 회고
...

### 5단계: 파일 저장

대상 파일: `{DAILY_NOTES_DIR}/{DATE}.md`

**3가지 케이스:**

1. **파일이 없는 경우**: 새로 생성하고 일기 내용을 작성
2. **파일이 있고 `## 📝 Daily Diary` 섹션이 없는 경우**: 기존 내용 끝에 `---` 구분선과 함께 일기를 추가
3. **파일이 있고 `## 📝 Daily Diary` 섹션이 있는 경우**: 해당 섹션만 교체 (멱등성 보장)
   - `## 📝 Daily Diary`부터 다음 `---` 또는 파일 끝까지를 교체 범위로 잡는다

**중요:** Write 도구로 전체 파일을 덮어쓰지 말 것. 기존 Daily Notes 내용을 보존해야 한다.
- 케이스 2: 기존 내용을 Read로 읽은 후, 뒤에 추가하는 형태로 Write
- 케이스 3: Read로 읽고, 해당 섹션만 Edit으로 교체
