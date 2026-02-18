---
name: clean-code-inspector
description: |
  TS/JS 특화 코드 품질 분석 스킬. AST/정적분석 기반 정량 메트릭과 정성 오버레이(근거 기반 루브릭)를
  결합해 clean-code-inspect-result.json / .md를 생성한다.
  트리거: "코드 리뷰", "품질 검사", "클린 코드", "인스펙션", "코드 분석" 등
---

# Clean Code Inspector v2.1 (AST 기반 정량 + 정성 오버레이)

## 핵심 원칙

- **정량 자동 생성**: 수동 계수 대신 AST/정적분석 도구로 `quantitative-metrics.json`을 생성한다.
- **정성은 오버레이**: 정량 `Hotspot 상위 20%` 파일에만 적용한다.
- **근거 필수**: 정성 항목은 파일+라인 근거 2개 이상 없으면 `N/A` 처리한다.
- **고정 가중치**: 최종 점수는 `정량 85% + 정성 15%`를 사용한다.
- **정성 단독 Fail 금지**: 정량이 통과인데 정성만으로 실패시키지 않는다.

## Phase 1: 입력 해석 및 파일 수집

사용자 인자를 아래 표에 매칭해 diff 명령을 결정한다.

| 입력 패턴 | 파일 목록 명령 | 분석 모드 |
|-----------|---------------|-----------|
| (없음) | `git diff --name-only` | `working` |
| `staged`, `--cached` | `git diff --cached --name-only` | `staged` |
| 브랜치명 (예: `main`, `develop`) | `git diff {branch}...HEAD --name-only` | `branch` + target=branch |
| 커밋 범위 `abc..def` | `git diff abc..def --name-only` | `range` + target=abc..def |
| 파일 경로 직접 지정 | (입력 그대로 사용) | `files` + target="a.ts,b.ts" |

필터링 규칙:
- 포함: `.ts`, `.tsx`, `.js`, `.jsx`
- 제외: `node_modules/`, `.d.ts`, `*.config.ts`, `*.config.js`, `*.stories.tsx`, `dist/`, `build/`
- 결과 0개: `분석 가능한 변경 파일이 없습니다.` 출력 후 종료
- 결과 25개 초과: 범위 축소 여부를 먼저 확인

## Phase 2: Toolchain 보장 + 정량 자동 수집

### 2-1) Toolchain 보장

먼저 다음 명령으로 의존성 상태를 확인한다.

```bash
node "${CODEX_HOME:-$HOME/.codex}/skills/clean-code-inspector/scripts/ensure-toolchain.mjs" \
  --skill-dir "${CODEX_HOME:-$HOME/.codex}/skills/clean-code-inspector" \
  --auto-install true
```

동작 규칙:
- 패키지 누락 시 `pnpm --dir <skill_dir> install --frozen-lockfile` 1회 자동 시도
- 실패 시 `analysisMode=degraded`로 계속 진행
- 누락 사유는 `unavailableMetrics`에 누적

### 2-2) 정량 JSON 생성

```bash
node "${CODEX_HOME:-$HOME/.codex}/skills/clean-code-inspector/scripts/collect-quantitative-metrics.mjs" \
  --project-root "{project_root}" \
  --mode "{working|staged|branch|range|files}" \
  --target "{target_if_needed}" \
  --window-days 90 \
  --profile "balanced" \
  --out ".clean-code-inspector/quantitative-metrics.json" \
  --out-unavailable ".clean-code-inspector/unavailable-metrics.json"
```

수집 규칙:
- 기본 분석 범위는 `변경 파일 + import 클로저`
- import 클로저는 BFS 전이 탐색, 기본 상한 300파일
- 상한 초과 시 잘라내고 `unavailableMetrics`에 기록

산출물:
- `.clean-code-inspector/quantitative-metrics.json`
- `.clean-code-inspector/unavailable-metrics.json`

## Phase 3: Hotspot 상위 20% 선정

정량 JSON의 `files[].hotspotScore`를 기준으로 내림차순 정렬한다.
- 상위 `max(1, ceil(N * 0.2))` 파일만 정성 평가 대상

## Phase 4: Qualitative Overlay (정성)

`architect-reviewer`를 Hotspot 파일에만 실행한다.

참조 문서:
- `references/qualitative-rubric.md`
- `references/scoring-model-v2.md`

필수 규칙:
- 5개 기준만 평가: `Intent Clarity`, `Local Reasoning`, `Failure Semantics`, `Boundary Discipline`, `Test Oracle Quality`
- 각 항목 `0~4점` 앵커드 루브릭
- 항목별 근거가 2개 미만이면 `N/A`
- `Boundary Discipline` 위반, `Failure Semantics` 부재는 `criticalFlags`에 반드시 기록

산출물:
- `.clean-code-inspector/qualitative-overlay.json`

## Phase 5: 스코어카드 생성

```bash
node "${CODEX_HOME:-$HOME/.codex}/skills/clean-code-inspector/scripts/build-scorecard.mjs" \
  --quant ".clean-code-inspector/quantitative-metrics.json" \
  --qual ".clean-code-inspector/qualitative-overlay.json" \
  --out-json "clean-code-inspect-result.json" \
  --out-md "clean-code-inspect-result.md" \
  --profile "balanced"
```

결과 규칙:
- 최종 점수 = `정량점수×0.85 + 정성점수×0.15`
- 정성 단독 fail 금지
- `criticalFlags[]`는 등급과 별개로 경고 표시

## Phase 6: 사용자 요약 출력

최종 요약은 아래 항목을 포함한다:
- 분석 대상 파일 수
- 정량/정성 점수와 최종 점수
- Hotspot 대상 파일 수
- Critical Flags 요약
- `clean-code-inspect-result.md` 저장 경로

## 리포트 필수 섹션

`clean-code-inspect-result.md`에는 다음 섹션이 반드시 있어야 한다:
1. `정성 오버레이 결과`
2. `정량-정성 교차 시그널`
3. `Critical Flags`
