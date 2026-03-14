---
name: reference-pack
description: >
  Advisory skill for task-local UI reference collection and curation. Use inside `design-task`
  whenever `delivery_strategy=ui-first` to search, shortlist, save, and document references under
  `tasks/<task-path>/DESIGN_REFERENCES/`, then feed those saved references into `UX_SPEC.md`.
---

# Workflow: Reference Pack

## Goal

`ui-first` planning에서 task-local reference evidence를 `tasks/<task-path>/DESIGN_REFERENCES/` 아래에
정리하고, `UX_SPEC.md`의 `Reference Pack (adopt/avoid)`가 저장된 파일과 이유를 직접 참조하게 만든다.

## Hard Rules

- 이 스킬은 `design-task` 내부 advisory workflow 전용이다.
- 저장 경로는 항상 `tasks/<task-path>/DESIGN_REFERENCES/`다.
- 결과물은 항상 `shortlist.md`, `manifest.json`, `raw/`, `curated/`를 포함한다.
- shortlist는 5~10개 후보를 남긴다.
- 최종 saved reference는 최소 3개를 남긴다. 기본 조합은 `adopt` 2개 + `avoid` 1개다.
- `manifest.json` entry schema는 `file`, `source_url`, `captured_at`, `kind`, `tags`, `adopt_reason`, `avoid_reason`, `notes`를 유지한다.
- `browser-explorer`나 web research는 후보/캡처 근거 수집에만 쓰고, repo file write는 main thread가 담당한다.
- 직접 저장 가능한 screenshot/component capture를 우선하고, raw hotlink asset만 남기지 않는다.
- overwrite가 필요한 기존 curated reference는 confirmation 없이는 덮어쓰지 않는다.

## Workflow

1. 기존 design system, shipped UI, Figma, repo-local screenshot source가 있으면 그것을 먼저 후보군에 포함한다.
2. 부족한 경우 browser/web research로 shortlist 후보를 5~10개 모은다.
3. 후보 중 adopt/avoid 판단이 가능한 3개 이상을 저장 대상으로 고른다.
4. `raw/`에는 캡처 원본을, `curated/`에는 문서에서 직접 참조할 최종 파일을 저장한다.
5. `shortlist.md`에는 후보 목록, source URL, selection status, adopt/avoid 이유를 기록한다.
6. `manifest.json`에는 saved reference만 남기고 `UX_SPEC.md`가 직접 참조할 `file` 경로를 기록한다.
7. `UX_SPEC.md`의 `Reference Pack (adopt/avoid)` 섹션에서는 saved file과 이유를 직접 요약한다.

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
