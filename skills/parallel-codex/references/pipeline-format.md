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
| Group | Tasks | Base Branch | Stage Branch | Status |
|-------|-------|-------------|--------------|--------|
| A | a1, a2 | main | stage/group-a | pending |
| B | b1 | stage/group-a | stage/group-b | pending |

## MR Plan
| Source | Target | Type | Status | URL |
|--------|--------|------|--------|-----|
| parallel/a1-db-schema | stage/group-a | task | pending | |
| parallel/a2-api-types | stage/group-a | task | pending | |
| stage/group-a | main | group | pending | |
| parallel/b1-endpoint | stage/group-b | task | pending | |
| stage/group-b | stage/group-a | group | pending | |

## Merge Order
1. parallel/a1-db-schema → stage/group-a
2. parallel/a2-api-types → stage/group-a
3. stage/group-a → main
4. parallel/b1-endpoint → stage/group-b
5. stage/group-b → stage/group-a
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
- **Status**: `pending` → `running` → `done` → `mr_created`
- **Base Branch**: 워크트리 분기 기준 브랜치
- **Stage Branch**: 그룹 통합 브랜치

### MR Plan 테이블
- **Type**: `task` (개별 작업) 또는 `group` (그룹 통합)
- **Status**: `pending` → `created`
- **URL**: MR 생성 후 채움

### Merge Order
- 번호 순서대로 리뷰 + 병합
- task MR 먼저, group MR 나중 (그룹 단위로)
- 앞 그룹부터 뒤 그룹으로

## 상태 업데이트 시점

| 시점 | 업데이트 |
|------|---------|
| 그룹 실행 시작 | Groups Status → `running` |
| 그룹 머지 완료 | Groups Status → `done` |
| MR 생성 완료 | Groups Status → `mr_created`, MR Plan Status → `created`, URL 채움 |
| 작업 실패 | Tasks 테이블에 실패 표시 (Description에 `[FAILED]` 접두어) |
