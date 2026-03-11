# Design Check Workflow Details

`SKILL.md`의 core flow를 실제 단계/명령으로 펼친 문서다.

## Stage 1: 병렬 수집

### A. Figma screenshot + bbox metadata

```bash
pnpm exec tsx ${SKILL_DIR}/scripts/capture-figma-screenshot.ts \
  --url "{figmaUrl}" \
  --output "artifacts/screenshots/figma/{Name}.png" \
  --scale 2
```

- `.meta.json`에서 `bbox.width`, `bbox.height`를 읽는다.
- `bbox.width`는 이후 구현 캡처의 `--container-width`로 연결한다.

### B. Figma context + variable definitions

- `get_design_context(nodeId)`
- `get_variable_defs(nodeId)`

Task B 실패는 warning으로 남기고 진행할 수 있다.

### C. Story preparation

- 컴포넌트 export, props, import dependency를 분석한다.
- screenshot Story는 `../_shared/storybook-screenshot-guidelines.md` 규칙을 따른다.
- 새 Story를 만들면 `../_shared/storybook-screenshot-template.tsx`를 출발점으로 쓴다.

## Stage 2: bbox injection + implementation capture

1. Story wrapper width placeholder를 `bbox.width`로 교체한다.
2. Storybook story id를 만든다.
3. 구현 캡처를 수행한다.

```bash
pnpm exec tsx ${SKILLS_ROOT}/component-screenshot/scripts/capture-screenshot.ts \
  --story-id "{storyId}" \
  --output "artifacts/screenshots/impl/{Name}.png" \
  --width {viewportWidth} \
  --height {viewportHeight} \
  --scale 2 \
  --container-width {bboxWidth} \
  --rebuild
```

## Stage 3: quantitative compare

```bash
pnpm exec tsx ${SKILL_DIR}/scripts/compare-screenshots.ts \
  --base "artifacts/screenshots/figma/{Name}.png" \
  --current "artifacts/screenshots/impl/{Name}.png" \
  --output "artifacts/screenshots/diff/{Name}.png"
```

보고서에는 최소한 아래를 넣는다.

- `diffPixels`
- `diffRatio`
- `result`
- size mismatch 여부

## Stage 4: qualitative review

비교 대상:

- layout / alignment / spacing
- typography
- color
- icon/image size and placement
- responsive/container fit

severity는 `Critical`, `Major`, `Minor`, `Nitpick` 네 단계로 정리한다.

## Report Skeleton

출력 위치: `artifacts/design-check/{Name}-report.md`

필수 섹션:

1. Executive Summary
2. Quantitative Analysis
3. Qualitative Analysis
4. Design Tokens
5. Recommendations
6. Artifacts
