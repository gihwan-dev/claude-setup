# Clean Code Inspector Scoring Model v2.1

## 1) 목적

이 문서는 clean-code-inspector v2.1 점수 계산 규칙을 정의한다.
핵심 원칙은 **AST/정적분석 기반 정량 측정** 위에 **근거 있는 정성 오버레이**를 얹는 것이다.

## 2) 최종 점수 공식

- 정량 점수(0~100): `Q`
- 정성 점수(0~100): `S`
- 최종 점수(0~100): `F`

`F = Q * 0.85 + S * 0.15`

정성 데이터가 모두 `N/A`인 경우:
- `F = Q`
- 왜 `N/A`인지 `unavailableMetrics`에 사유를 남긴다.

## 3) 정량 축 정의 및 가중치

정량 축은 아래 4개로 고정한다.

1. Complexity (35)
2. Type Safety (30)
3. Test Reliability (20)
4. Change Risk (15)

각 축 계산에 필요한 데이터가 부족하면 해당 축은 `N/A`로 표시한다.
축별 재정규화는 하지 않는다.

## 4) 정성 오버레이 범위

- 정성 평가는 정량 기준 `Hotspot 상위 20%` 파일에만 적용한다.
- 파일 수가 적어도 `최소 1개`는 평가 대상에 포함한다.

## 5) 정성 항목 및 점수 변환

정성 항목은 아래 5개로 고정한다.

1. Intent Clarity
2. Local Reasoning
3. Failure Semantics
4. Boundary Discipline
5. Test Oracle Quality

각 항목은 `0~4점`으로 평가하고, 항목 점수 평균을 `avgC`라고 할 때:

`S = avgC * 25`

## 6) 근거 부족 처리

각 항목은 코드 근거(파일+라인) 2개 이상이 있어야 점수로 인정한다.
- 근거 2개 미만: 항목 점수 `N/A`
- `N/A` 항목은 평균 계산에서 제외

## 7) 정성 단독 Fail 금지

정량 점수가 Fail이 아닌데 정성 반영으로 최종이 Fail이 되면 안 된다.
- Fail 기준은 `F < 50` (grade F)
- `Q >= 50`이고 `F < 50`이면 `F`를 50으로 보정하고 로그를 남긴다.

## 8) Critical Flag 규칙

등급과 무관하게 아래 항목은 강제 경고한다.

- `boundary_discipline_violation`
- `missing_failure_semantics`

Critical Flag는 반드시 `criticalFlags[]`에 기록하고,
`clean-code-inspect-result.md`의 `Critical Flags` 섹션에 출력한다.

## 9) 등급 기준

- A: 90~100
- B: 80~89.99
- C: 70~79.99
- D: 60~69.99
- E: 50~59.99
- F: 0~49.99

## 10) 출력 스키마 요구사항

### `quantitative-metrics.json`

- `schemaVersion`, `generatedAt`, `profile`, `analysisMode`
- `files[]`: `{ path, metrics, hotspotScore }`
- `files[].metrics` 필수 키:
  - `cyclomatic`, `cognitive`, `halsteadVolume`, `maintainabilityIndex`
  - `locLogical`, `locPhysical`, `importCount`, `stateCount`
  - `anyCount`, `assertionCount`, `tsIgnoreCount`
  - `lineCoverage`, `branchCoverage`, `mutationScore`
  - `churnLines`, `churnTouches`
  - `fanIn`, `fanOut`, `instability`, `circular`
- `axes`: `complexity`, `typeSafety`, `testReliability`, `changeRisk`
- `summary`: `quantitativeScore`, `quantitativeGrade`
- `unavailableMetrics[]`

### `clean-code-inspect-result.json`

- `qualitativeOverlay.criteria[]`
- `qualitativeOverlay.score`
- `qualitativeOverlay.evidence[]`
- `criticalFlags[]`
