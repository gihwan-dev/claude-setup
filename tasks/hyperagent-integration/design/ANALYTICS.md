<!-- Status: flesh -->
<!-- Confidence: high -->
<!-- doc_type: analytics (custom) -->

# Analytics: 에이전트/스킬 성능 측정 이벤트 택소노미 및 신호 추출 전략

## 1. 개요

이 문서는 HyperAgent 자기개선 시스템의 **측정 기반(measurement layer)**을 정의한다. 세션 JSONL에서 성능 신호를 추출하고, 에이전트/스킬별 점수를 산출하며, 개선 트리거 조건을 판단하는 전체 파이프라인을 다룬다.

**핵심 원칙**: 대화가 최고의 신호 소스다. 별도 계측(instrumentation) 없이 기존 세션 JSONL만으로 충분한 성능 데이터를 추출한다.

**데이터 소스**:

| 소스 | 경로 | 형식 | 역할 |
|------|------|------|------|
| 세션 대화 | `~/.claude/projects/<project>/<sessionId>.jsonl` | JSONL (type, message, timestamp, uuid, parentUuid, sessionId, cwd, gitBranch) | 1차 신호 소스. 사용자 피드백, 도구 호출, 에이전트 행동 전체 기록 |
| 명령어 히스토리 | `~/.claude/history.jsonl` | JSONL (display, timestamp, project, sessionId) | 세션 → 프로젝트 매핑, 명령어 패턴 분석 |
| 활동 통계 | `~/.claude/stats-cache.json` | JSON (dailyActivity, 모델별 토큰 사용량) | 거시 추세. 일별 메시지/세션/도구호출 카운트 |
| 메모리 | `~/.claude/projects/<project>/memory/*.md` | Markdown | 사용자의 명시적 피드백/선호도. 이미 정제된 신호 |

---

## 2. 성능 신호 택소노미 (Performance Signal Taxonomy)

### 2.1 부정 신호 (Negative Signals)

사용자가 에이전트/스킬 출력에 불만족하거나 수정을 요구하는 패턴.

| 신호 ID | 이름 | 설명 | 가중치 | 감지 방법 |
|---------|------|------|--------|----------|
| `NEG-CORRECT` | 직접 보정 | 사용자가 에이전트 출력을 명시적으로 수정 지시 | 1.0 | 한국어 보정 패턴 매칭 |
| `NEG-REJECT` | 거부 | 사용자가 결과를 거부하고 재시도 요청 | 1.5 | 재시도 키워드 + 직전 assistant 메시지 존재 확인 |
| `NEG-REPEAT` | 반복 지시 | 동일 세션에서 같은 의도의 지시를 2회 이상 반복 | 2.0 | 의미적 유사도(임베딩) 또는 동일 도구 연속 호출 |
| `NEG-TOOL-FAIL` | 도구 실패 | tool_result에 에러 메시지 포함 | 0.5 | tool_result 내 에러 패턴 매칭 |
| `NEG-ROLLBACK` | 롤백 | git revert, git checkout --, "되돌려" 등 롤백 행동 | 1.5 | git 명령어 + 한국어 롤백 키워드 |
| `NEG-ABANDON` | 작업 포기 | 사용자가 작업을 중단하고 다른 주제로 전환 | 1.0 | 주제 전환 감지 (비완료 상태에서 새 요청) |

**한국어 보정 패턴 (NEG-CORRECT)**:

```python
CORRECTION_PATTERNS = [
    # 직접 부정
    r"아니[요]?\s",
    r"아닌데",
    r"그게\s*아니[라고]",
    r"아니야",
    r"틀렸[어는]",
    # 재지시
    r"다시\s*(해|하|만들|작성|생성|수정)",
    r"다시\s*해\s*봐",
    r"그거\s*말고",
    r"그게\s*아니[라고]",
    r"[이그]렇게\s*말고",
    # 불만 표현
    r"왜\s*(이렇게|그렇게|자꾸|계속|또)",
    r"제대로\s*(해|안|좀)",
    r"똑바로",
    r"잘못\s*(했|된|되)",
    # 누락 지적
    r"빠[졌뜨트]",
    r"빠져\s*있",
    r"안\s*(했|됐|빠)",
    r"누락",
    r"빠[뜨트]렸",
]
```

**한국어 거부 패턴 (NEG-REJECT)**:

```python
REJECTION_PATTERNS = [
    r"다시\s*해\s*줘",
    r"처음부터\s*다시",
    r"리셋",
    r"취소",
    r"됐[어고].*말[어고]",
    r"하지\s*마",
    r"그만",
    r"필요\s*없",
]
```

### 2.2 긍정 신호 (Positive Signals)

사용자가 에이전트/스킬 출력에 만족하거나 수정 없이 수용하는 패턴.

| 신호 ID | 이름 | 설명 | 가중치 | 감지 방법 |
|---------|------|------|--------|----------|
| `POS-ACCEPT` | 무수정 수용 | 에이전트 출력 후 수정 없이 다음 작업으로 진행 | 0.5 | assistant 메시지 후 비보정 user 메시지 (새 주제 또는 후속 요청) |
| `POS-PRAISE` | 명시적 칭찬 | 사용자가 결과를 긍정적으로 평가 | 1.0 | 한국어 칭찬 패턴 매칭 |
| `POS-REUSE` | 재사용 | 동일 에이전트/스킬을 후속 세션에서 다시 호출 | 0.3 | 세션 간 동일 entity 사용 빈도 |
| `POS-COMPLETE` | 완료 | 작업이 정상적으로 완료됨 | 0.5 | 세션 종료 시 미완료 작업 없음 |
| `POS-MEMORY` | 메모리 저장 | 사용자가 결과를 memory에 명시적으로 저장 | 1.5 | memory 파일 쓰기 감지 |

**한국어 칭찬 패턴 (POS-PRAISE)**:

```python
PRAISE_PATTERNS = [
    r"좋[아았]",
    r"완벽",
    r"잘\s*(했|됐|만들|나왔)",
    r"맞[아았]",
    r"그래\s*그거",
    r"오[케게]이",
    r"[ㅋk]{2,}",  # 웃음 반응 (가벼운 긍정)
    r"고마[워웠]",
    r"감사",
    r"딱\s*(이거|좋|맞)",
    r"훌륭",
    r"대박",
    r"ㅇㅇ",  # 긍정 응답
]
```

### 2.3 중립 신호 (Neutral / Context-Dependent Signals)

단독으로는 품질을 판단할 수 없으나, 추세 분석에 유용한 신호.

| 신호 ID | 이름 | 설명 | 용도 |
|---------|------|------|------|
| `CTX-SESSION-LEN` | 세션 길이 | 메시지 수, 경과 시간 | 정규화 분모. 같은 보정 1건이라도 긴 세션 vs 짧은 세션에서 의미가 다름 |
| `CTX-TOOL-COUNT` | 도구 호출 수 | 세션 내 도구 호출 총 횟수 | 복잡도 프록시. 도구 호출 대비 실패율 산출 |
| `CTX-TURN-COUNT` | 턴 수 | user-assistant 쌍의 수 | 대화 깊이 프록시 |
| `CTX-ENTITY-ACTIVE` | 활성 엔티티 | 해당 세션에서 사용된 에이전트/스킬 목록 | 신호 귀속(attribution) 기준 |
| `CTX-TOKEN-USAGE` | 토큰 사용량 | 세션의 총 토큰 소비 | 비용 효율 분석 |

---

## 3. 엔티티별 점수 모델 (Per-Entity Scoring Model)

### 3.1 점수 대상 엔티티

```
Entity Types:
├── Agent (agent-registry의 각 에이전트)
│   예: test-engineer, code-quality-reviewer, architecture-reviewer
├── Skill (skills의 각 스킬)  
│   예: commit, build, design-docs, parallel-codex
└── Orchestration (메타 수준 의사결정)
    예: 에이전트 선택, fan-out 정책, 실행 순서
```

### 3.2 에이전트 점수 차원

| 차원 | 설명 | 산출 공식 | 범위 |
|------|------|----------|------|
| `accuracy` | 리뷰/분석 정확도 | `1 - (NEG-CORRECT 건수 / 총 출력 턴 수)` | 0.0 ~ 1.0 |
| `relevance` | 제안의 적절성 | `1 - (NEG-REJECT 건수 / 총 제안 수)` | 0.0 ~ 1.0 |
| `false_positive_rate` | 잘못된 지적/제안 비율 | `(사용자가 무시 또는 거부한 지적 수) / 총 지적 수` | 0.0 ~ 1.0 (낮을수록 좋음) |
| `composite` | 종합 점수 | `0.4 * accuracy + 0.4 * relevance + 0.2 * (1 - false_positive_rate)` | 0.0 ~ 1.0 |

### 3.3 스킬 점수 차원

| 차원 | 설명 | 산출 공식 | 범위 |
|------|------|----------|------|
| `acceptance_rate` | 출력 수용율 | `(POS-ACCEPT + POS-PRAISE 건수) / 총 실행 수` | 0.0 ~ 1.0 |
| `modification_freq` | 수정 빈도 | `NEG-CORRECT 건수 / 총 실행 수` | 0.0 ~ 1.0 (낮을수록 좋음) |
| `completion_rate` | 완료율 | `정상 완료 세션 수 / 총 호출 세션 수` | 0.0 ~ 1.0 |
| `rework_rate` | 재작업율 | `NEG-REPEAT 건수 / 총 실행 수` | 0.0 ~ 1.0 (낮을수록 좋음) |
| `composite` | 종합 점수 | `0.35 * acceptance_rate + 0.25 * (1 - modification_freq) + 0.25 * completion_rate + 0.15 * (1 - rework_rate)` | 0.0 ~ 1.0 |

### 3.4 오케스트레이션 점수

| 차원 | 설명 | 산출 공식 |
|------|------|----------|
| `dispatch_accuracy` | 올바른 에이전트 배정률 | `(교체 없이 완료된 태스크) / 총 태스크` |
| `fanout_efficiency` | 병렬 실행 효율 | `(병렬 실행 태스크 성공률) / 총 병렬 태스크` |
| `routing_relevance` | 라우팅 적절성 | `1 - (사용자가 에이전트 교체를 요청한 횟수 / 총 에이전트 배정 수)` |

---

## 4. 신호 추출 파이프라인 (Signal Extraction Pipeline)

### 4.1 파이프라인 개요

```
Session JSONL
    │
    ▼
[Stage 1] Parse & Normalize
    │  JSONL → StructuredMessage[]
    │  도구 호출 분리, 타임스탬프 정렬
    ▼
[Stage 2] Entity Attribution
    │  각 메시지를 에이전트/스킬에 귀속
    │  Skill 호출은 tool_use의 Skill 도구 호출로 감지
    │  Agent는 assistant 메시지 내 subagent 패턴으로 감지
    ▼
[Stage 3] Signal Classification
    │  regex 기반 1차 분류 (빠르고 저비용)
    │  모호한 케이스만 LLM 2차 분류 (정확하지만 고비용)
    ▼
[Stage 4] Event Emission
    │  분류된 신호를 이벤트 스키마에 맞춰 출력
    ▼
[Stage 5] Score Aggregation
       세션 단위 → 일 단위 → 주 단위 집계
```

### 4.2 Stage 1: Parse & Normalize

```python
@dataclass
class StructuredMessage:
    uuid: str
    parent_uuid: str | None
    timestamp: datetime
    session_id: str
    msg_type: Literal["user", "assistant", "system", "file-history-snapshot"]
    role: str | None          # user, assistant
    content_text: str | None  # 텍스트 콘텐츠 추출
    tool_calls: list[ToolCall]  # assistant 메시지에서 추출한 도구 호출
    tool_results: list[ToolResult]  # user 메시지(tool_result 타입)에서 추출
    is_meta: bool             # isMeta 플래그 (시스템 메시지 필터링용)
    cwd: str | None
    git_branch: str | None

@dataclass
class ToolCall:
    tool_id: str
    tool_name: str
    input_data: dict
    caller_type: str  # "direct", "subagent" 등

@dataclass
class ToolResult:
    tool_use_id: str
    content: str
    is_error: bool
```

**파싱 규칙**:
- `type == "file-history-snapshot"`: 스냅샷 메시지. 무시하되 타임스탬프 참조용으로 보존.
- `type == "user"` + `message.content`가 문자열: 일반 사용자 메시지. `content_text`에 저장.
- `type == "user"` + `message.content`가 dict with `type: "tool_result"`: 도구 결과. `tool_results`에 추가.
- `type == "assistant"` + content가 리스트: 각 항목을 분류.
  - `type: "text"`: `content_text`에 추가.
  - `type: "tool_use"`: `tool_calls`에 추가.
  - `type: "thinking"`: 무시 (thinking 블록은 분석 대상 외).
- `isMeta == true`: 시스템 메시지. 신호 추출에서 제외하되 컨텍스트 참조용 보존.

### 4.3 Stage 2: Entity Attribution (엔티티 귀속)

세션 내 각 메시지 구간을 어떤 에이전트 또는 스킬의 동작으로 귀속할지 결정한다.

**스킬 감지**:
```python
def detect_skill_activation(msg: StructuredMessage) -> str | None:
    """Skill 도구 호출로 스킬 활성화를 감지한다."""
    for tc in msg.tool_calls:
        if tc.tool_name == "Skill":
            return tc.input_data.get("skill")
    # 사용자 메시지에서 슬래시 커맨드 감지
    if msg.msg_type == "user" and msg.content_text:
        match = re.match(r"^[/$](\w[\w-]*)", msg.content_text.strip())
        if match:
            return match.group(1)
    return None
```

**에이전트 감지**:
```python
def detect_agent_activation(msg: StructuredMessage) -> str | None:
    """TeamCreate/Agent 도구 호출에서 에이전트 이름을 추출한다."""
    for tc in msg.tool_calls:
        if tc.tool_name == "Agent":
            subagent_type = tc.input_data.get("subagent_type", "")
            # subagent_type이 agent-registry의 에이전트 이름과 매칭되면 귀속
            if subagent_type in KNOWN_AGENTS:
                return subagent_type
    return None

KNOWN_AGENTS = [
    "architecture-reviewer", "browser-explorer", "code-quality-reviewer",
    "design-evaluator", "design-skeptic", "docs-researcher",
    "react-state-reviewer", "socratic-partner", "structure-reviewer",
    "test-engineer", "type-specialist", "verification-worker", "web-researcher",
]
```

**귀속 범위**: 스킬/에이전트 활성화 시점부터 다음 활성화 또는 세션 종료까지의 모든 메시지를 해당 엔티티에 귀속한다. 활성화된 엔티티가 없는 구간은 `orchestration`으로 귀속한다.

### 4.4 Stage 3: Signal Classification (신호 분류)

**2단계 분류 전략**:

```
사용자 메시지
    │
    ▼
[Tier 1] Regex 패턴 매칭
    │  CORRECTION_PATTERNS → NEG-CORRECT
    │  REJECTION_PATTERNS  → NEG-REJECT
    │  PRAISE_PATTERNS     → POS-PRAISE
    │  매칭 성공 → 즉시 분류 완료
    │  매칭 실패 → Tier 2로 전달
    ▼
[Tier 2] 컨텍스트 기반 휴리스틱
    │  직전 assistant 메시지 후 새 요청 → POS-ACCEPT (암묵적 수용)
    │  /clear 또는 주제 전환 → CTX (중립) 또는 NEG-ABANDON 판단
    │  도구 결과에 에러 → NEG-TOOL-FAIL
    │  모호 → UNCLASSIFIED로 버퍼링
    ▼
[Tier 3] LLM 배치 분류 (Codex 활용)
       UNCLASSIFIED 버퍼가 20건 이상 누적 시
       Codex에 배치 전송하여 분류 (Codex 토큰 충분, 비용 제약 완화)
       프롬프트: "다음 사용자 메시지를 [NEG-CORRECT, NEG-REJECT, POS-ACCEPT, POS-PRAISE, NEUTRAL] 중 하나로 분류하시오. 직전 assistant 메시지 컨텍스트를 함께 제공합니다."
```

**도구 실패 감지**:
```python
TOOL_ERROR_PATTERNS = [
    r"(?i)error",
    r"(?i)failed",
    r"(?i)exception",
    r"(?i)timeout",
    r"REDIRECT DETECTED",
    r"permission denied",
    r"not found",
    r"InputValidationError",
]
```

**롤백 감지**:
```python
ROLLBACK_PATTERNS = [
    # git 명령어
    r"git\s+(revert|reset|checkout\s+--)",
    # 한국어 롤백 표현
    r"되돌[려리]",
    r"원래대로",
    r"롤백",
    r"복원",
    r"이전\s*버전",
]
```

### 4.5 Stage 4: 이벤트 생성

분류된 신호를 구조화된 이벤트로 변환한다. 이벤트 스키마는 Section 6에서 정의한다.

### 4.6 파이프라인 실행 모드

| 모드 | 트리거 | 처리 범위 | 비용 |
|------|--------|----------|------|
| `daily-batch` (기본) | 일일 배치 cron (매일 저녁 지정 시각) | 전일 모든 세션 | 중간 (LLM Tier 3 포함, Codex 토큰 활용) |
| `on-demand` | 사용자 명시 요청 | 지정 기간 | 가변 |

---

## 5. 집계 및 추세 분석 (Aggregation and Trending)

### 5.1 집계 계층

```
Level 0: Raw Event
    단일 신호 이벤트 (예: NEG-CORRECT 1건)
    
Level 1: Session Score
    세션 내 모든 이벤트를 엔티티별로 집계
    session_score = Σ(positive_weights) - Σ(negative_weights)
    정규화: session_score / session_length (턴 수)
    
Level 2: Daily Score  
    당일 모든 세션의 엔티티별 점수 가중 평균
    daily_score = Σ(session_score × session_weight) / Σ(session_weight)
    session_weight = ln(turn_count + 1)  # 긴 세션일수록 신뢰도 높음
    
Level 3: Rolling Window Score
    최근 N일의 decay-weighted 평균
    rolling_score = Σ(daily_score × decay_weight) / Σ(decay_weight)
```

### 5.2 시간 감쇠 (Temporal Decay)

최근 세션의 데이터가 더 높은 가중치를 가진다.

```python
def decay_weight(days_ago: int, half_life: int = 7) -> float:
    """지수 감쇠. half_life일 전의 데이터는 가중치 0.5."""
    return 2 ** (-days_ago / half_life)

# 예시 (half_life=7):
# 오늘: 1.0
# 1일 전: 0.906
# 3일 전: 0.741
# 7일 전: 0.5
# 14일 전: 0.25
# 28일 전: 0.0625
```

[ASSUMPTION][candidate] `half_life = 7`일. 1주 전 데이터는 절반 가중치. 4주 이전 데이터는 사실상 무시됨.

### 5.3 베이스라인 설정

```python
@dataclass
class EntityBaseline:
    entity_id: str       # 에이전트/스킬 이름
    entity_type: str     # "agent" | "skill" | "orchestration"
    baseline_score: float
    baseline_sessions: int  # 베이스라인 산출에 사용된 세션 수
    established_at: datetime
    
    @staticmethod
    def compute(scores: list[float], min_sessions: int = 5) -> float | None:
        """최소 N개 세션이 축적되어야 베이스라인 설정."""
        if len(scores) < min_sessions:
            return None  # 데이터 부족
        return statistics.median(scores)  # 중앙값 사용 (이상치 영향 최소화)
```

[ASSUMPTION][candidate] 최소 5세션이 축적되어야 베이스라인을 설정한다. 그 이전에는 개선 트리거를 발동하지 않고 데이터만 수집한다.

### 5.4 추세 감지

```python
@dataclass
class Trend:
    entity_id: str
    direction: Literal["improving", "stable", "degrading"]
    magnitude: float      # 베이스라인 대비 변화율
    confidence: float     # 0.0 ~ 1.0
    period_sessions: int  # 추세 산출에 사용된 세션 수

def detect_trend(
    baseline: float,
    recent_scores: list[float],  # 최근 7일
    threshold: float = 0.15,     # 15% 변화부터 유의미
) -> Trend:
    if len(recent_scores) < 3:
        return Trend(direction="stable", magnitude=0, confidence=0.3)
    
    recent_avg = statistics.mean(recent_scores)
    delta = (recent_avg - baseline) / max(baseline, 0.01)
    
    if delta > threshold:
        direction = "improving"
    elif delta < -threshold:
        direction = "degrading"
    else:
        direction = "stable"
    
    confidence = min(1.0, len(recent_scores) / 10)
    return Trend(direction=direction, magnitude=abs(delta), confidence=confidence)
```

---

## 6. 이벤트 스키마 (Event Schema)

### 6.1 기본 이벤트 엔벨로프

```jsonc
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["event_id", "event_type", "timestamp", "session_id", "entity"],
  "properties": {
    "event_id": {
      "type": "string",
      "format": "uuid",
      "description": "이벤트 고유 식별자"
    },
    "event_type": {
      "type": "string",
      "enum": [
        "signal.negative.correction",
        "signal.negative.rejection",
        "signal.negative.repeat",
        "signal.negative.tool_failure",
        "signal.negative.rollback",
        "signal.negative.abandon",
        "signal.positive.accept",
        "signal.positive.praise",
        "signal.positive.reuse",
        "signal.positive.complete",
        "signal.positive.memory_save",
        "signal.context.session_summary",
        "score.session",
        "score.daily",
        "score.rolling",
        "trend.detected",
        "trigger.improvement"
      ]
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "session_id": {
      "type": "string",
      "format": "uuid"
    },
    "entity": {
      "type": "object",
      "required": ["id", "type"],
      "properties": {
        "id": {
          "type": "string",
          "description": "에이전트/스킬 이름 (예: test-engineer, commit)"
        },
        "type": {
          "type": "string",
          "enum": ["agent", "skill", "orchestration"]
        }
      }
    },
    "project": {
      "type": "string",
      "description": "프로젝트 경로 (cwd 기반)"
    },
    "data": {
      "type": "object",
      "description": "이벤트 타입별 상세 데이터"
    }
  }
}
```

### 6.2 신호 이벤트 상세 (data 필드)

**signal.negative.correction**:
```jsonc
{
  "source_message_uuid": "uuid",       // 보정 메시지의 uuid
  "target_message_uuid": "uuid",       // 보정 대상 assistant 메시지의 uuid
  "correction_text": "string",         // 사용자 보정 메시지 원문 (200자 이내 발췌)
  "matched_pattern": "string",         // 매칭된 regex 패턴 이름
  "classification_tier": 1,            // 1=regex, 2=heuristic, 3=LLM
  "weight": 1.0
}
```

**signal.negative.tool_failure**:
```jsonc
{
  "tool_name": "string",              // 실패한 도구 이름
  "tool_call_id": "string",
  "error_snippet": "string",          // 에러 메시지 발췌 (200자 이내)
  "error_pattern": "string",          // 매칭된 에러 패턴
  "weight": 0.5
}
```

**signal.positive.praise**:
```jsonc
{
  "source_message_uuid": "uuid",
  "praise_text": "string",            // 칭찬 메시지 원문 (200자 이내 발췌)
  "matched_pattern": "string",
  "preceding_action": "string",       // 직전 assistant 행동 요약
  "weight": 1.0
}
```

**signal.positive.accept**:
```jsonc
{
  "accepted_message_uuid": "uuid",    // 수용된 assistant 메시지의 uuid
  "next_message_uuid": "uuid",        // 후속 사용자 메시지의 uuid (새 주제/후속 요청)
  "gap_seconds": 30,                  // 수용까지 경과 시간
  "weight": 0.5
}
```

**signal.context.session_summary**:
```jsonc
{
  "total_turns": 42,
  "total_tool_calls": 18,
  "duration_minutes": 35.5,
  "entities_active": [
    {"id": "commit", "type": "skill", "turns": 8},
    {"id": "test-engineer", "type": "agent", "turns": 12}
  ],
  "signal_counts": {
    "NEG-CORRECT": 2,
    "NEG-REJECT": 0,
    "POS-ACCEPT": 8,
    "POS-PRAISE": 1
  }
}
```

### 6.3 점수 이벤트 상세

**score.session**:
```jsonc
{
  "scores": {
    "accuracy": 0.85,
    "relevance": 0.92,
    "composite": 0.88
  },
  "signal_breakdown": {
    "positive_total": 4.5,
    "negative_total": -1.0,
    "net": 3.5,
    "normalized": 0.88
  },
  "session_weight": 2.1      // ln(turn_count + 1)
}
```

**score.rolling**:
```jsonc
{
  "window_days": 7,
  "sessions_in_window": 12,
  "scores": {
    "composite": 0.82,
    "accuracy": 0.80,
    "relevance": 0.85
  },
  "baseline": {
    "composite": 0.75,
    "established_at": "2026-04-01T00:00:00Z",
    "sessions_used": 8
  },
  "trend": {
    "direction": "improving",
    "magnitude": 0.09,
    "confidence": 0.7
  }
}
```

### 6.4 개선 트리거 이벤트

**trigger.improvement**:
```jsonc
{
  "trigger_reason": "score_degradation",  // 아래 Section 7에서 정의
  "details": {
    "current_score": 0.58,
    "baseline_score": 0.75,
    "delta": -0.17,
    "degrading_since": "2026-04-10T00:00:00Z",
    "sessions_since_last_improvement": 15
  },
  "recommended_action": "profile_refinement",
  "priority": "high",
  "evidence": [
    {
      "event_id": "uuid",
      "event_type": "signal.negative.correction",
      "summary": "'vi.mock을 사용하라'는 보정이 3회 반복"
    }
  ]
}
```

---

## 7. 개선 트리거 기준 (Improvement Trigger Criteria)

### 7.1 트리거 조건

| 트리거 ID | 조건 | 우선순위 | 설명 |
|-----------|------|---------|------|
| `TRIG-DEGRADE` | rolling_score < baseline - 0.15 | high | 점수가 베이스라인 대비 15% 이상 하락 |
| `TRIG-ACCUMULATE` | sessions_since_last_improvement >= [ASSUMPTION][candidate] 20 | medium | 마지막 개선 이후 충분한 데이터 축적 |
| `TRIG-REPEAT-PATTERN` | 동일 NEG-CORRECT 패턴이 [ASSUMPTION][candidate] 3회 이상 | high | 같은 보정이 반복됨 (명백한 프로파일 결함) |
| `TRIG-USER-REQUEST` | 사용자가 명시적으로 개선 요청 | critical | "이 에이전트 개선해줘", "스킬 업데이트" 등 |
| `TRIG-NEW-PATTERN` | 기존 에이전트/스킬로 커버 안 되는 작업 패턴이 [ASSUMPTION][candidate] 5회 이상 | medium | 새 에이전트/스킬 생성 후보 |
| `TRIG-SUSTAINED-LOW` | rolling_score < 0.5이 [ASSUMPTION][candidate] 7일 이상 지속 | high | 장기 저성능. 근본적 재설계 검토 필요 |

### 7.2 반복 패턴 감지 (TRIG-REPEAT-PATTERN)

같은 보정이 반복되는 것은 가장 명확한 개선 신호다.

```python
def detect_repeated_corrections(
    events: list[SignalEvent],
    entity_id: str,
    similarity_threshold: float = 0.8,
    min_occurrences: int = 3,
    window_days: int = 14,
) -> list[RepeatedPattern]:
    """동일 엔티티에 대한 반복 보정 패턴을 감지한다."""
    corrections = [
        e for e in events
        if e.event_type == "signal.negative.correction"
        and e.entity.id == entity_id
        and e.age_days <= window_days
    ]
    
    # 보정 텍스트를 클러스터링 (간단한 토큰 겹침 기반)
    clusters = cluster_by_similarity(
        [c.data["correction_text"] for c in corrections],
        threshold=similarity_threshold,
    )
    
    return [
        RepeatedPattern(
            pattern_summary=cluster.centroid_text,
            occurrences=len(cluster.members),
            first_seen=min(m.timestamp for m in cluster.members),
            last_seen=max(m.timestamp for m in cluster.members),
            example_messages=[m.data["correction_text"] for m in cluster.members[:3]],
        )
        for cluster in clusters
        if len(cluster.members) >= min_occurrences
    ]
```

### 7.3 트리거 디바운싱

같은 엔티티에 대해 트리거가 너무 자주 발동되지 않도록 제어한다.

```python
TRIGGER_COOLDOWN = {
    "TRIG-DEGRADE": timedelta(days=3),       # 최소 3일 간격
    "TRIG-ACCUMULATE": timedelta(days=7),    # 최소 7일 간격
    "TRIG-REPEAT-PATTERN": timedelta(days=1),# 최소 1일 간격
    "TRIG-USER-REQUEST": timedelta(hours=0), # 즉시 (쿨다운 없음)
    "TRIG-NEW-PATTERN": timedelta(days=7),   # 최소 7일 간격
    "TRIG-SUSTAINED-LOW": timedelta(days=7), # 최소 7일 간격
}
```

### 7.4 트리거 → 행동 매핑

| 트리거 | 권장 행동 | 자동/수동 |
|--------|----------|----------|
| `TRIG-DEGRADE` | 프로파일/프롬프트 미세 조정 | 자동 적용 (rollback 안전장치 포함) |
| `TRIG-ACCUMULATE` | 전체 점수 리뷰 + 필요 시 개선 | 자동 분석, 변경은 자동 적용 |
| `TRIG-REPEAT-PATTERN` | 반복 패턴을 프로파일에 반영 | 자동 적용 |
| `TRIG-USER-REQUEST` | 사용자 요청에 따른 개선 | 사용자 지시 기반 |
| `TRIG-NEW-PATTERN` | 새 에이전트/스킬 초안 생성 | 초안 생성 후 사용자 승인 필요 |
| `TRIG-SUSTAINED-LOW` | 근본적 재설계 제안 | 제안 후 사용자 승인 필요 |

---

## 7.5 보조 지표: 커밋 반영률 (git blame 기반)

세션 피드백만으로는 포착하기 어려운 **실질적 기여도**를 측정하기 위해, 자동 개선된 프로파일/스킬의 내용이 실제 코드 커밋에 얼마나 반영되었는지를 보조 지표로 활용한다.

### 측정 방법

```python
def compute_commit_adoption_rate(
    entity_id: str,
    improvement_date: datetime,
    window_days: int = 14,
    repo_path: str = ".",
) -> float:
    """
    개선 적용 후 window_days 기간 동안의 커밋에서
    해당 에이전트/스킬이 관여한 코드 변경 비율을 측정한다.
    
    git blame 기반으로 에이전트/스킬 세션에서 생성된 코드가
    최종 커밋에 얼마나 남아있는지(반영률)를 산출한다.
    """
    # 1. 개선 이후 기간의 세션 중 해당 entity 사용 세션 식별
    # 2. 해당 세션에서 수정된 파일 목록 추출
    # 3. git blame으로 해당 파일의 최종 커밋 귀속 확인
    # 4. 반영률 = (에이전트/스킬 세션 커밋 잔존 라인) / (총 변경 라인)
    ...
```

### 활용

| 활용 시점 | 방법 |
|-----------|------|
| 변종 평가 보조 | 실사용 데이터 기반 점수와 함께 커밋 반영률을 가중 평균하여 종합 평가 |
| 장기 추세 분석 | 에이전트/스킬 개선 전후 커밋 반영률 변화를 추적하여 개선 효과 검증 |
| 정체 감지 | 점수는 안정적이나 커밋 반영률이 하락하면 실질적 기여가 줄어든 신호 |

커밋 반영률은 보조 지표로만 사용하며, 메인 점수 모델(Section 3)의 composite 점수를 대체하지 않는다.

---

## 7.6 작업 난이도 태깅 (Session Complexity Tagging)

Session Analyzer가 세션별 복잡도를 태깅하여, 점수 정규화와 공정한 에이전트/스킬 평가를 지원한다. 동일한 보정 1건이라도 단순 작업 세션과 복잡 작업 세션에서 의미가 다르기 때문이다.

### 복잡도 차원

| 차원 | 설명 | 산출 방법 |
|------|------|----------|
| `turn_depth` | 대화 깊이 | 총 턴 수 (단순: <10, 보통: 10-30, 복잡: 30+) |
| `tool_diversity` | 도구 다양성 | 사용된 고유 도구 종류 수 |
| `entity_count` | 관여 엔티티 수 | 세션 내 활성화된 에이전트 + 스킬 수 |
| `file_scope` | 파일 변경 범위 | 수정/생성된 파일 수 |
| `branch_complexity` | 분기 복잡도 | git branch 전환 횟수, merge/rebase 포함 여부 |

### 복잡도 등급

```python
@dataclass
class SessionComplexity:
    session_id: str
    grade: Literal["simple", "moderate", "complex", "extreme"]
    score: float  # 0.0 ~ 1.0 연속값
    dimensions: dict[str, float]

def compute_complexity(session: AnalyzedSession) -> SessionComplexity:
    """세션의 복잡도를 다차원 가중 합산으로 산출한다."""
    weights = {
        "turn_depth": 0.25,
        "tool_diversity": 0.20,
        "entity_count": 0.20,
        "file_scope": 0.20,
        "branch_complexity": 0.15,
    }
    # 각 차원을 0-1로 정규화 후 가중 합산
    score = sum(normalize(dim) * w for dim, w in weights.items())
    grade = (
        "simple" if score < 0.25
        else "moderate" if score < 0.50
        else "complex" if score < 0.75
        else "extreme"
    )
    return SessionComplexity(session_id=session.id, grade=grade, score=score, dimensions=dims)
```

### 점수 정규화 적용

복잡도가 높은 세션에서의 부정 신호는 가중치를 낮추고, 단순 세션에서의 부정 신호는 가중치를 높인다. 이를 통해 작업 난이도에 따른 공정한 점수 산출이 가능하다.

```python
def adjust_signal_weight(base_weight: float, complexity: SessionComplexity) -> float:
    """복잡도에 따라 부정 신호 가중치를 조정한다."""
    # 복잡한 세션일수록 부정 신호에 관대 (0.7x ~ 1.0x)
    complexity_factor = 1.0 - (complexity.score * 0.3)
    return base_weight * complexity_factor
```

---

## 8. 저장 구조

### 8.1 이벤트 저장소

```
~/.claude/hyperagent/
├── events/
│   ├── 2026-04-13.jsonl          # 일별 이벤트 로그 (append-only)
│   └── 2026-04-12.jsonl
├── scores/
│   ├── agents/
│   │   ├── test-engineer.json    # 에이전트별 점수 히스토리
│   │   └── code-quality-reviewer.json
│   ├── skills/
│   │   ├── commit.json
│   │   └── build.json
│   └── orchestration.json
├── baselines/
│   └── baselines.json            # 엔티티별 베이스라인
├── triggers/
│   └── trigger-log.jsonl         # 트리거 발동 이력 (디바운싱 참조용)
└── config.json                   # 파이프라인 설정 (임계값, 감쇠율 등)
```

### 8.2 config.json 기본값

```jsonc
{
  "pipeline": {
    "mode": "daily-batch",                    // 확정: 일일 배치 cron (ADR-0004)
    "llm_tier3_enabled": true,                // 확정: Codex 토큰 충분, 비용 제약 완화 (ADR-0001)
    "llm_tier3_batch_threshold": 20,
    "llm_tier3_model": "codex"                // Codex 활용
  },
  "scoring": {
    "decay_half_life_days": 7,
    "baseline_min_sessions": 5,
    "trend_threshold": 0.15
  },
  "triggers": {
    "degrade_threshold": 0.15,
    "accumulate_sessions": 20,
    "repeat_pattern_min": 3,
    "new_pattern_min": 5,
    "sustained_low_threshold": 0.5,
    "sustained_low_days": 7
  },
  "retention": {
    "events_max_days": 90,                    // [ASSUMPTION][candidate] 90일 보관
    "scores_max_days": 365
  }
}
```

---

## 9. Assumptions 요약

| ID | 가정 | 기본값 | 검증 방법 |
|----|------|--------|----------|
| A1 | regex Tier 1이 보정/칭찬의 대부분을 분류 가능 | 80%+ 분류율 기대 | 초기 50세션으로 recall/precision 측정 |
| A2 | Codex Tier 3 배치 분류의 비용이 허용 범위 (Codex 토큰 충분) | 비용 제약 완화 | Codex 토큰 사용량 모니터링 |
| A3 | 감쇠 반감기 7일이 적절 | half_life=7 | 사용자 체감과 비교하여 조정 |
| A4 | 베이스라인 최소 5세션이면 통계적으로 유의미 | min_sessions=5 | 분산(variance) 확인 |
| A5 | 반복 패턴 3회면 노이즈가 아닌 진짜 패턴 | min_occurrences=3 | false positive 비율 모니터링 |
| A6 | daily-batch cron이 기본 실행 모드로 확정 (ADR-0004) | mode=daily-batch, trigger=daily-cron | 사용자 피드백 반영 지연 체감 확인 |
| A7 | 이벤트 90일 보관이면 충분 | 90일 | 저장 용량 모니터링 |
| A8 | Tier 3 Codex 배치 임계값 20건이 적절 | batch_threshold=20 | Codex 토큰 소비 대 분류 개선 효과 측정 |

---

## 10. Open Questions

1. **[QUESTION][nice-to-have]** 한국어 보정 패턴의 정규식 커버리지가 실제 사용 패턴의 몇 %를 커버하는지. 기본값: 초기 50세션 대상 calibration 후 패턴 보강.
2. **[QUESTION][nice-to-have]** 프로젝트 간 점수 격리 vs 통합. 프로젝트 A에서의 에이전트 점수가 프로젝트 B에도 영향을 줘야 하는지. 기본값: 프로젝트별 독립 점수, 향후 cross-project 학습 전이로 확장.
3. **Tier 3 LLM 분류 모델 (확정)**: Codex를 활용한다. Codex 토큰이 충분하여 비용 제약이 완화되었으므로, 분류 전용 저비용 모델 대신 Codex의 높은 정확도를 직접 활용한다. 배치 분류 시 Codex에 세션 컨텍스트와 함께 전달하여 분류 품질을 극대화한다. (ADR-0001 참조)

---

## 11. Quality Gate

| 항목 | 상태 | 비고 |
|------|------|------|
| 신호 택소노미가 부정/긍정/중립을 모두 커버하는가 | PASS | 6 부정 + 5 긍정 + 5 중립 신호 정의 |
| 한국어 패턴이 구체적 regex로 제공되는가 | PASS | 보정, 거부, 칭찬, 롤백 4개 패턴 세트 |
| 엔티티 귀속 로직이 명확한가 | PASS | Skill/Agent 감지 + 구간 귀속 규칙 |
| 이벤트 스키마가 JSON Schema로 정의되었는가 | PASS | 기본 엔벨로프 + 6개 상세 스키마 |
| 트리거 조건이 정량적 임계값을 포함하는가 | PASS | 6개 트리거, 각각 수치 기준 명시 |
| 집계 전략(감쇠, 베이스라인, 추세)이 수식으로 정의되었는가 | PASS | 지수 감쇠, 중앙값 베이스라인, 변화율 추세 |
| 저장 구조가 명시되었는가 | PASS | 디렉토리 구조 + 보관 기간 |
| ASSUMPTION 태그가 candidate 레벨로 표기되었는가 | PASS | 8개 assumption 명시 |
| PRD의 Success Criteria와 정합하는가 | PASS | 보정 빈도 추적(NEG-CORRECT), 프로파일 최신성(TRIG-ACCUMULATE) 직접 연결 |

---

## References

- PRD: `tasks/hyperagent-integration/design/PRD.md` --- Success Criteria 정의, 시나리오 정의
- Spike-3 결과: `_state.yaml` --- 세션 JSONL 구조 검증
- 세션 데이터: `~/.claude/projects/<project>/<sessionId>.jsonl`
- 통계 캐시: `~/.claude/stats-cache.json`
- 에이전트 목록: `agents/` (13개), `skills/` (14개)
