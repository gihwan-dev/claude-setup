## 실행 흐름

### Fast lane

1. 메인 스레드에서 필요한 최소 파일만 확인한다.
2. 최소 diff를 직접 적용한다.
3. 검증 1개를 집중 실행한다.
4. 실질 영향 문서만 재탐색/검토하고 필요한 sync/check를 마무리한다.
5. 변경 요약, 검증 결과, 잔여 리스크를 보고한다.

### Standard delegated flow

1. 탐색/증거 수집이 필요할 때 `explorer`를 사용한다.
2. live browser reproduction, visual evidence 확인이 필요할 때 `browser-explorer`를 사용한다. handoff에 `target URL 또는 Electron entry`, `scenario checklist`, `evidence checklist`를 포함한다.
3. 메인 스레드에서 의사결정을 확정한다.
4. 현재 slice의 code/doc diff를 적용한다.
5. `small slices + run-to-boundary`를 기본으로 사용한다. slice budget(`workflow.toml [slice_budget]` 참조)을 넘는 handoff는 split/replan으로 되돌린다.
6. 문서 영향 여부를 판정하고 문서 diff는 focused validation 전에 구현 단계에서 반영한다.
7. 검증 출력이 noisy/multi-step일 때 `verification-worker`를 사용한다.
8. 실질 영향 문서 재검토와 sync/check를 마무리한다.
9. 결과를 통합해 최종 응답한다.

### Long-running path 개요

- 사용자에게는 `design-task`, `implement-task`만 노출한다.
- 여러 active task 폴더 공존은 정상 경로다.
- `design-task`, `implement-task` 스킬의 상세 워크플로우는 각 스킬의 SKILL.md와 references에서 관리한다.
- helper agent close/timeout 계약은 `workflow.toml [helper_close]`와 각 `agent.toml [orchestration]`에서 관리한다.
