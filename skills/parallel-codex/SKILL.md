---
name: parallel-codex
description: >
  DAG 기반 그룹 순차 + 그룹 내 병렬 파이프라인 디스패처.
  작업 리스트를 의존성 분석하여 위상 정렬된 그룹으로 배치하고,
  각 그룹 내 작업을 git worktree + Codex로 병렬 실행한다.
  그룹 간 전이는 Codex가 stage 브랜치로 통합 + 검증 + 상태 요약.
  완료 후 draft MR 일괄 생성 + 머지 순서 가이드 제공.
  "$parallel-codex" 또는 "병렬 작업" 요청 시 호출.
---

# Parallel Codex

Claude: 의존 분석 + 그룹 배치 + 프롬프트 설계 + PIPELINE.md 관리.
Codex: 구현 + 검증 + 머지 + MR 생성. Claude는 머지 리포트만 읽어 컨텍스트를 fresh하게 유지.

## Hard Rules

1. Claude는 코드를 직접 작성하지 않는다. 모든 구현/머지/MR 생성은 Codex를 통해.
2. 승인 게이트 없이 전체 파이프라인을 자동 실행한다.
3. 각 작업은 반드시 **별도의 git worktree**에서 실행한다.
4. **같은 파일을 수정하는 작업은 반드시 다른 그룹**에 배치한다 (같은 그룹 = 병렬이므로 충돌).
5. Codex 실행 실패 시 해당 작업만 실패로 표시. 다른 작업에 영향 없음.
6. Codex 검증 통과 = 완료. 신뢰한다.
7. Claude는 그룹 간 전이 시 **머지 리포트만 읽는다** (컨텍스트 최소화).
8. 모든 MR은 **draft**로 생성한다.
9. `PIPELINE.md`가 전체 파이프라인의 **single source of truth**이다.

## Codex Plugin Skills (세션당 1회 로드)

시작 시 Skill 도구로 아래 플러그인 스킬을 로드한다:

1. `codex:gpt-5-4-prompting` — 프롬프트 구조, XML 블록 규칙
2. `codex:codex-cli-runtime` — Codex 호출 명령어, 플래그, 실행 규칙

로드된 스킬이 제공하는 호출 계약과 프롬프트 규칙을 따른다.

## Workflow

### Step 0: Bootstrap

Skill 도구로 Codex plugin skills를 로드한다 (세션당 1회).

### Step 1: 작업 수집

어떤 형태의 입력이든 받아서 구조화된 작업 리스트로 변환한다.
입력: 자연어, 이슈 번호 목록, 구조화된 리스트 등 무관.

각 작업으로 파싱:
- **ID**: 짧은 식별자 (예: `a1`, `b2`)
- **이름**: 작업명
- **설명**: 무엇을 해야 하는지
- **관련 파일**: 주로 수정할 파일/디렉토리 (코드베이스 탐색으로 식별)

### Step 2: 의존성 분석 + DAG 구성

코드베이스를 탐색하여 작업 간 의존성을 분석한다:

**의존성 판단 기준** (Claude가 종합 판단):
- **파일 겹침**: 같은 파일을 수정하는 작업 → 반드시 다른 그룹 (순차)
- **모듈 의존성**: import/export 관계. A의 출력물을 B가 사용 → B는 A 이후 그룹
- **논리적 의존성**: A의 결과가 존재해야 B가 의미 있는 경우

결과물: 방향성 비순환 그래프 (DAG).

### Step 3: 위상 정렬 + 그룹 배치

DAG를 위상 정렬하여 병렬 배치 그룹으로 나눈다.
같은 레벨(깊이)의 노드가 하나의 그룹을 형성한다.

```
Group A (depth 0): 의존성 없는 작업들 → 병렬 실행
Group B (depth 1): Group A에 의존하는 작업들 → 병렬 실행
Group C (depth 2): Group B에 의존하는 작업들 → 병렬 실행
...
```

### Step 4: PIPELINE.md 생성

`PIPELINE.md`를 프로젝트 루트에 생성한다.
포맷은 `${SKILL_DIR}/references/pipeline-format.md` 참조.

내용:
- 전체 작업 목록 (ID, 이름, 설명, 관련 파일)
- 의존성 그래프
- 그룹 배치 (각 그룹의 작업, 베이스 브랜치, stage 브랜치, 상태)
- MR 계획 (소스, 타겟, 타입, 상태)
- 머지 순서

이 파일이 전체 파이프라인의 source of truth.

### Step 5: 그룹 루프 (자동, 중단 없음)

각 그룹에 대해 아래를 반복한다:

#### 5a. 워크트리 생성

현재 그룹의 베이스 브랜치에서 각 작업의 워크트리를 생성한다:

- **Group A**: `main` (또는 현재 브랜치)에서 분기
- **Group B**: `stage/group-a`에서 분기
- **Group N**: `stage/group-<N-1>`에서 분기

```bash
git worktree add .worktrees/<group>/<task-name> -b parallel/<task-name> <base-branch>
```

#### 5b. 프롬프트 설계

각 작업의 Codex 프롬프트를 `codex:gpt-5-4-prompting`의 XML 블록 규칙과
`${SKILL_DIR}/references/worker-prompt-template.md`의 변수 구조를 결합하여 작성.

이전 그룹의 머지 리포트가 있으면 `REFERENCE_CONTEXT`에 압축하여 포함한다.

#### 5c. 병렬 디스패치

Bash 도구의 `run_in_background=true`를 사용하여 그룹 내 모든 작업을 동시 디스패치.
`codex:codex-cli-runtime`의 호출 계약에 따라 실행.
각 워크트리를 `--cwd` 플래그로 지정하고 `--write`로 쓰기 모드 실행.

#### 5d. 결과 대기

모든 작업의 완료 알림을 기다린다.

#### 5e. 머지 디스패치

그룹 내 모든 작업 완료 후, **머지 전담 Codex**를 디스패치한다.
프롬프트는 `${SKILL_DIR}/references/merger-prompt-template.md` 참조.
리포트 출력: `.worktrees/MERGE_REPORT_<GROUP>.md`

#### 5f. 머지 리포트 읽기 + PIPELINE.md 업데이트

Claude는 머지 리포트만 읽는다 (수십 줄).
PIPELINE.md의 해당 그룹 상태를 업데이트한다.
다음 그룹의 프롬프트 설계에 머지 리포트 내용을 활용한다.

### Step 6: MR 일괄 생성

전체 그룹 루프 완료 후, **MR 생성 전담 Codex**를 디스패치한다.
프롬프트는 `${SKILL_DIR}/references/mr-creator-prompt-template.md` 참조.
PIPELINE.md의 MR Plan을 입력으로 전달한다.

### Step 7: 최종 보고

PIPELINE.md에서 최종 상태를 읽어 사용자에게 제시한다:
- 그룹별 실행 결과 (성공/실패)
- MR 링크 목록
- **머지 순서 가이드** — PIPELINE.md의 Merge Order를 기반으로 리뷰 + 병합 순서 안내
- 워크트리 정리 명령: `git worktree prune`

## Error Handling

- **Codex 타임아웃**: 해당 작업만 타임아웃으로 표시. 나머지 작업 영향 없음. PIPELINE.md에 기록.
- **워크트리 생성 실패**: 더티 상태 확인 후 PIPELINE.md에 기록하고 해당 작업 스킵.
- **Codex 플러그인 미설치**: `codex:setup` 안내 후 중단.
- **부분 실패**: 성공한 작업만 머지 진행. 실패 작업은 PIPELINE.md에 기록.
- **머지 Codex 실패**: PIPELINE.md에 기록하고 사용자에게 수동 개입 요청. 후속 그룹은 중단.

## Session Resumption

`PIPELINE.md` 존재 여부를 확인하여 재개:

1. `PIPELINE.md`가 있으면 읽는다
2. Groups 테이블에서 마지막으로 완료된 그룹을 확인
3. `running` 또는 `pending` 상태의 그룹부터 재개
4. `.worktrees/` 디렉토리와 `git worktree list`로 실제 상태 교차 검증

## References

- `${SKILL_DIR}/references/worker-prompt-template.md` — 워커 Codex 프롬프트 구조 + 변수
- `${SKILL_DIR}/references/merger-prompt-template.md` — 머지 전담 Codex 프롬프트 구조
- `${SKILL_DIR}/references/mr-creator-prompt-template.md` — MR 생성 Codex 프롬프트 구조
- `${SKILL_DIR}/references/pipeline-format.md` — PIPELINE.md 파일 포맷 명세
