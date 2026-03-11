# Plan Continuity Rules

기존 task를 재사용할지, 새 task를 만들지 결정할 때만 이 파일을 읽는다.
기본 원칙은 continuity gate다. 재사용은 예외고 새 task 생성이 기본이다.

## Comparison Matrix

| Signal | Reuse existing | Create new |
| --- | --- | --- |
| Goal | 동일한 사용자 결과 | 다르면 create new task when goal differs |
| Success criteria | 동일 | 다르면 새 task |
| Primary change boundary | 동일 모듈/흐름 | 다르면 새 task |
| Task type | 동일한 `feature`/`bugfix`/`refactor`/`prototype` | 다르면 새 task |
| Quality preflight verdict | 동일 | 다르면 새 task |
| Candidate count | 정확히 1개 | 2개 이상이면 ambiguous case |

## Decision Rules

1. 사용자가 path를 직접 지정하면 해당 path를 사용한다.
2. continuation 표현이 없더라도 관련 task가 보이면 continuity gate를 적용한다.
3. 모든 핵심 신호가 같은 단일 후보가 있을 때만 `reuse-existing`를 선택한다.
4. 하나라도 다르면 `create-new`를 선택한다.
5. 후보가 2개 이상이면 자동 선택하지 않고 `Need user decision`에 남긴다.

## Examples

### Reuse existing

- 현재 요청이 기존 목표를 더 잘게 쪼개거나 acceptance criteria만 구체화한다.
- quality preflight verdict와 주요 변경 경계가 유지된다.

### Create new

- 목표는 비슷하지만 성공 기준이 다르다.
- 같은 도메인이라도 변경 경계가 API에서 UI로 바뀐다.
- 기존 task는 refactor인데 새 요청은 bugfix다.

### Ambiguous case

- 관련 task가 2개 이상이고 둘 다 미완료다.
- 비교 근거는 `Task continuity`에 기록하고 사용자 확인 전까지 자동 재사용하지 않는다.
