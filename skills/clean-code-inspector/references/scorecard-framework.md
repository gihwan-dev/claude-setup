# React Clean Code Scorecard Framework

이 파일은 clean-code-inspector 에이전트가 참조하는 정량적 평가 프레임워크입니다.

## 1. 구조적 복잡도 (Structural Complexity)
- **순환 복잡도 (CC)**: 모든 분기점(if, else, &&, ||, ?:, ??, switch case, catch) 개수.
  - JSX 내 삼항 중첩은 곱셈적 복잡도로 계산.
  - 1-10: 양호 | 11-20: 주의 | 21-50: 위험 | >50: 불가
- **인지 복잡도**: 중첩 깊이(max-depth > 3-4 주의), 훅 의존성 배열 크기(>5 위험), 콜백 중첩.

## 2. 컴포넌트 책임 점수 (CRS)
- CRS = w1(LoC) + w2(CC) + w3(SC) + w4(DC)
- **LoC**: >200줄 위험, <100줄 권장
- **State Count (SC)**: useState/useReducer 수. 0-3: 건강 | 4-6: 주의 | >6: 위험
- **Dependency Count (DC)**: import 문 수. >10: 주의
- CRS 결과: <50(Atomic) | 50-100(Boundary) | >100(God Component - Refactor Alert)

## 3. 응집도와 결합도 (Cohesion & Coupling)
- **LCOM4 (React Hook Cohesion)**: 내부 상태(useState)와 메서드(Effect/Callback/Handler)의 연결 그래프.
  - 비연결 부분그래프 수 = LCOM4. 1: 양호 | >1: 분리 필요
  - LCOM4 > 1이면 각 비연결 그래프가 커스텀 훅 후보.
- **Props Drilling**: 원점에서 소비처까지 전달 깊이. >3: 불필요한 결합.

## 4. 컴포넌트 인터페이스 품질
- **Props 개수**: <5(이상적) | 5-7(허용) | >7(Code Smell)
- **Boolean Props**: 다수의 boolean은 Enum/Union 타입으로 통합 권장. 상호 배타적 boolean 조합 확인.
- **명명 규칙**: Props 이벤트 핸들러 `on*` 접두사, 구현 핸들러 `handle*` 접두사. boolean은 `is*/has*/should*`.

## 5. 정적 분석 지표 (ESLint)
- `react-hooks/rules-of-hooks`: 0 위반
- `max-lines-per-function`: < 100
- `no-console`: 0 위반
- `TypeScript noImplicitAny`: 0%

## 6. 테스트 가능성
- 비즈니스 로직 훅/유틸리티의 Mutation Score > 80% 목표.
- 사이드 이펙트 격리 수준, 컴포넌트 독립 테스트 가능 여부.

## 7. 상태 아키텍처
- **State Colocation**: 상태가 사용되는 곳과 얼마나 가까운가.
- **Global State Density**: 전역 상태가 정말 전역이어야 하는가.

## 8. 종합 스코어카드 형식

| 카테고리 | 평가 항목 | 측정/관찰 값 | 상태 (양호/주의/위험) | 비고 |
|---------|---------|------------|-------------------|------|
| 복잡도 | 순환 복잡도 (CC) | ... | ... | ... |
| 복잡도 | 인지 복잡도 | ... | ... | ... |
| 규모 | 라인 수 (LoC) | ... | ... | ... |
| 책임 | CRS | ... | ... | ... |
| 인터페이스 | Props 개수 | ... | ... | ... |
| 인터페이스 | Boolean Props | ... | ... | ... |
| 인터페이스 | 명명 규칙 | ... | ... | ... |
| 결합도 | Props 드릴링 깊이 | ... | ... | ... |
| 응집도 | LCOM4 (추정) | ... | ... | ... |
| 상태 | State Colocation | ... | ... | ... |
| 상태 | Global State Density | ... | ... | ... |
| 위생 | ESLint 위반 | ... | ... | ... |
| 테스트 | 테스트 가능성 | ... | ... | ... |

## 9. 자동 수정 가능 기준

이슈가 아래 세 조건을 **모두** 충족하면 자동 수정 가능:
1. **결정적 변환**: 정확히 하나의 올바른 수정 방법만 존재 (설계 판단 불필요)
2. **로컬 범위**: 수정이 해당 파일 내에서 완결 (크로스 파일 영향 없음)
3. **동작 보존**: 런타임 동작이 변하지 않음 (순수 리팩토링)

자동 수정 가능 예시: 명명 규칙 위반, unused import, console.log, 추론 가능한 explicit any
자동 수정 불가 예시: 컴포넌트 분할, 훅 추출, boolean→enum, 상태 아키텍처 변경, 메모이제이션 변경
