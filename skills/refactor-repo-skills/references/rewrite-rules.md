# Rewrite Rules

이 문서는 `refactor-repo-skills`가 local skill을 압축 리팩토링할 때 따르는 기준이다.

## Official Snapshot

기준일: 2026-03-14

- OpenAI instruction guide: main instruction text는 짧게 유지하고, 계층 구조와 탐색성을 높인다.
- OpenAI skill-creator: `SKILL.md`는 핵심 workflow만 두고 상세는 `references/`나 `scripts/`로 분리한다.
- OpenAI Codex prompting guide: 장황한 upfront ceremony보다 명확한 목표, 경계, 실행 규칙을 우선한다.
- Anthropic Claude Code memory: root memory는 얇게 유지하고 `@import` 또는 분리 파일로 구조화한다.

## Compression Rules

### 1. Frontmatter Description

- trigger와 대상 범위를 먼저 적는다.
- 사용 시점, 핵심 결과물, 제외 범위를 짧게 적는다.
- 장문 배경 설명, 구현 철학, 반복 예시는 넣지 않는다.

### 2. SKILL.md Body

- 남겨야 할 내용은 workflow, selection logic, guardrail, validation entrypoint다.
- 실행에 직접 필요 없는 rationale, 장문 배경, 상세 카탈로그는 뺀다.
- 큰 표나 변형별 분기, 장문 예시는 `references/`로 이동한다.

### 3. References Split

- variants, rubric, templates, decision matrix는 `references/`로 이동한다.
- `SKILL.md`에서는 언제 어떤 reference를 읽어야 하는지만 남긴다.
- reference는 한 단계 깊이에서 끝내고, 필요할 때만 읽도록 명시한다.

### 4. Scripts Over Repetition

- 반복 계산, 냄새 점수, 파일 선택, deterministic transform은 `scripts/`로 옮긴다.
- 스크립트가 있으면 `SKILL.md`에는 실행 시점과 인자만 남긴다.

### 5. Agents Metadata

- `agents/openai.yaml`은 explicit invocation이 유용한 skill에만 추가한다.
- `display_name`, `short_description`, `default_prompt`는 사람과 모델이 빠르게 이해할 수 있게 짧게 적는다.
- default prompt는 scope와 기본 batch rule을 분명히 적는다.

### 6. What To Remove

- 불필요한 fallback 설명
- 중복 checklist
- 같은 의미를 반복하는 `Hard Rules`/`Rules`/`Checklist` 섹션
- 구현과 무관한 historical rationale
- extraneous docs를 요구하는 절차

### 7. Repo-Specific Boundaries

- canonical source는 항상 `skills/`다.
- generated 파일은 직접 수정하지 않고 sync로만 맞춘다.
- v1 범위는 `skills/`와 generated sync로 제한한다.
- `agent-registry`와 non-skill repo infrastructure는 참고만 하고 직접 수정하지 않는다.

## Rewrite Checklist

- frontmatter description이 trigger 중심인가?
- `SKILL.md` 본문이 workflow와 guardrail 위주인가?
- 장문 세부 규칙이 `references/` 또는 `scripts/`로 이동했는가?
- generated update는 sync 명령으로만 처리되는가?
- 새로 생긴 파일이 skill 기능에 직접 필요한 파일뿐인가?
