---
name: fresh-loop
description: >
  매 반복마다 새 세션에서 실행되는 Ralph 스타일 반복 개발 루프.
  동일 프롬프트를 반복 전달하되 각 세션이 독립적이며, 파일 시스템과
  PROGRESS.md를 통해 상태를 이어간다. 스킬은 루프 환경과 실행
  스크립트만 생성하고, 실제 루프는 외부 터미널에서 사용자가 실행한다.
  "$fresh-loop" 또는 "/fresh-loop" 명시 호출 시에만 실행한다.
  자동 트리거하지 않는다.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# Fresh Loop

매 반복을 새 Claude 세션에서 실행하는 Ralph 스타일 반복 루프.
**스킬은 루프 환경과 `run.sh`만 생성**하고, 실제 루프 실행은 **사용자가 외부 터미널에서** 수행한다.

## Hard Rules

1. 이 스킬은 명시적 호출(`/fresh-loop`, `$fresh-loop`)에서만 실행한다.
2. 스킬은 루프를 직접 실행하지 않는다. `.fresh-loop/run.sh`만 생성하고 사용자에게 외부 터미널 실행을 안내한다.
3. Claude Code 세션 내부에서 `claude -p`를 중첩 spawn하면 `~/.claude/session-env` 권한 충돌로 공회전하므로 반드시 외부 터미널에서 실행한다.
4. 루프 상태 파일은 `.fresh-loop/` 디렉토리에 저장한다.
5. 완료 신호는 `.fresh-loop/done` 마커 파일로 판단한다.
6. 변경이 있을 때만 git 커밋한다. 빈 커밋은 생성하지 않는다.
7. 연속 무변경 횟수가 임계치를 넘으면 자동 중단한다.

## Workflow

### Step 1: 파라미터 수집

사용자로부터 다음 정보를 확인한다:

| 파라미터 | 필수 | 기본값 | 설명 |
|---------|------|--------|------|
| task | O | — | 수행할 작업 설명 |
| max | X | 없음 (무제한) | 최대 반복 횟수. 명시하지 않으면 완료까지 무제한 반복 |
| scope | X | 자동 감지 | 작업 대상 파일/디렉토리 범위 |

예시 호출:
```
/fresh-loop "캐시 레이어를 Redis에서 인메모리로 전환"
/fresh-loop "인증 모듈 리팩토링" --max 10
```

### Step 2: 루프 환경 준비

1. `.fresh-loop/` 디렉토리를 생성한다.
2. `.gitignore`에 `.fresh-loop/`이 포함되어 있는지 확인하고, 없으면 추가한다.
3. PROMPT.md, PROGRESS.md, run.sh를 생성한다.

#### PROMPT.md 템플릿

```markdown
# Task
{사용자가 지정한 작업 설명}

# Scope
{작업 대상 범위}

# Instructions
1. .fresh-loop/PROGRESS.md를 읽어서 현재 진행 상태를 파악하라.
2. "## Current" 섹션에 있는 다음 단계를 수행하라.
3. 한 번에 하나의 단계만 수행하라.
4. 작업 후 .fresh-loop/PROGRESS.md를 업데이트하라:
   - 완료한 항목을 "## Completed"로 이동
   - 다음 항목을 "## Current"로 이동
5. 모든 목표가 완료되면 `touch .fresh-loop/done`을 실행하라.

# Rules
- 한 번에 하나의 단계만 수행한다.
- 변경 전 관련 코드를 반드시 읽는다.
- 기존 코드 스타일과 패턴을 따른다.
- 불필요한 변경을 하지 않는다.
```

#### PROGRESS.md 초기 템플릿

```markdown
# Progress

## Completed
(없음)

## Current
- [ ] 코드베이스 분석 및 작업 계획 수립

## Remaining
(Claude가 첫 반복에서 계획을 세워 채운다)

## Notes
- 작업 시작: {현재 시각}
```

#### run.sh 템플릿

```bash
#!/usr/bin/env bash
set -u

# 세션 중첩 방지: Claude Code 내부에서 실행되면 즉시 중단
if [ -n "${CLAUDE_CODE_SESSION:-}" ] || [ -n "${CLAUDECODE:-}" ]; then
  echo "[fresh-loop] ERROR: Claude Code 세션 내부에서는 실행할 수 없습니다."
  echo "외부 터미널(일반 셸)에서 직접 실행해주세요."
  exit 1
fi

LOOP_DIR=".fresh-loop"
MAX_ITER={max_or_0}       # 0 = 무제한
MAX_NO_CHANGE=3            # 연속 무변경 임계치

i=0
no_change=0

echo $$ > "$LOOP_DIR/pid"
trap 'rm -f "$LOOP_DIR/pid"' EXIT

while true; do
  i=$((i + 1))
  echo "$i" > "$LOOP_DIR/iteration"

  if [ "$MAX_ITER" -gt 0 ] && [ "$i" -gt "$MAX_ITER" ]; then
    echo "[fresh-loop] Reached max iterations ($MAX_ITER)"
    break
  fi

  echo ""
  echo "============================================"
  if [ "$MAX_ITER" -gt 0 ]; then
    echo "  Fresh Loop — Iteration $i / $MAX_ITER"
  else
    echo "  Fresh Loop — Iteration $i"
  fi
  echo "============================================"
  echo ""

  # 서브 Claude 세션 실행 + exit code 체크
  if ! claude -p --dangerously-skip-permissions < "$LOOP_DIR/PROMPT.md"; then
    ec=$?
    echo "[fresh-loop] claude -p failed (exit code $ec) — 중단"
    break
  fi

  # 완료 마커 확인
  if [ -f "$LOOP_DIR/done" ]; then
    echo ""
    echo "[fresh-loop] Completed at iteration $i"
    break
  fi

  # 실제 변경이 있을 때만 커밋, 없으면 정체 카운터 증가
  git add -A
  if git diff --cached --quiet; then
    no_change=$((no_change + 1))
    echo "[fresh-loop] No changes at iteration $i (stall count: $no_change/$MAX_NO_CHANGE)"
    if [ "$no_change" -ge "$MAX_NO_CHANGE" ]; then
      echo "[fresh-loop] $MAX_NO_CHANGE회 연속 무변경 — 서브세션 고장 의심, 중단"
      break
    fi
  else
    no_change=0
    git commit -m "fresh-loop: iteration $i" 2>/dev/null || true
  fi
done

# 최종 상태 출력
echo ""
if [ -f "$LOOP_DIR/done" ]; then
  echo "[fresh-loop] Task completed successfully."
else
  echo "[fresh-loop] Loop ended without completion marker. Review PROGRESS.md."
fi
```

### Step 3: 사용자에게 실행 안내

스킬은 직접 루프를 실행하지 않는다. 대신 사용자에게 다음 메시지를 출력한다:

```
fresh-loop 환경이 준비되었습니다.

외부 터미널(일반 셸)에서 다음 명령을 실행해주세요:

  cd {프로젝트 루트 절대경로}
  bash .fresh-loop/run.sh

실행 중 상태 확인:
  - 현재 반복: cat .fresh-loop/iteration
  - 진행 상태: cat .fresh-loop/PROGRESS.md
  - 프로세스: ps -p $(cat .fresh-loop/pid)

중단:
  - Ctrl+C (루프가 실행 중인 터미널에서)
  - kill $(cat .fresh-loop/pid) (다른 터미널에서)

루프 종료 후 다시 /fresh-loop으로 저에게 결과 보고를 요청하세요.
```

### Step 4: 결과 보고 (루프 종료 후 사용자가 재호출 시)

사용자가 루프 종료 후 `/fresh-loop`을 다시 호출하면:

1. `.fresh-loop/` 디렉토리 존재 여부를 확인한다.
2. `.fresh-loop/PROGRESS.md`를 읽어 최종 상태를 확인한다.
3. `.fresh-loop/done` 파일 유무로 완료/미완료 판단한다.
4. `git log --oneline`으로 fresh-loop 커밋 목록을 보여준다.
5. 총 변경 사항을 요약한다.

### Step 5: 정리

사용자 확인 후:

1. `.fresh-loop/` 디렉토리를 삭제할지 묻는다.
2. 체크포인트 커밋들을 하나로 squash할지 묻는다.

## 중단 및 재개

- **중단**: 루프 터미널에서 `Ctrl+C`. PROGRESS.md 상태는 보존된다.
- **외부 중단**: 다른 터미널에서 `kill $(cat .fresh-loop/pid)`.
- **재개**: `.fresh-loop/`이 존재하는 상태에서 다시 `bash .fresh-loop/run.sh`를 실행하면 PROGRESS.md 상태에서 이어서 작업한다. 단, iteration 카운터는 0부터 다시 시작한다.
- **취소**: `rm -rf .fresh-loop/`로 완전 초기화.

## Important Notes

- **절대 Claude Code 세션 안에서 `bash .fresh-loop/run.sh`를 실행하지 말 것.** 세션 중첩으로 `~/.claude/session-env` 권한 충돌이 발생해 서브세션이 마비되고 공회전한다.
- `claude -p --dangerously-skip-permissions`로 실행하므로 모든 도구가 허용된다.
- 각 서브세션의 컨텍스트는 PROMPT.md + PROGRESS.md + 파일 시스템이 전부다.
- PROMPT.md는 반드시 자기 완결적이어야 한다 — 대화 히스토리에 의존하지 않는다.
- 빈 커밋은 생성하지 않으므로 git log가 깨끗하다.
- 연속 3회 무변경 시 자동 중단으로 공회전을 방지한다.
