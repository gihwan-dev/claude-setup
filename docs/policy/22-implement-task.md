## implement-task 실행

### 진입 조건

- 새 task에서 `task.yaml + EXECUTION_PLAN.md + STATUS.md`를 우선 읽는다.
- `blocking` validation을 해소한 뒤 구현을 시작한다.
- `source_of_truth.implementation`이 있으면 `IMPLEMENTATION_CONTRACT.md`를 함께 읽는다.
- `task.yaml.delivery_strategy`를 구현 계약으로 읽고, `ui-first`면 early UI slice에는 static/mock만 포함한다.

### slice 생명주기

- 각 slice는 `slice implementation(구현 + 필요한 문서/source-of-truth 반영) -> main focused validation -> commit -> STATUS update -> next slice decision` 순서를 따른다.
- 문서 diff는 구현 단계에서 focused validation 전에 함께 반영한다.
- 문서 영향 판정은 메인 스레드 기본 책임이다.
- 문서 diff도 slice budget에 포함한다. budget을 넘기면 replan한다.

### 실행 guardrails

- path 미지정 시 자동 선택은 후보가 1개일 때만 허용한다. 2개 이상이면 사용자 확인을 기다린다.
- pre-edit 상태 보고는 1회 structure preflight로 마친다.
- slice budget(`workflow.toml [slice_budget]` 참조)을 넘는 handoff는 `split/replan before execution`으로 되돌린다.
- soft limit를 넘긴 파일은 additive diff 대신 split을 사용한다 (strong mode).
- 공통 리팩터링, 여러 화면 치환, 테스트 전수 갱신, 정적 스캔은 별도 slice로 분리한다.
- full-history/forked-context는 thread-local reasoning 또는 uncommitted local state lineage가 필요할 때 사용한다.

### helper 활용

- helper fan-out은 탐색/리뷰/검증 로그 해석이 필요할 때 read-only로 사용한다.
- browser-explorer는 live browser reproduction, DOM/visual QA, screenshot evidence가 필요할 때 사용한다. handoff에 `target URL 또는 Electron entry`, `scenario checklist`, `evidence checklist`를 포함한다.
- 작은/저위험 slice는 메인 스레드 수동 리뷰를 기본으로 두고, advisory helper fan-out은 slice 의사결정을 바꿀 때만 사용한다.

### 검증

- phase 2 기본 검증: `타깃 검증 1개 + 저비용 체크 1개`. shared/public boundary 변경일 때만 full-repo validation을 사용한다.
- noisy/multi-step validation log는 `verification-worker`가 해석한다.
- focused validation 실패 시 해당 slice를 커밋하지 않고 원인을 해결한다.
- `STATUS.md` 구현 요약에 문서 영향 판단을 남기고, `Verification results`에 sync/check 명령과 pass/fail을 남긴다.

### 커밋과 sync

- hook 실패로 커밋이 막히면 동일 메시지로 `git commit --no-verify`를 1회 재시도한다.
- 재시도까지 실패하면 해당 slice를 실패로 기록하고 원인을 해결한다.
- `docs/policy` 변경 시: `sync_instructions.py` → `--check` 통과 <!-- repo-only -->
- `skills` 변경 시: `sync_skills_index.py` → `--check` 통과 <!-- repo-only -->
- `agent-registry` 변경 시: `sync_agents.py` → `--check` 통과 <!-- repo-only -->

### 종료

- 종료 전 메인 스레드는 실질 영향 문서만 다시 탐색/검토한다.
- 기본 대상: `README`, `docs/**`, task bundle docs, `openapi.yaml`, `schema.json`, architecture/change docs, workflow/SSOT runbook docs
- 문서 대상이 불명확할 때만 read-only helper를 사용한다.
