# 코멘트 템플릿

## 1) TS export 함수용 JSDoc (타입 중복 최소화)

```ts
/**
 * 사용자 입력을 정규화하고 정책 우선순위에 따라 최종 설정을 만든다.
 * CLI 인자가 있으면 ENV/기본값보다 우선한다.
 *
 * @param input 원본 입력 객체.
 * @returns 실행 가능한 설정 객체.
 * @throws 설정이 상호 충돌하면 오류를 던진다.
 */
export function buildRuntimeConfig(input: RawConfig): RuntimeConfig {
  // ...
}
```

## 2) JS 함수용 JSDoc (타입 표기 포함)

```js
/**
 * Build a retry plan from network error metadata.
 * @param {{code: string, attempt: number}} errorInfo Retry input.
 * @returns {{shouldRetry: boolean, waitMs: number}} Retry decision.
 */
function createRetryPlan(errorInfo) {
  // ...
}
```

## 3) 분기/예외 처리용 인라인 코멘트

```ts
// 캐시 미스 직후 재시도하지 않는다.
// 동일 이벤트 루프에서 즉시 재시도하면 외부 API rate limit을 더 자주 유발한다.
if (!cached && justFailed) {
  return BACKOFF_REQUIRED;
}
```

## 4) 순서 의존 로직 코멘트

```ts
// 순서 중요: sanitize -> validate -> persist
// validate를 먼저 호출하면 sanitize에서 제거되는 필드 때문에 false negative가 발생한다.
const sanitized = sanitize(payload);
validate(sanitized);
persist(sanitized);
```

## 5) 호출부 파라미터 이름 코멘트

```ts
scheduleJob(userId, /* shouldNotify= */ false, /* delayMs= */ 30_000);
```

## 안티 패턴 빠른 점검

- 코드와 동일 문장 반복: 삭제
- "임시" 설명만 있고 근거 없음: 수정
- 현재 로직과 불일치: 즉시 갱신
- 문서 길이만 길고 결정 근거 없음: 축약
