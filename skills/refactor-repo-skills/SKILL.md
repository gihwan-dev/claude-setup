---
name: refactor-repo-skills
description: >
  Repository-specific execution skill for refactoring verbose local skills. Audit `skills/*/SKILL.md`,
  score verbosity and structure smells, then rewrite only the top 1-3 candidates or a user-specified
  skill/path so the source of truth stays concise. Keep scope to `skills/` and generated skill index
  sync only; do not edit `agent-registry` or non-skill repo infrastructure.
---

# Refactor Repo Skills

`skills/`를 source-of-truth 기준으로 압축 리팩토링한다. 기본 동작은 전체 감사 후 상위 1~3개 후보만 수정하는 배치 실행이다.

## Hard Rules

- 항상 `python3 ${SKILL_DIR}/scripts/audit_skills.py`로 감사부터 시작한다.
- 사용자가 `skill name` 또는 `path`를 주면 해당 대상만 수정한다.
- 대상이 없으면 감사 결과 상위 1~3개만 수정한다.
- generated 파일(`skills/INDEX.md`, `skills/manifest.json`)은 직접 수정하지 않고 sync로만 맞춘다.
- v1 범위는 `skills/`와 generated sync뿐이다. `agent-registry`와 non-skill repo infrastructure는 수정하지 않는다.
- `SKILL.md` 본문에는 workflow, selection logic, guardrail만 남긴다.
- 변형, 상세 기준, 예시, 장문 rationale은 `references/`로 이동한다.
- 불필요한 fallback, 중복 checklist, 반복 explanation, 장문 non-goal은 제거한다.
- extraneous docs(`README.md`, `CHANGELOG.md`, `INSTALLATION_GUIDE.md` 등)는 만들지 않는다.
- 한 배치에서 source-of-truth 수정 대상은 최대 3개 skill이다.

## Required References

- rewrite 기준이 필요할 때 `${SKILL_DIR}/references/rewrite-rules.md`를 읽는다.

## Workflow

1. `audit_skills.py`로 전체 또는 지정 scope를 스캔한다.
2. score와 이유를 보고 상위 1~3개 후보를 고른다.
3. 대상 skill의 `SKILL.md`, 필요 시 `references/`, `agents/openai.yaml`을 읽고 source-of-truth 구조를 판단한다.
4. frontmatter description을 trigger 중심으로 압축하고, 본문은 workflow와 guardrail만 남긴다.
5. 세부 규칙이 필요하면 같은 skill의 `references/`로 분리한다.
6. `agents/openai.yaml`이 없고 explicit invocation이 유용하면 추가한다.
7. `python3 scripts/sync_skills_index.py`와 `python3 scripts/sync_skills_index.py --check`로 generated output을 맞춘다.
8. 필요 시 `python3 scripts/install_assets.py --dry-run --target all`과 관련 테스트를 실행하고 결과와 잔여 리스크를 요약한다.

## Targeting

- 기본 입력 없음: 전체 감사 + 상위 1~3개 수정.
- `skill name` 또는 `path`가 주어지면 해당 대상만 수정.
- 후보가 이미 짧고 구조가 명확하면 수정하지 않고 감사 결과만 보고한다.

## Validation

- `python3 ${SKILL_DIR}/scripts/audit_skills.py --limit 5`
- `python3 scripts/sync_skills_index.py`
- `python3 scripts/sync_skills_index.py --check`
- `python3 scripts/install_assets.py --dry-run --target all`
