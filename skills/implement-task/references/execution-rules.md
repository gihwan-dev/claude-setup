# Execution Rules

`implement-task`의 상세 실행 규칙을 모아 둔 reference다. `SKILL.md`에는 핵심 흐름만 남기고, 아래 세부 규칙은 필요할 때만 읽는다.

## Task Selection Rules

1. 사용자 지정 slug/path가 있으면 해당 task를 사용한다.
2. path가 없으면 active 후보를 만든다. (`미완료 Next slice`가 있거나 현재 실행 가능한 task만 후보로 본다.)
3. 후보가 정확히 1개일 때만 자동 선택한다.
4. 후보가 2개 이상이면 항상 사용자에게 task를 확인받고 자동 실행하지 않는다.
5. 후보가 0개면 최근 수정 task를 참고하되 사용자 확인 전까지 실행하지 않는다.
6. 새 bundle 후보가 있으면 legacy 후보보다 bundle 후보를 우선한다.

## Mode Rules

- 사용자가 `계속해`라고 하면 현재 task의 다음 slice 1개를 수행한다.
- 사용자가 `끝까지` 또는 `stop condition 만날 때까지`를 명시하면 연속 실행 루프를 사용한다.
- 연속 실행 중 아래 조건이면 즉시 중단하고 `STATUS.md`만 갱신한다.
  - focused validation 실패
  - 커밋 실패(`--no-verify` 재시도 실패 포함)
  - 구현 단계가 `blocked + exact split proposal`로 중단됨
  - bundle `SPEC_VALIDATION.md` blocking issue 미해소
  - `EXECUTION_PLAN.md` 또는 legacy `PLAN.md`의 stop/replan 조건 충족
  - public boundary drift 발생
  - 다음 slice 진행 전 의사결정 공백 발생

## Structure And Handoff Rules

- 각 slice 실행 전에는 structure preflight(대상 파일 역할, 예상 post-change LOC, split 필요 여부)를 먼저 고정한다.
- hybrid mode default는 `small slices + run-to-boundary`다.
- pre-edit 상태 보고는 1회 structure preflight만 허용하고 첫 edit 전 추가 checkpoint 요청은 금지한다.
- split-first trigger가 켜지면 target file append 대신 같은 slice 안에서 새 모듈 추출 또는 `blocked + exact split proposal`로 되돌린다.
- broad `setup`/`skeleton`/`wrapper`/`docs` handoff이거나 slice hard guardrail을 넘는 PREP-0 스타일 handoff는 실행 전에 `split/replan before execution`으로 되돌린다.
- 종료 전 메인 스레드는 README, `docs/**`, task bundle docs, `openapi.yaml`, `schema.json`, architecture/change docs, workflow/SSOT runbook docs 같은 실질 영향 문서를 다시 확인한다.
- 필요한 문서 diff나 generated projection sync는 구현 단계에서 focused validation 전에 함께 반영한다.

## Validation Fallback

- bundle이면 `EXECUTION_PLAN.md`의 검증 명령을 우선 사용한다.
- legacy면 `PLAN.md`의 검증 명령을 우선 사용한다.
- 문서에 검증 명령이 비어 있을 때만 repo-aware fallback을 사용한다.
- focused validation owner는 메인 스레드다.
- 기본 focused validation은 `타깃 검증 1개 + 저비용 체크 1개`다.
- full-repo validation은 shared/public boundary 변경 시에만 사용한다.
- JS/TS repo는 `package.json` + lockfile 기준으로 package manager를 고르고, 존재하는 script만 사용한다.
- Python repo는 `pyproject.toml` 또는 `tests/`/`test_*.py`를 기준으로 `python3 -m unittest discover`를 후보로 본다.
- 안전한 기본 검증을 추론할 수 없으면 사용자 확인 전까지 중단한다.
- SSOT sync/check가 필요하면 아래 fallback을 사용한다.
  - `skills`: `python3 scripts/sync_skills_index.py` + `python3 scripts/sync_skills_index.py --check`
  - `agent-registry`: `python3 scripts/sync_agents.py` + `python3 scripts/sync_agents.py --check`

## CSV Fan-out Execution Rules

### 환경 감지

- Codex 환경: `spawn_agents_on_csv` 가용 여부로 판단한다.
- Claude Code 환경: `keep-local` fallback으로 순차 실행한다.

### Row Worker 제약

- 각 row worker는 CSV의 `target_path`에만 파일을 생성/수정한다.
- `GLOBAL_CONTEXT.md`의 layout/import rules를 따른다.
- row worker는 다른 row의 output을 참조하지 않는다 (no cross-row reference).
- shared file(barrel exports, route registration, package.json)은 수정 금지다.

### Integrator 역할

- 모든 row worker 완료 후 integrator가 shared file을 통합한다.
- `MERGE_POLICY.md`의 integrator-only 파일 목록에 따라 barrel export, route 등록 등을 갱신한다.
- row output이 같은 shared file section에 영향을 주면 `row_id` 순서로 적용한다.

### 실패 복구

- 실패한 row는 1회 자동 재시도한다.
- 재시도 후에도 실패하면 해당 row를 `failed`로 기록하고 나머지를 계속 진행한다.
- 전체 행의 50% 이상이 실패하면 slice 실행을 중단한다.

### Row-level Continuity

- 이전 실행에서 성공한 `row_id` → skip.
- acceptance criteria나 target_path가 변경된 `row_id` → re-execute.
- 새로 추가된 `row_id` → append.
- 삭제된 `row_id` → superseded (결과 보존).

### STATUS.md 확장 (csv-fanout)

csv-fanout slice의 `STATUS.md`에는 아래 정보를 추가로 기록한다.

- 총 행 수
- 성공 / 실패 / skip / superseded 행 수
- 재시도 횟수
- integrator 결과 (shared file merge 성공/실패)

## STATUS Contract

### Template

```markdown
# Current slice
# Done
# Decisions made during implementation
# Verification results
# Known issues / residual risk
# Next slice
```

### Update Rules

- `# Current slice`: 이번 실행 대상 slice를 적는다.
- `# Done`: 구현 세부 나열 대신 완료된 결과와 사용자/시스템 영향만 요약한다.
- `# Decisions made during implementation`: 다음 slice 또는 공개 경계에 영향을 주는 의사결정과 문서 영향 판단 결과를 남긴다.
- `# Verification results`: 검증 명령, pass/fail, 문서/SSOT sync-check 결과, 커밋 시도 결과, 핵심 실패 원인만 적는다.
- `# Known issues / residual risk`: 남은 위험과 미해결 이슈를 적는다.
- `# Next slice`: 다음 실행 목표, 선행조건, 먼저 볼 경계를 적는다.
- `STATUS.md`를 최초 생성한 실행에서는 템플릿 생성 사실을 `# Done` 또는 `# Decisions made during implementation`에 기록한다.
- design 단계에서 생성된 초기 bundle은 `# Current slice=Not started.` / `# Next slice=SLICE-1` 기준을 유지한다.
