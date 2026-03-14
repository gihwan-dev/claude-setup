# Decision Catalog

`bootstrap-project-rules`가 implementation rules를 고정할 때 사용하는 분류표다.
탐색으로 확정 가능한 사실을 먼저 채우고, 정말 필요한 항목만 질문한다.

## Locked now

지금 결정하지 않으면 구현 surface, 디렉터리 구조, validation path가 흔들리는 항목이다.

- runtime / language (`node`, `python`, `typescript`)
- framework / app shell (`next`, `react`, `fastapi`, `django`, `cli`)
- package manager / workspace model
- lint / format / typecheck / test stack
- 기본 state/data fetching 전략
- 기본 styling / design-system 방향
- module boundary / folder ownership
- validation commands / definition of done

## Deferred

feature slice가 구체화되기 전까지는 최적 판단이 어려운 선택 라이브러리다.
문서에는 `Decision`, `Why deferred`, `Trigger`, `Needed input`을 함께 적는다.

- rich table / chart / editor / animation libraries
- analytics / monitoring / experiment SDK
- form helper / cache helper / image helper 등 optional utility
- specific auth adapter / payment SDK / vendor SDK

## Banned/Avoid

현재 architecture, validation contract, maintenance 비용과 충돌하는 선택지다.

- 기존 package manager와 충돌하는 tooling
- 동일 책임을 중복하는 state/data layer
- design system과 충돌하는 styling stack 이중화
- validation command를 약화시키는 bypass 패턴

## Question Filter

아래 둘 중 하나를 만족할 때만 질문한다.

- `Locked now`인데 탐색 결과만으로 확정 불가
- `Deferred`로 미루면 현재 blocker를 해소할 수 없음

질문은 1~3개로 제한하고, 답변에 따라 문서가 실제로 달라지는 항목만 묻는다.
