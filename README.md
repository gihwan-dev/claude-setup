# AI Agent Skills

AI 에이전트(Claude Code, Codex 등)를 위한 스킬 및 에이전트 정의 저장소입니다.
SKILL.md 규칙을 지원하는 모든 AI 도구에서 사용할 수 있습니다.

## 구조

```
skills/<skill-name>/SKILL.md          # 개별 스킬 정의
skills/<skill-name>/scripts/          # 스킬 실행 스크립트
skills/<skill-name>/references/       # 스킬 참고 문서
agents/*.md                           # 에이전트 정의 (멀티 에이전트 워크플로우용)
scripts/install-skills.sh             # 통합 설치 스크립트
scripts/sync-instructions.sh          # INSTRUCTIONS.md → CLAUDE.md/AGENTS.md 동기화
INSTRUCTIONS.md                       # 프로젝트 가이드라인 (단일 소스)
CLAUDE.md / AGENTS.md                 # INSTRUCTIONS.md에서 자동 생성
```

## 설치

### 자동 감지 (권장)

설치된 AI 도구를 자동으로 감지하여 해당 경로에 스킬을 설치합니다.

```bash
git clone <YOUR_REPO_URL> ~/ai-skills
cd ~/ai-skills
./scripts/install-skills.sh --link
```

`--link`는 심볼릭 링크로 설치하여, 수정 시 즉시 반영되어 유지보수에 유리합니다.

### 특정 플랫폼 지정

```bash
./scripts/install-skills.sh --target claude --link   # Claude Code만
./scripts/install-skills.sh --target codex --link    # Codex만
./scripts/install-skills.sh --target all --link      # 둘 다
```

### 설치 옵션

```bash
--target <claude|codex|all>   # 대상 플랫폼 (기본: auto-detect)
--copy                        # 복사 설치
--link                        # 심볼릭 링크 설치 (기본)
--dest <path>                 # 커스텀 경로
--force                       # 기존 항목 덮어쓰기
```

설치 후 AI 에이전트를 재시작하면 반영됩니다.

### 개별 스킬 설치 (npx skills)

[npx skills](https://github.com/vercel-labs/skills)를 사용하여 개별 스킬을 선택 설치할 수 있습니다:

```bash
npx skills add gihwan-dev/claude-setup
```

## 경로 규칙

스킬 내부에서 자체 리소스를 참조할 때는 플랫폼 독립적인 변수를 사용합니다:

| 변수 | 의미 | 용도 |
|------|------|------|
| `${SKILL_DIR}` | 현재 SKILL.md가 위치한 디렉토리 | 자체 scripts/references 참조 |
| `${SKILLS_ROOT}` | 스킬 루트 디렉토리 (SKILL_DIR의 부모) | 다른 스킬 참조 |

## INSTRUCTIONS.md 동기화

`INSTRUCTIONS.md`가 프로젝트 가이드라인의 단일 소스입니다.
마커 기반으로 `CLAUDE.md`(프로젝트 컨텍스트)와 `AGENTS.md`(멀티 에이전트 정책)를 자동 생성합니다.

```bash
./scripts/sync-instructions.sh   # CLAUDE.md, AGENTS.md 자동 생성
```

| 파일 | 내용 |
|------|------|
| `CLAUDE.md` | 프로젝트 개요, 스킬/에이전트 목록, 경로 규칙 |
| `AGENTS.md` | 멀티 에이전트 오케스트레이션 정책, 역할 매핑 |

설치 스크립트(`install-skills.sh`) 실행 시 자동으로 동기화됩니다.
