# Worker Prompt Template

parallel-codex 스킬이 각 워크트리의 Codex 워커에게 전달하는 프롬프트 구조.
Claude가 변수를 치환한 뒤 사용자 승인을 거쳐 Codex에 전달한다.

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

## Goal
${TASK_GOAL}

## 완료 기준
${DONE_CRITERIA}
</task>

<structured_output_contract>
작업 완료 후 반드시:
1. 변경된 파일 목록 (파일 경로 + 변경 내용 요약)
2. 수행한 작업 요약 (2-3문장)
3. 구현 결정 사항 (WHAT을 HOW로 구체화한 결정과 근거)
4. 셀프 리뷰 결과:
   - 정확성: 요구사항 충족 여부
   - 엣지 케이스: 누락된 경계 조건
   - 부작용: 다른 코드에 미치는 영향
5. 검증 결과 (명령어별 PASS/FAIL)
</structured_output_contract>

<verification_loop>
완료 전 반드시:
- 실행: ${VERIFICATION_COMMANDS}
- 모든 완료 기준 충족 여부 확인
- 검증 실패 시 수정 후 재검증. 최대 3회 반복
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
| `TASK_PURPOSE` | 사용자 작업 설명 또는 BRIEF.md Phase "Purpose" | 1-2문장 |
| `TASK_SCOPE` | 작업의 관련 파일/디렉토리 목록 | 줄바꿈 구분 |
| `OUT_OF_SCOPE` | 다른 병렬 작업이 담당하는 파일 | 충돌 방지 |
| `TASK_GOAL` | 작업의 구체적 목표 | 행동 가능한 형태 |
| `DONE_CRITERIA` | 완료 판단 기준 | 체크리스트 형태 |
| `VERIFICATION_COMMANDS` | 검증 명령어 | 타입체크, 테스트 등 |

## 예시: 채워진 프롬프트

```xml
<task>
## 목적
DataGrid 옵션 객체를 정규화하여 내부적으로 일관된 형태로 변환하는 로직을 구현한다.

## 작업 범위
이 워크트리에서 수정할 파일/디렉토리:
- src/options/normalize.ts
- src/options/types.ts
- src/options/__tests__/normalize.test.ts

수정하지 않을 파일:
- src/columns/ (다른 병렬 작업 담당)
- src/query/ (후속 작업 담당)

## Goal
normalizeOptions() 함수가 사용자 입력 옵션을 내부 타입으로 변환하고,
기본값 채우기와 유효성 검증을 수행하도록 구현한다.

## 완료 기준
- normalizeOptions()가 모든 옵션 필드에 기본값 적용
- 유효하지 않은 옵션에 대해 명확한 에러 메시지
- 단위 테스트 5개 이상 (정상, 부분 입력, 잘못된 입력, 기본값, 엣지 케이스)
</task>

<structured_output_contract>
작업 완료 후 반드시:
1. 변경된 파일 목록 (파일 경로 + 변경 내용 요약)
2. 수행한 작업 요약 (2-3문장)
3. 구현 결정 사항
4. 셀프 리뷰 결과
5. 검증 결과
</structured_output_contract>

<verification_loop>
완료 전 반드시:
- 실행: npm run typecheck && npm run test -- --grep "normalize"
- 모든 완료 기준 충족 여부 확인
- 검증 실패 시 수정 후 재검증. 최대 3회 반복
</verification_loop>

<action_safety>
- 이 작업 범위 내 변경만 수행
- 범위 밖 파일 수정 금지
- 무관한 리팩터링 금지
- 다른 병렬 작업의 영역을 침범하지 않는다
</action_safety>
```
