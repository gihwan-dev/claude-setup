## 핵심 원칙

- 메인 스레드는 의사결정과 구현에 집중한다. 대규모 변경 시 파일 경계가 명확한 코드 작성은 writer에 위임할 수 있다.
- 조사/리뷰는 에이전트에 적극 위임하고 병렬 활용한다.
- 에이전트 결과는 하나의 의사결정 가능한 요약으로 통합한다.

## 에이전트 카탈로그

| ID | 역할 | 도구 | 언제 소환하나 |
|----|------|------|-------------|
| `explorer` | 코드베이스 탐색/증거 수집 | Read, Grep, Glob | 원인/소유 영역 불명확, 탐색 필요 |
| `browser-explorer` | 브라우저 재현/시각 QA | Read, Bash, Grep, Glob | live browser reproduction, DOM/visual QA 필요 |
| `web-researcher` | 외부 문서/벤치마크 조사 | Read, Grep, Glob, WebFetch, WebSearch | 외부 docs, 벤치마크, official vendor docs 필요 |
| `code-quality-reviewer` | 코드 품질 리뷰 | Read, Write, Edit, Bash, Grep | 3+ 파일 변경, 보안/에러 로직, 명시적 요청 |
| `structure-reviewer` | 구조/복잡도 리뷰 + 분해 계획 | Read, Bash, Grep, Glob | non-trivial diff 후 항상 |
| `architecture-reviewer` | 경계/레이어/public surface 리뷰 | Read, Grep, Glob | public surface 또는 모듈 경계 변경 |
| `type-specialist` | 타입 계약 안정성 리뷰 | Read, Grep, Glob | shared/public type, generics 변경 |
| `test-engineer` | 테스트 품질 심사/회귀 리스크 | Read, Grep, Glob | 테스트 코드 변경·추가 또는 회귀 리스크 |
| `verification-worker` | 검증 결과 분석 | Read, Grep, Glob | 검증 로그가 noisy하거나 multi-step |
| `writer` | 범위 제한 코드 작성 | Read, Write, Edit, Bash, Grep, Glob | 대규모 변경에서 파일 경계가 명확한 위임 작성 |

## 에이전트 응답 포맷

- 필수: 핵심결론, 근거
- 선택: 리스크, 권장 다음 행동

## 언어

- 한국어 기본, 코드 식별자는 원어
