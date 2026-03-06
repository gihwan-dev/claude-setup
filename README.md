# AI Agent Skills

AI 에이전트(Claude Code, Codex 등)를 위한 스킬/에이전트 레지스트리 저장소다.

## 구조

```text
skills/<skill-name>/...                         # 스킬 정의/스크립트/레퍼런스
agent-registry/<agent-id>/agent.toml           # 에이전트 단일 진실원 메타데이터
agent-registry/<agent-id>/instructions.md      # 에이전트 단일 진실원 지시문
agents/*.md                                    # generated projection (수정 금지)
dist/codex/agents/*.toml                       # generated codex agent profiles
dist/codex/config.managed-agents.toml          # generated codex managed config block
scripts/sync_instructions.py                   # INSTRUCTIONS.md -> AGENTS.md/CLAUDE.md
scripts/sync_agents.py                         # agent-registry -> generated projections
scripts/install_assets.py                      # 설치/동기화 통합 진입점
scripts/install-skills.sh                      # legacy wrapper (install_assets.py 호출)
scripts/sync-instructions.sh                   # legacy wrapper (sync_instructions.py 호출)
INSTRUCTIONS.md                                # 프로젝트 정책 단일 소스
CLAUDE.md / AGENTS.md                          # generated files
```

## 단일 진실원 정책

- 에이전트: `agent-registry/<agent-id>/agent.toml` + `instructions.md`
- `agents/*.md`, `dist/codex/*`: generated projection
- 정책 문서: `INSTRUCTIONS.md`

## 동기화/검증

```bash
python3 scripts/sync_instructions.py
python3 scripts/sync_agents.py
```

drift 확인:

```bash
python3 scripts/sync_instructions.py --check
python3 scripts/sync_agents.py --check
```

## 설치 (Python-first)

자동 감지:

```bash
python3 scripts/install_assets.py --link
```

대상 지정:

```bash
python3 scripts/install_assets.py --target claude --link
python3 scripts/install_assets.py --target codex --link
python3 scripts/install_assets.py --target all --link
```

옵션:

```text
--target <claude|codex|all>
--copy
--link
--dest <path>    # custom path (skills only)
--dry-run
```

## Legacy Wrapper

기존 명령도 동작한다.

```bash
./scripts/install-skills.sh --target codex --dry-run
./scripts/sync-instructions.sh --check
```

## 경로 규칙

| 변수 | 의미 | 용도 |
|------|------|------|
| `${SKILL_DIR}` | 현재 SKILL.md 위치 | 자체 scripts/references 참조 |
| `${SKILLS_ROOT}` | 스킬 루트 디렉토리 | 다른 스킬 참조 |
