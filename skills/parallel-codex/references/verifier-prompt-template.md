# Verifier Prompt Template

그룹 실행 완료 후 호환성 검증을 수행하는 검증 전담 Codex 프롬프트 구조.
Claude가 변수를 치환한 뒤 Codex에 전달한다.

## Template

```xml
<task>
## 목적
${GROUP_NAME} 그룹의 완료된 작업 브랜치들을 임시 통합하여 호환성을 검증한다.

## 작업 내용
1. 임시 검증 브랜치 생성: `${VERIFY_BRANCH}` (베이스: `${BASE_BRANCH}`)
2. 아래 작업 브랜치들을 순서대로 머지:
${TASK_BRANCHES}
3. 통합 상태에서 검증 실행
4. 실패 시 **개별 task 브랜치에서** 수정 (검증 브랜치가 아님)
5. 수정 후 검증 브랜치를 재구성하여 재검증
6. 검증 리포트 작성

## 검증 절차
1. `git checkout -b ${VERIFY_BRANCH} ${BASE_BRANCH}`
2. TASK_BRANCHES의 각 브랜치를 순서대로 머지: `git merge <branch> --no-edit`
3. 충돌 발생 시 양쪽 의도를 파악하여 양쪽 모두 보존하는 방향으로 해결
4. 해결 불가 시 리포트에 기록

## 검증 실패 시 수정 규칙
검증(lint/typecheck/test) 실패 시:
1. 실패 원인이 어느 task 브랜치의 코드인지 파악
2. 해당 task 브랜치의 워크트리에서 직접 수정 (`cd .worktrees/<group>/<task>` 후 수정).
   주의: 해당 브랜치가 워크트리에 체크아웃되어 있으므로 프로젝트 루트에서 `git checkout <branch>`를 하면 실패한다.
3. 워크트리에서 수정 커밋
4. 프로젝트 루트로 돌아와서 검증 브랜치를 삭제하고 재구성:
   - `git checkout ${BASE_BRANCH}` (삭제 전에 다른 브랜치로 전환해야 함)
   - `git branch -D ${VERIFY_BRANCH}`
   - `git checkout -b ${VERIFY_BRANCH} ${BASE_BRANCH}`
   - 모든 task 브랜치를 다시 머지
5. 재검증

이렇게 하면 수정이 개별 task 브랜치에 반영되어 verify 브랜치 재구성 시 포함된다.

## 완료 기준
- 모든 작업 브랜치가 검증 브랜치에 머지됨
- lint/typecheck/test 전부 통과
- 검증 리포트 작성 완료
</task>

<structured_output_contract>
검증 완료 후 반드시 `${VERIFY_REPORT_PATH}`에 리포트를 작성하라:

# Verify Report: ${GROUP_NAME}

## Summary
호환성 검증 요약 (2-3문장)

## Merged Branches
| Branch | Status | Conflicts |
|--------|--------|-----------|
| parallel/xxx | merged | none |

## Verification Result
- `lint`: PASS/FAIL
- `typecheck`: PASS/FAIL
- `test`: PASS/FAIL

## Fixes Applied
검증 실패로 개별 task 브랜치에서 수정한 내용. 없으면 "없음".
수정한 경우 어느 브랜치에서 수정했는지 명시.

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
- **수정은 반드시 개별 task 브랜치에서** 수행. 검증 브랜치에서 직접 수정 금지.
</verification_loop>

<action_safety>
- 머지와 검증 수정만 수행
- 기능 추가나 리팩터링 금지
- 검증 실패 수정은 최소 범위로
- 수정은 개별 task 브랜치에서만
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
| `VERIFY_BRANCH` | PIPELINE.md Verify Branch | 예: `temp/verify-a` |
| `BASE_BRANCH` | 이전 그룹의 검증 브랜치 또는 `main` | Group A는 `main` |
| `TASK_BRANCHES` | 해당 그룹의 **성공한** 작업 브랜치만 포함 (PIPELINE.md에서 `[FAILED]` 표시된 작업 제외) | 줄바꿈 구분. 예: `parallel/a1-db-schema\nparallel/a2-api-types` |
| `VERIFY_REPORT_PATH` | `.worktrees/VERIFY_REPORT_<GROUP>.md` | 예: `.worktrees/VERIFY_REPORT_A.md` |
| `VERIFICATION_COMMANDS` | 프로젝트 전용 테스트 명령 (`npm test`, `pytest` 등) | format/lint/typecheck는 위 `<verification_loop>` 텍스트에서 이미 처리됨. 이 변수에는 추가 테스트 명령만 기입. 없으면 빈 문자열. |

## 검증 Codex 실행 위치

검증 Codex는 **프로젝트 루트**에서 실행한다 (워크트리가 아님).
검증 브랜치를 직접 checkout하여 작업하고, 수정이 필요하면 개별 task 브랜치로 전환한다.
