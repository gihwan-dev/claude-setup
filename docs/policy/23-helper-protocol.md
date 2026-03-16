## Helper agent 계약

### timeout과 close 기본 원칙

- `wait timeout`과 stalled는 다른 상태다. `liveness gate`와 `completion gate`를 분리한다.
- non-interrupt status ping은 queued-only semantics를 따른다.
- 상세 값은 `workflow.toml [helper_close]`를 참조한다.

### timeout 경로

- `wait timed_out` 시: `longer wait -> optional queued status probe -> background or natural completion` 경로를 따른다.
- `non-cancel observe path`: `wait -> inspect/status ping(interrupt=false) -> observe/drain -> background or natural completion`
- Immediate status check requires explicit cancel path.

### cancel 경로

- `explicit cancel path`: `wait -> inspect/status ping -> interrupt -> drain grace -> close 판단`
- non-cancel 경로에서는 synthetic interrupt를 보내지 않는다.
- `explicit cancel`만 종료 근거로 사용한다. `result가 더 이상 필요 없음`은 종료 근거가 아니다.
- `wait timed_out → status running → no result → close`는 유효하지 않은 시퀀스다.

### advisory helper 규칙

- advisory helper는 구현/테스트/커밋 완료만으로 close하지 않고, background/advisory로 유지한다.
- advisory helper 미응답은 slice 실패가 아니라 background/advisory로 전환한다.
- 늦게 도착한 advisory 결과는 현재 판단과 관련 있으면 merge-if-relevant로 병합한다.
- `verification-worker`는 commit sign-off가 필요할 때만 semi-blocking으로 승격하고, 그 외에는 advisory로 유지한다.

### helper 출력 형식

- core helper 출력은 `상태:`와 `진행 상태:` 두 줄로 시작한다.
- `진행 상태:` 형식: `phase=<...>; last=<...>; next=<...>`
- interrupt/close 요청 시: 새 작업을 중지하고 `final`을 우선 flush한다. 불가능하면 `checkpoint`를 1회 flush한 뒤 마지막 줄에 다음 행동 또는 차단 사유를 남긴다.

### STATUS.md

- `STATUS.md`는 오케스트레이터 전용 메타 상태 문서다.
- 메인 스레드가 helper 요약을 통합해 `STATUS.md`를 갱신하고 다음 slice 진행/중단을 결정한다.
