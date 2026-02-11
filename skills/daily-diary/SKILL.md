---
name: daily-diary
description: >
  매일 하루가 끝날 때 Claude Code 채팅 히스토리와 Obsidian 볼트 변경사항을 기반으로
  자동 일기를 생성한다. "일기 써줘", "daily diary", "오늘 일기", "어제 일기" 등의 요청 시 사용.
---

# Daily Diary

Claude Code 활동 로그와 Obsidian 볼트 변경사항을 종합하여 Daily Notes에 일기를 자동 생성한다.

## 설정

```
VAULT_PATH=/Users/choegihwan/Documents/Projects/Obsidian-frontend-journey
DAILY_NOTES_DIR={VAULT_PATH}/Daily Notes
HISTORY_FILE=~/.claude/history.jsonl
SCRIPT_PATH=.claude/skills/daily-diary/scripts/extract_history.py
```

## 워크플로우

### 1단계: 날짜 결정

- 기본값: 오늘 날짜 (`YYYY-MM-DD`)
- 사용자가 "어제 일기", "2026-02-10 일기" 등 지정 시 해당 날짜 사용
- `DATE` 변수에 `YYYY-MM-DD` 형식으로 저장

### 2단계: Claude Code 활동 추출

Python 스크립트를 실행하여 해당 날짜의 Claude Code 활동을 추출한다.

```bash
python3 .claude/skills/daily-diary/scripts/extract_history.py --date {DATE}
```

이 스크립트는 다음을 수행한다:
- `~/.claude/history.jsonl`에서 해당 날짜의 사용자 요청을 필터링
- 프로젝트별로 그룹화하여 시간순 정렬
- 각 프로젝트 디렉토리에서 해당 날짜의 `git log`를 수집
- 결과를 구조화된 텍스트로 stdout에 출력

스크립트 출력이 비어있거나 "활동 없음"이면 → "오늘은 Claude Code 작업이 없었습니다"로 처리.

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

2-3단계 출력을 읽고 아래 템플릿에 맞춰 자연스러운 한국어 일기를 합성한다.

**작성 규칙:**
- 한국어로 작성
- 간결하게 (프로젝트당 핵심 활동 2-4개 bullet point)
- 의도(사용자 요청)와 결과(git 커밋)를 통합하여 서술
- Obsidian wiki link 형식 사용: `[[노트명]]`
- 불필요한 장식이나 과도한 이모지 금지 (섹션 헤더의 이모지는 템플릿대로)

**출력 템플릿:**

```markdown
---

## 📝 Daily Diary

### 🖥️ 개발 활동

#### {프로젝트명}
- 주요 작업 요약 (의도 + 결과 통합)
- 커밋 내용 기반 완료된 작업

### 📓 기록 활동
- 새로 작성한 노트: [[노트명]]
- 수정한 노트: [[노트명]]

### 💭 회고
하루를 돌아보며 1-2문장.
```

**엣지 케이스:**
- Claude Code 활동만 있고 Obsidian 변경 없음 → `### 📓 기록 활동` 섹션 생략
- Obsidian 변경만 있고 Claude Code 활동 없음 → `### 🖥️ 개발 활동` 대신 "오늘은 Claude Code 작업이 없었습니다" 한 줄
- 둘 다 없음 → 최소한의 일기: "조용한 하루였다. 특별한 개발이나 기록 활동이 없었다."

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
