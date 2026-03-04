# Korean Naming Playbook

## 목적

원문 식별자를 삭제하지 않고, 이해를 돕는 한국어 별칭을 제공한다.

## 별칭 작성 규칙

- 원문을 항상 함께 표기한다. 예: `calculateAdjustedPrice`(보정가격 계산)
- 기능 의미를 보존하고, 구현 방식은 이름에 넣지 않는다.
- 약어는 가능하면 풀어서 해석한다. 예: `ctx` -> 실행 문맥
- 동사+목적어 구조를 유지한다. 예: `fetchUserProfile` -> 사용자 프로필 조회

## 권장 번역 패턴

| 패턴 | 예시 원문 | 권장 별칭 |
| --- | --- | --- |
| `get*` | `getSession` | 세션 조회 |
| `fetch*` | `fetchOrders` | 주문 목록 가져오기 |
| `load*` | `loadConfig` | 설정 불러오기 |
| `build*` | `buildPayload` | 페이로드 구성 |
| `create*` | `createInvoice` | 인보이스 생성 |
| `update*` | `updateProfile` | 프로필 갱신 |
| `delete*` | `deleteComment` | 댓글 삭제 |
| `validate*` | `validateInput` | 입력값 검증 |
| `handle*` | `handleSubmit` | 제출 처리 |
| `is*`/`has*` | `isExpired` | 만료 여부 |

## 피해야 할 번역

- 의미가 넓은 단어만 단독 사용. 예: `processData` -> 데이터 처리(맥락 없음)
- 구현 세부 포함. 예: `sortByQuickSort` -> 퀵소트로 정렬
- 비속어/팀 내부 은어 사용

## 설명용 표 템플릿

```md
| 원문 | 한국어 별칭 | 역할 | 비고 |
| --- | --- | --- | --- |
| `calculateFee` | 수수료 계산 | 주문 수수료 산출 | 세율 정책 의존 |
```
