# Design Check Error Handling

## Hard Stop

| 상황 | 대응 |
|------|------|
| Figma URL에서 node-id를 파싱하지 못함 | 올바른 URL 예시와 함께 중단 |
| Figma screenshot 캡처 실패 | bbox 없이 진행하지 않고 중단 |
| 컴포넌트 파일 없음 | 경로 확인 요청 후 중단 |
| Storybook 빌드/캡처가 완전히 실패 | 재현 명령을 남기고 중단 |

## Continue With Warning

| 상황 | 대응 |
|------|------|
| `get_design_context` 실패 | 정성 분석 범위를 줄이고 진행 |
| `get_variable_defs` 실패 | Design Tokens 섹션을 `Not available`로 표기 |
| 이미지 크기 mismatch | 보고서에 mismatch를 명시하고 diff는 계속 생성 |

## Common Operator Guidance

- `FIGMA_TOKEN` 미설정: 토큰 생성 경로를 안내한다.
- 403: 파일 접근 권한/토큰 권한을 확인하게 한다.
- 404: fileKey 또는 nodeId를 다시 확인하게 한다.
- 이미지 URL null: 캡처 가능한 Figma 노드인지 확인하게 한다.
- 빈 스크린샷/타임아웃: Story URL과 `--timeout`, `--rebuild` 조건을 먼저 확인한다.
