<!-- Status: flesh -->
<!-- Confidence: high -->
<!-- doc_type: prd-lite -->

# PRD: HyperAgent Self-Improvement 통합

## Problem

현재 claude-setup SSOT 시스템의 15개 에이전트와 14개 이상의 스킬은 **완전히 정적**이다. 사용자(1인 개발자)가 수백 번 세션을 반복하면서 축적하는 경험적 신호(어떤 에이전트가 잘 동작하는지, 어떤 프롬프트 패턴이 실패하는지, 어떤 작업 유형에 에이전트가 아예 없는지)가 시스템 개선에 전혀 반영되지 않는다.

구체적 증상:
- **에이전트 프로파일 고착**: explorer나 test-engineer의 instructions.md가 최초 작성 이후 수동 편집 없이는 개선되지 않음. 사용 중 발견되는 약점(예: 특정 프레임워크 탐색 패턴 누락)이 축적되어도 프로파일에 반영되려면 사용자가 직접 수정해야 함.
- **스킬 프롬프트 정체**: commit, build, design-docs 등 스킬의 SKILL.md가 반복 사용에서 나온 실패 패턴이나 개선 아이디어를 자동 흡수하지 못함. 사용자가 매번 같은 보정 피드백을 반복해야 함.
- **수동 에이전트/스킬 생성**: 새로운 작업 유형이 등장할 때(예: 새 프레임워크 도입, 새 워크플로우 필요) 에이전트나 스킬을 사용자가 직접 skill-creator로 만들어야 함. 시스템이 빈번한 패턴을 감지하고 자동 제안/생성하지 못함.
- **오케스트레이션 경직**: parallel-codex의 DAG 실행 정책, 에이전트 선택 기준 등이 고정되어 있어 프로젝트 특성이나 사용 패턴에 적응하지 못함.

이 문제는 Meta HyperAgents(DGM-H)의 핵심 통찰 --- 태스크 에이전트와 메타 에이전트가 하나의 편집 가능한 프로그램이며, 진화적 루프를 통해 자기 수정이 가능하다 --- 을 적용하여 해결할 수 있다.

## Goals

1. **에이전트 프로파일 자동 개선**: 세션 데이터에서 성능 신호를 추출하여 agent-registry의 instructions.md를 자동으로 개선한다. 개선된 프로파일은 symlink를 통해 다음 세션에 즉시 반영된다.
2. **스킬 프롬프트 자동 튜닝**: 스킬 사용 세션에서 실패/성공 패턴을 분석하여 SKILL.md의 프롬프트를 자동 조정한다.
3. **새 에이전트/스킬 자동 생성**: 반복되는 작업 패턴 중 기존 에이전트/스킬로 커버되지 않는 영역을 감지하고, 새 에이전트 또는 스킬 초안을 자동 생성하여 사용자 승인 후 등록한다.
4. **오케스트레이션 정책 자동 조정**: 에이전트 선택, 실행 순서, 병렬화 정책 등을 사용 패턴에 따라 자동으로 최적화한다.

## Non-goals

- **모델 파인튜닝**: Claude/GPT 모델 자체의 가중치를 수정하지 않는다. 프롬프트와 구성 수준에서만 개선한다.
- **팀 공유 메커니즘**: 다수 사용자 간 개선 사항을 공유하거나 동기화하는 기능은 범위 외.
- **인-세션 실시간 자기수정**: 현재 진행 중인 세션 내에서 에이전트/스킬을 실시간으로 수정하지 않는다. 개선은 항상 세션 종료 후 비동기로 이루어진다.
- **범용 AI 에이전트 프레임워크**: 이 시스템은 claude-setup SSOT 파이프라인 전용이며, 범용 에이전트 진화 프레임워크를 만드는 것이 아니다.

## Success Criteria

| 지표 | 현재 상태 | 목표 상태 | 측정 방법 |
|------|----------|----------|----------|
| 보정 피드백 빈도 | 빈번 (정량화 미측정) | 도입 4주 후 체감 감소 | 세션 JSONL에서 사용자 보정 메시지 패턴 추적 (예: "아니 그게 아니라", "다시 해줘", 부정 피드백 키워드) |
| 수동 에이전트/스킬 생성 | 모든 생성이 수동 | 반복 패턴 감지 시 자동 초안 제안 | 자동 생성 제안 횟수 / 사용자 승인율 |
| 에이전트 프로파일 최신성 | 최초 작성 후 정적 | 주 1회 이상 자동 개선 시도 | improvement-log에 기록된 프로파일 수정 횟수 |
| 시스템 자율 구성 | 0% (전부 수동) | 구성 변경의 50% 이상이 자동 제안 기반 | 자동 제안 대비 수동 변경 비율 |

## User Scenarios

### Scenario 1: 에이전트 프로파일 자동 개선 (Primary Happy Path)

**전제**: 사용자가 `test-engineer` 에이전트를 여러 세션에서 반복 사용하며, 매번 "Vitest 환경에서는 jest.mock 대신 vi.mock을 사용해야 해"라는 보정 피드백을 제공하고 있다.

1. 일일 배치 cron이 저녁 지정 시각에 전일 세션 JSONL을 성능 분석기에 일괄 전달한다.
2. 성능 분석기가 해당 세션들에서 `test-engineer` 에이전트 사용을 감지하고, 사용자 보정 메시지를 추출한다.
3. 보정 패턴이 3회 이상 반복되었음을 확인하고, instructions.md 개선안을 생성한다: "Vitest 프로젝트에서는 `vi.mock`을 우선 사용" 항목 추가.
4. 개선안을 `agent-registry/test-engineer/instructions.md`에 반영하고, 변경 사항을 improvement-log에 기록한다.
5. symlink 구조 덕분에 다음 세션에서 `test-engineer`가 즉시 개선된 프로파일로 동작한다.
6. 사용자는 더 이상 해당 보정 피드백을 제공할 필요가 없다.

### Scenario 2: 자동 생성 제안 및 사용자 거부 (Recovery)

**전제**: 시스템이 세션 분석에서 "Docker Compose 관련 작업"이 빈번하다고 감지하고 새 에이전트 초안을 자동 생성한다.

1. 분석기가 최근 2주간 세션에서 Docker Compose 관련 대화가 5회 이상임을 감지한다.
2. 기존 에이전트 중 해당 영역을 커버하는 에이전트가 없음을 확인한다.
3. `docker-compose-specialist` 에이전트 초안(agent.toml + instructions.md)을 `proposals/` 디렉토리에 생성한다.
4. 다음 세션 시작 시 사용자에게 제안을 알린다: "Docker Compose 전문 에이전트 생성을 제안합니다. 승인/거부/수정?"
5. 사용자가 "이건 일시적이었어, 거부"라고 응답한다.
6. 시스템이 해당 제안을 거부 로그에 기록하고, 동일 패턴에 대한 제안 임계값을 상향 조정한다(적응적 임계값).
7. proposals/ 디렉토리의 초안을 정리(삭제 또는 아카이브)한다.

### Scenario 3: 개선 루프 충돌 및 롤백 (Edge/Error)

**전제**: 자동 개선이 에이전트 프로파일을 잘못 수정하여 성능이 오히려 저하된 경우.

1. 자동 개선 루프가 `code-quality-reviewer`의 instructions.md에서 "TypeScript strict mode 관련 검사를 완화"하는 변경을 적용한다.
2. 이후 3개 세션에서 사용자가 "타입 오류를 왜 안 잡아?" 형태의 부정 피드백을 제공한다.
3. 성능 분석기가 해당 변경 이후 부정 피드백 증가를 감지한다.
4. 시스템이 자동으로 변경 전 버전으로 롤백한다. (agent-registry는 git 저장소이므로 `git revert` 또는 파일 복원으로 처리)
5. 롤백 사유를 improvement-log에 기록하고, 해당 유형의 변경에 대한 보수성을 높인다.
6. 사용자에게 "code-quality-reviewer 프로파일 변경을 롤백했습니다. 사유: 변경 후 부정 피드백 3건 감지"를 알린다.

## Constraints

- **Claude Code 런타임 제약**: hooks API(`Stop`, `PostToolUse` 등)와 환경변수(`CLAUDE_TOOL_NAME` 등)가 제공하는 인터페이스 범위 내에서만 동작해야 한다. Claude Code 내부 수정 불가.
- **SSOT 파이프라인 호환**: 모든 변경은 기존 `sync_agents.py` -> `install_assets.py --link` 파이프라인과 호환되어야 한다. 에이전트/스킬의 정규 구조(agent.toml + instructions.md / SKILL.md)를 준수해야 한다.
- **비용 예산**: 진화 루프의 LLM 호출이 실제 작업 비용 대비 과도하지 않아야 한다. [ASSUMPTION][candidate] 개선 루프당 LLM 호출 비용이 해당 세션 비용의 10% 이내로 유지.
- **Git 저장소 무결성**: 자동 변경은 git commit으로 추적 가능해야 하며, 수동 변경과 자동 변경이 명확히 구분되어야 한다.

## Assumptions

1. **[ASSUMPTION][candidate]** 세션 JSONL의 사용자 보정 메시지(부정 피드백, 재시도 요청)는 LLM으로 분류 가능하다. 키워드 기반 휴리스틱 + LLM 분류의 2단계 파이프라인이 비용 대비 효과적이다.
2. **[ASSUMPTION][candidate]** 에이전트/스킬 개선의 최소 유효 단위는 3회 이상의 동일 패턴 감지이다. 1-2회는 노이즈일 가능성이 높다.
3. **[ASSUMPTION][candidate]** 개선된 프로파일의 품질 검증은 이후 세션의 피드백 변화로 충분하다. 별도의 오프라인 평가 벤치마크는 초기 버전에서 불필요하다.
4. **[ASSUMPTION][confirmed]** 일일 배치 cron(매일 저녁 지정 시각)이 분석 트리거로 적절하다. 모든 세션 종료마다 분석하지 않고, 전일 세션을 일괄 분석한다. (검증: ADR-0004)
5. **[ASSUMPTION][candidate]** 자동 생성된 에이전트/스킬은 사용자 승인 없이 활성화되지 않는다 (human-in-the-loop). 프로파일 개선(기존 에이전트 미세 조정)은 자동 적용이 허용된다.

## Open Questions

1. **개선 트리거 전략 (확정)**: 일일 배치 cron을 채택한다. 매일 저녁 지정 시각에 cron이 전일 세션을 일괄 분석한다. hooks/signals.jsonl 기반의 세션 종료 시점 트리거는 사용하지 않는다. 비용 효율과 충분한 데이터 축적 간의 균형을 고려한 결정이다. (ADR-0004 참조)
2. **자동 변경 범위 (확정)**: 3-Tier 단계적 적용을 채택한다. Tier 1(프로파일 미세 조정)은 즉시 자동 적용, Tier 2(스킬 프롬프트 수정, 오케스트레이션 파라미터)는 관찰 기간 후 자동 적용, Tier 3(새 에이전트/스킬 생성, 근본적 재설계)는 사용자 승인 후 적용한다. 안전성과 자율성의 단계적 균형을 확보한다. (ADR-0002 참조)
3. **[QUESTION][nice-to-have]** 진화 루프의 변종(variant) 관리에 git branch를 사용할지, 별도 아카이브 디렉토리를 사용할지. HyperAgents는 MAP-Elites 아카이브를 사용하지만, 1인 개발자 환경에서는 git history가 더 자연스러울 수 있다. 기본값: git commit history로 변종 추적.
4. **[QUESTION][nice-to-have]** 오케스트레이션 정책 자동 조정의 구체적 범위. 에이전트 선택 우선순위만 조정할지, parallel-codex의 DAG 구성까지 조정할지. 기본값: 에이전트 선택 우선순위부터 시작.

## Quality Gate Result

**Verdict: proceed-with-advisory** (2026-04-13)

### Critical Criteria (7/7 pass)

| # | Criterion | Score | Evidence |
|---|-----------|-------|----------|
| C1 | Goal clarity | **pass** | PRD Goals: 4개 목표, Non-goals 4개 경계 |
| C2 | Success criteria defined | **pass** | Success Criteria 표: 4지표 현재/목표/측정 |
| C3 | System model explainability | **pass** | ARCHITECTURE.md: C4 다이어그램 3개 + 불변식 5개 |
| C4 | Alternatives compared | **pass** | ADR-0001~0004: 각 3~5개 옵션 대칭 비교 |
| C5 | Decision reasoning | **pass** | ADR-0001~0004: 번호 매긴 근거 + Revisit Triggers |
| C6 | Failure modes identified | **pass** | NFR.md: F1~F3 + 파이프라인별 복구 표 |
| C7 | Feasibility verified | **pass** | spike-1~3 모두 passed |

### Important Criteria (3/4 pass, 1 weak)

| # | Criterion | Score | Evidence |
|---|-----------|-------|----------|
| I8 | Assumption ledger | **pass** | NFR.md 21개 assumption + 전 문서 태그 |
| I9 | Rollback strategy | **pass** | ADR-0002 + NFR 6.2 + PRD Scenario 3 |
| I10 | Validation plan | **weak** | 분산된 검증, cold-start 계획 없음 |
| I11 | Open questions | **pass** | must_answer=0, nice-to-have 구분 명확 |

### Advisory (구현 초기 보완 권장)
1. Validation Plan: regex 패턴 초기 검증 방법, 첫 자동 개선 성공 판단 기준, cold-start 대기 정책 명시
2. 비용 assumption 일관성: ARCHITECTURE.md Invariant 5의 confirmed 태그와 NFR.md candidate 태그 정렬

## References

- [Meta HyperAgents (DGM-H)](https://arxiv.org/abs/2603.19461) --- 자기 수정 에이전트의 진화적 프레임워크. Task agent + meta agent = 단일 편집 가능 프로그램. Generate variants -> evaluate -> archive -> select parent -> repeat.
- [Anthropic Managed Agents](https://www.anthropic.com/engineering/managed-agents) --- Session(append-only event log) / Harness(stateless control loop) / Sandbox 분해. Brain vs Hands 분리 패턴.
- [HyperAgents Source](https://github.com/facebookresearch/Hyperagents) --- DGM-H 참조 구현.
- Spike 결과: `tasks/hyperagent-integration/design/_state.yaml` --- hooks 인프라, symlink 즉시 반영, 세션 JSONL 접근 모두 검증 완료.
- 현재 시스템: `agent-registry/` (15개 에이전트), `skills/` (14개 스킬), `scripts/sync_agents.py`, `scripts/install_assets.py`.
