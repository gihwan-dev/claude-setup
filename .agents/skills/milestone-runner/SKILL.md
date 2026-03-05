---
name: milestone-runner
description: >
  Execute and resume milestone.md with artifact-based state and fresh-per-unit writers.
  milestone.md를 계획 단일 진실원(plan source of truth)으로 소비해 unit 단위 실행/재개를 수행하는 runner 스킬.
---

# Milestone Runner (Instruction-Only)

## 목적과 경계

- 이 스킬은 `planner`가 아니라 `runner`다.
- 계획의 단일 진실원은 항상 `milestone.md`다.
- 런타임 진실원(runtime truth)은 `repo/.codex/milestones/<run_id>/run-state.yaml` + `.codex/milestones/<run_id>/phases/<unit_id>/status.json`이다.
- `phase-manifest.yaml`은 비권위(snapshot)이며 mutable status를 저장하지 않는다.
- 설계는 instruction-only다. 외부 스크립트 실행, 새 profile 추가, config patch를 요구하지 않는다.
- 실행 셸은 항상 `bash`를 사용한다(`zsh` 문법 가정 금지).
- 사람-facing 개념은 `phase`, 실행 단위는 `unit`으로 고정한다.
- 경로명 `phases/`는 호환성 목적의 디렉터리 이름이며, 내부 상태 파일은 unit 단위로 관리한다.

## 실행 안정성 가드 (필수)

아래 가드는 모든 invocation에서 예외 없이 적용한다.

1. 셸/옵션 고정
- 멀티라인 로직은 반드시 `bash -lc '<script>'`로 실행한다.
- 스크립트 시작부에 `set -euo pipefail`를 선언한다.
- `zsh` 전용 문법(1-based 배열 인덱스 가정 포함) 사용을 금지한다.

2. 문자열 안전 규칙
- 문서에서 추출한 텍스트(특히 제목)는 raw shell literal로 직접 삽입하지 않는다.
- 백틱(`` ` ``)이 포함될 수 있는 값은 JSON(`jq -n --arg`) 또는 single-quoted heredoc(`<<'EOF'`)으로만 기록한다.
- command substitution이 의도된 경우를 제외하고 백틱 표기 자체를 금지한다(항상 `$(...)`만 허용).

3. 파일 생성/갱신 규칙
- 상태 파일은 `tmp` 파일에 먼저 쓰고 `mv`로 원자적 교체한다.
- 새 run 디렉터리 생성 시 실패를 대비해 `trap`으로 부분 생성물을 정리한다.
- `phase-manifest.yaml`에는 status 계열 필드를 절대 쓰지 않는다.

4. 실행 전 사전 점검
- `milestone_path` 존재, `bash`/`jq`/`shasum` 사용 가능 여부를 먼저 확인한다.
- 필수 의존성이 없으면 즉시 `blocked`로 종료하고 `reason`에 누락 항목을 기록한다.

5. 에러 처리
- write/revalidate 실패 시 해당 unit의 `status.json` + `handoff.md`를 같은 invocation 안에서 반드시 갱신한다.
- 에러 메시지는 "원인 1줄 + 재시도 조건 1줄"로 정규화해 기록한다.

## 명시 호출 인터페이스

```yaml
milestone_path: string | null       # 기본 "milestone.md" (선택)
run_id: string | null               # 선택 (미지정 시 새 run_id 생성)
target_phase: string | null         # 예: "phase-2" (선택)
target_unit: string | null          # 예: "phase-2/unit-1" (선택, target_phase보다 우선)
force_retry: boolean                # 기본 false
force_revalidate: boolean           # 기본 false
```

### 파라미터 규칙

- 우선순위: `target_unit` > `target_phase`.
- `force_retry` 역할: `failed|blocked` unit을 재시도 가능 상태로 되돌려 write 실행 대상으로 만든다.
- `force_revalidate` 역할: 구현 재실행 없이 검증 artifact만 갱신한다.
- `force_revalidate` 기본 대상: `done` unit, 또는 `warn|fail` verdict unit/final verification.
- dependency 미완료(`pending|ready|running`) unit에는 `force_revalidate`를 적용하지 않는다.
- `force_retry`와 `force_revalidate`는 목적이 다르며 상호 대체가 아니다.

## 상태 모델

### unit status enum

- `pending`
- `ready`
- `running`
- `done`
- `blocked`
- `failed`
- `skipped`

### phase verdict enum

- `not_run`
- `pass`
- `warn`
- `fail`

### phase verdict 계산 규칙

- `fail`: phase 내 unit 중 하나라도 `failed|blocked`.
- `warn`: `fail`은 아니지만 `skipped`가 존재.
- `pass`: 모든 실행 대상 unit이 `done`이고 `failed|blocked` 없음.
- `not_run`: 아직 어떤 unit도 `running|done|failed|blocked|skipped`에 도달하지 않음.

## Artifact 파일 책임 (Repo 모드 본문 규정)

| 파일 | 권위성 | 변경 가능 | 책임 |
|---|---|---|---|
| `milestone.md` | 계획 권위 | 사용자/러너 입력으로 변경 가능 | phase/unit 순서와 정의의 단일 진실원 |
| `.codex/milestones/<run_id>/run-state.yaml` | 런타임 권위 | mutable | run 단위 집계 상태, 현재 선택 대상, phase verdict, blocker reason |
| `.codex/milestones/<run_id>/phases/<unit_id>/status.json` | 런타임 권위 | mutable | unit 단위 상태/시도 횟수/최근 결과/오류 이유 |
| `.codex/milestones/<run_id>/decision-log.md` | 비권위 실행 기록 | mutable | 실행 의사결정, 분기 근거, 예외 처리 로그 |
| `.codex/milestones/<run_id>/final-verification.md` | 비권위 검증 기록 | mutable | 전체 unit 완료 후 분리 실행한 final verification 결과(PASS/WARN/FAIL) |
| `.codex/milestones/<run_id>/phases/<unit_id>/writer-brief.md` | 비권위 실행 입력 | mutable | unit write 직전 전달한 작업 지시/제약 요약 |
| `.codex/milestones/<run_id>/phases/<unit_id>/summary.md` | 비권위 실행 요약 | mutable | unit 구현 결과 요약 |
| `.codex/milestones/<run_id>/phases/<unit_id>/evidence.md` | 비권위 검증 증적 | mutable | unit 검증 로그/근거 링크/명령 결과 요약 |
| `.codex/milestones/<run_id>/phases/<unit_id>/handoff.md` | 비권위 인수인계 기록 | mutable | 다음 실행자에게 넘길 상태, 실패 원인, 재시도 조건 |
| `.codex/milestones/<run_id>/phase-manifest.yaml` | 비권위 스냅샷 | 생성/갱신 가능, status 필드 금지 | 당시 파싱 결과(phase/unit id, 제목, 순서, milestone_hash) 기록 |

- runtime truth 권위는 항상 `run-state.yaml + phases/<unit_id>/status.json`에만 있다.

### phase-manifest 제약

- mutable status 금지: `status`, `phase_verdict`, `attempt`, `running_at` 같은 필드를 두지 않는다.
- 선택적으로 문서 구조 스냅샷만 보관한다.

## 실행 알고리즘

1. 초기화
- 입력 파라미터 유효성 검사.
- `milestone_path` 파일 존재 확인. 없으면 즉시 종료(`blocked`).
- 글로벌 `AGENTS.md` 라우팅 정책을 재사용한다고 명시하고 별도 라우팅 프로필을 만들지 않는다.

2. manifest/state 준비
- `milestone.md`를 문서 순서대로 파싱해 phase/unit 목록을 만든다.
- 정규화 텍스트 기반 `milestone_hash`를 계산한다.
- `.codex/milestones/<run_id>/`가 없으면 생성한다.
- `phase-manifest.yaml` 스냅샷을 생성/갱신한다(상태값 없이).
- `run-state.yaml`과 `.codex/milestones/<run_id>/phases/<unit_id>/status.json`이 없으면 초기화한다.

3. reconcile
- 저장된 `milestone_hash`와 현재 해시가 다르면 reconcile 수행.
- 매핑 우선순위:
1. hidden metadata V2의 안정 ID 매핑
2. 동일 제목 + 동일 phase 내 문서 순서
3. 동일 제목 + 인접 순서(단일 후보일 때만)
- 매핑이 1:1로 확정되지 않으면 모호성으로 판단하고 `blocked`로 종료한다.
- reconcile 후 `run-state.yaml` 집계값은 `.codex/milestones/<run_id>/phases/<unit_id>/status.json`에서 재계산해 덮어쓴다.

4. ready set 계산
- 기본 ready 후보: 상태가 `ready`인 unit.
- `force_retry=true`면 `failed|blocked`를 `ready`로 재승격해 후보에 포함한다.
- `force_revalidate=true`면 `done` 또는 `warn|fail` verdict unit/final verification만 검증 후보에 포함한다(write 후보에는 포함 금지).
- dependency 미완료(`pending|ready|running`) unit은 `force_revalidate` 후보에서 제외한다.
- `target_unit`이 있으면 해당 unit만 후보로 제한한다.
- `target_phase`만 있으면 해당 phase 후보만 남긴다.

5. batch 선택
- write batch는 invocation당 최대 1개 unit만 선택한다.
- 특히 `target_phase` 내 write-ready unit이 여러 개면 문서 순서상 첫 1개만 실행한다.
- `target_unit` 지정 시 해당 unit 하나만 처리한다.

6. unit 실행
- write는 unit마다 fresh worker 1회성으로 실행한다(재사용 금지).
- retry도 반드시 새 worker를 할당한다.
- 실행 전 unit 상태를 `running`으로 기록하고, 종료 시 `done|failed|blocked` 중 하나로 갱신한다.
- `force_revalidate` 경로는 write 없이 검증만 수행하고 검증 artifact와 상태만 갱신한다.
- 실패 시 `status.json` + `handoff.md`에 실패 원인과 재시도 조건을 반드시 기록한다.

7. final verification (구현과 분리)
- 모든 unit 완료 후 구현(write)과 분리된 final verification을 수행한다.
- 결과는 `.codex/milestones/<run_id>/final-verification.md`에 `PASS|WARN|FAIL`로 기록한다.
- final verification 결과에는 남은 리스크, blocker, 재실행 추천 unit을 반드시 포함한다.

8. 종료
- phase verdict를 재계산하고 `run-state.yaml`에 반영한다.
- 이번 invocation에서 처리한 unit, 다음 ready 후보, blocker 여부를 사용자에게 보고한다.

## 글로벌 AGENTS 라우팅 재사용 정책

- 라우팅 판단은 저장소의 글로벌 `AGENTS.md`(fast lane / deep solo / delegated team)를 그대로 재사용한다.
- 이 스킬은 라우팅 원칙을 덮어쓰지 않는다.
- delegated lane일 때도 single-writer 원칙을 유지하며, 본 스킬의 write 단위는 항상 unit 1개 + fresh worker다.

## 사용자 출력 형식

출력은 아래 순서를 고정한다.

- 중간 진행 로그(탐색 N건, 목록 탐색 마침, 전체 쉘 스크립트 덤프, 명령 원문 나열)는 출력하지 않는다.
- 사용자에게는 최종 결과만 1회 보고한다.
- 명령 실행 근거는 `evidence.md`에 기록하고, 사용자 응답에는 요약만 포함한다.

1. 실행 요약
- `run_id`, `milestone_path`, `milestone_hash`, `selected_scope(target_unit|target_phase|auto)`, `action(write|revalidate|noop)`

2. 상태표 (필수 컬럼)

| phase_id | unit_id | doc_order | before | after | attempts | phase_verdict | worker_fresh | reason |
|---|---|---|---|---|---|---|---|---|

3. 다음 액션
- 다음 invocation 추천 대상 1개(unit id)
- blocker 존재 시 해제 조건

## Acceptance 테스트 시나리오

1. 초기 실행 생성
- 조건: 상태 아티팩트가 없는 새 `run_id`.
- 기대: `run-state.yaml`, `.codex/milestones/<run_id>/phases/<unit_id>/status.json`, `phase-manifest.yaml` 생성. 첫 ready unit 1개만 실행.

2. `target_unit` 우선순위
- 조건: `target_unit`과 `target_phase`를 동시에 전달.
- 기대: `target_unit`만 실행되고 `target_phase`는 필터 힌트로만 처리.

3. phase 다중 ready 제한
- 조건: `target_phase` 내 write-ready unit이 2개 이상.
- 기대: 문서 순서 첫 1개만 실행, 나머지는 다음 invocation으로 이월.

4. `force_retry` 동작 분리
- 조건: unit 상태가 `failed`.
- 기대: `force_retry=true`에서만 write 재시도 가능. 재시도는 새 worker로 1회성 실행.

5. `force_revalidate` 동작 분리
- 조건: unit 상태가 `done`.
- 기대: `force_revalidate=true`일 때만 검증 artifact 갱신. 구현/write는 수행하지 않음.

6. milestone_hash 변경 + 명확 매핑
- 조건: 문서 편집 후 hash 변경, metadata 또는 제목/순서로 1:1 매핑 가능.
- 기대: 기존 상태 보존 + 집계 재계산 후 계속 실행.

7. milestone_hash 변경 + 모호 매핑
- 조건: 동일 제목 중복 등으로 1:1 매핑 불가.
- 기대: 즉시 `blocked` 종료, blocker reason에 모호성 원인 기록.

8. phase-manifest status 금지 검증
- 조건: 어떤 실행/재시도 후에도 manifest 확인.
- 기대: manifest에 `status`/`phase_verdict`/`attempts` 등 mutable 상태 필드 없음.

9. failure artifact 기록
- 조건: unit 실행이 `failed` 또는 `blocked`로 종료.
- 기대: `status.json`과 `handoff.md`에 실패 원인/재시도 조건이 함께 기록됨.

10. final verification 분리
- 조건: 모든 unit이 처리된 시점.
- 기대: 구현과 분리된 final verification이 수행되고 `final-verification.md`에 `PASS|WARN|FAIL` + 리스크/블로커/재실행 권고가 기록됨.

## Hidden Metadata V2 제안 (선택)

`milestone.md`의 phase/unit에 아래 주석 메타데이터를 숨김 삽입해 reconcile 안정성을 높일 수 있다.

```markdown
<!-- MRUN:v2 phase_id=phase-2 unit_id=phase-2-unit-1 unit_sig=sha256:... -->
```

- V2 메타데이터는 권장 사항이며 필수는 아니다.
- 존재하면 reconcile 1순위 키로 사용한다.

## Appendix (Optional): codex_home 모드

- 본문 규정의 core state mode는 repo(`.codex/milestones/...`)다.
- 필요 시 `codex_home`에 미러/백업을 둘 수 있으나 비권위 사본으로만 취급한다.
- 충돌 시 항상 repo 아티팩트를 우선한다.
