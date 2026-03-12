# Execution slices

## SLICE-1

- Change boundary: static timeline overview UI, information architecture, copy, navigation shell
- Expected files: 3
- Validation owner: main thread
- Focused validation plan: visual shell snapshot review + low-cost fixture smoke check
- Stop / Replan trigger: timeline information architecture 또는 core UX direction 미승인

## SLICE-2

- Change boundary: local interaction model, mock data, loading/empty/error/permission states
- Expected files: 3
- Validation owner: main thread
- Focused validation plan: state matrix review + low-cost mock interaction smoke check
- Stop / Replan trigger: local state model 또는 mock strategy 미정

## SLICE-3

- Change boundary: real ingestion pipeline, timeline normalization, API/data integration
- Expected files: 3
- Validation owner: main thread
- Focused validation plan: parser unit test + normalization smoke check
- Stop / Replan trigger: event schema drift 또는 backend contract mismatch

# Verification

- visual shell snapshot review
- mock interaction smoke check
- parser unit test
- normalization smoke check

# Stop / Replan conditions

- `SLICE-1` UI 방향이 승인되지 않으면 `SLICE-2`로 진행하지 않는다.
- `SLICE-2` 상태 모델이나 mock strategy가 미정이면 `SLICE-3`로 진행하지 않는다.
- event schema drift 또는 backend contract mismatch가 생기면 `SLICE-3` 진입 전 재설계
