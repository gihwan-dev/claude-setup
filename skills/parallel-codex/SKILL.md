---
name: parallel-codex
description: >
  DAG 기반 그룹 순차 + 그룹 내 병렬 파이프라인 디스패처.
  작업 리스트를 의존성 분석하여 위상 정렬된 그룹으로 배치하고,
  각 그룹 내 작업을 git worktree + Codex로 병렬 실행한다.
  그룹 간 전이는 임시 브랜치(temp/verify-*)로 호환성 검증 + 상태 요약.
  모든 그룹 실행·검증 완료 후 마지막 verify 브랜치에서 단일 MR 생성.
  "$parallel-codex" 명시 호출 시 실행한다.
  사용자가 "병렬 작업", "여러 작업 동시에", "기능 여러 개 동시 개발",
  "동시에 돌려줘" 등을 언급하면 `$parallel-codex` 사용을 제안하라.
  단일 task나 순차 1개 작업에는 사용하지 않는다 — 일반 Codex 호출이 적합하다.
---

# Parallel Codex

Claude: 의존 분석 + 그룹 배치 + 프롬프트 설계 + PIPELINE.md 관리.
Codex: 구현 + 검증. Claude는 검증 리포트만 읽어 컨텍스트를 fresh하게 유지.
모든 그룹 완료 후 마지막 verify 브랜치에서 단일 MR을 생성한다.

## Hard Rules

1. Claude는 코드를 직접 작성하지 않는다. 모든 구현/검증은 Codex를 통해. (Claude가 코드를 읽으면 컨텍스트가 소모되고 Codex의 독립 검증이 무력화됨)
2. 실행 Phase는 승인 게이트 없이 자동 실행한다. MR은 모든 그룹 완료 후 단일 생성.
3. 각 작업은 **별도의 git worktree**에서 실행한다. (병렬 실행 중 파일 시스템 충돌을 원천 차단)
4. **같은 파일을 수정하는 작업은 다른 그룹**에 배치한다. (같은 그룹 = 병렬이므로 머지 충돌 불가피)
5. Codex 실행 실패 시 해당 작업만 실패로 표시. 다른 작업에 영향 없음.
6. Codex 검증 통과 = 완료. 신뢰한다. (Claude가 재검증하면 컨텍스트 오염 + 중복 비용)
7. Claude는 그룹 간 전이 시 **검증 리포트만 읽는다**. (전체 diff를 읽으면 컨텍스트 폭발)
8. 모든 MR은 **draft**로 생성한다. (사용자가 리뷰 후 직접 머지해야 하므로)
9. `PIPELINE.md`가 전체 파이프라인의 **single source of truth**이다.
10. **단일 MR**: 모든 그룹 실행·검증 완료 후, 마지막 그룹의 `temp/verify-*` 브랜치에서 `main`으로 **하나의 MR**만 생성한다. (마지막 verify 브랜치에 전체 변경이 통합되어 있으므로 별도 머지 불필요)

## Codex Plugin Skills (세션당 1회 로드)

시작 시 Skill 도구로 아래 플러그인 스킬을 로드한다:

1. `codex:gpt-5-4-prompting` — Claude가 Codex 프롬프트를 **조합**할 때 참고하는 가이드. 실제 XML 블록 구조(`<task>`, `<verification_loop>` 등)는 로컬 템플릿에 이미 정의되어 있다.
2. `codex:codex-cli-runtime` — Codex CLI 호출 명령어, 플래그, 실행 규칙

이 스킬들이 로드 실패하면: 로컬 템플릿의 XML 구조가 자급 가능하므로 실행은 계속한다. 단, Codex CLI 호출 형식(`codex:codex-cli-runtime`)이 없으면 디스패치 자체가 불가능하므로 `codex:setup` 안내 후 중단한다.

## Workflow

진입 분기:
- `PIPELINE.md`가 이미 존재하면 → **Session Resumption** 섹션에서 상태를 판단한 뒤 적절한 Step으로 진입한다.
- 그 외 → Step 0부터 시작한다.

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
- 그룹 배치 (각 그룹의 작업, 베이스 브랜치, 검증 브랜치, 상태)
- MR 계획 (마지막 verify 브랜치 → main, 상태)

이 파일이 전체 파이프라인의 source of truth.

### Step 5: 그룹 실행 루프 (자동, 중단 없음)

각 그룹에 대해 아래를 반복한다:

#### 5a. 워크트리 생성

현재 그룹의 베이스 브랜치에서 각 작업의 워크트리를 생성한다:

- **Group A**: `main` (또는 현재 브랜치)에서 분기
- **Group B**: `temp/verify-a`에서 분기 (= 이전 그룹의 Verify Branch)
- **Group C**: `temp/verify-b`에서 분기 (항상 이전 그룹의 Verify Branch)

브랜치명 형식: `parallel/<task-id>-<task-name-kebab>` (예: `parallel/a1-db-schema`)

```bash
git worktree add .worktrees/<group>/<task-id>-<task-name> -b parallel/<task-id>-<task-name> <base-branch>
```

#### 5b. 프롬프트 설계

각 작업의 Codex 프롬프트를 `codex:gpt-5-4-prompting`의 XML 블록 규칙과
`${SKILL_DIR}/references/worker-prompt-template.md`의 변수 구조를 결합하여 작성.

이전 그룹의 검증 리포트가 있으면 `REFERENCE_CONTEXT`에 압축하여 포함한다.

#### 5c. 병렬 디스패치

Bash 도구의 `run_in_background=true`를 사용하여 그룹 내 모든 작업을 동시 디스패치.
`codex:codex-cli-runtime`의 호출 계약에 따라 실행.
각 워크트리를 `--cwd` 플래그로 지정하고 `--write`로 쓰기 모드 실행.

#### 5d. 결과 대기

모든 작업의 완료 알림을 기다린다.

#### 5e. 검증 디스패치

그룹 내 모든 작업 완료 후, **검증 전담 Codex**를 프로젝트 루트에서 디스패치한다 (`--cwd` 없이 기본 루트).
프롬프트는 `${SKILL_DIR}/references/verifier-prompt-template.md` 참조.
리포트 출력: `.worktrees/VERIFY_REPORT_<GROUP>.md`

검증 Codex의 역할:
1. `temp/verify-<group>` 임시 브랜치를 생성하고 모든 task 브랜치를 머지
2. 통합 상태에서 lint/typecheck/test를 실행하여 호환성 검증
3. 실패 시 **개별 task 브랜치에서** 수정 (temp 브랜치가 아님)
4. 검증 리포트 작성

**중요**: `temp/verify-*` 브랜치는 다음 그룹의 branching point로 사용되며, 마지막 그룹의 verify 브랜치가 단일 MR의 소스 브랜치가 된다.

#### 5f. 검증 리포트 읽기 + PIPELINE.md 업데이트

Claude는 검증 리포트만 읽는다 (수십 줄).
PIPELINE.md의 해당 그룹 상태를 `verified`로 업데이트한다.
다음 그룹의 프롬프트 설계에 검증 리포트 내용을 활용한다.

#### 5g. Browser QA (conditional)

모든 그룹의 검증이 완료된 후 **1회만** 실행한다 (중간 그룹에서는 실행하지 않음).

1. `git diff main...<last-verify-branch> --name-only`로 전체 변경 파일 확인
2. UI 패턴 매칭: `\.(tsx|jsx|vue|svelte|html|css|scss|sass|less|styled)\b` (create-mr과 동일)
3. UI 파일이 없으면 → 스킵
4. UI 파일이 있으면:
   - 마지막 verify 브랜치를 checkout
   - `package.json` scripts에서 dev server 명령어 확인
   - `skills/_shared/references/browser-qa-prompt-template.md`의 변수를 치환하여 프롬프트 작성
   - `Agent(subagent_type="general-purpose")`로 서브에이전트 소환
     - general-purpose 타입이어야 Claude in Chrome MCP 도구(`mcp__claude-in-chrome__*`) 접근 가능
   - 서브에이전트가 `.worktrees/QA_REPORT.md`에 QA 리포트 작성
5. QA 리포트를 읽고 Step 7 최종 보고에 요약 포함
6. PIPELINE.md MR Plan의 QA 컬럼 업데이트 (`pass` 또는 `issues_found`)

QA 결과는 **정보 제공용**이다. 이슈가 발견되어도 MR 생성을 자동으로 차단하지 않는다.
이슈 발견 시 MR body에 QA 결과 요약을 포함한다.

### Step 6: 단일 MR 생성

모든 그룹의 실행·검증이 완료되면, **마지막 그룹의 `temp/verify-*` 브랜치**에서 `main`으로 **하나의 draft MR**을 생성한다.

마지막 verify 브랜치에는 모든 task의 변경이 순차적으로 머지·검증된 상태이므로 별도 통합 작업이 불필요하다.

Claude가 `git remote get-url origin`으로 플랫폼(GitLab/GitHub)을 감지하여 `PLATFORM` 변수를 채운 뒤,
`${SKILL_DIR}/references/mr-creator-prompt-template.md`의 프롬프트를 MR 생성 Codex에 전달한다.

### Step 7: 최종 보고

PIPELINE.md에서 최종 상태를 읽어 사용자에게 제시한다:

- 그룹별 실행 결과 (성공/실패)
- **단일 MR 링크**
- 포함된 전체 task 목록 요약
- 워크트리 정리 안내: MR 머지 완료 후 `git worktree prune` + `git branch -d temp/verify-*`

## Error Handling

- **Codex 타임아웃**: 해당 작업만 타임아웃으로 표시. 나머지 작업 영향 없음. PIPELINE.md에 기록.
- **워크트리 생성 실패**: 더티 상태 확인 후 PIPELINE.md에 기록하고 해당 작업 스킵.
- **Codex 플러그인 미설치**: `codex:setup` 안내 후 중단.
- **부분 실패**: 성공한 작업만 검증 진행. 실패 작업은 PIPELINE.md에 기록.
- **검증 Codex 실패**: PIPELINE.md에 기록하고 사용자에게 수동 개입 요청. 후속 그룹은 중단.
- **검증 시 worktree 체크아웃 충돌**: 검증 Codex가 `git checkout <task-branch>`를 시도할 때 해당 브랜치가 이미 워크트리에 체크아웃되어 있으면 실패한다. 이 경우 워크트리 경로에서 직접 수정해야 한다 (`cd .worktrees/<group>/<task>` 후 수정+커밋).
- **Browser QA 실패**: dev server 미기동, Chrome 미연결 등으로 QA를 수행할 수 없으면
  경고만 표시하고 MR 생성을 계속 진행한다.

## Session Resumption

`PIPELINE.md` 존재 여부를 확인하여 재개:

1. `PIPELINE.md`가 있으면 읽는다
2. 파이프라인 상태에 따라 분기:
   - 실행 중인 그룹이 있으면 (`running`): 해당 그룹부터 실행 재개 → Step 5로 진입
   - 모든 그룹이 `verified`이고 MR 미생성: → Step 6 (단일 MR 생성)으로 진입
   - MR이 `created` 상태: 사용자에게 리뷰 + 머지 안내
   - MR이 `merged`: 파이프라인 완료 메시지 + 정리 안내
3. `.worktrees/` 디렉토리와 `git worktree list`로 실제 상태 교차 검증

## References

- `${SKILL_DIR}/references/worker-prompt-template.md` — 워커 Codex 프롬프트 구조 + 변수
- `${SKILL_DIR}/references/verifier-prompt-template.md` — 검증 전담 Codex 프롬프트 구조
- `${SKILL_DIR}/references/mr-creator-prompt-template.md` — MR 생성 Codex 프롬프트 구조
- `${SKILL_DIR}/references/pipeline-format.md` — PIPELINE.md 파일 포맷 명세
- `skills/_shared/references/browser-qa-prompt-template.md` — Browser QA 서브에이전트 프롬프트 (build과 공유)
- `${SKILL_DIR}/agents/openai.yaml` — Codex 에이전트 인터페이스 설정
