---
name: parallel-codex
description: >
  Codex 기반 병렬 작업 디스패처. 독립적인 작업들을 git worktree로 격리하고
  각 worktree에서 Codex를 병렬 실행한다. 의존 그래프를 분석하여 병렬 가능한
  작업을 식별한다. "$parallel-codex" 또는 "병렬 작업" 요청 시 호출.
allowed-tools: Bash, Read, Grep, Glob, Write, Agent
---

# Parallel Codex

독립적인 작업들을 git worktree로 격리하고 Codex를 병렬 실행하는 디스패처.

Claude는 **의존 분석 + 워크트리 생성 + 프롬프트 설계 + 상태 모니터링**만 담당.
Codex가 각 워크트리에서 **구현 + 리뷰**를 독립적으로 수행.
작업 완료 후 머지/통합은 사용자가 직접 처리.

## Hard Rules

1. Claude는 코드를 직접 작성하지 않는다. 모든 구현은 Codex를 통해.
2. 병렬 실행 전 반드시 **의존 그래프**를 사용자에게 보여주고 승인받는다.
3. 각 병렬 작업은 반드시 **별도의 git worktree**에서 실행한다.
4. 워크트리 간 파일 충돌이 예상되면 병렬 실행하지 않고 경고한다.
5. Codex 실행 실패 시 해당 작업만 실패로 표시. 다른 작업에 영향 없음.
6. 모든 작업 완료 후 결과 요약을 제시하고 멈춘다. 자동 머지하지 않는다.

## Workflow

### Step 1: 작업 수집

사용자로부터 작업 목록을 받는다. 각 작업에는:
- **이름**: 짧은 식별자
- **설명**: 무엇을 해야 하는지
- **관련 파일**: 주로 수정할 파일/디렉토리

작업은 사용자가 직접 나열하거나, BRIEF.md의 Phases에서 가져올 수 있다.

### Step 2: 의존 분석

관련 파일을 기반으로 의존 그래프를 분석한다:
- 같은 파일을 수정하는 작업은 **의존 관계** (직렬)
- 수정 파일이 겹치지 않는 작업은 **독립** (병렬 가능)

사용자에게 의존 그래프를 제시:

```
의존 그래프:
  #1 (옵션 정규화) ─┐
                     ├──→ #3 (query 상태 통합) ──→ #4 (toolbar controller)
  #2 (컬럼 컴파일) ─┘

병렬 가능: #1 + #2
```

사용자 승인을 받은 뒤 진행한다.

### Step 3: 워크트리 생성

병렬 가능한 각 작업에 대해 git worktree를 생성한다:

```bash
git worktree add .worktrees/<task-name> -b parallel/<task-name>
```

워크트리 경로: `.worktrees/<task-name>` (프로젝트 루트 기준)

### Step 4: 프롬프트 설계 + 승인

각 작업의 Codex 프롬프트를 작성하여 사용자에게 일괄 제시한다:

```
--- 병렬 작업 프롬프트 ---

[작업 1: 옵션 정규화]
  Worktree: .worktrees/option-normalize
  Prompt:
    목적: ...
    Goal: ...
    완료 기준: ...
    리뷰 포인트: ...

[작업 2: 컬럼 컴파일]
  Worktree: .worktrees/column-compile
  Prompt:
    목적: ...
    Goal: ...
    완료 기준: ...
    리뷰 포인트: ...

[1] 전체 승인하고 실행
[2] 특정 작업 프롬프트 수정
[3] 작업 구성 변경
```

프롬프트는 `skills/parallel-codex/references/worker-prompt-template.md` 참조.

### Step 5: 병렬 실행

승인 후 Bash 도구의 `run_in_background=true`를 사용하여 모든 작업을 동시에
디스패치한다. 각 Bash 호출은 독립적으로 백그라운드 실행되며, 완료 시 Claude에
자동 알림이 온다.

```
# 하나의 메시지에서 여러 Bash를 동시에 호출 (각각 run_in_background=true):

Bash#1: codex exec --full-auto --cd .worktrees/task-a "<prompt A>"
Bash#2: codex exec --full-auto --cd .worktrees/task-b "<prompt B>"
```

각 Codex 인스턴스는 자신의 워크트리에서 독립 실행된다.
완료 알림이 오면 해당 작업의 결과를 수집한다.

### Step 6: 결과 수집 + 보고

각 작업 완료 알림이 오면 결과를 수집한다:

```bash
git -C .worktrees/<task-name> diff main --stat
```

최종 결과를 요약하여 제시:

```
--- 병렬 실행 결과 ---

[작업 1: 옵션 정규화] ✓ 성공
  Branch: parallel/option-normalize
  Worktree: .worktrees/option-normalize
  변경 파일: src/options/normalize.ts, src/options/types.ts
  Codex 요약: ...

[작업 2: 컬럼 컴파일] ✓ 성공
  Branch: parallel/column-compile
  Worktree: .worktrees/column-compile
  변경 파일: src/columns/compiler.ts
  Codex 요약: ...

다음 단계 (사용자 직접 수행):
  1. 각 브랜치의 변경사항 확인: git diff main...parallel/<task-name>
  2. 머지: git merge parallel/<task-name>
  3. 워크트리 정리: git worktree remove .worktrees/<task-name>
```

**여기서 멈춘다.** 머지와 통합은 사용자가 직접 처리한다.

## Worker Prompt Structure

각 Codex 워커에게 전달되는 프롬프트 구조.
상세 템플릿은 `${SKILL_DIR}/references/worker-prompt-template.md` 참조.

```xml
<task>
## 목적
${TASK_PURPOSE}

## 작업 범위
${TASK_SCOPE}

## Goal
${TASK_GOAL}

## 완료 기준
${DONE_CRITERIA}
</task>

<structured_output_contract>
작업 완료 후:
1. 변경된 파일 목록
2. 수행한 작업 요약
3. 셀프 리뷰 결과 (정확성, 엣지 케이스, 부작용)
</structured_output_contract>

<verification_loop>
완료 전 검증:
- ${VERIFICATION_COMMANDS}
</verification_loop>

<action_safety>
- 이 작업 범위 내 변경만 수행
- 워크트리 밖 경로 접근 금지
</action_safety>
```

## Cleanup

사용자에게 워크트리 정리 명령을 안내하되 자동 실행하지 않는다:

```bash
# 개별 정리
git worktree remove .worktrees/<task-name>
git branch -d parallel/<task-name>

# 전체 정리
git worktree list
git worktree prune
```

## Error Handling

- **Codex 타임아웃**: 해당 작업만 타임아웃으로 표시. 나머지 작업 진행에 영향 없음.
- **워크트리 생성 실패**: 더티 상태 확인 후 사용자에게 보고.
- **codex CLI 미설치**: `npm i -g @openai/codex` 안내.
- **부분 실패**: 성공한 작업과 실패한 작업을 분리하여 보고.

## Session Resumption

`.worktrees/` 디렉토리 존재 여부와 각 워크트리의 상태를 확인하여 재개:

```bash
git worktree list
```

활성 워크트리가 있으면 각 Codex 작업 상태를 확인하고 보고한다.
