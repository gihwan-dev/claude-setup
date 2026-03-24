---
name: reference-pack
description: >
  Advisory skill for task-local UI reference collection and curation. Use inside
  design-task whenever delivery_strategy=ui-first to search, shortlist, save, and
  document references under DESIGN_REFERENCES/. Do not invoke standalone outside
  of a design-task context.
allowed-tools: Read, Grep, Glob, Write, Agent
---

# Workflow: Reference Pack

## Goal

Curate task-local reference evidence under `tasks/<task-path>/DESIGN_REFERENCES/` for `ui-first` planning, and make `UX_SPEC.md` reference the saved files and their reasons directly in `Reference Pack (adopt/avoid)`.

## Hard Rules

- This skill is advisory-only and only runs inside `design-task`.
- The save path is always `tasks/<task-path>/DESIGN_REFERENCES/`.
- Outputs always include `shortlist.md`, `manifest.json`, `raw/`, and `curated/`.
- Keep 5 to 10 shortlist candidates.
- Keep at least 3 final saved references. The default mix is 2 `adopt` and 1 `avoid`.
- Preserve the `manifest.json` entry schema: `file`, `source_url`, `captured_at`, `kind`, `tags`, `adopt_reason`, `avoid_reason`, `notes`.
- Use `browser-explorer` or web research only to gather candidates and capture evidence; repository writes stay with the main thread.
- Prefer screenshots or component captures you can save directly instead of leaving only raw hotlinked assets.
- Do not overwrite an existing curated reference without confirmation.

## Workflow

1. Include any existing design system, shipped UI, Figma, or repo-local screenshot source first.
2. If that is not enough, gather 5 to 10 shortlist candidates through browser or web research.
3. Save at least 3 candidates that support a clear adopt or avoid judgment.
4. Save raw captures under `raw/` and final document-facing assets under `curated/`.
5. Record candidate list, source URL, selection status, and adopt or avoid reasoning in `shortlist.md`.
6. Keep only saved references in `manifest.json` and record the `file` paths that `UX_SPEC.md` should cite directly.
7. In `UX_SPEC.md`, summarize the saved files and reasons directly inside `Reference Pack (adopt/avoid)`.

## `shortlist.md` Minimum Fields

- title
- source URL
- selected status (`selected` / `rejected`)
- intended use (`adopt` / `avoid`)
- notes

## `manifest.json` Example

```json
[
  {
    "file": "curated/timeline-shell-adopt.svg",
    "source_url": "https://example.com/shell",
    "captured_at": "2026-03-14T00:00:00Z",
    "kind": "adopt",
    "tags": ["shell", "desktop", "dense"],
    "adopt_reason": "3-pane hierarchy and strong orientation.",
    "avoid_reason": "",
    "notes": "Use for app-shell and density guidance."
  }
]
```
