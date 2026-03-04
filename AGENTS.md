<!-- AUTO-GENERATED from INSTRUCTIONS.md. Do not edit directly. -->
<!-- Run: ./scripts/sync-instructions.sh -->

# 멀티 에이전트 오케스트레이션 정책

## 핵심 목표

메인 스레드는 전략과 의사결정에 집중한다.
실행 작업은 서브 에이전트에 위임하고, 간결한 요약만 반환받는다.

## 오케스트레이션 기본 규칙

- 작업 복잡도와 영향 범위를 먼저 평가한다.
- 단순 단일 파일 수정은 단일 에이전트로 처리한다.
- 탐색, 분석, 테스트, 광범위 스캔은 서브 에이전트를 활용한다.
- 읽기 전용 작업은 병렬 실행을 허용한다.
- 코드 수정은 단일 작성자(single-writer) 규칙을 적용한다.
- 서브 에이전트 결과는 하나의 의사결정 가능한 요약으로 통합한다.

## 단일 작성자 규칙 (필수)

- 코드/테스트/설정/문서 변경은 정확히 하나의 implementer가 수행한다.
- 메인 스레드(orchestrator)는 직접 파일을 수정하지 않는다.
- 변경이 발생했는데 implementer 위임 없이 이루어졌다면 무효 실행으로 간주한다.

## 필수 실행 흐름

1. **탐색 (explorer)**: 증거 수집이 필요하면 읽기 전용 탐색을 먼저 수행한다.
2. **의사결정 (orchestrator)**: 메인 스레드에서 방향을 확정한다.
3. **구현 (implementer)**: 정확히 하나의 구현 에이전트가 변경을 적용한다.
4. **검증 (verifier)**: 변경 후 검증 요약을 수행한다 (또는 implementer가 검증 후 요약).
5. **통합 (orchestrator)**: 메인 스레드가 모든 서브 에이전트 결과를 최종 응답으로 통합한다.

## 워크플로우 역할

| 역할 | 접근 권한 | 책임 |
|------|----------|------|
| orchestrator | 전략만 | 계획, 라우팅, 최종 의사결정 |
| implementer | 읽기/쓰기 | 코드 변경의 유일한 수행자 |
| explorer | 읽기 전용 | 레포지토리 탐색 및 증거 수집 |
| reviewer | 읽기 전용 | 코드 품질, 아키텍처 리뷰 |
| verifier | 읽기 전용 | 검증/테스트 결과 분석 |

## 역할-에이전트 매핑

| 작업 성격 | 워크플로우 역할 | 도메인 에이전트 |
|-----------|----------------|----------------|
| 코드 탐색/분석 | explorer | — |
| React UI 구현 | implementer | frontend-developer |
| 테스트 작성 | implementer | qa-engineer |
| 코드 품질 리뷰 | reviewer | code-reviewer |
| 아키텍처 리뷰 | reviewer | architect-review |
| 리팩토링 실행 | implementer | refactoring-expert |
| TypeScript 타입 설계 | implementer | typescript-pro |
| 인터페이스 품질 점검 | reviewer | interface-inspector |
| 정량 복잡도 분석 | reviewer | complexity-analyst |
| 스펙 문서 작성 | implementer | spec-writer |
| Storybook/디자인 검증 | implementer | storybook-specialist |
| 마일스톤 관리 | orchestrator | project-planner |
| 프롬프트 최적화 | implementer | prompt-engineer |
| 검증/결과 분석 | verifier | — |

## 자동 리뷰 트리거

- 코드 파일이 변경되면 `code-reviewer` 에이전트를 실행한다.
- 아래 조건 중 하나라도 충족하면 `architect-review` 에이전트를 실행한다:
  - 변경 파일 7개 이상
  - 모듈/패키지 경계 2개 이상 변경
  - public surface 변경 (export, entrypoint, 핵심 설정)

## 서브 에이전트 응답 가이드라인

서브 에이전트는 간결하고 의사결정 가능한 요약을 우선한다.

**필수 항목:**
1. 핵심결론
2. 근거 (`file:line` 또는 `error-id`)

**선택 항목 (관련 시):**
3. 리스크
4. 권장 다음 행동
5. 추가 확인 필요 (불확실성/차단 요인)

원문 출력이 필요하면 최소 발췌만 포함하고 소스 경로를 명시한다.

## 에이전트 정의 파일

각 에이전트의 상세 정의는 `agents/*.md` 파일을 참조한다.
에이전트 파일에는 `role` 필드로 워크플로우 역할이 명시되어 있다.

## 언어 및 스타일

- 설명은 기본적으로 한국어를 사용한다.
- 코드 식별자, 명령어, 로그는 원어를 유지한다.
