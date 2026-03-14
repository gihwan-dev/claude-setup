# Execution slices

## SLICE-1

- Change boundary: static timeline overview UI, information architecture, copy, navigation shell
- Expected files: 3
- Validation owner: main thread
- Focused validation plan: 30-second checklist review + visual shell snapshot review
- Stop / Replan trigger: checklist/layout/token/screen-flow 또는 interaction/a11y/microcopy 계약 미승인

## SLICE-2

- Change boundary: local interaction model, keyboard/focus, live update, mock data, loading/empty/error/permission states
- Expected files: 3
- Validation owner: main thread
- Focused validation plan: state matrix + keyboard/focus walkthrough + low-cost mock interaction smoke check
- Stop / Replan trigger: keyboard/focus, live semantics, state matrix/fixture, degradation, task-based approval criteria 미정

## SLICE-3

- Change boundary: real ingestion pipeline, timeline normalization, API/data integration
- Expected files: 3
- Validation owner: main thread
- Focused validation plan: parser unit test + normalization smoke check
- Stop / Replan trigger: event schema drift 또는 backend contract mismatch

# Verification

- 30-second checklist review
- visual shell snapshot review
- keyboard/focus walkthrough
- mock interaction smoke check
- parser unit test
- normalization smoke check

# Stop / Replan conditions

- `SLICE-1` UX 구조나 behavior shell 계약이 승인되지 않으면 `SLICE-2`로 진행하지 않는다.
- `SLICE-2` keyboard/focus, live semantics, state matrix/fixture, degradation, task-based approval criteria가 미정이면 `SLICE-3`로 진행하지 않는다.
- event schema drift 또는 backend contract mismatch가 생기면 `SLICE-3` 진입 전 재설계
