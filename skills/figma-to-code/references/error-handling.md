# Error Handling And Output

`figma-to-code` 실행 중 자주 만나는 예외와 결과 요약 형식을 정리한다.

## Overwrite Policy

- 대상 파일이 비어 있지 않으면 overwrite 여부를 먼저 확인한다.
- overwrite가 거부되면 새 파일 경로를 제안하거나 중단한다.

## Error Cases

| 상황 | 대응 |
|---|---|
| URL에 `node-id`가 없음 | 올바른 Figma URL 형식을 요청하고 `node-id`가 필요하다고 안내 |
| MCP 호출 실패 | Figma Desktop 앱을 실행하고 대상 파일을 열어 달라고 안내 |
| 변수/토큰 매칭 실패 | 가장 가까운 토큰을 사용하고 TODO를 남김 |
| 대상 파일이 비어 있지 않음 | overwrite 확인 전까지 쓰지 않음 |

## Result Summary Format

```text
Figma -> Code 완료: {ComponentName}

사용된 디자인 토큰:
- 색상: {token list}
- 타이포: {type list}
- 기타: {radius/shadow/etc}

사용된 컴포넌트:
- @exem-fe/react: {...}
- @exem-fe/icon: {...}
- @/shared/ui: {...}

생성된 파일: {component path}
```

## Example Input

```text
/figma-to-code https://figma.com/design/abc123/MyProject?node-id=1-2 src/features/widget-builder/ui/ColumnHeader.tsx
```

## Example Execution Summary

```text
1. 입력 파싱: nodeId=`1:2`, component=`ColumnHeader`
2. Figma 데이터 수집: screenshot/context/variables
3. 로컬 패턴 탐색: `src/shared/ui/` 및 형제 파일 확인
4. 토큰 매핑: Figma 값 -> Tailwind token class
5. 코드 생성: `ColumnHeader.tsx`
6. 검증: token usage, import alias, named export 확인
```
