---
name: clean-code-inspector
description: |
  React/TypeScript 코드 품질 분석. 다양한 소스(git diff, 브랜치 비교, PR, 커밋 범위, 파일 경로)의
  변경 코드를 전문 관점별 에이전트가 다각도로 분석하여 클린 코드 스코어카드를 생성한다.
  트리거: "코드 리뷰", "품질 검사", "클린 코드", "인스펙션", "코드 분석" 등
---

## Phase 1: 입력 해석 및 파일 수집

사용자 인자를 아래 표에 매칭하여 diff 명령을 결정한다. 질문 없이 추론한다.

| 입력 패턴 | 파일 목록 명령 | diff 명령 |
|-----------|---------------|-----------|
| (없음) | `git diff --name-only` | `git diff` |
| `staged`, `--cached` | `git diff --cached --name-only` | `git diff --cached` |
| 브랜치명 (예: `main`, `develop`) | `git diff {branch}...HEAD --name-only` | `git diff {branch}...HEAD` |
| `#N`, `PR N` | `gh pr diff {N} --name-only` | `gh pr diff {N}` |
| 커밋 범위 `abc..def` | `git diff abc..def --name-only` | `git diff abc..def` |
| `HEAD~N` 또는 "최근 N커밋" | `git diff HEAD~{N}..HEAD --name-only` | `git diff HEAD~{N}..HEAD` |
| 파일 경로 직접 지정 | (입력 그대로 사용) | `git diff -- {files}` 또는 전체 파일 읽기 |

파일 목록 명령 실행 후 필터링:
- **포함**: `.ts`, `.tsx`, `.js`, `.jsx`
- **제외**: `node_modules/`, `.d.ts`, `*.config.ts`, `*.config.js`, `*.stories.tsx`, `design-system/token/src/generated/`, `design-system/icon/src/components/`
- 결과 0개 → "분석 가능한 변경 파일이 없습니다." 출력 후 종료.
- 결과 25개 초과 → 사용자 확인 질문: "N개 파일이 변경되었습니다. 전체 분석은 시간이 소요됩니다. 전체 진행 / 범위 축소?"

## Phase 2: 전문가 에이전트 병렬 분석

파일 수에 관계없이 항상 3개 전문 에이전트를 병렬 실행한다. 동시에 `pnpm lint`도 실행.

**Agent 1: Complexity Analyst**
```
Task:
  subagent_type: "complexity-analyst"
  model: "opus"
  description: "Analyze structural complexity for {N} files"
  run_in_background: true
  prompt: |
    분석 대상 파일: {file_list}
    각 파일 변경 확인: `{diff_command} -- {file}` 실행 후, 전체 파일도 Read로 읽으세요.
    평가 기준: `${CODEX_HOME:-$HOME/.codex}/skills/clean-code-inspector/references/scorecard-framework.md` 읽기.
```

**Agent 2: Interface Inspector**
```
Task:
  subagent_type: "interface-inspector"
  model: "opus"
  description: "Analyze component interface quality for {N} files"
  run_in_background: true
  prompt: |
    분석 대상 파일: {file_list}
    각 파일 변경 확인: `{diff_command} -- {file}` 실행 후, 전체 파일도 Read로 읽으세요.
    평가 기준: `${CODEX_HOME:-$HOME/.codex}/skills/clean-code-inspector/references/scorecard-framework.md` 읽기.
```

**Agent 3: Architecture Reviewer**
```
Task:
  subagent_type: "architect-reviewer"
  model: "opus"
  description: "Analyze architecture and cohesion for {N} files"
  run_in_background: true
  prompt: |
    분석 대상 파일: {file_list}
    각 파일 변경 확인: `{diff_command} -- {file}` 실행 후, 전체 파일도 Read로 읽으세요.
    관련 파일(import된 훅, Context, 상위 컴포넌트)도 Grep/Glob으로 추적하여 읽으세요.
    평가 기준: `${CODEX_HOME:-$HOME/.codex}/skills/clean-code-inspector/references/scorecard-framework.md` 읽기.

    **React 특화 측정 메트릭 (이것만 측정)**:
    1. LCOM4 추정: 상태 변수와 Effect/Callback/핸들러의 연결 그래프. 비연결 부분그래프 수 = LCOM4.
    2. Props Drilling 깊이: Props 원점에서 소비처까지 몇 단계 전달인지 추적.
    3. 상태 아키텍처: State Colocation, Global State Density 평가.
    4. 테스트 가능성: 사이드 이펙트 격리 수준, 독립 테스트 가능 여부.

    **출력 형식**:
    ### 크로스 파일 아키텍처 평가
    (파일 간 의존 관계, 공유 상태 패턴, 순환 import)

    ### 파일별 분석
    | 메트릭 | 측정값 | 근거 |
    (LCOM4 행에는 연결 그래프 분석 과정을 근거 열에 기재)

    한국어로 작성. 아키텍처 개선 권장사항을 영향도 순으로 나열.
```

모든 에이전트 완료 후 결과를 수집한다.

## Phase 3: 종합 및 스코어카드 생성

오케스트레이터가 `references/scorecard-framework.md`를 참조하여 다음을 수행:

1. **파일별 통합**: 3개 에이전트(또는 직접 분석)의 결과를 파일 기준으로 병합.
2. **CRS 계산**: LoC, CC, SC, DC로 CRS = w1(LoC) + w2(CC) + w3(SC) + w4(DC) 산출.
3. **크로스 메트릭 패턴 식별**:
   - 높은 CC + 낮은 LCOM4 = 복잡+비응집 → 강력한 리팩토링 시그널
   - 높은 Props 수 + 깊은 Drilling = 인터페이스+결합도 동시 문제
   - 여러 파일의 공통 위반 패턴
4. **스코어카드 테이블 생성** (framework Section 8 형식)
5. **이슈 분류**:
   - `자동 수정 가능`: 결정적 변환 + 로컬 범위 + 동작 보존. (예: 명명 규칙, unused import, console.log)
   - `설계 판단 필요`: 위 미충족. (예: 컴포넌트 분할, 훅 추출, boolean→enum, 상태 변경)

사용자에게 인라인 요약을 보여준다:
```
## 분석 결과 요약

분석 대상: {N}개 파일 ({분석 방식})

| 카테고리 | 평가 항목 | 측정값 | 상태 | 비고 |
| ... 스코어카드 ... |

### 자동 수정 가능 ({n}건)
- {파일}: {이슈}

### 설계 판단 필요 ({m}건)
- {파일}: {이슈 + 권장 방향}
```

## Phase 4: 액션 선택

**스킵 조건**: 모든 메트릭이 양호 + 자동 수정 0건 + 설계 판단 0건 → "전체 메트릭이 양호합니다." 출력 후 종료.

그 외 사용자 확인 질문:
```
분석이 완료되었습니다. 어떻게 진행할까요?
1. 전체 수정 + 보고서 — 자동 수정 {n}건 + 설계 리팩토링 {m}건 선택 적용 + 보고서 생성
2. 자동 수정 + 보고서 — 결정적 수정만 {n}건 적용 + 보고서 생성
3. 보고서만 — clean-code-inspect-result.md에 상세 분석 결과를 저장합니다
4. 요약만 — 현재 요약으로 충분합니다
```

설계 판단 필요 이슈가 0건이면 옵션 1은 표시하지 않는다.
자동 수정 가능 이슈가 0건이면 옵션 2는 표시하지 않는다.

## Phase 5: 액션 실행

### Phase 5A: 자동 수정 (선택 1, 2)

수정 대상을 유형별로 그룹화하여 보여준 뒤 사용자 확인 질문으로 승인:
```
다음 수정을 적용합니다:
[명명 규칙] {파일}: {수정 내용}
[미사용 코드] {파일}: {수정 내용}
진행할까요?
```
승인 후 Edit 도구로 순차 수정. 완료 후 `pnpm typecheck && pnpm lint` 실행. 실패 시 수정을 되돌리고 원인 보고.

### Phase 5B: 설계 리팩토링 (선택 1)

Phase 3에서 분류한 "설계 판단 필요" 이슈 목록을 사용자 확인 질문의 multiSelect로 제시:
```
설계 리팩토링이 필요한 이슈입니다. 수정할 항목을 선택하세요:
□ {파일}: CC {값} → 함수/컴포넌트 분할
□ {파일}: any {n}개 → 타입 구조 개선
□ {파일}: LCOM4 {값} → 커스텀 훅 추출
□ ...
```

선택된 이슈를 유형별 전문 에이전트에 매핑:

| 이슈 유형 | subagent_type | 근거 |
|-----------|---------------|------|
| CC 감소, 컴포넌트/훅 분할 | `refactoring-expert` | 비판적 분석 + 리팩토링 패턴 내장 |
| any 제거, 타입 구조 개선 | `typescript-pro` | 고급 타입 시스템 전문 |
| 상태 아키텍처, 의존성 구조 | `refactoring-expert` | 코드 구조 개선 전문 |

**실행 규칙**:
- **순차 실행** (파일 충돌 방지) — 같은 파일에 대한 이슈는 반드시 순차 처리
- 다른 파일에 대한 이슈는 병렬 실행 가능
- 각 이슈마다:
  1. 해당 에이전트에 Task로 수정 위임
  2. 에이전트가 Edit 적용
  3. `pnpm typecheck && pnpm lint` 검증
  4. 실패 시 `git checkout -- {file}` 로 롤백하고 원인 보고

에이전트 Task 프롬프트 템플릿:
```
Task:
  subagent_type: "{agent_type}"
  model: "sonnet"
  description: "Refactor {issue_type} in {filename}"
  prompt: |
    대상 파일: {file_path}
    이슈: {issue_description}
    분석 결과: {analysis_summary}

    위 이슈를 수정하세요.
    수정 후 동작이 보존되는지 확인하세요.
    모든 변경은 Edit 도구로 적용하세요.
```

## Phase 6: 보고서 생성 (선택 1, 2, 3)

프로젝트 루트에 `clean-code-inspect-result.md` 생성. **한국어**. 내용:
- 요약
- 파일별 상세 분석 (에이전트 결과 통합)
- 스코어카드 테이블
- 자동 수정 가능 이슈 (수정 선택 시 적용 결과 포함)
- 설계 판단 필요 이슈 (권장 방향 포함, 수정 선택 시 적용 결과 포함)
- 분석 방식 (직접/병렬, 에이전트 구성)
