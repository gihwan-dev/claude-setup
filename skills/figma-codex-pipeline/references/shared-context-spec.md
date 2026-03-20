# shared_context.json Specification

A global context file written by the planner, which the executor and verifier workers read as read-only input.

## Ownership

- **Writer**: Main agent, created in Phase 1 and optionally updated in Phase 3
- **Reader**: Executor workers and verifier workers, read-only

## Schema

```jsonc
{
  // Metadata
  "version": "1.0",
  "page_name": "string",               // PascalCase page name
  "figma_file_key": "string",          // Figma file key
  "figma_page_node_id": "string",      // Top-level page nodeId, for example "1:2"

  // === Collected during the Setup Interview (varies by project) ===

  "design_system": {
    "primary_library": "string|null",   // Example: "@exem-fe/react", "shadcn/ui", "antd", null
    "icon_library": "string|null",      // Example: "@exem-fe/icon", "lucide-react"
    "icon_pattern": "string|null",      // Example: "{Name}{Variant}Icon", "<Icon name={...} />"
    "available_components": ["string"], // Components auto-detected from local code
    "custom_ui_path": "string|null"     // Example: "src/shared/ui/"
  },

  "code_rules": {
    "import_alias": "string|null",      // Example: "@/", "~/", null for relative paths
    "class_merge_util": "string|null",  // Example: "cn", "clsx", "classnames"
    "class_merge_import": "string|null",// Example: "@/shared/util", auto-detected
    "export_style": "string",           // "named" | "default"
    "styling_approach": "string|null",  // "tailwind" | "css-modules" | "styled-components" | "emotion"
    "root_class_name_prop": true        // Whether the root element supports className composition
  },

  // === Auto-extracted from Figma data (Phase 1, Step 1-2) ===

  "tokens": {
    "color_mode": "string",             // "semantic-first" | "primitive-only"
    "primary_colors": ["string"],       // List of primary color tokens
    "typography_scale": ["string"],     // List of typography scale tokens
    "radius_tokens": ["string"],        // Radius tokens
    "shadow_tokens": ["string"],        // Shadow tokens
    "custom_tokens": {}                 // Project-specific custom tokens
  },

  "layout": {
    "page_width": "number|null",        // Full page width in px
    "breakpoints": {},                  // Example: { "sm": 640, "md": 768, "lg": 1024, "xl": 1280 }
    "page_structure": "string|null",    // Example: "sidebar-left + main", "full-width"
    "grid_columns": "number|null",      // Number of grid columns
    "grid_gap": "string|null"           // Grid gap, for example "24px" or "gap-6"
  },

  // === Collected during the Setup Interview (optional) ===

  "project_patterns": {
    "state_management": "string|null",  // Example: "zustand", "redux", "jotai"
    "routing": "string|null",           // Example: "react-router", "next/router"
    "api_layer": "string|null",         // Example: "tanstack-query", "swr"
    "form_library": "string|null",      // Example: "react-hook-form"
    "page_structure_pattern": "string|null" // Example: "src/pages/{feature}/"
  },

  // === Pre-fetch metadata (Phase 1, Step 1-2) ===

  "prefetch": {
    "cache_dir": "string",              // Default: ".figma-cache/"
    "page_screenshot": "string",        // Default: ".figma-cache/page-screenshot.png"
    "variables_file": "string"          // Default: ".figma-cache/variables.json"
  }
}
```

## Setup Interview Fields

These fields are collected through user questions in Phase 1, Step 1-0. A `null` value means the field has not been collected yet.

### Required Questions

| Field Path | Question |
|-----------|------|
| `design_system.primary_library` | Is there a design system library? For example `@exem-fe/react`, `shadcn/ui`, `antd`, or none |
| `code_rules.styling_approach` | What is the CSS or styling approach? For example Tailwind + `cn()`, CSS Modules, or styled-components |
| `code_rules.import_alias` | What is the import alias convention? For example `@/`, `~/`, or relative paths |
| `code_rules.export_style` | What is the export style? Named or default |
| `project_patterns.page_structure_pattern` | What is the page file path structure? For example `src/pages/{feature}/` |

### Optional Questions

| Field Path | Question |
|-----------|------|
| `project_patterns.state_management` | Which state management library is used? For example zustand, redux, or jotai |
| `project_patterns.routing` | Which routing solution is used? For example react-router or next/router |
| `project_patterns.api_layer` | Which API layer is used? For example tanstack-query or SWR |
| `project_patterns.form_library` | Which form library is used? For example react-hook-form |
| `design_system.icon_library` | Which icon library is used? |
| `code_rules.class_merge_util` | Which className merge utility is used? For example `cn` or `clsx` |

### AI Auto-Detected Fields

| Field Path | Detection Method |
|-----------|-----------|
| `design_system.available_components` | Scan files under `custom_ui_path` |
| `code_rules.class_merge_import` | Grep for usage of `class_merge_util` |

## Automatically Extracted Fields

These fields are filled from Figma data in Phase 1, Step 1-2.

| Section | Source |
|------|------|
| `tokens.*` | Extracted from `get_variable_defs` and `get_design_context` responses |
| `layout.*` | Extracted from the top-level frame's auto-layout properties |
| `prefetch.*` | Derived from fixed cache directory paths |

## Pre-fetch Directory Structure

```text
.figma-cache/
  page-screenshot.png          # Full-page screenshot
  variables.json               # Full get_variable_defs response
  {nodeId}/                    # Directory for each semantic unit node
    screenshot.png             # get_screenshot result
    context.json               # get_design_context result
```

The `:` in `nodeId` remains unchanged in the directory name, for example `10:1/`.

## Validation Rules

- `version` must be `"1.0"`
- `page_name` must not be empty
- `figma_file_key` must not be empty
- `design_system`, `code_rules`, `tokens`, `layout`, `project_patterns`, and `prefetch` must all exist
- The directory referenced by `prefetch.cache_dir` must actually exist
- Executor workers must not modify this file because it is read-only
