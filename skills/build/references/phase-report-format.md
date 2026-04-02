# Phase Report Format

Codex가 매 페이즈 완료 후 작성하는 보고서 명세.
파일 경로: `tasks/<slug>/PHASE_REPORT_<NN>.md` (NN은 01, 02, ...).

이 포맷은 Codex 프롬프트의 `structured_output_contract`에서 강제된다.
Claude는 이 보고서를 읽고 다음 페이즈의 프롬프트를 구성한다.

## Format

```markdown
# Phase Report: Phase N - <Name>

## Summary
수행한 작업 2-3문장. 무엇을 왜 했는지 간결하게.

## Files Changed
| File | Action | Description |
|------|--------|-------------|
| src/foo/bar.ts | created | X 기능을 위한 새 컴포넌트 |
| src/foo/baz.ts | modified | Y 통합 추가 |
| src/foo/old.ts | deleted | bar.ts로 대체 |

## Decisions Made
구현 과정에서 내린 결정. BRIEF.md에 없던 세부 결정만 기록.
- A 대신 B 방식 선택: <근거>
- 라이브러리 X 사용: <근거>

## Verification Result
검증 명령어 실행 결과.
- `npm run typecheck`: PASS
- `npm run test`: PASS (14/14)
- `npm run lint`: PASS

## Impact on Future Phases
다음 페이즈가 반드시 알아야 할 사항.
- X가 이제 Y에 의존한다
- API 계약이 <파일 경로>에 정의되어 있다
- 환경 변수 FOO_BAR 설정 필요

## Open Issues
미해결 사항. 없으면 "없음"으로 기록.
- [severity: minor] 기존 테스트 하나가 flaky — 이 페이즈와 무관하나 발견
- [severity: major] 이전 Phase 1의 jwt.ts에서 토큰 갱신 로직 누락 발견
```

## 작성 규칙

1. **Summary**: 2-3문장 이내. "X를 Y하기 위해 Z했다" 형식.
2. **Files Changed**: 테이블 필수. Action은 `created`, `modified`, `deleted` 중 하나.
3. **Decisions Made**: BRIEF.md에 이미 명시된 결정은 반복하지 않는다. 구현 중 새로 내린 결정만.
4. **Verification Result**: 모든 검증 명령어의 결과를 PASS/FAIL로 기록. FAIL인 경우 에러 요약 포함.
5. **Impact on Future Phases**: 빈 값 금지. 영향이 없으면 "이 페이즈는 독립적이다. 특별한 영향 없음." 기록.
6. **Open Issues**: 심각도 태그 필수 (`minor`, `major`, `critical`). 이전 페이즈 문제 발견 시 여기에 기록하고 직접 수정하지 않는다.
