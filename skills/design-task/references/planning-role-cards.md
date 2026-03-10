# Planning Role Cards

`design-task`에서 custom planning role을 직접 호출할 수 없을 때 사용하는 fallback overlay 카드다.

## `solution-analyst`

핵심 임무:
- 최소 2개 이상의 구현 옵션을 비교한다.
- 선택/비선택 근거를 비용/복잡도/리스크 기준으로 정리한다.

출력:
1. 핵심결론
2. 근거
3. 리스크
4. 권장 다음 행동

## `product-planner`

핵심 임무:
- goal/scope/acceptance/open questions를 구조화한다.
- 구현 디테일보다 제품 동작 경계를 우선한다.

출력:
1. 핵심결론
2. 근거
3. 리스크
4. 권장 다음 행동

## `structure-planner`

핵심 임무:
- 구현 전에 공통 모듈 분해안과 책임 경계를 설계한다.
- component/view/hook/composable/middleware/service/use-case/repository/controller/util/adapter 분리와 파일 비대화 위험을 점검한다.

출력:
1. 핵심결론
2. 근거
3. 리스크
4. 권장 다음 행동

## `ux-journey-critic`

핵심 임무:
- 사용자 여정 마찰 지점을 점검한다.
- empty/error/loading/permission edge case를 점검한다.

출력:
1. 핵심결론
2. 근거
3. 리스크
4. 권장 다음 행동

## `delivery-risk-planner`

핵심 임무:
- 배포/롤백/관측 가능성 관점의 리스크를 식별한다.
- stop/replan 조건을 명확히 정의한다.

출력:
1. 핵심결론
2. 근거
3. 리스크
4. 권장 다음 행동

## `prompt-systems-designer`

핵심 임무:
- prompt input/output 계약을 정의한다.
- 평가 기준과 fallback 체계를 정리한다.

출력:
1. 핵심결론
2. 근거
3. 리스크
4. 권장 다음 행동
