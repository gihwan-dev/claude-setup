---
name: change-architecture-doc
description: >
  Analyze git changes and generate/update architecture documentation with Mermaid diagrams.
  현재 브랜치와 워크트리의 git 변경사항을 분석해 아키텍처 중심 변경 문서를 생성하거나 갱신한다.
  프로젝트 안에서 이미 문서가 관리되는 폴더(docs, packages/docs, guides, documentation, doc)를 우선 사용하고,
  적합한 위치가 없으면 프로젝트 루트에 마크다운 문서를 생성한다. 세부 구현보다 시스템 경계,
  모듈 상호작용, 데이터/이벤트 흐름, 영향 범위를 Mermaid 다이어그램으로 시각화해 기록해야 할 때 사용한다.
  트리거: "변경사항 문서화", "브랜치 작업 문서 정리", "아키텍처 문서 업데이트", "worktree 변경 요약", "머메이드 문서".
---

# Change Architecture Doc

현재 작업 브랜치에서 발생한 구조적 변화를 빠르게 문서화한다.

## 핵심 원칙

- 구현 디테일보다는 시스템 흐름과 구조를 설명한다.
- 변경된 파일 목록을 그대로 나열하지 말고 "왜 구조가 바뀌었는지"를 먼저 기록한다.
- Mermaid 다이어그램을 최소 2개 이상 포함한다.
- 문서 위치는 기존 문서 폴더를 우선 사용하고, 없으면 루트로 폴백한다.

## 워크플로우

### 1) 변경 범위를 확인한다

- 작업 루트에서 `git status --short`로 워킹 트리 상태를 확인한다.
- `git branch --show-current`로 브랜치 이름을 확인한다.
- 변경 범위를 읽기 쉽게 수집한다.

```bash
git status --short
git diff --name-status
git diff --stat
```

- 공통 조상 기준이 필요하면 merge-base 기반 diff를 추가로 확인한다.

```bash
BASE_REF=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/@@')
[ -z "$BASE_REF" ] && BASE_REF="origin/main"
MERGE_BASE=$(git merge-base HEAD "$BASE_REF" 2>/dev/null || true)
[ -n "$MERGE_BASE" ] && git diff --name-status "$MERGE_BASE"...HEAD
```

### 2) 문서 대상 폴더를 결정한다

- 아래 스크립트로 문서화 폴더를 자동 탐색한다.

```bash
python3 ${SKILL_DIR}/scripts/find_doc_target.py
```

- 반환값 `target_kind`가 `docs`이면 `target_path`를 사용한다.
- 반환값 `target_kind`가 `root`이면 저장 위치를 프로젝트 루트로 결정한다.
- 문서화 폴더가 여러 개여도, 현재 변경 범위와 가장 가까운 위치를 우선 사용한다.

### 3) 기존 문서를 우선 수정하고, 없으면 새 문서를 만든다

- 대상 폴더에서 아래 이름 패턴의 문서를 먼저 찾는다.
  - `*architecture*.md*`
  - `*design*.md*`
  - `*overview*.md*`
  - `*change*.md*`
- 관련 문서가 존재하면 해당 문서의 "아키텍처/구조/흐름" 섹션을 갱신한다.
- 관련 문서가 없으면 새 파일을 생성한다.
  - 파일명 규칙: `architecture-change-<branch>-<YYYY-MM-DD>.md`
  - 브랜치명 `/`는 `-`로 치환한다.

### 4) 아키텍처 중심 문서를 작성한다

- `${SKILL_DIR}/references/doc-template.md` 구조를 기본으로 사용한다.
- `${SKILL_DIR}/references/mermaid-patterns.md`에서 상황에 맞는 Mermaid 패턴을 선택한다.
- 최소 2개 이상의 Mermaid 다이어그램을 포함한다.
  - 1개: 시스템/모듈 구조(예: flowchart, C4 component)
  - 1개: 요청/데이터/이벤트 흐름(예: sequenceDiagram)
- 세부 구현(함수 단위 로직, 미세한 타입 변경) 설명 비중은 20% 이내로 제한한다.

### 5) 품질 게이트를 통과시킨다

- 문서에 아래 항목이 모두 있는지 확인한다.
  - 변경 배경(왜 바뀌었는지)
  - 변경 전/후 구조 설명
  - Mermaid 다이어그램 2개 이상
  - 영향 범위 및 리스크
  - 후속 작업 또는 오픈 질문
- 다이어그램 문법 오류가 없는지 렌더링 가능한 형태로 점검한다.
- 변경 파일 목록과 문서의 영향 범위가 논리적으로 연결되는지 확인한다.

## 출력 규칙

- 첫 단락에 "이번 변경의 구조적 요약"을 3~5문장으로 작성한다.
- 문체는 설명형으로 유지하고, 체크리스트 나열만으로 끝내지 않는다.
- 문서 마지막에 "문서 기준 시점"과 "분석한 git 범위"를 남긴다.
- 사용자가 추가 컨텍스트를 주면 기존 문서를 패치 방식으로 갱신한다.

## 참조 파일

- 문서 템플릿: `${SKILL_DIR}/references/doc-template.md`
- Mermaid 패턴: `${SKILL_DIR}/references/mermaid-patterns.md`
- 문서 위치 탐색 스크립트: `${SKILL_DIR}/scripts/find_doc_target.py`
