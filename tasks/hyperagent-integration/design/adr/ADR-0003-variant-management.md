# ADR-0003: Variant Management — 변종 저장 및 선택 전략

- Status: accepted
- Date: 2026-04-13
- Related docs: ../PRD.md, ../ARCHITECTURE.md, ADR-0001-evolution-strategy.md, ADR-0002-safety-boundary.md

## Context

ADR-0001에서 하이브리드 전략(증분 + 상황적 진화)을 채택하면, 시스템은 시간이 지남에 따라 에이전트/스킬의 다양한 "변종(variant)"을 생성한다:

- **증분 모드**: 현재 버전에서 단일 변종 생성 → 적용 (이전 버전은 git 히스토리에 존재)
- **진화 모드**: N개 변종 동시 생성 → 평가 → 최적 선택 (선택되지 않은 변종의 처리?)

핵심 질문들:
1. **저장**: 변종을 어디에, 어떤 형태로 저장하는가?
2. **메타데이터**: 각 변종의 생성 맥락, 평가 결과, 부모 관계를 어떻게 기록하는가?
3. **선택**: 여러 변종 중 최적을 어떻게 결정하는가?
4. **정리**: 오래된/열등한 변종을 언제 삭제하는가?

HyperAgents는 MAP-Elites 기반 아카이브를 사용한다. 행동 공간(behavioral space)을 그리드로 나누고, 각 셀에 가장 높은 적합도(fitness)를 가진 변종을 보관한다. 이는 다양성과 품질을 동시에 유지하는 강력한 메커니즘이지만, 에이전트/스킬의 "행동 공간"을 정의하는 것 자체가 난제다.

### 현재 시스템의 버전 관리 현황

- agent-registry의 모든 파일은 git으로 관리됨
- parallel-codex는 git worktree를 사용하여 병렬 작업 수행
- 별도의 변종 아카이브나 메타데이터 저장소는 존재하지 않음
- 세션 JSONL이 사실상 "사용 로그"이지만 변종과 연결되어 있지 않음

## Options Considered

### Option A: Git 브랜치 기반 변종 관리

각 변종을 별도 git 브랜치로 관리한다. parallel-codex의 worktree 패턴을 확장.

구조:
```
main                          ← 현재 프로덕션 버전
evolve/agent-reviewer/v1      ← 변종 1
evolve/agent-reviewer/v2      ← 변종 2
evolve/agent-reviewer/v3      ← 변종 3
```

**장점:**
- git의 모든 기능(diff, merge, cherry-pick) 활용 가능
- parallel-codex worktree 인프라 직접 재사용
- 변종 간 차이를 `git diff`로 즉시 확인 가능
- 브랜치 삭제로 정리 간단

**단점:**
- 브랜치 수 폭발: 에이전트 13개 × 스킬 17개 × 변종 N개 = 수백 개 브랜치
- 메타데이터(적합도, 부모, 생성 맥락) 저장에 git 브랜치가 부적합 — 별도 메타데이터 저장 필요
- 브랜치 간 의존성 추적 어려움 — A 에이전트의 변종 2가 B 에이전트의 변종 3과만 호환되는 경우
- 장기 보관이 아닌 임시 탐색용으로 설계된 구조 — "아카이브"로서의 의미가 약함
- 오래된 브랜치의 stale 문제 — main이 진행되면 브랜치가 뒤처짐

### Option B: archive/ 디렉토리 기반 버전 파일 관리

프로젝트 내 `archive/` 디렉토리에 변종 파일을 직접 저장한다.

구조:
```
archive/
  agents/
    architecture-reviewer/
      v001_2026-04-13_baseline.md
      v002_2026-04-15_clarity-improvement.md
      v003_2026-04-20_evolved-from-v002.md
  skills/
    commit/
      v001_2026-04-13_baseline.md
      ...
  metadata.jsonl          ← 변종 메타데이터
```

**장점:**
- 직관적 파일 구조 — 파일 시스템만으로 탐색 가능
- 메타데이터와 변종 파일이 같은 위치에 공존
- git으로 관리되므로 이력 추적 가능
- 브랜치 폭발 문제 없음

**단점:**
- 저장 공간 문제: 전체 프로파일 파일을 매 변종마다 복사 → 중복 데이터
- 변종 수 증가 시 디렉토리가 비대해짐
- 변종 파일과 프로덕션 파일 간 동기화 수동 관리 필요
- diff 기반 비교가 자연스럽지 않음 — 두 파일을 직접 비교해야 함
- git 리포지토리 크기 증가

### Option C: Git 태그 + archive.jsonl 메타데이터

HyperAgents의 아카이브 개념을 git 태그와 JSONL 메타데이터로 구현한다.

작동 방식:
1. **프로덕션 버전**은 항상 `main` 브랜치의 최신 커밋
2. **변종 생성** 시 main에서 변경 → 커밋 → 평가 결과에 따라:
   - 채택: main에 유지 (이전 버전은 git 히스토리에 존재)
   - 보관: git tag `archive/agent-reviewer/v003`으로 표시 후 main에서 revert
   - 폐기: revert만 하고 태그 없음
3. **archive.jsonl**: 모든 변종의 메타데이터를 단일 JSONL 파일로 관리

archive.jsonl 레코드 구조:
```json
{
  "id": "variant-20260413-001",
  "target": "agents/architecture-reviewer/instructions.md",
  "git_tag": "archive/architecture-reviewer/v003",
  "parent_variant": "variant-20260410-002",
  "created_at": "2026-04-13T14:30:00Z",
  "trigger": "incremental",
  "change_summary": "코드 리뷰 시 아키텍처 경계 위반 감지 정확도 개선",
  "fitness": {
    "feedback_reduction": 0.3,
    "session_success_rate": 0.85,
    "token_efficiency": 0.92
  },
  "status": "archived",
  "observation_sessions": ["session-abc", "session-def"],
  "behavioral_tags": ["code-review", "architecture", "boundary-detection"]
}
```

**장점:**
- **공간 효율**: 프로덕션은 main에, 아카이브는 tag로. 파일 중복 없음
- **풍부한 메타데이터**: JSONL 형식으로 구조화된 메타데이터. 검색·필터링·분석 용이
- **HyperAgents 아카이브와 개념 정렬**: behavioral_tags가 MAP-Elites의 행동 차원 역할
- **Git 네이티브**: tag는 특정 커밋에 대한 불변 참조 — 변종이 정확히 어떤 상태인지 항상 복원 가능
- **점진적 구현**: 증분 모드에서는 archive.jsonl에 기록만 하면 되고, 진화 모드에서 태그 기능 활용
- **세션 데이터와 자연스러운 연결**: observation_sessions 필드로 변종과 평가 세션 직접 연결

**단점:**
- archive.jsonl이 단일 파일로 커질 수 있음 — 장기적으로 분할 필요 가능
- git tag가 많아지면 `git tag -l` 출력이 길어짐 — 네이밍 규칙과 정리 정책 필요
- 변종 복원 시 `git show archive/agent-reviewer/v003:agents/architecture-reviewer/instructions.md` 같은 명령이 직관적이지 않음
- behavioral_tags 정의가 수동 — 자동 태깅 로직 개발 필요

## Decision

**Option C (Git 태그 + archive.jsonl)** 채택.

근거:
1. HyperAgents의 핵심 혁신인 아카이브 기반 다양성 유지를 git 네이티브 방식으로 구현. MAP-Elites의 "행동 공간 그리드"를 behavioral_tags로 대체하여 연속적·비정형적 행동 공간 지원.
2. 공간 효율성이 가장 높음. 변종은 git 히스토리/태그에 존재하므로 추가 파일 저장 불필요.
3. archive.jsonl의 구조화된 메타데이터가 자기개선 루프의 "기억(memory)" 역할. 어떤 변종이 어떤 맥락에서 효과적이었는지 검색 가능.
4. ADR-0001의 하이브리드 전략과 자연스럽게 통합. 증분 모드에서는 JSONL 기록만, 진화 모드에서는 태그+JSONL 풀 활용.
5. ADR-0004의 세션 기반 분석과 observation_sessions 필드로 직접 연결.

[ASSUMPTION][C] archive.jsonl은 `tasks/hyperagent-integration/archive.jsonl` 또는 프로젝트 루트의 `evolution/archive.jsonl`에 위치한다. 위치는 구현 시 확정.

## Rejected Alternatives

- **Option A** (Git 브랜치)는 기각. 단기 탐색용으로는 적합하나 장기 아카이브로서 부적합. 브랜치 수 폭발, 메타데이터 부재, stale 브랜치 문제가 심각하다. 다만 진화 모드에서 변종 생성 시 임시 브랜치/worktree를 사용하는 것은 Option C와 병용 가능.
- **Option B** (archive/ 디렉토리)는 기각. 파일 중복에 의한 저장 공간 문제, git 리포지토리 크기 증가, 변종 수 증가 시 관리 어려움. git이 이미 제공하는 버전 관리 기능을 파일 복사로 재구현하는 것은 비효율적.

## Consequences

### Positive
- git 히스토리 + 태그로 모든 변종이 복원 가능한 상태로 영구 보관
- archive.jsonl이 자기개선 시스템의 "장기 기억" 역할 — 과거 실험 결과를 미래 개선에 활용
- behavioral_tags를 통한 다양성 추적 — 특정 행동 영역에서 최적 변종 빠르게 탐색
- 세션 데이터와 변종 데이터의 연결로 인과 분석 가능

### Negative
- archive.jsonl의 스키마 진화 관리 필요 — 필드 추가/변경 시 하위 호환성
- git 태그 네이밍 규칙과 정리 정책 설계 필요
- 변종 복원 UX가 직관적이지 않음 — 래퍼 스크립트/명령어 필요
- behavioral_tags의 자동 태깅 품질이 아카이브의 유용성을 좌우

### Future work
- archive.jsonl → SQLite 또는 DuckDB 마이그레이션 (변종 수 1000개 이상 시)
- behavioral_tags 자동 생성: 변경 diff를 분석하여 태그 자동 부여
- "프로젝트 간 학습 전이" 시 archive.jsonl의 cross-project 검색
- 변종 계보(lineage) 시각화 도구

## Assumptions

1. [ASSUMPTION][C] archive.jsonl의 레코드 수는 초기 6개월 동안 100-300건 수준이며, JSONL 단일 파일로 충분히 관리 가능하다.
2. [ASSUMPTION][C] behavioral_tags는 초기에 수동(자기개선 에이전트가 변경 내용에서 추론)으로 부여하고, 데이터 축적 후 자동 태깅으로 전환한다.
3. [ASSUMPTION][C] 진화 모드에서 생성된 비채택 변종 중 fitness가 일정 수준 이상인 것만 archive 태그를 부여한다. 나머지는 git 히스토리에만 존재.
4. [ASSUMPTION][C] fitness 메트릭은 ADR-0004의 세션 분석에서 도출된 값을 사용하며, 초기에는 단순 지표(피드백 빈도 감소율)로 시작한다.
5. [ASSUMPTION][C] git 태그 정리는 6개월 이상 된 태그 중 fitness 하위 50%를 삭제하는 정책으로 시작한다.

## Revisit Triggers

- archive.jsonl 레코드가 1000건을 초과하여 파싱 성능이 저하되는 경우 → DB 마이그레이션 검토
- git 태그가 500개를 초과하여 git 명령 성능에 영향을 미치는 경우 → 태그 정리 정책 강화 또는 Option B 부분 도입
- behavioral_tags의 유용성이 낮아 아카이브 검색이 비효율적인 경우 → 태그 체계 재설계 또는 embedding 기반 유사도 검색 도입
- 프로젝트 간 학습 전이 구현 시 → 단일 리포 archive.jsonl에서 cross-repo 메타데이터 저장소로 확장 필요

## References

- [Meta HyperAgents (arXiv:2603.19461)](https://arxiv.org/abs/2603.19461) — MAP-Elites archive, behavioral space, quality-diversity optimization
- [MAP-Elites (Mouret & Clune, 2015)](https://arxiv.org/abs/1504.04909) — Illuminating search spaces by mapping the performance of solutions across a feature space
- 현재 시스템: `parallel-codex` worktree 기반 병렬 실행, `agent-registry/` SSOT 구조
- JSONL 형식: 세션 데이터(`.claude/projects/<project>/<uuid>.jsonl`)와 동일한 형식으로 일관성 확보
