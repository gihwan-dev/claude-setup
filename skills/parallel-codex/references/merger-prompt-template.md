# Merger Prompt Template

그룹 간 전이 시 stage 브랜치로 통합하는 머지 전담 Codex 프롬프트 구조.
Claude가 변수를 치환한 뒤 Codex에 전달한다.

## Template

```xml
<task>
## 목적
${GROUP_NAME} 그룹의 완료된 작업 브랜치들을 stage 브랜치로 통합한다.

## 작업 내용
1. stage 브랜치 생성: `${STAGE_BRANCH}` (베이스: `${BASE_BRANCH}`)
2. 아래 작업 브랜치들을 순서대로 머지:
${TASK_BRANCHES}
3. 통합 후 검증 실행
4. 실패 시 수정
5. 머지 리포트 작성

## 머지 절차
1. git checkout -b ${STAGE_BRANCH} ${BASE_BRANCH}
2. 각 브랜치: git merge parallel/&lt;task-name&gt; --no-edit
3. 충돌 발생 시 양쪽 의도를 파악하여 양쪽 모두 보존하는 방향으로 해결
4. 해결 불가 시 리포트에 기록

## 완료 기준
- 모든 작업 브랜치가 stage 브랜치에 머지됨
- lint/typecheck/test 전부 통과
- 머지 리포트 작성 완료
</task>

<structured_output_contract>
머지 완료 후 반드시 `${MERGE_REPORT_PATH}`에 리포트를 작성하라:

# Merge Report: ${GROUP_NAME}

## Summary
통합 작업 요약 (2-3문장)

## Merged Branches
| Branch | Status | Conflicts |
|--------|--------|-----------|
| parallel/xxx | merged | none |

## Verification Result
- `lint`: PASS/FAIL
- `typecheck`: PASS/FAIL
- `test`: PASS/FAIL

## Fixes Applied
통합 후 검증 실패로 수정한 내용. 없으면 "없음".

## State Summary for Next Group
다음 그룹이 알아야 할 현재 코드베이스 상태:
- 새로 생성된 모듈/파일
- 변경된 API/인터페이스
- 설정/환경 변수 변경
- 주요 구조적 변화
</structured_output_contract>

<verification_loop>
머지 완료 후 반드시:
- 프로젝트의 포매터를 찾아 실행하여 변경 파일 포매팅
- 프로젝트의 린터를 찾아 실행하여 변경 파일 검증. 에러가 있으면 수정
- 프로젝트의 타입체커를 찾아 실행. 에러가 있으면 수정
- ${VERIFICATION_COMMANDS}
- 하나라도 실패하면 수정 후 재검증. 전부 통과할 때까지 반복
</verification_loop>

<action_safety>
- 머지와 검증 수정만 수행
- 기능 추가나 리팩터링 금지
- 검증 실패 수정은 최소 범위로
</action_safety>

<default_follow_through_policy>
가장 합리적인 해석을 기본으로 삼고 계속 진행.
정보 부재가 잘못된 동작을 야기할 때만 멈춘다.
</default_follow_through_policy>
```

## 변수 치환 규칙

| 변수 | 출처 | 비고 |
|------|------|------|
| `GROUP_NAME` | PIPELINE.md 그룹 이름 | 예: `Group A` |
| `STAGE_BRANCH` | PIPELINE.md Stage Branch | 예: `stage/group-a` |
| `BASE_BRANCH` | 이전 그룹의 stage 브랜치 또는 `main` | Group A는 `main` |
| `TASK_BRANCHES` | 해당 그룹의 완료된 작업 브랜치 목록 | 줄바꿈 구분 |
| `MERGE_REPORT_PATH` | `.worktrees/MERGE_REPORT_<GROUP>.md` | 예: `.worktrees/MERGE_REPORT_A.md` |
| `VERIFICATION_COMMANDS` | 프로젝트의 검증 명령어 | 타입체크, 테스트 등 |

## 머지 Codex 실행 위치

머지 Codex는 **프로젝트 루트**에서 실행한다 (워크트리가 아님).
stage 브랜치를 직접 checkout하여 작업한다.
