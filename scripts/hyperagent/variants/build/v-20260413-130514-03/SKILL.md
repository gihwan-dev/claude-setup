---
name: build
description: >
  Execute all phases from BRIEF.md sequentially by orchestrating Codex. Invoke
  when the user writes "build" or "$build". Claude designs prompts and
  orchestrates; Codex implements, reviews, and fixes code. No approval gates —
  all phases run automatically. Claude never writes code directly.
allowed-tools: Bash, Read, Grep, Glob, Edit, Write, Agent
---

# Build

Orchestrate Codex execution of phases from `tasks/<slug>/BRIEF.md`.

Claude is the **orchestrator**: reads files, crafts prompts, communicates with
the user, reads Codex output, and manages state. Codex is the **executor**:
writes code, runs tests, produces phase reports.

## Hard Rules

1. **Claude never writes code directly.** All code changes go through Codex.
2. If no `BRIEF.md` exists or Phases is empty, stop and suggest `$plan`.
3. **All phases run sequentially without pause.** Do not ask for approval
   between phases. Execute every remaining phase in one invocation.
4. Codex must write a `PHASE_REPORT_<NN>.md` after each phase (enforced in
   the prompt template).
5. Claude must read the previous phase report before crafting the next prompt.
6. If Codex execution fails, report the failure. Do not implement as Claude.
7. Session resumption: read `BRIEF.md` Status + Log + all existing
   `PHASE_REPORT_*.md` files, then continue from where it left off.

## Codex Plugin Skills (세션당 1회 로드)

Build 시작 시 Skill 도구로 아래 플러그인 스킬을 로드한다:

1. `codex:gpt-5-4-prompting` — 프롬프트 구조, XML 블록 규칙, 레시피
2. `codex:codex-cli-runtime` — Codex 호출 명령어, 플래그, 실행 규칙

로드된 스킬이 제공하는 호출 계약과 프롬프트 규칙을 따른다.

## Build Loop (Per Phase)

```
0. Bootstrap    — Codex plugin skills 로드 (세션당 1회)
1. Read         — BRIEF.md + previous PHASE_REPORT_*.md
2. Craft        — Draft Codex prompt
3. Log          — 실행할 프롬프트 요약을 한 줄로 출력
4. Execute      — Invoke Codex (codex:codex-cli-runtime 계약에 따라)
5. Review       — Read Codex output + PHASE_REPORT
5.5 Browser QA  — UI 파일 변경 시 서브에이전트 QA (conditional)
6. Update       — Update BRIEF.md Status + Log
7. Next         — 남은 페이즈가 있으면 Step 1로 자동 복귀
```

### Step 1: Read

- Read `tasks/<slug>/BRIEF.md`, identify the current phase from `Status`.
- Read all existing `tasks/<slug>/PHASE_REPORT_*.md` files.
- Read reference documents listed in `BRIEF.md` References section.

### Step 2: Craft

`codex:gpt-5-4-prompting`의 XML 블록 규칙과
`${SKILL_DIR}/references/codex-prompt-template.md`의 변수 구조를 결합하여
Codex 프롬프트를 작성한다.

Fill variables:
- `PHASE_PURPOSE` ← BRIEF Phase "Purpose"
- `REFERENCE_CONTEXT` ← compressed previous phase reports + relevant doc
  excerpts + BRIEF decisions/context (target: under 500 tokens accumulated)
- `PHASE_GOAL` ← BRIEF Phase "Done when" expanded into actionable goal
- `DONE_CRITERIA` ← BRIEF Phase "Done when" + "Verification" merged
- `PHASE_REPORT_PATH` ← `tasks/<slug>/PHASE_REPORT_<NN>.md`
- `VERIFICATION_COMMANDS` ← BRIEF Phase "Verification"

### Step 3: Log

승인 없이 바로 실행한다. 실행 전 한 줄 요약만 출력:

```
▶ Phase N: <Name> — <Purpose 요약>
```

### Step 4: Execute

`codex:codex-cli-runtime`에서 로드된 호출 계약에 따라 Codex를 실행한다.
`--write` 플래그로 쓰기 가능 모드로 실행.

### Step 5: Review

- Read Codex stdout for immediate results.
- Read `tasks/<slug>/PHASE_REPORT_<NN>.md` that Codex was instructed to write.
- If the phase report is missing, extract key facts from Codex stdout as
  fallback and warn the user.
- Present a summary to the user: what was done, verification result, any
  open issues.

### Step 5.5: Browser QA (conditional)

PHASE_REPORT의 `Files Changed` 테이블에서 UI 파일 변경 여부를 확인한다.
패턴: `\.(tsx|jsx|vue|svelte|html|css|scss|sass|less|styled)\b` (create-mr과 동일)

UI 파일이 없으면 이 스텝을 건너뛴다.

UI 파일이 있으면:
1. `package.json` scripts에서 dev server 명령어 확인 (`dev` > `start` > `serve` 우선순위)
2. `skills/_shared/references/browser-qa-prompt-template.md`의 변수를 치환하여 프롬프트 작성
3. `Agent(subagent_type="general-purpose")`로 서브에이전트 소환
   - general-purpose 타입이어야 Claude in Chrome MCP 도구(`mcp__claude-in-chrome__*`) 접근 가능
4. 서브에이전트가 `tasks/<slug>/QA_REPORT_<NN>.md`에 QA 리포트 작성
5. QA 리포트를 읽고 최종 요약에 포함

QA 결과는 **정보 제공용**이다. 이슈가 발견되어도 phase 완료를 차단하지 않고
다음 페이즈로 자동 진행한다.

### Step 6: Update

- Update `BRIEF.md` Status: move completed phase to `done`, advance `current`.
- Append to `BRIEF.md` Log: date + what was completed + any issues.

### Step 7: Next

남은 페이즈가 있으면 Step 1로 자동 복귀하여 다음 페이즈를 실행한다.
모든 페이즈 완료 시 최종 요약을 사용자에게 출력한다:
- 완료된 페이즈 목록
- 각 페이즈 검증 결과
- 미해결 이슈 (있는 경우)

## Reference Document Integration

- Read all documents listed in `BRIEF.md` References before each prompt.
- For Socratic design docs: extract "Chosen Direction", "Decisions", "Risks",
  and "Constraints" sections.
- For previous phase reports: compress to key facts. Most recent 2-3 in detail;
  older ones as 1-2 lines each. Target: under 500 tokens accumulated.
- Users can add arbitrary reference documents to `BRIEF.md` References.

## Phase Report Format

See `skills/build/references/phase-report-format.md` for the full spec.
Codex writes `tasks/<slug>/PHASE_REPORT_<NN>.md` after each phase.

## Error Handling

- **Codex timeout**: Report timeout. Suggest retrying with adjusted prompt or
  splitting the phase.
- **Codex failure**: Report the error. Do not fall back to Claude implementation.
- **Phase report missing**: Warn user. Extract what's available from stdout.
- **Verification failure reported by Codex**: Present the failure. Ask user
  whether to retry (re-invoke Codex with fix instructions) or mark blocked.
- **Browser QA 실패**: dev server 미기동, Chrome 미연결 등으로 QA를 수행할 수 없으면
  경고만 표시하고 다음 스텝으로 진행한다. phase 완료를 차단하지 않는다.

## Session Resumption

Read `BRIEF.md` Status + Log + all `PHASE_REPORT_*.md` → identify where to
resume → continue from that phase.


<!-- HyperAgent variant patch: v-20260413-130514-03 -->
<!-- Created at: 2026-04-13T13:05:14Z -->
<!-- Entity: skill:build -->
<!-- Reason: acceptance_rate -->
<!-- Score: 0.2157 -->
<!-- Priority: high -->
<!-- Evidence sessions: e1309bb6-e031-43d4-9006-138745680682 -->
<!-- Improvement suggestion: -->
<!-- 수용률이 낮습니다. 입력 조건, 성공 기준, 산출물 형식을 더 명확히 고정하는 개선이 우선입니다. -->
<!-- End HyperAgent variant patch -->
