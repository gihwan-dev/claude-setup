# HyperAgent Self-Improvement 통합

## Goal
Claude Code의 에이전트/스킬이 사용 경험에서 자동으로 개선되는 자기개선 파이프라인을 구축한다. 매일 저녁 세션 데이터를 분석하여 에이전트 프로파일 개선, 스킬 프롬프트 튜닝, 새 에이전트/스킬 자동 생성, 오케스트레이션 정책 조정을 수행한다. Meta HyperAgents(DGM-H)의 진화적 자기수정 개념을 Claude Code + claude-setup SSOT 시스템에 적용한다.

## Context
- 현재 15개 에이전트와 14개 스킬이 완전히 정적. 사용자가 수백 세션에서 축적하는 경험적 신호가 시스템에 자동 반영되지 않음.
- SSOT 구조: `agent-registry/` → `sync_agents.py` → `agents/` → `install_assets.py --link` → `~/.claude/agents/` (symlink). 이 파이프라인은 변경하지 않고 호출만 한다.
- 세션 데이터: `~/.claude/projects/<project>/<uuid>.jsonl` (대화 전체), `stats-cache.json`, `history.jsonl`. 프로그래밍적 접근 가능 (spike-3 검증 완료).
- 설계 문서: `tasks/hyperagent-integration/design/` (PRD, ARCHITECTURE, ADR 4개, API-CONTRACT, NFR, ANALYTICS)
- ADR 결정 확정: 하이브리드 진화 전략, 3-Tier 안전 경계, Git 태그+archive.jsonl 변종 관리, 일일 배치 cron 트리거

## Scope
- In scope:
  - Session Analyzer: 세션 JSONL 파싱 + 성능 신호 추출 + 작업 난이도 태깅
  - Performance Scorer: 다차원 점수화 + 커밋 반영률 보조지표 + 기준선 비교
  - Variant Generator: LLM/Codex 기반 프롬프트 변종 생성
  - Archive Manager: archive.jsonl 계보 추적 + Git 태그 + pruning
  - Improvement Applier: 3-Tier 적용 + SSOT 반영 + 롤백 지원
  - Meta-Loop Trigger: 일일 배치 cron + `$evolve` CLI
  - `policy/hyperagent.toml` 설정 파일
- Out of scope:
  - 모델 파인튜닝
  - 팀 공유 메커니즘
  - 인-세션 실시간 자기수정
  - 기존 SSOT 파이프라인(sync_agents.py, install_assets.py) 수정
- Do not touch:
  - `scripts/sync_agents.py` (호출만, 수정 안 함)
  - `scripts/install_assets.py` (호출만, 수정 안 함)
  - `~/.claude/` 하위 세션 파일 (읽기 전용)

## Success Criteria
- [ ] `python3 scripts/hyperagent/analyze_sessions.py --date-range <today> --json`이 세션 JSONL을 파싱하여 에이전트/스킬별 성능 신호(보정 횟수, 긍정 피드백, 도구 실패율)를 JSON으로 출력
- [ ] `python3 scripts/hyperagent/score.py --json`이 분석 결과를 점수화하고 개선 대상 순위를 반환
- [ ] `python3 scripts/hyperagent/generate_variant.py --target <agent-id>`가 대상 에이전트의 개선된 instructions.md 변종을 생성
- [ ] `python3 scripts/hyperagent/archive.py add`가 변종을 archive.jsonl에 등록하고 Git 태그를 생성
- [ ] `python3 scripts/hyperagent/apply.py`가 3-Tier 규칙에 따라 변종을 SSOT에 반영하고 sync+install 파이프라인을 실행
- [ ] `python3 scripts/hyperagent/evolve.py`가 전체 파이프라인을 연결 실행 (analyze→score→generate→archive→apply)
- [ ] cron으로 `evolve.py`를 매일 지정 시각에 실행하는 설정이 동작
- [ ] 자동 개선된 에이전트 프로파일이 다음 세션에서 즉시 반영됨 (symlink 경로)
- [ ] 롤백: 개선 후 부정 피드백 증가 시 `git revert`로 이전 상태 복원 가능

## Phases

### Phase 1: Session Analyzer
- **Purpose**: 세션 JSONL을 파싱하여 에이전트/스킬별 성능 신호를 구조화된 JSON으로 출력하는 CLI를 만든다. 전체 파이프라인의 입력 데이터를 생산하는 첫 단계.
- **Inputs**:
  - `tasks/hyperagent-integration/design/API-CONTRACT.md` — 인터페이스 1 스펙 (CLI 옵션, 출력 스키마, 파싱 규칙)
  - `tasks/hyperagent-integration/design/ANALYTICS.md` — 성능 신호 택소노미, 한국어 패턴 regex, 작업 난이도 태깅 로직
  - `~/.claude/projects/` 하위 실제 세션 JSONL 파일 (테스트 데이터)
- **Done when**: `analyze_sessions.py --date-range 2026-04-12 2026-04-13 --json`이 실제 세션에서 에이전트/스킬별 보정 횟수, 긍정 피드백, 도구 실패율을 JSON으로 출력
- **Verification**: `python3 scripts/hyperagent/analyze_sessions.py --date-range 2026-04-12 2026-04-13 --json | python3 -m json.tool`

### Phase 2: Performance Scorer
- **Purpose**: 분석 결과를 다차원 점수로 변환하고, 기준선 대비 변화를 계산하며, 개선 대상 순위를 매긴다. 커밋 반영률 보조지표를 포함.
- **Inputs**:
  - `tasks/hyperagent-integration/design/API-CONTRACT.md` — 인터페이스 2 스펙
  - `tasks/hyperagent-integration/design/ANALYTICS.md` — 엔티티별 점수 모델, 집계/추세 분석, 지수 감쇠
  - Phase 1의 `analysis-report.json` 출력
- **Done when**: `score.py`가 analysis-report.json을 입력받아 에이전트/스킬별 종합 점수, 변화 추세, 개선 제안 목록을 JSON으로 출력
- **Verification**: `python3 scripts/hyperagent/score.py --input analysis-report.json --json | python3 -m json.tool`

### Phase 3: Variant Generator
- **Purpose**: 점수가 낮은 에이전트/스킬에 대해 LLM으로 개선된 프롬프트 변종을 생성한다.
- **Inputs**:
  - `tasks/hyperagent-integration/design/API-CONTRACT.md` — 인터페이스 3 스펙
  - `tasks/hyperagent-integration/design/adr/ADR-0001-evolution-strategy.md` — 하이브리드 전략 (증분 기본, 정체 시 진화)
  - Phase 2의 `score-report.json` 출력
  - 대상 에이전트/스킬의 현재 SSOT 파일 (instructions.md, SKILL.md 등)
- **Done when**: `generate_variant.py --target test-engineer`가 현재 instructions.md + 점수 리포트를 기반으로 개선된 변종 파일을 생성
- **Verification**: 생성된 변종 파일이 원본 대비 의미 있는 차이를 포함하고, agent.toml 구조를 유지

### Phase 4: Archive Manager
- **Purpose**: 변종을 archive.jsonl에 등록하고, Git 태그로 세대를 관리하며, pruning 정책을 적용한다.
- **Inputs**:
  - `tasks/hyperagent-integration/design/API-CONTRACT.md` — 인터페이스 4 스펙 (서브커맨드 4종)
  - `tasks/hyperagent-integration/design/adr/ADR-0003-variant-management.md` — Git 태그 + archive.jsonl 전략
  - Phase 3의 변종 파일들
- **Done when**: `archive.py add`, `archive.py list`, `archive.py select`, `archive.py prune` 4개 서브커맨드가 동작. archive.jsonl에 변종 메타데이터(ID, 점수, 계보, behavioral_tags)가 기록됨
- **Verification**: `python3 scripts/hyperagent/archive.py list --json` 출력 확인

### Phase 5: Improvement Applier
- **Purpose**: 선택된 변종을 3-Tier 규칙에 따라 SSOT에 반영하고, sync+install 파이프라인을 실행하며, 롤백을 지원한다.
- **Inputs**:
  - `tasks/hyperagent-integration/design/API-CONTRACT.md` — 인터페이스 5 스펙
  - `tasks/hyperagent-integration/design/adr/ADR-0002-safety-boundary.md` — 3-Tier 단계적 적용
  - Phase 4에서 선택된 변종
  - 기존 `scripts/sync_agents.py`, `scripts/install_assets.py` (호출만)
- **Done when**: `apply.py`가 Tier 1 변종을 자동 적용하고, git commit + sync_agents.py + install_assets.py를 실행하며, improvement-log.jsonl에 기록
- **Verification**: 적용 후 `~/.claude/agents/<target>.md`가 변종 내용과 일치하고, git log에 자동 개선 커밋이 존재

### Phase 6: Meta-Loop Orchestrator + Cron
- **Purpose**: 전체 파이프라인(Phase 1~5)을 연결하는 `evolve.py` CLI와, 매일 자동 실행하는 cron 설정을 만든다.
- **Inputs**:
  - `tasks/hyperagent-integration/design/API-CONTRACT.md` — 인터페이스 6 스펙 (메타루프 트리거)
  - `tasks/hyperagent-integration/design/adr/ADR-0004-session-as-event-log.md` — 일일 배치 cron 결정
  - Phase 1~5의 모든 스크립트
- **Done when**: `python3 scripts/hyperagent/evolve.py`가 전체 파이프라인을 순차 실행하고, launchd plist 또는 crontab 설정 파일이 생성되어 매일 지정 시각에 실행 가능
- **Verification**: `evolve.py --dry-run`이 전체 파이프라인을 시뮬레이션하고 각 단계의 예상 출력을 보여줌

### Phase 7: 설정 파일 + 테스트
- **Purpose**: `policy/hyperagent.toml` 설정 파일, 전체 테스트 스위트, 검증 스크립트를 완성한다.
- **Inputs**:
  - `tasks/hyperagent-integration/design/API-CONTRACT.md` — hyperagent.toml 스키마
  - `tasks/hyperagent-integration/design/NFR.md` — 비용 예산, 변종 상한, 실패 복구 시나리오
  - `tests/` 기존 테스트 패턴 (test_agent_sync.py 등)
- **Done when**: hyperagent.toml이 존재하고, `pytest tests/test_hyperagent*.py`가 모든 컴포넌트를 커버하며, `validate_workflow_contracts.py`가 hyperagent 관련 계약도 검증
- **Verification**: `pytest tests/ -k hyperagent -v` 전체 통과

## Decisions
- 일일 배치 cron 트리거 (ADR-0004): hooks 대신 매일 저녁 cron으로 전일 세션 일괄 분석. 단순하고 비용 효율적.
- 하이브리드 진화 전략 (ADR-0001): 증분 개선 기본, 정체 감지 시 parallel-codex + Codex로 다수 변종 병렬 생성.
- 3-Tier 안전 경계 (ADR-0002): Tier1 즉시 / Tier2 관찰 / Tier3 사용자 승인.
- Git 태그 + archive.jsonl (ADR-0003): 변종 메타데이터는 JSONL, 세대는 Git 태그.
- 커밋 반영률 보조지표: git blame 기반으로 에이전트 출력의 실제 커밋 반영 여부를 추적. "피드백 감소 = 개선"의 함정 방지.
- 작업 난이도 통제: Session Analyzer가 세션별 복잡도를 태깅하여 확증 편향 방지.

## Risks
| Risk | Mitigation |
|------|-----------|
| 세션 JSONL 신호 신뢰성 — 사용자 보정이 에이전트 품질 아닌 다른 원인일 수 있음 | 커밋 반영률 보조지표로 교차 검증, 작업 난이도 분리, 3회 이상 반복만 반응 |
| 조용한 퇴화 — 에이전트가 예스맨이 되면 측정 지표는 개선되나 실질은 악화 | 커밋 반영률(실제 코드 반영 여부)이 독립적 검증 장치 |
| 비용 폭발 — 진화 모드가 예상보다 자주 발동 | 사이클당 $5 하드캡, 월 $30 예산, LLM 호출 전 비용 추정 |
| 롤백 복잡성 — 자동 커밋과 수동 커밋 혼재 시 선택적 revert 어려움 | 자동 개선 커밋에 `[hyperagent]` prefix 추가, git log --grep으로 필터 가능 |
| Cold-start — 베이스라인 5세션 미달 시 개선 루프 무동작 | 충분한 세션 축적 전까지 분석만 실행, 개선 생성은 건너뜀 |

## References
- `tasks/hyperagent-integration/design/PRD.md` — 문제 정의, 목표, 시나리오, 성공 기준
- `tasks/hyperagent-integration/design/ARCHITECTURE.md` — 시스템 컨텍스트, 컨테이너 뷰, 데이터 흐름, HyperAgents 매핑
- `tasks/hyperagent-integration/design/adr/ADR-0001-evolution-strategy.md` — 하이브리드 진화 전략
- `tasks/hyperagent-integration/design/adr/ADR-0002-safety-boundary.md` — 3-Tier 안전 경계
- `tasks/hyperagent-integration/design/adr/ADR-0003-variant-management.md` — Git 태그 + archive.jsonl
- `tasks/hyperagent-integration/design/adr/ADR-0004-session-as-event-log.md` — 일일 배치 cron
- `tasks/hyperagent-integration/design/API-CONTRACT.md` — 6개 CLI 인터페이스 스펙
- `tasks/hyperagent-integration/design/NFR.md` — 비용, 성능, 변종 상한, 실패 모드
- `tasks/hyperagent-integration/design/ANALYTICS.md` — 성능 신호 택소노미, 점수 모델, 이벤트 스키마
- https://arxiv.org/abs/2603.19461 — Meta HyperAgents (DGM-H)
- https://www.anthropic.com/engineering/managed-agents — Anthropic Managed Agents

## Status
- current: complete
- done: [Phase 1: Session Analyzer, Phase 2: Performance Scorer, Phase 3: Variant Generator, Phase 4: Archive Manager, Phase 5: Improvement Applier, Phase 6: Meta-Loop + Cron, Phase 7: Settings + Tests]
- blocked: none

## Log
- 2026-04-13: design-docs 완료 (proceed-with-advisory). BRIEF.md 생성.
- 2026-04-13: Phase 1 완료. analyze_sessions.py CLI 구현. 8개 검증 모두 PASS. 실제 16세션 분석 성공.
- 2026-04-13: Phase 2 완료. score.py CLI 구현. 파이프 체이닝 성공. baseline 자동 생성, 지수 감쇠, 난이도 정규화 포함.
- 2026-04-13: Phase 3 완료. generate_variant.py CLI 구현. 3개 에이전트 변종 생성 성공. --dry-run 지원.
- 2026-04-13: Phase 4 완료. archive.py CLI 구현. add/list/select/prune 4개 서브커맨드. archive.jsonl + --no-tag 지원.
- 2026-04-13: Phase 5 완료. apply.py CLI 구현. 3-Tier 판정, dry-run 검증, [hyperagent] 커밋, sync+install 파이프라인 호출, 롤백 지원.
- 2026-04-13: Phase 6 완료. evolve.py CLI 구현. 5단계 파이프라인 연결, --dry-run 시뮬레이션, launchd plist 생성.
- 2026-04-13: Phase 7 완료. hyperagent.toml 설정, 15개 테스트 전체 통과, validate_workflow_contracts.py 확장.
- 2026-04-13: BUILD COMPLETE. 7/7 Phases 완료.
