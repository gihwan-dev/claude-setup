---
name: commter
description: >
  Add/improve JSDoc and inline comments for changed TS/JS code based on git diff.
  git diff 기준으로 변경된 TypeScript/JavaScript 코드에 필요한 주석과 JSDoc을 추가/개선한다.
  유지보수자 관점에서 의도, 제약, 부작용, 트레이드오프를 문서화하고,
  자명하거나 코드와 불일치한 코멘트를 제거해 가독성과 신뢰도를 높인다.
  코드 리뷰 준비, 신규 팀원 온보딩, 공개 API 문서화, 복잡 로직 설명 보강 요청에서 사용한다.
  트리거: "주석 추가", "JSDoc 작성", "코멘트 보강", "diff 기반 문서화", "주석 정리".
---

# Commter

변경된 코드만 빠르게 읽어 "필요한 설명"만 남기는 주석 보강 스킬이다.

## 핵심 원칙

- 코드를 번역하지 말고 판단 근거를 남긴다.
- 구현 상세보다 의도와 제약을 우선 설명한다.
- 주석 수를 늘리기보다, 잘못된 주석을 줄이는 것을 우선한다.
- 변경된 영역(`git diff`) 밖으로 불필요한 편집을 확장하지 않는다.

## 실행 절차

### 1) diff 범위를 고정한다

- 먼저 staged 변경을 확인한다.

```bash
git diff --cached --name-only --diff-filter=AM -- '*.ts' '*.tsx' '*.js' '*.jsx'
git diff --cached -U0 -- '*.ts' '*.tsx' '*.js' '*.jsx'
```

- staged가 비어 있으면 working tree diff를 사용한다.

```bash
git diff --name-only --diff-filter=AM -- '*.ts' '*.tsx' '*.js' '*.jsx'
git diff -U0 -- '*.ts' '*.tsx' '*.js' '*.jsx'
```

- 브랜치 전체 점검이 필요하면 merge-base 기준을 사용한다.

```bash
BASE_REF=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/@@')
[ -z "$BASE_REF" ] && BASE_REF="origin/main"
MERGE_BASE=$(git merge-base HEAD "$BASE_REF" 2>/dev/null || true)
[ -n "$MERGE_BASE" ] && git diff -U0 "$MERGE_BASE"...HEAD -- '*.ts' '*.tsx' '*.js' '*.jsx'
```

### 2) 주석 후보를 식별한다

아래 조건 중 하나라도 만족하면 "주석 후보"로 분류한다.

- 새로 추가/수정된 export 함수, 클래스, 훅, 컴포넌트.
- 비즈니스 규칙 또는 외부 정책(정산, 권한, 계약 제약) 반영 코드.
- 순서 의존 로직(호출 순서가 바뀌면 깨지는 코드).
- 예외 처리와 fallback이 비직관적인 코드.
- 성능 트레이드오프(캐시, 배치, debounce, memoization).
- 매직 넘버, 정규식, 경계값 처리처럼 의도를 추정하기 어려운 코드.

### 3) 주석 종류를 선택한다

- 사용자(호출자)가 읽어야 하는 정보면 `/** JSDoc */`를 사용한다.
- 구현 경계/주의사항이면 `//` 라인 코멘트를 사용한다.
- 긴 설명이 필요해도 함수 내부에서는 여러 줄 `//`을 우선한다.
- 함수 호출 파라미터 의미가 불명확하면 파라미터 이름 코멘트를 고려한다.

```ts
someFunction(obviousArg, /* shouldRetry= */ true, /* timeoutMs= */ 5000);
```

### 4) 주석을 작성한다

작성 시 반드시 아래를 지킨다.

- "무엇"보다 "왜"를 먼저 쓴다.
- 한 주석에 판단 포인트를 1개만 담는다.
- 이름/타입을 반복 설명하지 않는다.
- TS 파일(`.ts`, `.tsx`)에서는 타입 정보가 코드에 이미 있으면 JSDoc 타입 선언을 생략한다.
- JS 파일(`.js`, `.jsx`)에서는 `@param`, `@returns` 타입 표기를 적극 사용한다.
- 기존 주석 언어(한국어/영어)를 파일 기준으로 맞춘다.

### 5) 안 좋은 주석을 정리한다

아래 패턴은 제거 또는 수정한다.

- 코드와 동일한 문장을 반복하는 주석.
- 리팩토링 이후 의미가 틀어진 stale 주석.
- 근거 없는 TODO/FIXME 주석.
- 길지만 실행 결정에 도움을 주지 않는 서술.

### 6) 품질 게이트를 통과시킨다

최종 점검 체크리스트:

- 변경된 공개 API에 최소한의 사용 맥락이 설명되어 있는가?
- 예외/부작용/순서 의존성 설명이 필요한 곳에만 있는가?
- 주석이 현재 코드와 모순되지 않는가?
- 주석 없이도 읽히는 부분에 불필요한 문장이 추가되지 않았는가?
- 주석이 팀 내 기존 스타일과 일관적인가?

## 출력 규칙

- 결과 보고 시 "추가", "수정", "삭제" 주석 수를 구분해 요약한다.
- 각 변경은 파일 경로와 함께 이유 1줄을 남긴다.
- 리스크가 남으면 `확인 필요`로 표시한다.

## 참조 파일 로드 규칙

- 근거 기반 원칙 확인: `${SKILL_DIR}/references/comment-research.md`
- 빠른 작성 템플릿 사용: `${SKILL_DIR}/references/comment-templates.md`
