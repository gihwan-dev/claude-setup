# Execution slices

## SLICE-1

- Change boundary: ingestion pipeline
- Expected files: 3
- Validation owner: main thread
- Focused validation plan: parser unit test + fixture smoke test
- Stop / Replan trigger: event schema drift

## SLICE-2

- Change boundary: timeline normalization
- Expected files: 3
- Validation owner: main thread
- Focused validation plan: normalization unit test + low-cost smoke check
- Stop / Replan trigger: wait/tool span ambiguity

# Verification

- parser unit test
- normalization smoke check

# Stop / Replan conditions

- event schema drift가 생기면 `SLICE-1` 이후 재설계
- wait/tool span ambiguity가 남으면 `SLICE-2` 진입 전 재정렬
