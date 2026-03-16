# CSV Schemas

Figma Codex Pipeline에서 사용하는 CSV 스키마 정의. Phase 간 데이터 계약으로 기능한다.

## 1. components.csv (Phase 1 -> Phase 2)

Phase 1(Decompose)에서 생성, Phase 2(Execute)의 `spawn_agents_on_csv` 입력으로 사용.

| 컬럼 | 필수 | 타입 | 설명 |
|------|------|------|------|
| `row_id` | Y | string | `comp-001` 형식 고유 ID. 3자리 zero-pad |
| `page_id` | Y | string | Figma page nodeId (예: `1:2`) |
| `component_name` | Y | string | PascalCase 컴포넌트 이름 |
| `figma_selection_url` | Y | string | 해당 노드의 Figma selection URL |
| `parent_id` | N | string | 부모 `row_id` (중첩 구조 표현용) |
| `depends_on` | N | string | Phase 3 통합 순서용. 쉼표 구분 `row_id` 목록. 워커는 무시 |
| `target_path` | Y | string | 생성 파일 경로. **행별 유일** |
| `prefetched_data_dir` | Y | string | `.figma-cache/{nodeId}/` 경로. screenshot.png + context.json 포함 |
| `design_system_hint` | N | string | 사용할 디자인 시스템 컴포넌트 힌트 (쉼표 구분) |
| `shared_context_ref` | Y | string | `shared_context.json` 파일 경로 |
| `acceptance_criteria` | Y | string | 검증 기준 1~2문장 |
| `estimated_complexity` | N | string | `simple` / `moderate` / `complex` |

### 제약

- `target_path`는 CSV 내에서 중복 불가. 워커 간 파일 충돌 방지.
- `row_id`는 CSV 내에서 유일해야 한다.
- `prefetched_data_dir` 경로에 `screenshot.png`과 `context.json`이 반드시 존재해야 한다.
- `depends_on`은 워커가 아닌 Phase 3 통합에서만 참조한다.

### 예시

```csv
row_id,page_id,component_name,figma_selection_url,parent_id,depends_on,target_path,prefetched_data_dir,design_system_hint,shared_context_ref,acceptance_criteria,estimated_complexity
comp-001,1:2,HeroSection,https://figma.com/design/abc?node-id=10-1,,,"src/features/dashboard/ui/HeroSection.tsx",.figma-cache/10:1/,,shared_context.json,"히어로 배너와 CTA 버튼이 정확히 렌더링됨",moderate
comp-002,1:2,SidebarNav,https://figma.com/design/abc?node-id=10-2,,,src/features/dashboard/ui/SidebarNav.tsx,.figma-cache/10:2/,"NavItem,Icon",shared_context.json,"네비게이션 메뉴 아이템이 올바른 순서로 렌더링됨",simple
comp-003,1:2,CardGrid,https://figma.com/design/abc?node-id=10-3,,comp-001,src/features/dashboard/ui/CardGrid.tsx,.figma-cache/10:3/,"Card",shared_context.json,"카드 그리드 레이아웃과 반복 아이템이 정확히 렌더링됨",complex
```

## 2. output CSV (Phase 2 결과)

`spawn_agents_on_csv`의 `output_schema`에 의해 자동 생성. 메인 에이전트가 Phase 3에서 소비.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `row_id` | string | components.csv의 `row_id`와 1:1 대응 |
| `status` | string | `success` / `failed` / `skipped` |
| `component_path` | string | 실제 생성된 파일 경로 |
| `exports` | string | export된 심볼 목록 (쉼표 구분) |
| `tokens_used` | string | 사용된 디자인 토큰 목록 (쉼표 구분) |
| `dependencies` | string | import한 외부 패키지/컴포넌트 목록 (쉼표 구분) |
| `warnings` | string | 워커 실행 중 경고 사항 |
| `error_message` | string | status=failed일 때 에러 내용 |

## 3. verification.csv (Phase 3 -> Phase 4)

Phase 3(Integrate) 완료 후 메인 에이전트가 생성, Phase 4(Verify)의 `spawn_agents_on_csv` 입력.

| 컬럼 | 필수 | 타입 | 설명 |
|------|------|------|------|
| `row_id` | Y | string | `ver-001` 형식 고유 ID |
| `check_type` | Y | string | `lint` / `typecheck` / `screenshot` / `viewport` / `accessibility` |
| `target_path` | Y | string | 검증 대상 파일 경로 |
| `figma_selection_url` | N | string | screenshot 비교용 Figma URL (`screenshot` 타입만) |
| `viewport_width` | N | number | viewport 검증 시 너비 (`viewport` 타입만) |
| `component_row_id` | N | string | components.csv의 `row_id` 참조 |
| `shared_context_ref` | Y | string | `shared_context.json` 경로 |
| `acceptance_criteria` | Y | string | 검증 기준 |

### check_type별 필수/선택 컬럼

| check_type | 추가 필수 | 비고 |
|------------|-----------|------|
| `lint` | - | ESLint/Prettier 검증 |
| `typecheck` | - | TypeScript 타입 검증 |
| `screenshot` | `figma_selection_url` | Figma vs 구현 시각 비교. Storybook 필요 |
| `viewport` | `viewport_width` | 반응형 레이아웃 검증 |
| `accessibility` | - | 기본 접근성 검증 (heading order, alt text 등) |

### Storybook 미사용 fallback

`screenshot`/`viewport` 검증은 Storybook 빌드가 필요하다. Storybook이 없는 프로젝트에서는:
- `screenshot` -> `lint` + `typecheck`로 대체
- `viewport` -> skip

### 예시

```csv
row_id,check_type,target_path,figma_selection_url,viewport_width,component_row_id,shared_context_ref,acceptance_criteria
ver-001,lint,src/features/dashboard/ui/HeroSection.tsx,,,,shared_context.json,"ESLint/Prettier 에러 없음"
ver-002,typecheck,src/features/dashboard/ui/HeroSection.tsx,,,,shared_context.json,"TypeScript 컴파일 에러 없음"
ver-003,screenshot,src/features/dashboard/ui/HeroSection.tsx,https://figma.com/design/abc?node-id=10-1,,comp-001,shared_context.json,"Figma 디자인과 시각적으로 일치"
ver-004,viewport,src/features/dashboard/ui/CardGrid.tsx,,768,comp-003,shared_context.json,"768px에서 카드가 2열로 재배치됨"
ver-005,accessibility,src/features/dashboard/ui/SidebarNav.tsx,,,comp-002,shared_context.json,"nav landmark 존재, 포커스 순서 올바름"
```

## Cross-Reference

- `components.csv`의 `row_id`는 output CSV와 `verification.csv`의 `component_row_id`에서 참조된다.
- 모든 CSV의 `shared_context_ref`는 동일한 `shared_context.json` 파일을 가리킨다.
- `prefetched_data_dir`의 파일 구조는 `shared-context-spec.md`의 `prefetch` 섹션과 일치해야 한다.
