# Codex API Contract

Figma Codex Pipeline에서 사용하는 Codex `spawn_agents_on_csv` / `report_agent_job_result` API 사용 규약.

## spawn_agents_on_csv

### Phase 2: Execute (컴포넌트 코드 생성)

```python
spawn_agents_on_csv(
    csv_path="components.csv",
    instruction=EXECUTOR_PROMPT,        # {column_name} 플레이스홀더 사용
    id_column="row_id",
    output_schema={
        "component_path": "string",     # 실제 생성된 파일 경로
        "exports": "string",            # export된 심볼 (쉼표 구분)
        "tokens_used": "string",        # 사용된 디자인 토큰 (쉼표 구분)
        "dependencies": "string",       # import한 패키지/컴포넌트 (쉼표 구분)
        "warnings": "string"            # 경고 사항
    },
    max_concurrency=6,
    max_runtime_seconds=300
)
```

### Phase 4: Verify (검증)

```python
spawn_agents_on_csv(
    csv_path="verification.csv",
    instruction=VERIFIER_PROMPT,        # {column_name} 플레이스홀더 사용
    id_column="row_id",
    output_schema={
        "pass": "boolean",             # 검증 통과 여부
        "severity": "string",          # "none" | "minor" | "major" | "critical"
        "findings": "string",          # 발견 사항 설명
        "artifact_paths": "string"     # 생성된 artifact 경로 (쉼표 구분)
    },
    max_concurrency=6,
    max_runtime_seconds=180
)
```

## Instruction Placeholder 규칙

`instruction` 파라미터 내에서 `{column_name}` 형식으로 CSV 컬럼 값을 참조한다.

- `{row_id}` -> 해당 행의 `row_id` 값으로 치환
- `{component_name}` -> 해당 행의 `component_name` 값으로 치환
- CSV에 없는 컬럼을 참조하면 빈 문자열로 치환된다
- 플레이스홀더는 instruction 텍스트 내 어디서든 사용 가능

## report_agent_job_result

각 워커는 작업 완료 시 정확히 1회 호출한다.

```python
report_agent_job_result(
    row_id="{row_id}",
    status="success" | "failed",
    output={
        # output_schema에 정의된 필드들
    }
)
```

### 규칙

- 워커당 정확히 1회 호출. 중복 호출 금지.
- `status="failed"`일 때도 가능한 한 `output`에 에러 정보를 포함한다.
- 호출하지 않고 워커가 종료되면 `max_runtime_seconds` 후 timeout으로 처리된다.

## 실패 복구 전략

### Phase 2 (Execute) 실패 복구

1. `spawn_agents_on_csv` 완료 후 output CSV에서 `status=failed` 행 수집
2. 실패 행에 에러 컨텍스트를 `acceptance_criteria`에 추가 (`[RETRY] 이전 에러: {error}. 다른 접근법 시도`)
3. 실패 행만 포함한 `components_retry.csv` 생성
4. 동일 `spawn_agents_on_csv` 호출로 1회 재시도
5. 2회 실패 시 해당 행은 `skipped` 처리

### Phase 4 (Verify) 실패 복구

1. Critical 발견이 있으면 Phase 3에서 수정
2. 수정 후 해당 컴포넌트만 재검증 CSV 생성
3. 최대 2회 반복

### 중단 조건

- Phase 2 전체 성공률 50% 미만 -> 파이프라인 중단, 사용자에게 분해 재검토 요청
- Phase 4 Critical 발견이 3회 반복 후에도 해소 안 됨 -> 사용자에게 수동 개입 요청

## Concurrency 가이드라인

| 파라미터 | Phase 2 | Phase 4 | 근거 |
|----------|---------|---------|------|
| `max_concurrency` | 6 | 6 | Codex 기본 제한 내 |
| `max_runtime_seconds` | 300 | 180 | 코드 생성은 검증보다 오래 걸림 |

컴포넌트 수가 6개 이하이면 모두 동시 실행. 초과 시 큐에서 순차 dispatch.

## 독립 산출물 원칙

- 각 워커는 자신의 `target_path`에만 파일을 생성/수정한다.
- 워커 간 파일 참조, import, 상호 의존 금지.
- 공유 컨텍스트는 오직 `shared_context.json` (읽기 전용)을 통해서만 접근.
- 워커가 다른 워커의 output을 참조해야 하는 통합 작업은 Phase 3에서 메인 에이전트가 수행.
