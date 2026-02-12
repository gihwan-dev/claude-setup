# Codex Skill Pack (from Claude setup)

이 저장소는 기존 Claude 중심 스킬 모음을 **Codex에서도 바로 사용할 수 있도록** 정리한 버전입니다.

## 구조

- `skills/<skill-name>/SKILL.md`: 개별 스킬 정의
- `skills/<skill-name>/scripts|references`: 스킬 보조 리소스
- `scripts/install-codex-skills.sh`: Codex 스킬 디렉토리로 설치(링크/복사)

Codex가 실제로 읽는 경로는 아래 형태입니다.

- `${CODEX_HOME:-$HOME/.codex}/skills/<skill-name>/SKILL.md`

## 권장 clone 경로/폴더명

폴더 이름은 **아무거나 가능**합니다. 다만 관리 편의를 위해 아래를 권장합니다.

- 권장: `~/.codex/skill-repo`

예시:

```bash
git clone <YOUR_REPO_URL> ~/.codex/skill-repo
cd ~/.codex/skill-repo
./scripts/install-codex-skills.sh --link
```

`--link`는 개발/수정 시 즉시 반영되어 유지보수에 유리합니다.

## 설치 옵션

```bash
# 기본: 심볼릭 링크 설치
./scripts/install-codex-skills.sh --link

# 복사 설치
./scripts/install-codex-skills.sh --copy

# 기존 항목 덮어쓰기
./scripts/install-codex-skills.sh --link --force

# 목적지 변경
./scripts/install-codex-skills.sh --dest /custom/path/to/skills
```

설치 후 Codex를 재시작하면 반영됩니다.

## Claude Code 설치

Claude Code용 설치 스크립트도 동일한 방식으로 제공합니다.

```bash
# 기본: ~/.claude/skills 에 심볼릭 링크 설치
./scripts/install-claude-skills.sh --link

# 복사 설치
./scripts/install-claude-skills.sh --copy

# 기존 항목 덮어쓰기
./scripts/install-claude-skills.sh --link --force
```

설치 후 Claude Code를 재시작하면 반영됩니다.
