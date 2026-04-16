---
name: hyperagent-evolve
description: >
  에이전트/스킬 프로필의 자가 개선 파이프라인. 세션 로그를 분석하고 성능을 채점한 뒤,
  개선이 필요한 엔티티의 프로필을 직접 리라이팅하여 적용한다.
  "$hyperagent-evolve", "/hyperagent-evolve", "자가 개선", "에이전트 진화",
  "evolve 돌려줘", "하이퍼에이전트 실행" 등을 입력할 때 사용한다.
  스케줄에서 자동 실행될 때도 이 스킬을 사용한다.
  에이전트나 스킬의 품질 개선, 성능 분석, 프롬프트 최적화 관련 요청에도 사용한다.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# HyperAgent Evolve

에이전트와 스킬 프로필의 자가 개선 파이프라인을 실행한다.
데이터 처리는 Python 스크립트가, 프로필 리라이팅은 이 스킬을 실행하는 Claude가 직접 수행한다.

## 레포 구조 (claude-setup)

이 스킬이 속한 레포는 Claude Code와 Codex CLI 환경을 통합 관리하는 설정 레포다.

- `agent-registry/` — 에이전트 SSOT. 각 에이전트별 `agent.toml`(설정) + `instructions.md`(프로필).
- `skills/` — 스킬 정의. 각 스킬별 `SKILL.md`.
- `scripts/sync_agents.py` — agent-registry → `agents/`(Claude Code용 .md) + `dist/codex/agents/`(Codex용 .toml) 동기화.
- `scripts/install_assets.py --link` — `dist/` → `~/.codex/`, `skills/` → `~/.claude/skills/` 심링크 설치.
- `agents/` — sync_agents.py가 생성하는 Claude Code 서브에이전트 프로필 (자동생성, 직접 편집 금지).
- `dist/codex/` — sync_agents.py가 생성하는 Codex 에이전트 설정 (자동생성, 직접 편집 금지).

프로필 수정 시 반드시 `agent-registry/`(에이전트) 또는 `skills/`(스킬)의 원본을 편집해야 한다.
`apply.py`가 SSOT 복사 → git commit → sync_agents.py → install_assets.py --link을 일괄 수행한다.

**데이터 소스**: Claude Code 세션(`~/.claude/projects/`)과 Codex 세션(`~/.codex/sessions/`, `~/.codex/archived_sessions/`)을 모두 자동으로 분석한다. Codex 서브에이전트 세션도 포함하여 에이전트별 성능 데이터를 수집한다.

## 파이프라인

```
analyze_sessions.py → score.py → generate_variant.py → 프로필 리라이팅 → archive.py → apply.py
```

## 실행 절차

### Step 1: 세션 분석

사용자가 날짜를 지정하지 않으면 **당일(오늘)** 기준으로 실행한다.
오후 10시 스케줄 실행 시에도 당일 세션을 분석 대상으로 한다.
Claude와 Codex 세션을 모두 자동으로 탐색한다.

```bash
python3 scripts/hyperagent/analyze_sessions.py \
  --json --date-range {TODAY} {TODAY} --min-turns 3 \
  > /tmp/hyperagent-analysis.json
```

출력이 `"sessions_analyzed": 0`이면 "분석할 세션 없음"을 보고하고 종료.

### Step 2: 성능 채점

```bash
python3 scripts/hyperagent/score.py \
  --json --baseline ~/.claude/hyperagent/baseline.json \
  --input /tmp/hyperagent-analysis.json \
  > /tmp/hyperagent-scores.json
```

`/tmp/hyperagent-scores.json`을 Read 도구로 읽어 `improvements` 배열을 확인한다.
비어 있으면 "개선 대상 없음"을 보고하고 종료.

### Step 3: 변종 계획

```bash
python3 scripts/hyperagent/generate_variant.py \
  --json --max-variants 3 \
  --input /tmp/hyperagent-scores.json \
  > /tmp/hyperagent-plan.json
```

variant 디렉토리와 meta.json만 생성된다. 프로필 내용은 생성되지 않는다.

`/tmp/hyperagent-plan.json`을 읽어 `variants` 배열을 확인한다. 각 variant에는:
- `source_path`: 원본 프로필 경로 (repo-relative)
- `variant_file`: 리라이팅 결과를 쓸 경로 (repo-relative)
- `variant_dir`: variant 디렉토리 경로
- `suggestion`: 개선 방향 설명
- `reason`: 개선이 필요한 차원 (accuracy, relevance 등)

### Step 4: 프로필 리라이팅

각 variant에 대해:

1. Read로 `source_path` 원본 프로필을 읽는다.
2. Read로 `{variant_dir}/meta.json`을 읽어 `change_reason`, `evidence_sessions`, `source_score`를 확인한다.
3. 아래 리라이팅 규칙에 따라 프로필을 수정한다.
4. Write로 `variant_file` 경로에 결과를 쓴다.

#### 리라이팅 규칙

원본 프로필을 개선할 때 다음 원칙을 지킨다:

- **구조 보존**: 원본의 섹션 구조, 포맷, 마크다운 스타일을 유지한다.
- **정밀 보강**: `change_reason`이 지적하는 약점만 보강한다. 무관한 섹션은 건드리지 않는다.
- **자연 삽입**: 보강 내용을 기존 섹션 안에 녹인다. "## HyperAgent 개선" 같은 별도 섹션을 추가하지 않는다.
- **메타 금지**: 주석, 패치 마커, 변경 이력을 프로필에 넣지 않는다.
- **행동 지침**: 일반론("근거를 확인하세요") 대신 구체적 행동("파일 경로를 인용하기 전에 Grep으로 존재를 확인한다")으로 쓴다.
- **최소 변경**: 3줄로 충분하면 3줄로 끝낸다. 과잉 확장하지 않는다.
- **언어 유지**: 원본이 영어면 영어로, 한국어면 한국어로 쓴다.
- **의도 충실**: 에이전트/스킬의 핵심 역할이나 성격을 바꾸지 않는다. 약한 부분을 보강할 뿐이다.

### Step 5: 아카이브 및 적용

각 variant에 대해 순서대로 실행:

```bash
python3 scripts/hyperagent/archive.py add \
  --variant-dir {VARIANT_DIR} --status staged --no-tag --json

python3 scripts/hyperagent/apply.py \
  --variant-dir {VARIANT_DIR} --approve --json
```

`apply.py`가 SSOT 파일 복사, git commit, sync_agents.py, install_assets.py --link을 수행한다.

한 variant의 apply가 실패하면 해당 variant만 skip하고 나머지를 계속 진행한다.

### Step 6: 커밋 및 푸시

파이프라인 산출물(프로젝션 sync, archive/improvement-log, variant/proposal 데이터)을 커밋하고 푸시한다.

1. `git add`로 변경된 프로젝션(`agents/`, `dist/codex/agents/`), 로그(`archive.jsonl`, `improvement-log.jsonl`), variant/proposal 디렉토리를 스테이징한다.
2. 커밋 메시지: `chore(hyperagent): 파이프라인 실행 데이터 및 variant 이력 추가`
3. `git push`로 리모트에 반영한다.

### Step 7: 결과 보고

적용된 variant 목록을 정리한다. 각 항목에:
- entity 이름과 타입
- 변경 요약 (무엇을 어떻게 보강했는지 1줄)
- 커밋 해시

## 대화형 vs 스케줄 실행

- **스케줄 실행**: 사용자 확인 없이 전체 파이프라인을 자동 실행한다.
- **대화형 실행**: Step 2 이후 improvements 목록을 보여주고, 사용자가 확인하면 Step 3으로 진행한다.
  사용자가 특정 entity만 선택할 수도 있다.

## 주의사항

- improvements가 비어 있으면 Step 3부터 건너뛴다.
- variants가 비어 있으면 Step 4부터 건너뛴다.
- 동일 entity에 uncommitted 변경이 있으면 apply가 거부된다. `git status`로 먼저 확인한다.
- `generate_variant.py`의 `--max-variants` 기본값은 3이다. 사용자가 더 많은 variant를 원하면 조절한다.
