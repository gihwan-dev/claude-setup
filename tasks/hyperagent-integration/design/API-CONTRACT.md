<!-- Status: drafted -->
<!-- Confidence: medium -->
<!-- doc_type: api-contract -->

# API Contract: HyperAgent 자기개선 시스템 내부 인터페이스

## Surface

- **Style**: Python CLI 스크립트 + 파일 기반 계약 (HTTP API 아님)
- **Base path / package**: `scripts/hyperagent/` (SSOT repo 내 Python 모듈)
- **Versioning scheme**: [ASSUMPTION][candidate] 파일 기반 계약이므로 SemVer 불필요. `archive.jsonl`의 `schema_version` 필드로 포맷 변경을 추적한다. 현재 v1.

## Auth Model

N/A — 1인 개발자 로컬 도구. 모든 CLI는 현재 사용자 권한으로 실행된다. 별도 인증 없음.

## 공통 규칙

### 파일 경로 해석

- 모든 입력 경로는 절대 경로 또는 `~` 시작을 허용한다.
- `~/.claude/` 하위 경로는 `$CLAUDE_HOME` 환경변수가 설정되어 있으면 해당 경로를 우선한다 (기존 `install_assets.py` 패턴과 동일).
- SSOT repo root는 `scripts/` 기준 상대 탐색으로 자동 결정한다 (기존 `workflow_contract.py`의 `REPO_ROOT = Path(__file__).resolve().parents[1]` 패턴).

### 종료 코드

| 코드 | 의미 |
|------|------|
| 0 | 성공 |
| 1 | 입력 검증 실패 (잘못된 경로, 스키마 불일치 등) |
| 2 | 처리 중 오류 (JSONL 파싱 실패, 파일 쓰기 실패 등) |
| 3 | 전제 조건 미충족 (필요한 파일 부재, sync 불일치 등) |

### JSON 출력 규칙

- 모든 CLI는 `--json` 플래그로 구조화된 JSON stdout 출력을 지원한다.
- `--json` 없이 실행 시 사람이 읽을 수 있는 텍스트 요약을 출력한다.
- stderr는 항상 로그/경고용 (JSON 출력과 혼합하지 않음).

---

## 인터페이스 1: Session Analyzer

### 목적

세션 JSONL을 파싱하여 에이전트/스킬 성능 신호를 추출한다.

### CLI 호출

```
python3 scripts/hyperagent/analyze_sessions.py [OPTIONS]
```

| 옵션 | 필수 | 설명 |
|------|------|------|
| `--sessions PATH [PATH...]` | 택1 | 분석할 세션 JSONL 파일 경로(들) |
| `--date-range START END` | 택1 | ISO 8601 날짜 범위 (예: `2026-04-01 2026-04-13`) |
| `--project PROJECT_PATH` | 선택 | 특정 프로젝트만 필터. 생략 시 `--sessions` 또는 전체 프로젝트 |
| `--json` | 선택 | JSON stdout 출력 |
| `--min-turns N` | 선택 | 최소 턴 수 이하 세션 무시 (기본: 3) |

`--sessions`와 `--date-range` 중 하나는 반드시 제공해야 한다.

`--date-range` 사용 시, 세션 탐색 경로:
1. `--project`가 지정되면: `~/.claude/projects/<project-slug>/` 하위 `.jsonl` 파일
2. 미지정이면: `~/.claude/projects/` 전체 하위 디렉토리 순회

### 세션 JSONL 파싱 규칙

[ASSUMPTION][candidate] 세션 JSONL은 줄 단위 JSON 객체이며, 각 객체의 `type` 필드로 메시지 종류를 구분한다. 관찰된 type 값: `user`, `assistant`, `system`, `file-history-snapshot`, `last-prompt`, `attachment`. `system` 타입은 `subtype` 필드로 세분화된다 (`local_command`, `stop_hook_summary`, `turn_duration` 등).

### 추출 신호 목록

| 신호 ID | 추출 소스 | 설명 |
|---------|-----------|------|
| `user_correction` | `type=user` 메시지에서 수정 패턴 탐지 | 사용자가 에이전트 출력을 교정한 횟수 |
| `repeated_instruction` | 연속 `type=user` 메시지에서 유사 지시 탐지 | 동일/유사 지시를 반복한 횟수 (에이전트가 이해 못한 신호) |
| `tool_failure` | `type=assistant` 메시지 내 tool_use 결과에서 에러 탐지 | 도구 호출 실패 횟수 및 패턴 |
| `positive_feedback` | `type=user` 메시지에서 긍정 표현 탐지 | 만족/칭찬 표현 횟수 |
| `session_duration` | 첫/마지막 메시지 timestamp 차이 | 세션 소요 시간 |
| `turn_count` | `type=user` 메시지 수 | 사용자 턴 수 |
| `skill_invocations` | `type=user` 메시지에서 `$skill-name` 또는 `/skill-name` 패턴 | 스킬별 호출 빈도 |
| `agent_dispatches` | `type=assistant` 메시지에서 subagent/TeamCreate 패턴 | 서브에이전트 디스패치 빈도 |

[ASSUMPTION][candidate] `user_correction`과 `repeated_instruction` 탐지는 키워드 기반 휴리스틱으로 시작한다. 예: "아니", "그게 아니라", "다시", "방금 말한", "이미 말했" 등의 한국어 패턴 + "no", "not what I", "I already said", "again" 등의 영어 패턴. 추후 LLM 기반 분류로 업그레이드 가능.

**신호 추출 전략 (확정)**: 하이브리드 방식을 채택한다. 1차로 휴리스틱(정규식 + 키워드)으로 빠르게 분류하고, 2차로 모호한 케이스에 대해 LLM(Codex) 분류를 수행한다. Codex 토큰이 충분하므로 LLM 2차 분류의 비용 부담이 사실상 없어, 정확도를 최대화할 수 있다. (ADR-0001 참조)

### 출력 스키마 (Performance Report)

```json
{
  "schema_version": "1",
  "generated_at": "2026-04-13T12:00:00Z",
  "date_range": { "start": "2026-04-01", "end": "2026-04-13" },
  "sessions_analyzed": 42,
  "sessions_skipped": 5,
  "signals": {
    "by_session": [
      {
        "session_id": "02103b28-...",
        "project": "-Users-choegihwan-Documents-Projects-claude-setup",
        "timestamp": "2026-04-13T00:04:34Z",
        "turn_count": 15,
        "session_duration_seconds": 3600,
        "user_corrections": 3,
        "repeated_instructions": 1,
        "tool_failures": [
          { "tool": "Bash", "error_pattern": "exit code 1", "count": 2 }
        ],
        "positive_feedback": 2,
        "skill_invocations": [
          { "skill": "build", "count": 1 },
          { "skill": "commit", "count": 2 }
        ],
        "agent_dispatches": [
          { "agent": "verification-worker", "count": 3 }
        ]
      }
    ],
    "aggregated": {
      "total_user_corrections": 28,
      "total_repeated_instructions": 7,
      "total_tool_failures": 15,
      "total_positive_feedback": 45,
      "correction_rate": 0.12,
      "top_failing_tools": [
        { "tool": "Bash", "failure_count": 10, "sessions_affected": 8 }
      ],
      "top_skills_by_usage": [
        { "skill": "build", "invocations": 30, "sessions": 20 }
      ],
      "top_agents_by_dispatch": [
        { "agent": "verification-worker", "dispatches": 45, "sessions": 25 }
      ]
    }
  }
}
```

### 멱등성

동일 입력 파일 + 동일 옵션이면 동일 출력을 보장한다. 상태를 변경하지 않는 순수 읽기 연산이다.

### 에러 처리

- 존재하지 않는 JSONL 경로: exit 1 + stderr에 경로 목록 출력
- 파싱 불가 JSONL 행: 해당 행 건너뛰기 + stderr 경고. `sessions_skipped` 카운트에 반영
- `--date-range`에 해당하는 세션 없음: exit 0 + `sessions_analyzed: 0` 결과 출력

---

## 인터페이스 2: Performance Scorer

### 목적

Analyzer 출력(Performance Report)과 현재 에이전트/스킬 메타데이터를 결합하여 개체별 점수와 개선 제안을 생성한다.

### CLI 호출

```
python3 scripts/hyperagent/score_performance.py [OPTIONS]
```

| 옵션 | 필수 | 설명 |
|------|------|------|
| `--report PATH` | 필수 | `analyze_sessions.py`의 JSON 출력 파일 경로 |
| `--registry PATH` | 선택 | agent-registry 루트 (기본: `<repo>/agent-registry/`) |
| `--skills PATH` | 선택 | skills 디렉토리 루트 (기본: `<repo>/skills/`) |
| `--json` | 선택 | JSON stdout 출력 |
| `--baseline PATH` | 선택 | 이전 스코어 결과와 비교 (추이 분석용) |

### 스코어링 로직

[ASSUMPTION][candidate] 스코어링은 가중 합산 방식이다. 각 신호를 0-1 범위로 정규화하고, 가중치를 곱해 총점을 산출한다. 가중치 기본값은 `policy/hyperagent.toml`에서 로드한다.

기본 가중치:

| 신호 | 가중치 | 방향 | 설명 |
|------|--------|------|------|
| `correction_rate` | 0.35 | 낮을수록 좋음 | 교정 비율 |
| `repeated_instruction_rate` | 0.25 | 낮을수록 좋음 | 반복 지시 비율 |
| `tool_failure_rate` | 0.15 | 낮을수록 좋음 | 도구 실패 비율 |
| `positive_feedback_rate` | 0.15 | 높을수록 좋음 | 긍정 피드백 비율 |
| `usage_frequency` | 0.10 | 참고용 | 사용 빈도 (활발히 사용되는 스킬 우선) |

### 개선 제안 생성

**개선 제안 생성 방식 (확정)**: LLM 기반(Codex 활용)을 채택한다. 세션 컨텍스트와 점수 근거를 포함하여 Codex에 구체적 개선 제안을 요청한다. Codex 토큰이 충분하여 비용 제약이 없으므로, 규칙 기반의 일반적 제안보다 세션 맥락에 맞는 구체적 제안을 생성할 수 있다. (ADR-0001 참조)

### 출력 스키마

```json
{
  "schema_version": "1",
  "generated_at": "2026-04-13T12:30:00Z",
  "report_source": "/path/to/performance-report.json",
  "scores": {
    "agents": [
      {
        "agent_id": "verification-worker",
        "score": 0.72,
        "score_breakdown": {
          "correction_rate": { "raw": 0.08, "weighted": 0.28 },
          "repeated_instruction_rate": { "raw": 0.03, "weighted": 0.24 },
          "tool_failure_rate": { "raw": 0.12, "weighted": 0.13 },
          "positive_feedback_rate": { "raw": 0.15, "weighted": 0.07 }
        },
        "trend": "improving",
        "suggestions": [
          {
            "type": "instruction_refinement",
            "target": "agent-registry/verification-worker/instructions.md",
            "description": "도구 실패율이 12%로 높음. instructions에 실패 시 재시도 패턴 추가 권장",
            "priority": "medium",
            "evidence_sessions": ["02103b28-...", "09c13a74-..."]
          }
        ]
      }
    ],
    "skills": [
      {
        "skill_name": "build",
        "score": 0.85,
        "score_breakdown": { "...": "..." },
        "trend": "stable",
        "suggestions": []
      }
    ]
  },
  "global_suggestions": [
    {
      "type": "new_skill_candidate",
      "description": "사용자가 반복적으로 '이슈 목록 보여줘'를 수동 지시. 전용 스킬 생성 후보",
      "evidence_pattern": "repeated_instruction",
      "evidence_sessions": ["..."]
    }
  ]
}
```

### 멱등성

동일 `--report` 입력이면 동일 출력. 상태 변경 없는 순수 계산이다. `--baseline` 제공 시 추이 필드가 추가되지만 기본 점수는 동일.

### 에러 처리

- 잘못된 report JSON 스키마: exit 1 + 구체적 스키마 검증 오류 메시지
- agent-registry 또는 skills 경로 부재: exit 3 + 누락 경로 안내
- 분석 대상 에이전트/스킬 0건: exit 0 + 빈 scores 출력 (에러가 아님)

---

## 인터페이스 3: Variant Generator

### 목적

현재 버전의 에이전트/스킬/정책 파일 + 스코어 + 개선 제안을 입력받아 개선된 버전(variant)을 생성한다.

### CLI 호출

```
python3 scripts/hyperagent/generate_variant.py [OPTIONS]
```

| 옵션 | 필수 | 설명 |
|------|------|------|
| `--scores PATH` | 필수 | `score_performance.py`의 JSON 출력 파일 경로 |
| `--target ENTITY_ID` | 선택 | 특정 에이전트/스킬만 대상. 생략 시 점수 하위 N개 자동 선택 |
| `--max-variants N` | 선택 | 최대 생성 variant 수 (기본: 3) |
| `--strategy STRATEGY` | 선택 | 생성 전략: `refine` (기존 수정), `scaffold` (새 스킬 생성), `auto` (기본, 제안 기반 자동 선택) |
| `--output-dir PATH` | 선택 | variant 출력 디렉토리 (기본: `<repo>/variants/staging/`) |
| `--dry-run` | 선택 | 파일 쓰기 없이 계획만 출력 |
| `--json` | 선택 | JSON stdout 출력 |

### 생성 전략

#### `refine` — 기존 파일 수정

1. 대상 에이전트의 `instructions.md` 또는 스킬의 `SKILL.md`를 읽는다.
2. 스코어의 `suggestions`를 기반으로 LLM에 개선 프롬프트를 전달한다.
3. 수정된 파일을 `variants/staging/<entity_id>/<variant_id>/` 하위에 출력한다.

#### `scaffold` — 새 스킬 생성

1. `global_suggestions`에서 `new_skill_candidate` 유형을 선택한다.
2. 기존 `skill-creator` 스킬의 템플릿 구조를 참조하여 `SKILL.md` + 디렉토리 구조를 생성한다.
3. `variants/staging/_new/<skill-name>/<variant_id>/` 하위에 출력한다.

[ASSUMPTION][candidate] variant 생성 시 LLM(Claude) 호출이 필요하다. 현재 세션의 Claude가 직접 생성하는 방식이 아니라, 별도 스크립트에서 Anthropic API를 호출한다. API 키는 `$ANTHROPIC_API_KEY` 환경변수에서 로드한다.

### variant 디렉토리 구조

```
variants/
  staging/                          # 아직 평가되지 않은 후보
    verification-worker/
      v-20260413-001/
        instructions.md             # 수정된 파일
        meta.json                   # variant 메타데이터
    _new/
      auto-issue-lister/
        v-20260413-001/
          SKILL.md
          meta.json
  archive/                          # Archive Manager가 관리
    archive.jsonl
```

### `meta.json` 스키마

```json
{
  "variant_id": "v-20260413-001",
  "entity_type": "agent",
  "entity_id": "verification-worker",
  "strategy": "refine",
  "parent_variant": null,
  "created_at": "2026-04-13T13:00:00Z",
  "source_score": 0.72,
  "suggestions_applied": ["instruction_refinement"],
  "files_modified": ["instructions.md"],
  "status": "staged"
}
```

### 멱등성

동일 입력 + 동일 `--target`이라도 LLM 호출로 인해 매번 다른 variant가 생성될 수 있다. 멱등하지 않다. 단, `variant_id`는 타임스탬프 기반으로 유일성을 보장하므로 기존 variant를 덮어쓰지 않는다.

### 에러 처리

- 잘못된 scores JSON: exit 1
- 대상 entity가 agent-registry/skills에 존재하지 않음: exit 1 + 해당 entity 안내
- LLM API 호출 실패: exit 2 + API 에러 메시지. 이미 생성된 variant는 staging에 유지
- `--dry-run`: exit 0 + 생성 계획 JSON 출력 (파일 쓰기 없음)

---

## 인터페이스 4: Archive Manager

### 목적

variant 메타데이터와 평가 결과를 시계열 아카이브에 기록하고, 계보(lineage)를 추적한다.

### CLI 호출

```
python3 scripts/hyperagent/manage_archive.py <SUBCOMMAND> [OPTIONS]
```

#### 서브커맨드: `record`

variant를 아카이브에 기록한다.

| 옵션 | 필수 | 설명 |
|------|------|------|
| `--variant-dir PATH` | 필수 | variant 디렉토리 경로 (meta.json 포함) |
| `--score FLOAT` | 선택 | 평가 점수 (평가 후 기록 시) |
| `--status STATUS` | 선택 | `staged`, `evaluated`, `applied`, `rejected` |

#### 서브커맨드: `query`

아카이브를 조회한다.

| 옵션 | 필수 | 설명 |
|------|------|------|
| `--entity ENTITY_ID` | 선택 | 특정 entity 필터 |
| `--status STATUS` | 선택 | 상태 필터 |
| `--top N` | 선택 | 점수 상위 N개 (기본: 5) |
| `--json` | 선택 | JSON stdout 출력 |

#### 서브커맨드: `lineage`

특정 variant의 계보를 추적한다.

| 옵션 | 필수 | 설명 |
|------|------|------|
| `--variant-id ID` | 필수 | 추적 대상 variant ID |
| `--json` | 선택 | JSON stdout 출력 |

#### 서브커맨드: `prune`

오래되었거나 점수가 낮은 variant를 정리한다.

| 옵션 | 필수 | 설명 |
|------|------|------|
| `--max-age DAYS` | 선택 | 최대 보존 일수 (기본: 90) |
| `--min-score FLOAT` | 선택 | 최소 점수 미만 제거 |
| `--keep-applied` | 선택 | applied 상태는 보존 (기본: true) |
| `--dry-run` | 선택 | 삭제 계획만 출력 |

### `archive.jsonl` 스키마

각 행은 아카이브 이벤트를 나타낸다:

```json
{
  "event_type": "record",
  "timestamp": "2026-04-13T13:05:00Z",
  "variant_id": "v-20260413-001",
  "entity_type": "agent",
  "entity_id": "verification-worker",
  "strategy": "refine",
  "parent_variant": null,
  "source_score": 0.72,
  "evaluated_score": null,
  "status": "staged",
  "files": ["instructions.md"],
  "suggestions_applied": ["instruction_refinement"]
}
```

상태 전이 시 추가 이벤트가 append된다:

```json
{
  "event_type": "status_change",
  "timestamp": "2026-04-13T14:00:00Z",
  "variant_id": "v-20260413-001",
  "previous_status": "staged",
  "new_status": "applied",
  "evaluated_score": 0.81
}
```

### 멱등성

`record`는 동일 `variant_id`에 대해 중복 호출 시 기존 레코드를 덮어쓰지 않고 무시한다 (append-only JSONL이므로 최신 이벤트가 현재 상태). `prune`은 멱등하다 (이미 삭제된 항목은 건너뜀).

### 에러 처리

- `meta.json` 부재 또는 파싱 불가: exit 1
- `archive.jsonl` 부재: 자동 생성 (빈 파일). exit 0
- `--variant-id`가 아카이브에 없음: exit 1 + "variant not found" 메시지

---

## 인터페이스 5: Improvement Applier

### 목적

선택된 variant를 SSOT(agent-registry/ 또는 skills/)에 적용하고 sync 파이프라인을 트리거한다.

### CLI 호출

```
python3 scripts/hyperagent/apply_variant.py [OPTIONS]
```

| 옵션 | 필수 | 설명 |
|------|------|------|
| `--variant-id ID` | 택1 | 적용할 variant ID (archive에서 조회) |
| `--variant-dir PATH` | 택1 | variant 디렉토리 직접 지정 |
| `--no-sync` | 선택 | sync_agents.py / install_assets.py 실행 생략 |
| `--no-backup` | 선택 | 적용 전 현재 파일 백업 생략 |
| `--dry-run` | 선택 | 실제 파일 쓰기 없이 계획만 출력 |
| `--json` | 선택 | JSON stdout 출력 |

### 적용 절차

1. **백업**: 대상 파일의 현재 버전을 `variants/backups/<entity_id>/<timestamp>/`에 복사
2. **파일 복사**: variant 디렉토리의 파일을 대상 위치에 복사
   - agent variant: `variants/staging/<id>/<vid>/instructions.md` → `agent-registry/<id>/instructions.md`
   - skill variant: `variants/staging/<name>/<vid>/SKILL.md` → `skills/<name>/SKILL.md`
   - policy variant: `variants/staging/_policy/<vid>/workflow.toml` → `policy/workflow.toml`
   - new skill: `variants/staging/_new/<name>/<vid>/` → `skills/<name>/`
3. **Sync 트리거**: `python3 scripts/sync_agents.py` 실행 (agent 변경 시)
4. **Install 트리거**: `python3 scripts/install_assets.py --link` 실행 (symlink 갱신)
5. **Archive 업데이트**: `manage_archive.py record --variant-dir ... --status applied`

[ASSUMPTION][candidate] 적용 시 git commit은 자동으로 하지 않는다. 사용자가 변경 사항을 확인한 후 수동 커밋하거나, meta-loop의 상위 오케스트레이션이 처리한다.

### 출력 스키마

```json
{
  "variant_id": "v-20260413-001",
  "entity_id": "verification-worker",
  "applied_files": [
    {
      "source": "variants/staging/verification-worker/v-20260413-001/instructions.md",
      "destination": "agent-registry/verification-worker/instructions.md",
      "backup": "variants/backups/verification-worker/20260413T130500/instructions.md"
    }
  ],
  "sync_result": { "exit_code": 0, "output": "ok  agents/\nok  dist/codex/agents/" },
  "install_result": { "exit_code": 0, "output": "Done." }
}
```

### 롤백

적용 후 문제 발견 시 백업에서 복원:

```
python3 scripts/hyperagent/apply_variant.py --variant-dir variants/backups/<entity_id>/<timestamp>/ --no-backup
```

[ASSUMPTION][candidate] 롤백은 전용 서브커맨드 없이, 백업 디렉토리를 variant로 재적용하는 방식으로 처리한다. 별도 `rollback` 커맨드 추가는 사용 빈도를 관찰한 후 결정한다.

### 멱등성

동일 variant를 두 번 적용하면 파일 내용이 동일하므로 실질적 변경은 없다. backup은 매번 새로 생성된다. sync/install은 멱등하다 (기존 스크립트 보장).

### 에러 처리

- variant 디렉토리/ID 부재: exit 1
- meta.json의 entity_id가 agent-registry/skills에 없음 (refine 전략): exit 1 + 안내
- sync_agents.py 실패: exit 2 + 원본 복원(백업에서) + stderr에 상세 오류
- install_assets.py 실패: exit 2 + 경고 (sync는 성공했으므로 수동 재시도 안내)

---

## 인터페이스 6: Meta-Loop Trigger

### 목적

전체 자기개선 사이클의 오케스트레이션 진입점. 개별 인터페이스(1~5)를 순서대로 실행하거나, 특정 단계만 실행한다.

### CLI 호출

```
python3 scripts/hyperagent/meta_loop.py [OPTIONS]
```

| 옵션 | 필수 | 설명 |
|------|------|------|
| `--phase PHASE` | 선택 | 특정 단계만 실행: `analyze`, `score`, `generate`, `apply`, `full` (기본: `full`) |
| `--date-range START END` | 선택 | analyze에 전달할 날짜 범위 (기본: 최근 7일) |
| `--auto-apply` | 선택 | 점수 개선 예상 variant를 자동 적용 (기본: false, 확인 프롬프트 표시) |
| `--max-variants N` | 선택 | generate에 전달할 최대 variant 수 |
| `--dry-run` | 선택 | 모든 단계를 dry-run으로 실행 |
| `--json` | 선택 | JSON stdout 출력 |

### 실행 파이프라인 (`--phase full`)

```
analyze_sessions → score_performance → generate_variant → [사용자 확인] → apply_variant → manage_archive record
```

각 단계의 출력 JSON을 다음 단계의 입력으로 전달한다. 중간 결과물은 `variants/runs/<run-id>/` 하위에 저장된다:

```
variants/runs/run-20260413-140000/
  01-analysis.json
  02-scores.json
  03-variants.json        # 생성된 variant 목록
  04-apply-result.json    # --auto-apply 시
  run-meta.json           # 실행 메타 (시작/종료 시간, 옵션, 결과 요약)
```

### Cron 통합 (확정)

일일 배치 cron으로 전체 진화 루프를 트리거한다. Stop hook 기반 트리거는 사용하지 않는다. (ADR-0004 참조)

```cron
# 매일 저녁 21시에 전일 세션을 일괄 분석 + 전체 진화 루프 실행
0 21 * * *  python3 /path/to/scripts/hyperagent/meta_loop.py --phase full --date-range $(date -v-1d +%Y-%m-%d) $(date +%Y-%m-%d) --json >> ~/.claude/hyperagent/daily-report.json 2>&1
```

[ASSUMPTION][confirmed] cron에서 전체 루프(`full`)를 일일 배치로 실행한다. 세션 종료 시점에 hook을 통한 분석은 수행하지 않으므로 세션 종료 지연 문제가 원천적으로 없다. (검증: ADR-0004)

### 멱등성

`--phase analyze`, `--phase score`는 멱등하다. `--phase generate`는 LLM 호출로 비멱등. `--phase apply`는 동일 variant 재적용 시 실질적 변경 없음. `--phase full`은 generate 단계로 인해 전체적으로 비멱등.

### 에러 처리

- 파이프라인 중간 단계 실패: 해당 단계에서 중단 + 이전 단계 결과물은 `runs/` 에 보존
- `--auto-apply` 없이 실행 시 variant 목록을 stdout에 출력하고 종료 (apply하지 않음)
- 모든 에러는 `run-meta.json`의 `error` 필드에 기록

---

## 파일 기반 계약: 설정 파일

### `policy/hyperagent.toml`

자기개선 시스템의 전역 설정. 기존 `policy/workflow.toml` 패턴을 따른다.

```toml
[scoring]
weights = { correction_rate = 0.35, repeated_instruction_rate = 0.25, tool_failure_rate = 0.15, positive_feedback_rate = 0.15, usage_frequency = 0.10 }

[generation]
max_variants_per_run = 3
default_strategy = "auto"
model = "claude-sonnet-4-20250514"
max_tokens = 4096

[archive]
max_age_days = 90
min_score_threshold = 0.3
archive_path = "variants/archive/archive.jsonl"

[loop]
default_date_range_days = 7
auto_apply = false
trigger = "daily-cron"  # cron 기반 일일 배치 트리거

[signals]
min_turns_threshold = 3
correction_keywords_ko = ["아니", "그게 아니라", "다시", "방금 말한", "이미 말했"]
correction_keywords_en = ["no", "not what I", "I already said", "again", "wrong"]
positive_keywords_ko = ["좋아", "완벽", "감사", "잘했"]
positive_keywords_en = ["great", "perfect", "thanks", "good job", "exactly"]
```

[ASSUMPTION][candidate] 설정 파일 형식으로 TOML을 사용한다. 기존 시스템이 TOML 중심(`agent.toml`, `workflow.toml`, `config.toml`)이므로 일관성을 유지한다.

---

## 인터페이스 간 데이터 흐름

```
  ┌─────────────────────────────────────────────────┐
  │           ~/.claude/projects/*/*.jsonl            │
  │              (세션 데이터 — 읽기 전용)               │
  └─────────────┬───────────────────────────────────┘
                │
                ▼
  ┌─────────────────────────┐
  │  1. Session Analyzer     │ ──→ performance-report.json
  └─────────────┬───────────┘
                │
                ▼
  ┌─────────────────────────┐     ┌──────────────────────────┐
  │  2. Performance Scorer   │ ←── │ agent-registry/, skills/  │
  └─────────────┬───────────┘     │ (현재 메타데이터)           │
                │                  └──────────────────────────┘
                ▼
  ┌─────────────────────────┐
  │  3. Variant Generator    │ ──→ variants/staging/<entity>/<vid>/
  └─────────────┬───────────┘
                │
                ▼
  ┌─────────────────────────┐
  │  4. Archive Manager      │ ──→ variants/archive/archive.jsonl
  └─────────────┬───────────┘
                │
                ▼
  ┌─────────────────────────┐     ┌──────────────────────────┐
  │  5. Improvement Applier  │ ──→ │ agent-registry/, skills/  │
  └─────────────┬───────────┘     │ + sync + install          │
                │                  └──────────────────────────┘
                ▼
  ┌─────────────────────────┐
  │  6. Meta-Loop Trigger    │  (1→2→3→4→5 오케스트레이션)
  └─────────────────────────┘
```

---

## Backward Compatibility

기존 SSOT 파이프라인(`sync_agents.py`, `install_assets.py`, `workflow_contract.py`)을 수정하지 않는다. HyperAgent 시스템은 기존 파이프라인의 **소비자**(agent-registry 파일 수정 → sync 호출)이지 파이프라인 자체를 변경하지 않는다.

기존 파일 계약:
- `agent-registry/<id>/agent.toml` — HyperAgent는 `instructions.md`만 수정. `agent.toml`은 건드리지 않음
- `skills/<name>/SKILL.md` — HyperAgent가 수정 가능
- `policy/workflow.toml` — [ASSUMPTION][candidate] 현재 단계에서 HyperAgent가 수정하지 않음. 향후 오케스트레이션 정책 자동 조정 시 확장 가능

새 스킬 생성(`scaffold` 전략) 시 `skills/<name>/` 구조는 기존 스킬 규격을 따른다:
```
skills/<name>/
  SKILL.md          # 필수
  assets/           # 선택
  references/       # 선택
```

## Deprecation Policy

N/A — 내부 도구, 1인 개발자. 계약 변경 시 `policy/hyperagent.toml`의 `schema_version`을 올리고 마이그레이션 스크립트를 함께 커밋한다.

## Open Questions

(refine 단계에서 이동 예정)

## References

- PRD: `../PRD.md`
- ADRs: `../adr/`
- Architecture: `../ARCHITECTURE.md`
- 기존 sync 파이프라인: `scripts/sync_agents.py`, `scripts/install_assets.py`
- 기존 설정 계약: `scripts/workflow_contract.py`, `policy/workflow.toml`
- 세션 데이터: `~/.claude/projects/<project>/<uuid>.jsonl`
- HyperAgents 논문: https://arxiv.org/abs/2603.19461
