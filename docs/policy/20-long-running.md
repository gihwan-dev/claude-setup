## 실행 흐름

### Fast lane

1. 메인 스레드에서 필요한 최소 파일만 확인한다.
2. 메인 스레드에서 최소 diff를 직접 적용한다.
3. 검증 1개를 집중 실행한다.
4. 종료 전 메인 스레드가 실질 영향 문서만 재탐색/검토하고 필요한 sync/check를 마무리한다.
5. 변경 요약, 검증 결과, 잔여 리스크를 보고한다.

### Standard delegated flow

1. 탐색/증거 수집이 필요할 때만 `explorer`를 사용한다.
2. live browser reproduction, visual evidence, Electron/window behavior 확인이 필요할 때만 `browser-explorer`를 선택적으로 사용한다. handoff에는 `target URL 또는 Electron entry`, `scenario checklist`, `evidence checklist`를 포함한다.
3. 메인 스레드에서 의사결정을 확정한다.
4. 정확히 하나의 `worker`가 필요한 code diff를 적용한다.
5. 메인 스레드가 문서 영향 여부를 판정하고 필요한 문서 diff는 same `worker`가 validation 전에 phase 1 안에서 반영한다.
6. 검증 출력이 noisy/multi-step일 때만 `verification-worker`를 사용한다.
7. 메인 스레드가 결과를 통합하기 전에 실질 영향 문서 재검토와 필요한 sync/check를 마무리한다.
8. 메인 스레드가 결과를 통합해 최종 응답한다.

### Long-running `implement-task` path

- 사용자에게는 `design-task`, `implement-task`만 노출한다.
- `design-task`는 새 task에서 `task.yaml` 중심 task bundle을 만들고, continuity gate를 적용해 같은 작업으로 입증된 경우에만 기존 task를 재사용한다.
- greenfield/new-project 설계는 `design-task` 이후 post-design bootstrap skill(`bootstrap-project-rules`)을 거쳐 repo baseline implementation rules와 task supplement contract를 만들 수 있다.
- `design-task`는 `work_type + impact_flags + delivery_strategy`를 결정한다.
- `design-task`와 `implement-task`는 각 slice에 `split decision`을 기록하고 target-file append 금지 trigger를 명시한다.
- 여러 active task 폴더 공존은 정상 경로다.
- `implement-task` long-running path는 single-writer delegated flow를 유지한다.
- 문서 영향 판정은 메인 스레드 기본 책임이다.
- 종료 전 메인 스레드는 실질 영향 문서만 다시 탐색/검토한다. 기본 대상은 `README`, `docs/**`, task bundle docs, `openapi.yaml`, `schema.json`, architecture/change docs, workflow/SSOT runbook docs다.
- 문서 대상이 불명확할 때만 read-only helper를 사용한다.
- path 미지정 시 자동 선택은 후보가 정확히 1개일 때만 허용한다.
- 후보가 2개 이상이면 사용자 확인 전까지 자동 실행하지 않는다.
- writable projection은 `worker`만 허용하고 slice마다 정확히 한 명만 code diff를 적용한다.
- `worker` handoff 기본값은 minimal handoff다. 기본 내용은 `slice goal`, `write scope`, `acceptance checks`, `current diff state`만 포함한다.
- pre-edit 상태 보고는 1회 structure preflight만 허용하고 첫 edit 전 추가 checkpoint 요청은 금지한다.
- full-history/forked-context는 정확한 thread-local reasoning 또는 uncommitted local state lineage가 꼭 필요할 때만 허용한다.
- 각 slice는 `worker edit(구현 + 필요한 문서/source-of-truth 반영) -> main focused validation -> same worker commit-only -> STATUS update -> next slice decision` 순서를 따른다.
- 필요한 문서 diff는 phase 1을 수행한 same `worker`가 focused validation 전에 함께 반영한다.
- helper fan-out은 탐색/리뷰/검증 로그 해석이 필요할 때만 read-only로 사용한다.
- live browser reproduction, DOM/visual QA, screenshot evidence가 필요할 때만 `browser-explorer`를 선택적으로 사용한다. handoff에는 `target URL 또는 Electron entry`, `scenario checklist`, `evidence checklist`를 포함한다.
- UI 영향 planning은 `ux-journey-critic`를 우선하고 scope가 모호할 때만 `product-planner`, 구조 분해가 필요할 때만 `structure-planner`를 추가한다.
- AI/agent workflow planning은 `web-researcher`를 official vendor docs 우선 조사 용도로 사용한다.
- 작은/저위험 slice는 메인 스레드 수동 리뷰를 기본값으로 두고 advisory helper fan-out은 결과가 현재 slice 의사결정을 바꿀 때만 허용한다.
- 새 task bundle core docs는 `task.yaml`, `README.md`, `EXECUTION_PLAN.md`, `SPEC_VALIDATION.md`, `STATUS.md`다.
- `task.yaml`은 machine entry point이고, `README.md`는 사람용 landing 문서다.
- post-design bootstrap이 적용되면 repo baseline source는 `docs/ai/ENGINEERING_RULES.md`이고, task bundle에는 optional `IMPLEMENTATION_CONTRACT.md`와 `source_of_truth.implementation` pointer가 추가될 수 있다.
- 새 task는 `PLAN.md`를 만들지 않는다. legacy `PLAN.md`/`STATUS.md` task는 fallback compatibility로만 유지한다.
- `design-task`는 `work_type + impact_flags`로 필수/선택 문서를 고르고 `required_docs`에 실제 bundle 집합을 기록한다.
- `task.yaml`은 `delivery_strategy`를 포함하고 `standard` 또는 `ui-first`만 허용한다.
- `work_type`이 `feature`, `prototype`, `refactor`, `bugfix` 중 하나고 `impact_flags`에 `ui_surface_changed` 또는 `workflow_changed`가 있으면 `delivery_strategy=ui-first`를 사용한다.
- `delivery_strategy=ui-first`면 `UX_SPEC.md`를 UX source of truth로 고정하고 `UI -> local state/mock -> real API/integration` 순서로 slice를 만든다.
- `delivery_strategy=ui-first`인 `EXECUTION_PLAN.md`는 `SLICE-1=static/visual UI`, `SLICE-2=local state/mock`, `SLICE-3+=real API/integration` 의미를 유지하고 `SLICE-1`/`SLICE-2`에는 real API/integration 금지를 적는다.
- `SLICE-1` 미승인 또는 `SLICE-2` 상태 모델 미정이면 다음 slice 진입은 stop/replan으로 막는다.
- `SPEC_VALIDATION.md`는 항상 생성한다.
- `SPEC_VALIDATION.md`의 gate는 `blocking`/`advisory`만 허용한다.
- `ui_surface_changed`, `workflow_changed`, `architecture_significant`, `public_contract_changed`, `data_contract_changed`, `operability_changed`, `high_user_risk` 중 하나가 있거나 설계 문서가 3종 이상이면 `blocking` gate를 사용한다.
- `SPEC_VALIDATION.md`는 `Requirement coverage`, `UX/state gaps`, `Architecture/operability risks`, `Slice dependency risks`, `Blocking issues`, `Proceed verdict` 순서를 유지한다.
- greenfield/new-project에서 repo implementation rules가 아직 없으면 `Blocking issues`에 `$bootstrap-project-rules` 실행 요구를 남기고, bootstrap이 끝나기 전에는 cleared로 바꾸지 않는다.
- `implement-task`는 새 task에서 `task.yaml + EXECUTION_PLAN.md + STATUS.md`를 우선 읽고, `blocking` validation이 해소되지 않았으면 구현을 시작하지 않는다.
- `implement-task`는 `source_of_truth.implementation`이 있으면 `IMPLEMENTATION_CONTRACT.md`를 함께 읽고, bootstrap 관련 blocking issue가 남아 있으면 구현을 시작하지 않는다.
- `implement-task`는 `task.yaml.delivery_strategy`를 구현 계약으로 읽고 `ui-first`면 early UI slice에 real API/integration diff를 허용하지 않는다.
- phase 2 기본 검증은 `타깃 검증 1개 + 저비용 체크 1개`다. shared/public boundary 변경일 때만 full-repo validation을 허용한다.
- noisy/multi-step validation log는 `verification-worker`가 메인 검증 로그를 해석한다.
- focused validation 실패 시 해당 slice는 커밋하지 않고 즉시 중단한다.
- `STATUS.md`의 구현 요약에는 문서 영향 판단을 남기고, `Verification results`에는 관련 sync/check 명령과 pass/fail을 남긴다.
- hook 실패로 커밋이 막히면 동일한 커밋 메시지로 `git commit --no-verify`를 1회 재시도한다.
- `--no-verify` 재시도까지 실패하면 해당 slice를 실패로 기록하고 다음 slice로 진행하지 않는다.
- `docs/policy`가 바뀌면 `python3 scripts/sync_instructions.py` 후 `python3 scripts/sync_instructions.py --check`를 통과해야 한다.
- `skills`가 바뀌면 `python3 scripts/sync_skills_index.py` 후 `python3 scripts/sync_skills_index.py --check`를 통과해야 한다.
- `agent-registry`가 바뀌면 `python3 scripts/sync_agents.py` 후 `python3 scripts/sync_agents.py --check`를 통과해야 한다.
- 문서 diff도 slice budget에 포함한다. 문서 반영까지 포함해 budget을 넘기면 현재 slice를 억지로 넓히지 말고 replan한다.
- slice budget 기본값은 `repo-tracked files 3개 이하` 또는 `하나의 응집된 모듈 경계`이며, 순 diff는 `150 LOC 내외`로 제한한다.
- 이미 soft limit를 넘긴 파일에 additive diff를 더하는 slice는 strong mode에서 허용하지 않는다.
- 공통 리팩터링 + 여러 화면 치환 + 테스트 전수 갱신 + 정적 스캔을 한 slice에 묶는 혼합 giant slice를 금지한다.
- `wait timeout`은 stalled와 동일하지 않다.
- `liveness gate`와 `completion gate`를 분리한다.
- `non-cancel observe path`는 `wait -> inspect/status ping(interrupt=false) -> observe/drain -> background or natural completion`만 허용한다.
- `explicit cancel path`는 `wait -> inspect/status ping -> interrupt -> drain grace -> close 판단`만 허용한다.
- non-cancel 경로에서는 synthetic interrupt를 보내지 않는다.
- `explicit cancel`만 종료 근거다.
- `result가 더 이상 필요 없음`은 close 근거가 아니다.
- advisory helper는 구현/테스트/커밋 완료만으로 close하지 않는다.
- advisory helper 미응답은 slice 실패로 처리하지 않고 close가 아니라 background/advisory로 전환한다.
- 늦게 도착한 advisory 결과는 현재 판단과 관련 있으면 merge-if-relevant로 병합한다.
- `wait timed_out -> status running -> no result -> close`는 invalid sequence다.
- `verification-worker`는 commit sign-off가 불가능할 때만 일시적으로 semi-blocking으로 승격하고, 그 외에는 advisory로 처리한다.
- core helper 출력은 반드시 `상태:`와 `진행 상태:` 두 줄로 시작한다. `진행 상태:` 형식은 `phase=<...>; last=<...>; next=<...>`를 사용한다.
- interrupt/close 요청 시 helper는 새 작업 시작을 중지하고 `final`을 우선 flush하고, 불가능하면 `checkpoint`를 정확히 1회 flush한 뒤 마지막 줄에 다음 행동 또는 차단 사유를 남긴다.
- `STATUS.md`는 오케스트레이터 전용 메타 상태 문서다.
- 메인 스레드는 helper 요약을 통합해 `STATUS.md`를 갱신하고 다음 slice 진행/중단을 결정한다.
