---
name: component-screenshot
description: >
  Capture component screenshots from Storybook stories.
  Use when you need to capture component screenshots from Story files, such as
  "/screenshot" or "capture a screenshot".
---


# Component Screenshot

This skill captures component screenshots from Storybook Story files.

## Workflow

### 1. Read the Story File

Read the Story file path provided by the user and extract:

- The `title` field from the meta object
- Exported Story names, such as `Default` and `WithIcon`

### 2. Convert to a Story ID

Generate the Story ID used internally by Storybook.

**Conversion rules:**

1. Convert the `title` value to lowercase.
2. Replace `/` with `-`.
3. Append the export name in kebab-case, separated by `--`.

**Conversion examples:**

| title | export | Story ID |
|-------|--------|----------|
| `Screenshots/Shared/Card` | `Default` | `screenshots-shared-card--default` |
| `Screenshots/Features/FilterBar/FilterList` | `Default` | `screenshots-features-filterbar-filterlist--default` |
| `Screenshots/Shared/Button` | `WithIcon` | `screenshots-shared-button--with-icon` |

**Detailed conversion:**

```
title: "Screenshots/Shared/Card" + export: "Default"
-> lowercase: "screenshots/shared/card"
-> `/` to `-`: "screenshots-shared-card"
-> + "--" + kebab(export): "screenshots-shared-card--default"
```

Convert PascalCase exports to kebab-case:
- `Default` → `default`
- `WithIcon` → `with-icon`
- `MSWExample` → `msw-example`

### 3. Determine the Viewport Size

Choose the viewport size in this priority order:

1. **User override**: when the user explicitly provides a size
2. **Story wrapper hint**: the `style={{ width: '...', height: '...' }}` value on the wrapper div inside `render`
3. **Default**: width=1280, height=800

### 4. Run the Capture

Run `${SKILL_DIR}/scripts/capture-screenshot.ts` to capture the screenshot.

The script serves a statically built Storybook (`.dist/`) through Express and captures from that server. Static files do not open an HMR websocket, so `networkidle` works reliably.

```bash
pnpm exec tsx ${SKILL_DIR}/scripts/capture-screenshot.ts \
  --story-id "{story-id}" \
  --output "artifacts/screenshots/{ComponentName}.png" \
  --width {width} --height {height}
```

**Script CLI options:**

| Option | Required | Default | Description |
|------|------|--------|------|
| `--story-id` | ✅ | - | Storybook story ID |
| `--output` | ✅ | - | Output PNG file path |
| `--width` | ❌ | 1280 | Viewport width |
| `--height` | ❌ | 800 | Viewport height |
| `--port` | ❌ | 6008 | Static server port |
| `--timeout` | ❌ | 30000 | Timeout in ms |
| `--rebuild` | ❌ | false | Ignore the existing build and rebuild |

- If `.dist/iframe.html` is missing, the script automatically runs `pnpm build-storybook`.
- If `--rebuild` is passed, the script ignores the existing build and always rebuilds.
- After navigation, it captures the first child under `#storybook-root > *`.

### 5. Validate the Result

After capture, confirm:

- The PNG file was created
- The file size is greater than 0 to catch empty screenshots
- The final file path is reported back to the user

## Error Handling

| Situation | Response |
|------|------|
| Story file missing | Stop and ask the user to verify the file path |
| Failed to parse `title` | Ask the user to verify the Story file format |
| Storybook build failure | Suggest running `pnpm build-storybook` manually to inspect the error |
| Empty screenshot (0 bytes) | Suggest checking the Story ID directly in the browser after serving the static build at `http://localhost:6006/iframe.html?id={story-id}&viewMode=story` |
| Capture script error | Surface the error message and show the manual command |

## Examples

### Input

```
/screenshot __screenshots__/Card.stories.tsx
```

### Execution

1. Read `__screenshots__/Card.stories.tsx`
2. Extract `title: Screenshots/Shared/Card` and `export: Default`
3. Generate Story ID `screenshots-shared-card--default`
4. Resolve the viewport: width=384 from the wrapper div, height=800 default
5. Run:
   ```bash
   pnpm exec tsx ${SKILL_DIR}/scripts/capture-screenshot.ts \
     --story-id "screenshots-shared-card--default" \
     --output "artifacts/screenshots/Card.png" \
     --width 384 --height 800
   ```
6. Confirm that `artifacts/screenshots/Card.png` was created

### When Multiple Story Exports Exist

If the Story file has multiple exports, ask the user which Story to capture.

```
/screenshot __screenshots__/Button.stories.tsx
```

-> Found three exports: `Default`, `WithIcon`, `Disabled`
-> Ask the user which one to capture, or whether to capture all of them
