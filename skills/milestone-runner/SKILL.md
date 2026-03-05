---
name: milestone-runner
description: >
  Continuously execute milestone.md until completion with fresh-per-attempt writers and artifact-based resume.
  milestone.md를 계획 단일 진실원으로 소비해 완료(PASS)까지 연속 실행/재개하는 runner 스킬.
---

# Milestone Runner (Continuous, Instruction-Only)

## 목적과 경계

- 이 스킬은 `planner`가 아니라 `runner`다.
- 계획의 단일 진실원은 항상 `milestone.md`다.
- 런타임 진실원(runtime truth)은 `repo/.codex/milestones/<run_id>/run-state.yaml` + `.codex/milestones/<run_id>/phases/<unit_id>/status.json`이다.
- 기본 동작은 **continuous**다. 호출 후 다음 unit을 계속 처리해 완료 조건을 만족할 때까지 진행한다.
- 사람-facing 개념은 `phase`, 실행 단위는 `unit`으로 고정한다.
- `target_unit`/`target_phase`는 디버그/복구를 위한 범위 제한 옵션이다.
- 설계는 instruction-only다. 외부 스크립트 의존을 강제하지 않는다.

## 실행 안정성 가드 (필수)

1. 셸/옵션 고정
- 멀티라인 로직은 반드시 `bash -lc '<script>'`로 실행한다.
- 스크립트 시작부에 `set -euo pipefail`를 선언한다.
- `zsh` 전용 문법을 금지한다.

2. 문자열 안전 규칙
- 문서에서 추출한 텍스트(특히 제목)는 raw shell literal로 직접 삽입하지 않는다.
- 백틱이 포함될 수 있는 값은 `jq -n --arg` 또는 `<<'EOF'`로만 기록한다.
- command substitution은 항상 `$(...)`만 사용한다.

3. 파일 생성/갱신 규칙
- 상태 파일은 `tmp`에 먼저 쓰고 `mv`로 원자적 교체한다.
- 새 run 디렉터리 생성 시 `trap`으로 부분 생성물을 정리한다.
- `phase-manifest.yaml`에는 status 계열 필드를 절대 쓰지 않는다.

4. 사전 점검
- `milestone_path` 존재 여부와 `bash`/`jq`/`shasum` 사용 가능 여부를 먼저 확인한다.
- 필수 의존성이 없으면 즉시 `blocked`로 종료하고 reason을 기록한다.

## 명시 호출 인터페이스

```yaml
milestone_path: string | null       # 기본 "milestone.md"
run_id: string | null               # 미지정 시 새 run_id 생성
target_phase: string | null         # 범위 제한(디버그/복구)
target_unit: string | null          # 범위 제한(최우선)
force_retry: boolean                # 기본 false
force_revalidate: boolean           # 기본 false
```

### 파라미터 규칙

- 우선순위: `target_unit` > `target_phase`.
- 기본 모드는 continuous이며, 범위 제한을 주지 않으면 전체 milestone을 끝까지 실행한다.
- `force_retry=true`면 `failed|blocked` unit을 재시도 큐로 복귀시킨다.
- `force_revalidate=true`면 write 없이 검증 artifact만 갱신한다.

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
- `pass`: 모든 실행 대상 unit이 `done`.
- `not_run`: 아직 실행 흔적이 없음.

## Artifact 파일 책임

| 파일 | 권위성 | 책임 |
|---|---|---|
| `milestone.md` | 계획 권위 | phase/unit 정의 단일 진실원 |
| `.codex/milestones/<run_id>/run-state.yaml` | 런타임 권위 | run 집계 상태/진행률/재시도 정책/마지막 오류 |
| `.codex/milestones/<run_id>/phases/<unit_id>/status.json` | 런타임 권위 | unit 상태/시도 횟수/에러/재시도 시점 |
| `.codex/milestones/<run_id>/decision-log.md` | 비권위 기록 | 분기 근거/예외 처리 로그 |
| `.codex/milestones/<run_id>/final-verification.md` | 비권위 기록 | PASS/WARN/FAIL 결과와 재실행 권고 |
| `.codex/milestones/<run_id>/phases/<unit_id>/writer-brief.md` | 비권위 입력 | unit write 직전 작업 지시 |
| `.codex/milestones/<run_id>/phases/<unit_id>/summary.md` | 비권위 요약 | unit 구현 결과 요약 |
| `.codex/milestones/<run_id>/phases/<unit_id>/evidence.md` | 비권위 증적 | 검증 로그/근거 |
| `.codex/milestones/<run_id>/phases/<unit_id>/handoff.md` | 비권위 인계 | 실패 원인/재시도 조건 |
| `.codex/milestones/<run_id>/phase-manifest.yaml` | 비권위 스냅샷 | 파싱 결과(상태값 금지) |

### 필수 상태 필드

`run-state.yaml`은 다음 필드를 포함해야 한다.

- `mode: continuous`
- `completion_gate: pass_only`
- `retry_policy: infinite_backoff_reanalyze`
- `loop_iteration`
- `last_backoff_sec`
- `last_error_signature`

`status.json`은 다음 필드를 포함해야 한다.

- `attempts`
- `error_signature`
- `next_retry_at`
- `last_writer_id`

## 실행 알고리즘 (Continuous)

1. 초기화
- 입력 파라미터를 검증한다.
- `milestone_path`와 필수 도구를 확인한다.
- 글로벌 `AGENTS.md` 라우팅 정책을 재사용한다.

2. manifest/state 준비
- `milestone.md`를 파싱해 phase/unit 목록을 생성한다.
- `milestone_hash`를 계산한다.
- run 디렉터리, `run-state.yaml`, `status.json`, `phase-manifest.yaml`을 초기화/보정한다.

3. reconcile
- 저장된 `milestone_hash`와 현재 해시가 다르면 reconcile을 수행한다.
- 매핑이 모호하면 `blocked`로 종료한다.

4. 연속 실행 루프
- 아래를 완료 조건 달성 시까지 반복한다.

4-1. ready/backlog 계산
- 상태와 의존성을 기반으로 `ready`/`retry_wait`/`blocked` backlog를 계산한다.
- `target_unit`/`target_phase`가 있으면 해당 범위로 제한한다.

4-2. 완료 가능성 판정
- 모든 대상 unit이 `done`이면 final verification을 수행한다.
- final verification이 `PASS`면 루프를 종료한다.
- final verification이 `WARN|FAIL`이면 권고 unit을 `ready`로 되돌리고 루프를 계속한다.

4-3. 실행 unit 선택
- 문서 순서상 첫 `ready` unit 1개를 선택한다.
- 동시 write는 금지하며 항상 unit 1개만 순차 실행한다.

4-4. write 실행 (fresh writer 강제)
- 선택된 unit을 `running`으로 기록한다.
- write attempt마다 새 writer를 할당한다(`writer_fresh=true`).
- 성공 시 `done`으로 갱신하고 `last_writer_id`를 기록한다.

4-5. milestone 체크박스 즉시 반영
- unit이 `done`이면 대응되는 `milestone.md` 체크박스를 `[x]`로 업데이트한다.

4-6. 실패 처리 + 무제한 재시도
- 실패 시 상태를 `failed|blocked`로 기록한다.
- backoff는 `30s, 60s, 120s, ...` 지수 증가하며 최대 `1800s`를 사용한다.
- `next_retry_at`과 `last_backoff_sec`를 기록한다.
- 동일 `error_signature`가 5회 누적되면 read-only 재분석을 수행하고 다음 `writer-brief.md`를 갱신한다.
- 재시도 횟수 상한은 없다.

5. 종료
- phase verdict를 재계산해 `run-state.yaml`에 반영한다.
- 최종 요약을 사용자에게 1회 보고한다.

## 사용자 출력 형식

출력은 중간 로그 덤프 없이 최종 요약만 보고한다.

1. 실행 요약
- `run_id`, `milestone_path`, `milestone_hash`, `mode`, `completion_gate`

2. 상태표

| phase_id | unit_id | before | after | attempts | worker_fresh | next_retry_at | reason |
|---|---|---|---|---|---|---|---|

3. 연속 실행 진행 상태
- 남은 ready/backlog 개수
- 재시도 대기 큐와 다음 재시도 시각
- final verification 상태(PASS/WARN/FAIL)

## Acceptance 테스트 시나리오 (Continuous)

1. 기본 연속 완주
- 조건: 새 `run_id`, 미완료 unit 3개.
- 기대: runner가 연속 실행하여 final verification `PASS`까지 도달.

2. fresh writer 강제
- 조건: unit 2개 + 재시도 1회.
- 기대: 모든 write attempt의 `last_writer_id`가 서로 다름.

3. 무제한 재시도 + 백오프
- 조건: 동일 unit이 반복 실패.
- 기대: 재시도는 중단되지 않고 backoff가 최대 1800초까지 증가.

4. 5회 재분석 트리거
- 조건: 동일 `error_signature` 5회 연속 발생.
- 기대: read-only 재분석 실행 후 `writer-brief.md`가 갱신됨.

5. WARN/FAIL 복구 루프
- 조건: 모든 unit done 이후 final verification이 WARN 또는 FAIL.
- 기대: 권고 unit을 ready로 복귀시켜 루프 지속, PASS일 때만 종료.

6. 체크박스 반영
- 조건: unit 1개 성공.
- 기대: 해당 `milestone.md` 체크박스가 즉시 `[x]`로 변경.

7. 범위 제한 실행
- 조건: `target_phase` 지정.
- 기대: 지정 범위 안에서만 continuous 실행.

## Hidden Metadata V2 (선택)

```markdown
<!-- MRUN:v2 phase_id=phase-2 unit_id=phase-2-unit-1 unit_sig=sha256:... -->
```

- 존재 시 reconcile 1순위 키로 사용한다.
