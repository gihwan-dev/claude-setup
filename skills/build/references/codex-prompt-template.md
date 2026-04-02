# Codex Phase Prompt Template

Build 스킬이 매 페이즈마다 Codex를 호출할 때 사용하는 프롬프트 구조.
Claude가 변수를 치환한 뒤 사용자 승인을 거쳐 Codex에 전달한다.

## Template

```xml
<task>
## 목적
${PHASE_PURPOSE}

## 참고 문서
${REFERENCE_CONTEXT}

## Goal
${PHASE_GOAL}

## 완료 기준
${DONE_CRITERIA}
</task>

<structured_output_contract>
구현 완료 후:
1. `${PHASE_REPORT_PATH}`에 phase report를 작성하라:
   - Summary: 수행한 작업 (2-3문장)
   - Files Changed: 생성/수정/삭제된 파일 테이블 (File | Action | Description)
   - Decisions Made: 구현 과정에서 내린 결정과 근거
   - Impact on Future Phases: 다음 페이즈가 반드시 알아야 할 사항
   - Open Issues: 미해결 사항 또는 이전 페이즈의 문제 발견 기록
2. 변경된 파일 전체 목록
3. 검증 결과 (명령어별 PASS/FAIL)
</structured_output_contract>

<verification_loop>
완료 전 반드시:
- 실행: ${VERIFICATION_COMMANDS}
- 모든 완료 기준 충족 여부 확인
- 검증 실패 시 수정 후 재검증. 최대 3회 반복
</verification_loop>

<action_safety>
- 이 페이즈 범위 내 변경만 수행
- 범위 밖 파일 수정 금지
- 무관한 리팩터링 금지
- 이전 페이즈 작업에서 문제 발견 시, 직접 수정하지 말고 phase report의 Open Issues에 기록
</action_safety>

<default_follow_through_policy>
가장 합리적인 해석을 기본으로 삼고 계속 진행.
정보 부재가 잘못된 동작을 야기할 때만 멈춘다.
</default_follow_through_policy>
```

## 변수 치환 규칙

Claude가 프롬프트를 조립할 때 아래 규칙에 따라 변수를 치환한다.

| 변수 | 출처 | 비고 |
|------|------|------|
| `PHASE_PURPOSE` | BRIEF.md Phase N "Purpose" | 그대로 복사 |
| `REFERENCE_CONTEXT` | 이전 phase report 압축 + 참고 문서 발췌 + BRIEF.md Decisions/Context | 누적 500토큰 이내 목표 |
| `PHASE_GOAL` | BRIEF.md Phase N "Done when"을 행동 가능한 목표로 확장 | Claude가 재구성 |
| `DONE_CRITERIA` | BRIEF.md Phase N "Done when" + "Verification" 병합 | 체크리스트 형태 |
| `PHASE_REPORT_PATH` | `tasks/<slug>/PHASE_REPORT_<NN>.md` | NN은 01, 02, ... |
| `VERIFICATION_COMMANDS` | BRIEF.md Phase N "Verification" | 그대로 복사 |

### REFERENCE_CONTEXT 구성 우선순위

1. **이전 phase report 압축**: 가장 최근 2-3개는 핵심 사실 위주, 그 이전은 1-2줄 요약
2. **BRIEF.md Decisions**: 현재 페이즈와 관련된 결정사항
3. **참고 문서 발췌**: BRIEF.md References에 나열된 문서 중 현재 페이즈에 관련된 부분만 발췌
4. **BRIEF.md Context**: 시스템 현재 상태, 제약조건

전체 REFERENCE_CONTEXT가 500토큰을 초과하면 오래된 phase report 요약을 줄인다.

## 예시: 채워진 프롬프트

```xml
<task>
## 목적
API 엔드포인트의 인증 미들웨어를 JWT 기반으로 교체한다.

## 참고 문서
- Phase 1에서 기존 세션 토큰 저장 방식을 제거하고 JWT 유틸리티를 src/auth/jwt.ts에 생성했다.
- BRIEF Decisions: RS256 알고리즘, 토큰 만료 15분, 리프레시 토큰 7일.
- docs/design/auth-migration.md의 "Chosen Direction": 점진적 마이그레이션, 이전 세션과 병행 2주.

## Goal
모든 보호된 라우트에서 JWT 검증 미들웨어가 동작하고, 기존 세션 기반 인증도 fallback으로 유지되도록 구현한다.

## 완료 기준
- src/middleware/auth.ts가 JWT 우선, 세션 fallback 순서로 인증
- 기존 인증 테스트 전부 통과
- 새 JWT 인증 테스트 3개 이상 추가
</task>

<structured_output_contract>
구현 완료 후:
1. `tasks/auth-migration/PHASE_REPORT_02.md`에 phase report를 작성하라:
   ...
</structured_output_contract>

<verification_loop>
완료 전 반드시:
- 실행: npm run typecheck && npm run test -- --grep "auth"
- 모든 완료 기준 충족 여부 확인
- 검증 실패 시 수정 후 재검증. 최대 3회 반복
</verification_loop>

<action_safety>
...
</action_safety>
```
