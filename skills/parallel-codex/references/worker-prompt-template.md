# Worker Prompt Template

parallel-codex 스킬이 각 워크트리의 Codex 워커에게 전달하는 프롬프트 구조.
Claude가 변수를 치환한 뒤 Codex에 전달한다.

## Template

```xml
<task>
## 목적
${TASK_PURPOSE}

## 작업 범위
이 워크트리에서 수정할 파일/디렉토리:
${TASK_SCOPE}

수정하지 않을 파일:
${OUT_OF_SCOPE}

## 참고 컨텍스트
${REFERENCE_CONTEXT}

## Goal
${TASK_GOAL}

## 완료 기준
${DONE_CRITERIA}
</task>

<structured_output_contract>
작업 완료 후 반드시 아래 마크다운 구조로 출력하라:

## Changed Files
| File | Action | Description |
|------|--------|-------------|
(Action: created / modified / deleted)

## Work Summary
수행한 작업 2-3문장.

## Decisions Made
프롬프트에 명시되지 않았던 세부 결정과 근거. 없으면 "없음".

## Self Review
- 정확성: 요구사항 충족 여부
- 엣지 케이스: 누락된 경계 조건
- 부작용: 다른 코드에 미치는 영향

## Verification Result
- `format`: PASS/FAIL
- `lint`: PASS/FAIL
- `typecheck`: PASS/FAIL
- `test`: PASS/FAIL
(FAIL이면 에러 요약 포함)
</structured_output_contract>

<verification_loop>
완료 전 반드시:
- 프로젝트의 포매터를 찾아 실행하여 변경 파일 포매팅
- 프로젝트의 린터를 찾아 실행하여 변경 파일 검증. 에러가 있으면 수정
- 프로젝트의 타입체커를 찾아 실행. 에러가 있으면 수정
- ${VERIFICATION_COMMANDS}
- 모든 완료 기준 충족 여부 확인
- 하나라도 실패하면 수정 후 재검증. 전부 통과할 때까지 반복
</verification_loop>

<action_safety>
- 이 작업 범위 내 변경만 수행
- 범위 밖 파일 수정 금지
- 무관한 리팩터링 금지
- 다른 병렬 작업의 영역을 침범하지 않는다
</action_safety>

<default_follow_through_policy>
가장 합리적인 해석을 기본으로 삼고 계속 진행.
정보 부재가 잘못된 동작을 야기할 때만 멈춘다.
</default_follow_through_policy>
```

## 변수 치환 규칙

| 변수 | 출처 | 비고 |
|------|------|------|
| `TASK_PURPOSE` | 작업 설명 | 1-2문장 |
| `TASK_SCOPE` | 작업의 관련 파일/디렉토리 목록 | 줄바꿈 구분 |
| `OUT_OF_SCOPE` | 같은 그룹 내 다른 병렬 작업이 담당하는 파일 | 충돌 방지 |
| `REFERENCE_CONTEXT` | 이전 그룹 머지 리포트 압축 (있을 경우) | 500토큰 이내 목표 |
| `TASK_GOAL` | 작업의 구체적 목표 | 행동 가능한 형태 |
| `DONE_CRITERIA` | 완료 판단 기준 | 체크리스트 형태 |
| `VERIFICATION_COMMANDS` | 프로젝트 전용 테스트 명령 (`npm test`, `pytest` 등) | format/lint/typecheck는 위 `<verification_loop>` 텍스트에서 이미 처리됨. 이 변수에는 추가 테스트 명령만 기입. 없으면 빈 문자열. |

### REFERENCE_CONTEXT 구성

- **Group A 작업**: 비어 있음 (첫 그룹이므로 이전 컨텍스트 없음)
- **Group B+ 작업**: 직전 그룹의 검증 리포트에서 다음을 추출:
  1. 변경된 파일 요약
  2. 다음 그룹을 위한 상태 요약
  3. 현재 작업과 관련된 결정 사항

전체 REFERENCE_CONTEXT가 500토큰을 초과하면 오래된 리포트를 줄인다.
