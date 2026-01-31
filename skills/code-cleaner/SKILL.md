---
name: unused-code-cleaner
description: "AI 코드 생성 후 불필요한 코드 정리 스킬. git diff로 변경된 TS/JS 파일을 분석하여 사용되지 않는 코드를 자동 제거한다. 트리거: unused 코드 정리, 불필요한 코드 삭제, dead code 제거, 코드 클린업, AI 작업 후 정리 요청 시"
---

# Unused Code Cleaner

AI 코드 생성 후 발생하는 불필요한 코드를 자동으로 정리한다.

## 워크플로우

### 1. 변경된 파일 확인

```bash
git diff --name-only HEAD
```

staged 파일 포함 시:
```bash
git diff --name-only HEAD --staged
```

특정 커밋/브랜치 비교 시:
```bash
git diff --name-only <base>..<target>
```

### 2. TS/JS 파일 필터링

확장자 필터: `.ts`, `.tsx`, `.js`, `.jsx`

제외 대상:
- `node_modules/`
- `.d.ts` 파일 (타입 선언)
- 설정 파일 (`*.config.ts`, `*.config.js`)

### 3. 파일별 분석 및 수정

각 파일을 읽고 다음 패턴을 찾아 제거:

#### 제거 대상 (lint/TS로 못 잡는 것들)

| 패턴 | 설명 |
|------|------|
| Unused exports | 새로 추가된 export 중 프로젝트 어디서도 import 안 되는 것 |
| Unused functions | 정의 후 호출되지 않는 함수 |
| Unused types/interfaces | 참조되지 않는 타입 선언 |
| Commented code blocks | 주석 처리된 코드 블록 (설명 주석은 유지) |
| Orphan console.log | 디버깅용으로 추가된 console.log |

#### Unused Export 탐지 방법

1. `git diff`로 새로 추가된 export 식별:
```bash
git diff HEAD -- <file> | grep "^+" | grep -E "export (const|function|class|type|interface|enum)"
```

2. 프로젝트 전체에서 해당 export가 import되는지 확인:
```bash
grep -r --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" "import.*<export_name>.*from" .
grep -r --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" "{ <export_name>" .
```

3. 어디서도 import 안 되면 삭제

#### 주의사항

- 동적 import (`import()`)로 사용될 수 있으므로 해당 패턴도 검색
- barrel file (index.ts)에서 re-export되는 경우 추적
- 주석 중 TODO, FIXME, NOTE, 설명 주석은 유지

### 4. 수정 적용

파일 수정 후 변경 사항 요약 출력:
- 제거된 import 수
- 제거된 변수/함수 수
- 제거된 코드 라인 수

## 사용 예시

```
사용자: 방금 작업한 코드 unused 정리해줘
사용자: git diff 보고 불필요한 코드 삭제해
사용자: dead code 클린업
```
