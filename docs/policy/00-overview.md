## 핵심 목표

메인 스레드는 전략과 의사결정에 집중한다.
실행 작업은 필요한 경우에만 위임하고, 간결한 요약만 반환받는다.

## 오케스트레이션 기본 규칙

- 작업 복잡도와 영향 범위를 먼저 평가한다.
- 기본은 메인 스레드 단일 실행(single-agent)과 직접 수정이다.
- 병렬 read-only 작업은 분명한 이점이 있을 때만 사용한다.
- delegated lane의 code diff는 단일 writer만 허용하고 writable projection은 `worker`만 사용한다.
- 서브 에이전트 결과는 하나의 의사결정 가능한 요약으로 통합한다.

## 역할-실행 매핑

| 작업 성격 | 워크플로우 역할 | 보조 수단 |
|-----------|----------------|-----------|
| 코드 탐색/분석 | explorer | — |
| React UI 구현 | main-thread | 관련 skill/레퍼런스만 사용 |
| 테스트 작성 | main-thread | 관련 skill/레퍼런스만 사용 |
| 코드 품질 리뷰 | reviewer | code-reviewer |
| 아키텍처 리뷰 | reviewer | architecture-reviewer |
| 리팩터링 실행 | main-thread | 관련 skill/레퍼런스만 사용 |
| TypeScript 타입 설계 | main-thread | 관련 skill/레퍼런스만 사용 |
| 인터페이스 품질 점검 | reviewer | interface-inspector |
| 정량 복잡도 분석 | reviewer | complexity-analyst |
| 공통 모듈 구조 분해 계획(구현 전) | reviewer | structure-planner |
| 공통 구조 게이트 리뷰(구현 후) | reviewer | module-structure-gatekeeper |
| React 구조 게이트 리뷰(구현 후) | reviewer | frontend-structure-gatekeeper |
| 장기 작업 설계/실행 | main-thread | `design-task`, `implement-task` |
| Storybook/디자인 검증 | main-thread | 관련 skill/레퍼런스만 사용 |
| 프롬프트 최적화 | main-thread | 관련 skill/레퍼런스만 사용 |
| 검증/결과 분석 | verifier | — |
