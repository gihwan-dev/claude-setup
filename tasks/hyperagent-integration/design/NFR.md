<!-- Status: drafted -->
<!-- Confidence: medium -->
<!-- doc_type: nfr-checklist -->

# Non-Functional Requirements: HyperAgent 자기개선 루프

> 개인 개발자 CLI 도구 맥락에 맞게 조정됨. SLO/SLA, 분산 트레이싱, 컴플라이언스 등
> 프로덕션 서비스 전용 항목은 N/A 처리.

---

## 1. 비용 예산 (Cost Budget)

자기개선 루프의 핵심 제약. LLM API 호출이 가장 비싼 자원이며, 변종(variant) 폭발 없이
점진적 개선을 달성해야 한다.

### 1.1 단위 비용 모델

| 단계 | 예상 토큰 | 예상 비용 (Opus) | 비고 |
|------|-----------|-----------------|------|
| 세션 파싱 + 스코어링 | ~50K input | ~$0.75 | 최근 N개 세션 JSONL 파싱 |
| 변종 생성 (프롬프트 리라이트) | ~20K input + ~5K output | ~$0.68 | 기존 프롬프트 + 피드백 → 새 변종 |
| 변종 평가 (A/B 시뮬레이션) | ~30K input + ~10K output | ~$1.20 | 테스트 케이스 대상 변종 실행 |
| **사이클 합계** | | **~$2.63** | |

[ASSUMPTION][candidate] 단일 개선 사이클당 약 $2-3 예상. Opus 대신 Sonnet 사용 시 ~$0.30으로 10배 절감 가능. 평가 단계에서 Sonnet 활용이 비용 효율적.

### 1.2 비용 가드레일

- **사이클당 상한**: [ASSUMPTION][candidate] $5/사이클 하드캡. 이 금액 초과 시 사이클 즉시 중단, 부분 결과 보존.
- **월간 예산**: [ASSUMPTION][candidate] $30/월. 월 예산 소진 시 자동 개선 루프 비활성화, 수동 트리거만 허용.
- **비용 추적**: 각 사이클의 토큰 사용량과 비용을 `meta/cost-log.jsonl`에 기록. 누적 비용이 월간 예산의 80%에 도달하면 경고.
- **모델 폴백**: [ASSUMPTION][candidate] 비용 최적화를 위해 파싱/스코어링은 Haiku, 생성은 Sonnet, 최종 평가만 Opus 사용하는 계층 모델 적용 가능.

### 1.3 HyperAgents 원논문 대비 제약

원논문은 수백 회 반복 + 복수 API 키로 실행. 개인 도구에서는:

- 반복 횟수: [ASSUMPTION][candidate] 주 1-2회 자동 사이클, 필요시 수동 트리거
- 동시 변종 평가: 1개 (순차 처리, 병렬 API 호출 없음)
- API 키: 단일 키, rate limit 고려

---

## 2. 성능 (Performance Targets)

### 2.1 개선 사이클 소요 시간

- **전체 사이클**: [ASSUMPTION][candidate] 5분 이내 (파싱 → 스코어링 → 생성 → 평가 → 아카이브)
- **세션 파싱**: 30초 이내. 최근 7일 세션만 대상.
- **변종 생성**: 60초 이내. 단일 LLM 호출.
- **변종 평가**: 120초 이내. 테스트 케이스 순차 실행.
- **아카이브 기록**: 5초 이내. 로컬 파일 I/O만.

### 2.2 일상 워크플로 영향

- **세션 시작 지연**: 0ms. 자기개선은 비동기 백그라운드 프로세스이며, 사용자 세션에 지연을 추가하지 않음.
- **Stop hook 오버헤드**: [ASSUMPTION][candidate] 500ms 이내. 세션 종료 시 성능 데이터 수집 (메트릭 스냅샷만, 분석은 별도).
- **Latency/Throughput**: N/A. 이 시스템은 사용자 대면 요청-응답 서비스가 아니므로 p50/p95/p99 지표 불필요.

---

## 3. 변종 관리 (Variant Limits)

진화 루프의 핵심 위험은 변종 폭발(variant explosion). 보수적 제한 필수.

### 3.1 아카이브 크기 제한

- **활성 변종 수**: [ASSUMPTION][candidate] 에이전트/스킬당 최대 5개. 현재 best + 최근 4개 후보.
- **전체 아카이브**: [ASSUMPTION][candidate] 최대 50개 변종 (전체 에이전트/스킬 합산). 초과 시 최저 스코어부터 pruning.
- **Pruning 전략**: 세대(generation) 기반 + 성능 기반 복합.
  - 3세대 이상 지난 변종 중 상위 1개만 유지 (계보 추적용)
  - 현세대에서 best 대비 20% 이상 성능 저하 변종 즉시 제거
  - [ASSUMPTION][candidate] 월 1회 전체 아카이브 GC (garbage collection) 실행

### 3.2 계보 추적 (Lineage)

- 각 변종은 `parent_id`, `generation`, `mutation_type` 메타데이터 보유
- 계보 그래프는 깊이 [ASSUMPTION][candidate] 최대 10세대로 제한. 이후 새 baseline으로 리셋.

---

## 4. 확장성 (Scalability)

- **현재 규모**: 에이전트 13개, 스킬 ~30개. 자기개선 대상은 이 중 활발히 사용되는 것만.
- **6개월 후**: N/A. 1인 개발자 도구이므로 사용자 수 증가에 따른 확장 불필요.
- **확장 축**: [ASSUMPTION][candidate] 에이전트/스킬 수가 100개까지 증가해도 개선 사이클 시간이 선형 이하로 증가해야 함 (대상 선정 단계에서 상위 N개만 필터).
- **Scaling model**: N/A. 단일 머신, 수직 확장도 불필요.

---

## 5. 가용성 (Availability)

- **SLO**: N/A. 개인 CLI 도구이며 24/7 가용성이 필요하지 않음.
- **Degradation mode**: 자기개선 루프 실패 시 기존 에이전트/스킬은 영향 없이 그대로 동작. 개선 레이어는 순수 부가 기능(additive layer).

---

## 6. 신뢰성 (Reliability)

### 6.1 실패 복구

자기개선 사이클은 여러 단계로 구성되며, 중간 실패 시 안전한 복구가 필수.

| 실패 지점 | 영향 | 복구 전략 |
|-----------|------|-----------|
| 세션 파싱 실패 | 스코어 없음 | 재시도 1회 → 실패 시 사이클 건너뜀, 다음 스케줄에서 재시도 |
| LLM API 오류 (변종 생성) | 변종 없음 | 재시도 2회 (exponential backoff) → 실패 시 사이클 중단, 기존 best 유지 |
| 변종 평가 실패 | 비교 불가 | 평가 결과 폐기, 생성된 변종은 `pending` 상태로 아카이브에 보존. 다음 사이클에서 재평가 |
| 아카이브 쓰기 실패 | 결과 유실 | 임시 파일에 먼저 기록 후 atomic rename. 실패 시 `meta/recovery/`에 덤프 |
| **사이클 중 프로세스 kill** | 부분 상태 | 각 단계 완료 시 체크포인트 기록. 재시작 시 마지막 체크포인트부터 resume |

### 6.2 안전 경계 (Safety Guardrails)

- **롤백**: 변종 적용 후 다음 3개 세션에서 성능이 이전 best 대비 [ASSUMPTION][candidate] 30% 이상 하락하면 자동 롤백.
- **변종 적용 방식**: 기존 프롬프트 원본은 항상 보존 (`meta/archive/`). 변종은 symlink 교체로 적용, 원복은 symlink 재지정.
- **변이 범위 제한**: [ASSUMPTION][candidate] 한 사이클에서 변경 가능한 에이전트/스킬은 최대 1개. 동시 다발 변경으로 인한 상호작용 효과(interaction effect) 방지.
- **Timeout**: [ASSUMPTION][candidate] 전체 사이클 10분 타임아웃. 초과 시 진행 중인 LLM 호출 취소, 부분 결과 보존.

---

## 7. 관측 가능성 (Observability)

### 7.1 개선 이력 로그

- **형식**: `meta/improvement-log.jsonl` — 사이클별 한 줄.
- **필드**: `cycle_id`, `timestamp`, `target` (에이전트/스킬 이름), `parent_variant_id`, `new_variant_id`, `score_before`, `score_after`, `cost_usd`, `duration_sec`, `status` (success/failed/rolled_back)
- **보존 기간**: [ASSUMPTION][candidate] 영구 보존 (JSONL append-only, 연간 ~50KB 예상)

### 7.2 변종 계보 추적

- 각 변종 디렉토리에 `variant-meta.yaml` 포함: 부모, 세대, 변이 유형, 생성일, 스코어 이력
- `meta/lineage.json`에 전체 변종 트리 캐시 (시각화용)

### 7.3 Before/After 비교

- 변종 적용 전후 diff를 `meta/diffs/` 하위에 보존
- 각 diff에 적용 사유(개선 목표)와 실제 결과(스코어 변화) 주석 포함

### 7.4 대시보드/알림

- **Metrics 대시보드**: N/A. 프로덕션 모니터링 시스템 불필요. CLI에서 `hyperagent status` 명령으로 최근 사이클 요약 조회.
- **Alerts**: N/A. 온콜 엔지니어 없음. 월간 예산 80% 도달 시 다음 세션 시작 시 CLI 경고 메시지 출력.
- **Distributed Tracing**: N/A. 단일 프로세스, 분산 시스템 아님.

---

## 8. 저장소 (Storage)

### 8.1 세션 JSONL 증가율

- **현재**: `~/.claude/` 하위 세션 데이터 ~4.1MB (history.jsonl 기준), 2175개 세션
- **증가율**: [ASSUMPTION][candidate] 월 ~500KB. 활발한 사용 기준.
- **자기개선 시스템이 추가하는 데이터**: 세션 JSONL 자체는 건드리지 않음 (읽기 전용). 별도 `meta/` 디렉토리에 파생 데이터 기록.

### 8.2 아카이브 크기

- **변종 아카이브**: [ASSUMPTION][candidate] 변종당 ~10KB (에이전트 instructions.md 또는 스킬 SKILL.md + 메타데이터). 50개 상한 기준 ~500KB.
- **개선 로그**: 연간 ~50KB (사이클당 ~1KB, 주 1회 기준)
- **Diff 아카이브**: [ASSUMPTION][candidate] 연간 ~200KB
- **전체 meta/ 디렉토리**: [ASSUMPTION][candidate] 1MB 이내 유지 목표

### 8.3 Git 저장소 비대화 방지

- `meta/archive/` 내 pruning된 변종은 git에서도 제거 (`git rm` + 커밋)
- [ASSUMPTION][candidate] `meta/sessions-cache/` (파싱된 세션 캐시)는 `.gitignore`에 추가. 원본 세션 데이터에서 언제든 재생성 가능.
- 대용량 JSONL 캐시는 git LFS 없이 `.gitignore`로 관리. SSOT repo는 프롬프트/설정만 추적.
- **연간 git 증가량**: [ASSUMPTION][candidate] 5MB 이내 (변종 교체 diff + 로그 append)

---

## 9. 컴플라이언스 (Compliance)

N/A. 개인 도구이며 GDPR, SOC2, HIPAA 등 규제 대상 아님. PII 미취급 (`handles_pii: false`).

---

## 10. 용량 계획 (Capacity Planning)

N/A. 단일 개발자 로컬 머신에서 실행. 클라우드 인프라, 오토스케일링, 용량 프로비저닝 불필요.
유일한 외부 자원 제약은 LLM API rate limit이며, 이는 비용 예산 섹션의 보수적 호출 빈도로 자연스럽게 관리됨.

---

## 실패 시나리오 분석 (Failure Modes)

디자인 품질 게이트(rubric #6: Failure modes identified)를 위한 구체적 실패 시나리오.

### F1: 변종 퇴화 (Variant Regression)

- **시나리오**: 새 변종이 평가에서는 높은 점수를 받았으나, 실제 사용에서 예상치 못한 엣지 케이스로 성능 하락.
- **영향**: 해당 에이전트/스킬의 품질 저하.
- **완화**: 3-세션 관찰 기간 + 자동 롤백 (6.2절). 원본은 항상 아카이브에 보존.
- **탐지**: 롤백 트리거 = 성능 30% 이상 하락 (improvement-log.jsonl에서 추적).

### F2: 비용 폭주 (Cost Runaway)

- **시나리오**: 평가 단계에서 예상보다 큰 컨텍스트가 전달되어 단일 사이클 비용이 예산 초과.
- **영향**: 월간 API 예산 조기 소진.
- **완화**: 사이클당 $5 하드캡 (1.2절). 토큰 카운트 사전 추정 후 예산 초과 예상 시 사이클 스킵.
- **탐지**: 각 LLM 호출 전 토큰 추정, 누적 비용 실시간 추적.

### F3: 아카이브 오염 (Archive Corruption)

- **시나리오**: 변종 쓰기 중 프로세스 중단으로 불완전한 변종 파일 생성.
- **영향**: 다음 사이클에서 파싱 에러, 아카이브 일관성 깨짐.
- **완화**: atomic write (임시 파일 → rename). 체크포인트 기반 resume. 아카이브 무결성 검사를 사이클 시작 시 실행.
- **탐지**: 사이클 시작 시 아카이브 스키마 검증. 불량 변종 발견 시 자동 제거 + 경고 로그.

---

## Assumptions

이 문서의 모든 `[ASSUMPTION][candidate]` 태그 요약:

1. 단일 개선 사이클당 약 $2-3 (모델 혼합 시 절감 가능)
2. 사이클당 $5 하드캡
3. 월간 $30 예산
4. 파싱/스코어링은 Haiku, 생성은 Sonnet, 평가는 Opus 계층 모델
5. 전체 사이클 5분 이내
6. Stop hook 오버헤드 500ms 이내
7. 에이전트/스킬당 활성 변종 최대 5개
8. 전체 아카이브 최대 50개 변종
9. 월 1회 아카이브 GC
10. 계보 최대 10세대
11. 롤백 임계값: 성능 30% 하락
12. 한 사이클에 변경 대상 최대 1개
13. 전체 사이클 10분 타임아웃
14. 개선 로그 영구 보존
15. 세션 데이터 월 ~500KB 증가
16. 변종당 ~10KB
17. meta/ 디렉토리 1MB 이내
18. sessions-cache는 .gitignore 처리
19. 연간 git 증가량 5MB 이내
20. 에이전트/스킬 100개까지 선형 이하 확장
21. 주 1-2회 자동 사이클

---

## Open Questions

(refine 단계에서 이동될 항목 공간)

---

## References

- PRD: `../PRD.md`
- ADRs: `../adr/`
- Architecture: `../ARCHITECTURE.md`
- API Contract: `../API-CONTRACT.md`
- Analytics: `../ANALYTICS.md`
- HyperAgents 원논문: https://arxiv.org/abs/2603.19461
- Claude API Pricing: https://www.anthropic.com/pricing
