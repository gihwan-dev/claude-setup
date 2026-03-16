---
name: figma-codex-pipeline
description: >
  Page-level Figma-to-Code pipeline using Codex spawn_agents_on_csv. Figma 페이지를 의미
  단위로 분해하고 컴포넌트별 병렬 코드 생성 후 통합/검증하는 4-phase 파이프라인.
  단일 컴포넌트는 figma-to-code, 페이지 단위는 이 스킬을 사용한다.
---

# Figma Codex Pipeline

Figma 페이지를 의미 단위로 분해 -> 컴포넌트별 병렬 코드 생성 -> 중앙 통합 -> 검증의 4-phase 파이프라인.
Codex의 `spawn_agents_on_csv` API를 활용해 context pollution 없이 대규모 페이지를 처리한다.

## Trigger

- `/figma-codex-pipeline`
- `페이지 피그마 구현`
- Figma URL이 페이지 단위(다수 컴포넌트)이고 병렬 처리가 필요한 요청

## Required Inputs

- Figma URL (`node-id` 포함, 페이지 또는 대형 프레임)
- 대상 디렉토리 경로 (예: `src/features/dashboard/ui/`)

## Existing Skill References

토큰 매핑과 에러 처리 규칙은 기존 스킬을 경로 참조로 재사용한다. 복사본을 만들지 않는다.

- 토큰 매핑: `skills/figma-to-code/references/token-mapping.md`
- 에러 처리: `skills/figma-to-code/references/error-handling.md`
- Screenshot 캡처: `skills/component-screenshot/scripts/capture-screenshot.ts`
- Figma screenshot: `skills/design-check/scripts/capture-figma-screenshot.ts`
- Screenshot 비교: `skills/design-check/scripts/compare-screenshots.ts`

## Phase 1: Decompose (메인 에이전트)

### Step 1-0: Setup Interview

첫 실행 시 (또는 `shared_context.json`이 없을 때) 프로젝트 규칙을 질문으로 수집한다.

**필수 질문:**
1. 디자인 시스템 라이브러리 (예: `@exem-fe/react`, `shadcn/ui`, `antd`, 없음)
2. CSS/스타일링 방식 (예: Tailwind + cn(), CSS Modules, styled-components)
3. import alias 규칙 (예: `@/`, `~/`, 상대경로)
4. export 스타일 (named vs default)
5. 대상 디렉토리 경로 구조 (예: `src/pages/{feature}/`)

**선택 질문 (프로젝트에 따라):**
- 상태 관리, 라우팅, API 레이어, 폼 라이브러리, 아이콘 라이브러리 패턴

답변을 `shared_context.json`의 `design_system`, `code_rules`, `project_patterns` 섹션에 기록한다.
이미 `shared_context.json`이 있으면 기존 설정을 보여주고 변경 여부만 확인한다.

상세 필드 규격: `references/shared-context-spec.md`

### Step 1-1: Figma 데이터 수집

1. Figma URL에서 `fileKey`, `nodeId` 추출. `.../branch/:branchKey/...` 형식이면 `branchKey`를 `fileKey`로 정규화
2. `get_screenshot`, `get_design_context`, `get_variable_defs`를 `clientLanguages=typescript`, `clientFrameworks=react` 힌트와 함께 병렬 호출

### Step 1-2: Pre-fetch (모든 노드 데이터 파일 저장)

design_context에서 식별된 각 의미 단위 노드에 대해:
1. `get_screenshot(nodeId)` -> `.figma-cache/{nodeId}/screenshot.png`
2. `get_design_context(nodeId)` -> `.figma-cache/{nodeId}/context.json`
3. 페이지 전체 `get_variable_defs` -> `.figma-cache/variables.json`
4. 페이지 전체 스크린샷 -> `.figma-cache/page-screenshot.png`

워커는 MCP를 직접 호출하지 않고 이 파일에서 읽는다.

### Step 1-3: 의미 단위 분해

1. design_context에서 **의미 단위** 식별:
   - top-level frame의 직접 자식 중 독립 레이아웃 단위 (hero, sidebar, card grid, filter bar 등)
   - 같은 컴포넌트 반복 인스턴스는 1행으로 합침
   - 공유 primitive (아이콘, 버튼)는 `design_system_hint`에 기록
2. `shared_context.json`의 `tokens`, `layout` 섹션을 Figma 데이터로 채움
3. `components.csv` 생성 (각 행의 `prefetched_data_dir`에 `.figma-cache/{nodeId}/` 경로 기록)

CSV 스키마: `references/csv-schemas.md`

### Step 1-4: 승인 게이트

사용자에게 분해 결과 + shared_context 요약을 보여주고 승인을 받는다.

표시 항목:
- 컴포넌트 목록 (이름, 복잡도, target_path)
- 프로젝트 규칙 요약 (디자인 시스템, 스타일링, alias)
- 예상 토큰/레이아웃 정보

**분기 규칙:**
- 의미 단위 1개 이하 -> 기존 `figma-to-code` 스킬로 redirect. 사용자에게 안내.
- 의미 단위 12개 초과 -> 하위 페이지 분할 제안.

## Phase 2: Execute (spawn_agents_on_csv)

승인 후 `components.csv`를 입력으로 병렬 코드 생성을 실행한다.

```
spawn_agents_on_csv(
  csv_path = "components.csv",
  instruction = executor_prompt,        # references/agent-prompts.md 참조
  id_column = "row_id",
  output_schema = {
    component_path, exports, tokens_used, dependencies, warnings
  },
  max_concurrency = 6,
  max_runtime_seconds = 300
)
```

각 워커의 동작:
1. `prefetched_data_dir`에서 screenshot.png + context.json을 읽음
2. `shared_context.json`에서 전역 규칙 로드
3. `target_path`에 React 컴포넌트 생성
4. `report_agent_job_result` 1회 호출

**독립 산출물 원칙:** 각 워커는 자신의 `target_path`에만 쓴다. 워커 간 참조 금지.

**실패 복구:**
- status=failed 행은 에러 컨텍스트 추가 후 1회 재시도
- 2회 실패 시 skipped
- 전체 성공률 50% 미만이면 파이프라인 중단

상세 API 규약: `references/codex-api-contract.md`
Executor prompt 골격: `references/agent-prompts.md`

## Phase 3: Integrate (메인 에이전트)

output CSV에서 성공 컴포넌트 목록을 파악하고 통합한다.

1. 페이지 루트 컴포넌트 생성: layout, import 조립, 라우팅/상태 연결
2. 토큰 일관성 검증: 워커 간 토큰 불일치 통일
3. import 경로 정규화, circular dependency 검출
4. responsive 래퍼 추가 (`shared_context.json`의 `layout.breakpoints` 반영)
5. skipped 컴포넌트에 TODO placeholder 삽입

통합 순서는 `components.csv`의 `depends_on` 관계와 `parent_id` 계층 구조를 따른다.

## Phase 4: Verify (spawn_agents_on_csv)

메인 에이전트가 `verification.csv`를 생성하고 검증을 fan-out한다.

```
spawn_agents_on_csv(
  csv_path = "verification.csv",
  instruction = verifier_prompt,        # references/agent-prompts.md 참조
  id_column = "row_id",
  output_schema = {
    pass, severity, findings, artifact_paths
  },
  max_concurrency = 6,
  max_runtime_seconds = 180
)
```

check_type: `lint`, `typecheck`, `screenshot`, `viewport`, `accessibility`

**Storybook fallback:** Storybook이 없으면 `screenshot`/`viewport` 검증은 skip하고 `lint`/`typecheck`만 수행.

**반복 수정:**
- Critical 발견 -> Phase 3에서 수정 -> 재검증 (최대 2회)
- 2회 반복 후에도 Critical 잔존 시 사용자에게 수동 개입 요청

## Guardrails

- `node-id`가 없는 URL은 중단하고 올바른 형식을 요청한다.
- Figma 데이터 수집 실패 시 Figma Desktop 앱 실행을 안내한다. (`skills/figma-to-code/references/error-handling.md` 참조)
- 워커는 `target_path` 외의 파일을 수정하지 않는다.
- 색상은 hex 하드코딩 대신 토큰 기반 클래스만 사용한다. (`skills/figma-to-code/references/token-mapping.md` 참조)
- Pre-fetch 캐시는 파이프라인 실행 단위로 생성되며 완료 후 정리를 제안한다.

## Output

```text
Figma Codex Pipeline 완료: {PageName}

[Phase 1] 분해:
- 의미 단위: {N}개 컴포넌트
- 프로젝트 규칙: {design_system}, {styling}, {alias}

[Phase 2] 코드 생성:
- 성공: {N}/{Total}
- Skipped: {list or "없음"}

[Phase 3] 통합:
- 루트 컴포넌트: {page_root_path}
- 토큰 통일: {N}건
- TODO placeholder: {N}건

[Phase 4] 검증:
- lint: {pass/fail}
- typecheck: {pass/fail}
- screenshot: {pass/fail/skipped}
- Critical 이슈: {N}건
```

## References

- CSV 스키마: `references/csv-schemas.md`
- shared_context.json 규격: `references/shared-context-spec.md`
- Codex API 사용 규약: `references/codex-api-contract.md`
- Executor/Verifier prompt 골격: `references/agent-prompts.md`
- 토큰 매핑: `skills/figma-to-code/references/token-mapping.md`
- 에러 처리: `skills/figma-to-code/references/error-handling.md`

## Related Skills

| 스킬 | 관계 |
|------|------|
| `figma-to-code` | 단일 컴포넌트용. 의미 단위 1개 이하일 때 redirect |
| `figma-design-pipeline` | 단일 컴포넌트 구현+검증. 이 스킬은 페이지 단위 |
| `design-check` | Phase 4 screenshot 검증에서 스크립트 참조 |
| `component-screenshot` | Phase 4 구현 screenshot 캡처에서 스크립트 참조 |
