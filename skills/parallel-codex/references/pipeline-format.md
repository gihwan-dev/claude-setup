# Pipeline Format

parallel-codex 스킬이 프로젝트 루트에 생성하는 `PIPELINE.md` 파일 명세.
전체 파이프라인의 single source of truth.
Claude가 그룹 전이마다 상태를 업데이트하고, 세션 복구 시 이 파일을 읽어 재개한다.

## Format

```markdown
# Pipeline: <파이프라인 제목>

## Tasks
| ID  | Name | Description | Files | Group |
|-----|------|-------------|-------|-------|
| a1  | DB 스키마 | 유저 테이블 추가 | src/db/schema.ts | A |
| a2  | API 타입 | 유저 DTO 정의 | src/types/user.ts | A |
| b1  | 엔드포인트 | 유저 CRUD API | src/api/user.ts | B |

## Dependency Graph
a1, a2 → b1

## Groups
| Group | Tasks | Base Branch | Verify Branch | Status |
|-------|-------|-------------|---------------|--------|
| A | a1, a2 | main | temp/verify-a | pending |
| B | b1 | temp/verify-a | temp/verify-b | pending |

## MR Plan
| Source | Target | Status | URL |
|--------|--------|--------|-----|
| temp/verify-b | main | pending | |
```

## 필드 규칙

### Tasks 테이블
- **ID**: 짧은 고유 식별자. `<그룹소문자><번호>` 형태 (예: `a1`, `b2`)
- **Name**: 작업명 (한국어)
- **Description**: 작업 설명 (1줄)
- **Files**: 주로 수정할 파일/디렉토리 (쉼표 구분)
- **Group**: 소속 그룹 (A, B, C, ...)

### Dependency Graph
- 화살표(`→`)로 의존 방향 표시
- 쉼표(`,`)로 같은 레벨 작업 나열
- 독립 작업은 별도 줄

### Groups 테이블
- **Status**: `pending` → `running` → `verified`
- **Base Branch**: 워크트리 분기 기준 브랜치
- **Verify Branch**: 호환성 검증용 임시 브랜치 (`temp/verify-*`). 마지막 그룹의 Verify Branch가 MR 소스가 된다.

### MR Plan 테이블
- **Source**: 마지막 그룹의 Verify Branch (전체 변경이 통합된 브랜치)
- **Target**: 항상 `main`
- **Status**: `pending` → `created` → `merged`
  - `pending`: MR 미생성 (실행 미완료)
  - `created`: draft MR 생성됨
  - `merged`: main에 머지 완료
- **URL**: MR 생성 후 채움
- 항상 **1행**만 존재 (단일 MR)

## 상태 업데이트 시점

| 시점 | 업데이트 |
|------|---------|
| 그룹 실행 시작 | Groups Status → `running` |
| 그룹 검증 완료 | Groups Status → `verified` |
| MR 생성 완료 | MR Plan Status → `created`, URL 채움 |
| MR main 머지 완료 | MR Plan Status → `merged` |
| 작업 실패 | Tasks 테이블에 실패 표시 (Description에 `[FAILED]` 접두어) |
