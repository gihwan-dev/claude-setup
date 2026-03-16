# shared_context.json Specification

Planner(메인 에이전트)가 생성하고, executor/verifier 워커가 읽기 전용으로 참조하는 전역 컨텍스트 파일.

## Ownership

- **Writer**: 메인 에이전트 (Phase 1에서 생성, Phase 3에서 갱신 가능)
- **Reader**: executor 워커, verifier 워커 (읽기 전용)

## Schema

```jsonc
{
  // 메타
  "version": "1.0",
  "page_name": "string",               // PascalCase 페이지 이름
  "figma_file_key": "string",          // Figma file key
  "figma_page_node_id": "string",      // 페이지 최상위 nodeId (예: "1:2")

  // === Setup Interview에서 수집 (프로젝트마다 다름) ===

  "design_system": {
    "primary_library": "string|null",   // 예: "@exem-fe/react", "shadcn/ui", "antd", null
    "icon_library": "string|null",      // 예: "@exem-fe/icon", "lucide-react"
    "icon_pattern": "string|null",      // 예: "{Name}{Variant}Icon", "<Icon name={...} />"
    "available_components": ["string"],  // AI가 로컬 코드에서 자동 탐지한 컴포넌트 목록
    "custom_ui_path": "string|null"     // 예: "src/shared/ui/"
  },

  "code_rules": {
    "import_alias": "string|null",      // 예: "@/", "~/", null(상대경로)
    "class_merge_util": "string|null",  // 예: "cn", "clsx", "classnames"
    "class_merge_import": "string|null",// 예: "@/shared/util" (AI 자동 탐지)
    "export_style": "string",           // "named" | "default"
    "styling_approach": "string|null",  // "tailwind" | "css-modules" | "styled-components" | "emotion"
    "root_class_name_prop": true        // 루트 요소에 className prop 합성 여부
  },

  // === Figma 데이터에서 자동 추출 (Phase 1, Step 1-2) ===

  "tokens": {
    "color_mode": "string",             // "semantic-first" | "primitive-only"
    "primary_colors": ["string"],       // 주요 색상 토큰 목록
    "typography_scale": ["string"],     // 타이포그래피 스케일 목록
    "radius_tokens": ["string"],        // 라운딩 토큰
    "shadow_tokens": ["string"],        // 그림자 토큰
    "custom_tokens": {}                 // 프로젝트 전용 커스텀 토큰
  },

  "layout": {
    "page_width": "number|null",        // 전체 페이지 너비 (px)
    "breakpoints": {},                  // 예: { "sm": 640, "md": 768, "lg": 1024, "xl": 1280 }
    "page_structure": "string|null",    // 예: "sidebar-left + main", "full-width"
    "grid_columns": "number|null",      // 그리드 컬럼 수
    "grid_gap": "string|null"           // 그리드 간격 (예: "24px", "gap-6")
  },

  // === Setup Interview에서 수집 (선택) ===

  "project_patterns": {
    "state_management": "string|null",  // 예: "zustand", "redux", "jotai"
    "routing": "string|null",           // 예: "react-router", "next/router"
    "api_layer": "string|null",         // 예: "tanstack-query", "swr"
    "form_library": "string|null",      // 예: "react-hook-form"
    "page_structure_pattern": "string|null" // 예: "src/pages/{feature}/"
  },

  // === Pre-fetch 메타 (Phase 1, Step 1-2) ===

  "prefetch": {
    "cache_dir": "string",              // 기본: ".figma-cache/"
    "page_screenshot": "string",        // 기본: ".figma-cache/page-screenshot.png"
    "variables_file": "string"          // 기본: ".figma-cache/variables.json"
  }
}
```

## Setup Interview 필드

Phase 1, Step 1-0에서 사용자 질문으로 수집하는 필드. `null`이면 아직 수집되지 않은 상태.

### 필수 질문 (반드시 수집)

| 필드 경로 | 질문 |
|-----------|------|
| `design_system.primary_library` | 디자인 시스템 라이브러리가 있나요? (예: `@exem-fe/react`, `shadcn/ui`, `antd`, 없음) |
| `code_rules.styling_approach` | CSS/스타일링 방식은? (예: Tailwind + cn(), CSS Modules, styled-components) |
| `code_rules.import_alias` | import alias 규칙은? (예: `@/`, `~/`, 상대경로) |
| `code_rules.export_style` | export 스타일은? (named vs default) |
| `project_patterns.page_structure_pattern` | 페이지 파일 경로 구조는? (예: `src/pages/{feature}/`) |

### 선택 질문 (프로젝트에 따라)

| 필드 경로 | 질문 |
|-----------|------|
| `project_patterns.state_management` | 상태 관리 라이브러리? (zustand, redux, jotai 등) |
| `project_patterns.routing` | 라우팅? (react-router, next/router 등) |
| `project_patterns.api_layer` | API 레이어? (tanstack-query, SWR 등) |
| `project_patterns.form_library` | 폼 라이브러리? (react-hook-form 등) |
| `design_system.icon_library` | 아이콘 라이브러리? |
| `code_rules.class_merge_util` | className 병합 유틸리티? (cn, clsx 등) |

### AI 자동 탐지 필드

| 필드 경로 | 탐지 방법 |
|-----------|-----------|
| `design_system.available_components` | `custom_ui_path` 하위 파일 스캔 |
| `code_rules.class_merge_import` | `class_merge_util` 사용처 grep |

## 자동 추출 필드

Phase 1, Step 1-2에서 Figma 데이터로 채우는 필드.

| 섹션 | 소스 |
|------|------|
| `tokens.*` | `get_variable_defs` + `get_design_context` 응답에서 추출 |
| `layout.*` | 페이지 최상위 프레임의 auto-layout 속성에서 추출 |
| `prefetch.*` | 캐시 디렉토리 경로 (고정값) |

## Pre-fetch 디렉토리 구조

```
.figma-cache/
  page-screenshot.png          # 페이지 전체 스크린샷
  variables.json               # get_variable_defs 전체 응답
  {nodeId}/                    # 각 의미 단위 노드별 디렉토리
    screenshot.png             # get_screenshot 결과
    context.json               # get_design_context 결과
```

`nodeId`의 `:`는 디렉토리명에서 그대로 사용한다 (예: `10:1/`).

## Validation Rules

- `version`은 `"1.0"`이어야 한다.
- `page_name`은 비어있지 않아야 한다.
- `figma_file_key`는 비어있지 않아야 한다.
- `design_system`, `code_rules`, `tokens`, `layout`, `project_patterns`, `prefetch` 섹션은 모두 존재해야 한다.
- `prefetch.cache_dir`에 해당하는 디렉토리가 실제 존재해야 한다.
- executor 워커는 이 파일을 수정하면 안 된다 (읽기 전용).
