# Current slice

완료

# Done

- `advisory-helper-close-guard` task 문서를 생성했다.
- helper `[orchestration]` schema에 `timeout_policy`, `allowed_close_reasons`를 추가했다.
- advisory helper close decision / spawn gate를 machine-checkable 함수로 고정했다.
- source policy, skill, agent instructions, registry metadata를 새 close guard 규칙으로 갱신했다.
- generated projection과 Codex agent profiles를 재생성했다.

# Decisions made during implementation

- advisory helper는 `result가 더 이상 필요 없음`이나 timeout만으로 close하지 않도록 고정했다.
- 작은/저위험 slice는 메인 스레드 수동 리뷰를 기본값으로 두고 advisory fan-out은 기존 trigger + decision relevance가 있을 때만 허용한다.
- close 허용은 strong close reason과 protocol completion(ack 포함)을 함께 요구하도록 정리했다.
- terminal runtime status(`interrupted`, `completed` 등)도 drain grace 이후 ack로 인정하도록 보강했다.

# Verification results

- PASS: `python3 scripts/sync_instructions.py`
- PASS: `python3 scripts/sync_agents.py`
- PASS: `python3 scripts/sync_instructions.py --check`
- PASS: `python3 scripts/sync_agents.py --check`
- PASS: `python3 scripts/validate_workflow_contracts.py`
- PASS: `python3 -m unittest tests/test_workflow_stability.py`

# Known issues / residual risk

- host runtime의 실제 `close_agent` 동작은 이 레포 범위 밖이므로 repo-local contract/test 수준까지만 강제된다.

# Next slice

없음.
