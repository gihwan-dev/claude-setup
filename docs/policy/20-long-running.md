## 실행 흐름

### Fast lane

1. 메인 스레드에서 필요한 최소 파일만 확인한다.
2. 메인 스레드에서 최소 diff를 직접 적용한다.
3. 검증 1개를 집중 실행한다.
4. 변경 요약, 검증 결과, 잔여 리스크를 보고한다.

### Standard delegated flow

1. 탐색/증거 수집이 필요할 때만 `explorer`를 사용한다.
2. 메인 스레드에서 의사결정을 확정한다.
3. 정확히 하나의 `worker`가 필요한 code diff를 적용한다.
4. 검증 출력이 noisy/multi-step일 때만 `verification-worker`를 사용한다.
5. 메인 스레드가 결과를 통합해 최종 응답한다.

### Long-running `implement-task` path

- 사용자에게는 `design-task`, `implement-task`만 노출한다.
- `design-task`는 continuity gate를 적용해 같은 작업으로 입증된 경우에만 기존 task를 재사용하고, 아니면 새 flat task path를 만든다.
- 여러 active task 폴더 공존은 정상 경로다.
- `implement-task` long-running path는 single-writer delegated flow를 유지한다.
- path 미지정 시 자동 선택은 후보가 정확히 1개일 때만 허용한다.
- 후보가 2개 이상이면 사용자 확인 전까지 자동 실행하지 않는다.
- writable projection은 `worker`만 허용하고 slice마다 정확히 한 명만 code diff를 적용한다.
- 각 slice는 `worker edit -> main focused validation -> same worker commit-only -> STATUS update -> next slice decision` 순서를 따른다.
- helper fan-out은 탐색/리뷰/검증 로그 해석이 필요할 때만 read-only로 사용한다.
- 작은/저위험 slice는 메인 스레드 수동 리뷰를 기본값으로 두고 advisory helper fan-out은 결과가 현재 slice 의사결정을 바꿀 때만 허용한다.
- phase 2 기본 검증은 `타깃 검증 1개 + 저비용 체크 1개`다. shared/public boundary 변경일 때만 full-repo validation을 허용한다.
- noisy/multi-step validation log는 `verification-worker`가 메인 검증 로그를 해석한다.
- focused validation 실패 시 해당 slice는 커밋하지 않고 즉시 중단한다.
- hook 실패로 커밋이 막히면 동일한 커밋 메시지로 `git commit --no-verify`를 1회 재시도한다.
- `--no-verify` 재시도까지 실패하면 해당 slice를 실패로 기록하고 다음 slice로 진행하지 않는다.
- slice budget 기본값은 `repo-tracked files 3개 이하` 또는 `하나의 응집된 모듈 경계`이며, 순 diff는 `150 LOC 내외`로 제한한다.
- 공통 리팩터링 + 여러 화면 치환 + 테스트 전수 갱신 + 정적 스캔을 한 slice에 묶는 혼합 giant slice를 금지한다.
- `wait timeout`은 stalled와 동일하지 않다.
- `liveness gate`와 `completion gate`를 분리한다.
- close 판단은 `observe -> inspect/status ping -> interrupt flush -> drain grace -> close 판단` 순서를 따른다.
- `explicit cancel`, `hard deadline`, `상태: blocked`만 강한 종료 근거다.
- `result가 더 이상 필요 없음`은 close 근거가 아니다.
- advisory helper는 구현/테스트/커밋 완료만으로 close하지 않는다.
- advisory helper 미응답은 slice 실패로 처리하지 않고 close가 아니라 background/advisory로 전환한다.
- 늦게 도착한 advisory 결과는 현재 판단과 관련 있으면 merge-if-relevant로 병합한다.
- `wait timed_out -> status running -> no result -> close`는 invalid sequence다.
- `verification-worker`는 commit sign-off가 불가능할 때만 일시적으로 semi-blocking으로 승격하고, 그 외에는 advisory로 처리한다.
- core helper 출력은 반드시 `상태:`와 `진행 상태:` 두 줄로 시작한다. `진행 상태:` 형식은 `phase=<...>; last=<...>; next=<...>`를 사용한다.
- interrupt/close 요청 시 helper는 새 작업 시작을 중지하고 `final` 또는 최소 `checkpoint/preliminary`를 1회 flush한 뒤 마지막 줄에 다음 행동 또는 차단 사유를 남긴다.
- `STATUS.md`는 오케스트레이터 전용 메타 상태 문서다.
- 메인 스레드는 helper 요약을 통합해 `STATUS.md`를 갱신하고 다음 slice 진행/중단을 결정한다.
