---
name: deep-think
description: >
   Structured deep reasoning skill using parallel sub-agents, mimicking Google's Deep Think mode.
   Spawns multiple independent Claude instances to explore different solution paths simultaneously,
   then uses a fresh verifier agent to critique and synthesize the best answer.
   Use when the user prefixes a question with "deep think", "딥씽크", "깊게 생각해", or when explicitly
   requesting thorough/exhaustive analysis. Also trigger for complex architecture, debugging,
   algorithmic, or multi-domain questions where highest quality is needed.
   NOT for simple factual lookups or casual conversation.
---

# Deep Think (Sub-Agent Architecture)

Multi-phase reasoning using **independent parallel sub-agents**. Each reasoning path is explored by a separate Claude instance with its own context, eliminating anchoring bias. A dedicated verifier agent then critiques and synthesizes all paths.

## Architecture

```
Orchestrator (you)
├── Phase 1-2: Analysis & Decomposition (you write these)
├── Phase 3: Parallel Paths (N independent sub-agents, each with a different persona)
│   ├── 🤖 Agent 1: First Principles Thinker
│   ├── 🤖 Agent 2: Pragmatic Engineer
│   ├── 🤖 Agent 3: Adversarial Reviewer
│   ├── 🤖 Agent 4: Creative Innovator
│   └── 🤖 Agent 5: Performance Optimizer
├── Phase 4-5: Verification & Synthesis (1 independent verifier agent)
└── Phase 6: Final Answer (1 independent agent)
```

Total agents: N path agents + 1 verifier + 1 final answer = N+2 Claude calls.

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/deep_think.py` | Session lifecycle (init, phase tracking, finalize) |
| `scripts/parallel_paths.py` | Spawn N parallel path-exploration agents |
| `scripts/verify_synthesize.py` | Independent verifier → synthesizer → final answer |
| `scripts/evaluate_paths.py` | Generate evaluation matrix (optional, for manual review) |
| `scripts/run_session.py` | All-in-one runner for standalone use |

## Workflow

For phase templates, see `references/phase-templates.md`.
For problem-type reasoning strategies, see `references/reasoning-patterns.md`.

### Phase 1-2: Analysis & Decomposition (Orchestrator)

These phases run in the orchestrator's context (you). Write the output to files so sub-agents can read them.

1. Initialize the session:
   ```bash
   python scripts/deep_think.py init "<question>" -c <complexity> -w .deep-think
   ```

2. Determine complexity and path count:
   - **low** → 2 paths | **medium** → 3 paths | **high** → 4 paths | **extreme** → 5 paths

3. Write `01-analysis/analysis.md`:
   - Precise problem restatement
   - Problem type (coding / debugging / math / analysis / creative)
   - Key constraints and implicit assumptions
   - What a perfect answer looks like

4. Write `02-decomposition/decomposition.md`:
   - Sub-problems and dependencies
   - Knowledge gaps
   - Attack plan

Track phases:
```bash
python scripts/deep_think.py start-phase 01-analysis -w .deep-think
# ... write analysis.md ...
python scripts/deep_think.py end-phase 01-analysis -w .deep-think
python scripts/deep_think.py start-phase 02-decomposition -w .deep-think
# ... write decomposition.md ...
python scripts/deep_think.py end-phase 02-decomposition -w .deep-think
```

### Phase 3: Parallel Path Exploration (Sub-Agents)

Launch N independent agents simultaneously. Each gets a different persona.

```bash
python scripts/deep_think.py start-phase 03-paths -w .deep-think
python scripts/parallel_paths.py -w .deep-think -n <num_paths> [-m <model>] [-c <extra_context_file>]
python scripts/deep_think.py end-phase 03-paths -w .deep-think
```

Options:
- `-n` Number of paths (2-5, default 3)
- `-m` Model override for sub-agents (e.g., `claude-sonnet-4-20250514` for cost savings)
- `-c` Extra context file to include in prompts

The 5 default personas are: First Principles, Pragmatic, Adversarial, Innovator, Optimizer. Each produces `03-paths/path-{N}.md`.

### Phase 4-6: Verify, Synthesize, Final Answer (Sub-Agents)

A fresh verifier agent reads ALL paths with no prior context, evaluates, critiques, and synthesizes. Then a final-answer agent produces the polished output.

```bash
python scripts/deep_think.py start-phase 04-verification -w .deep-think
python scripts/verify_synthesize.py -w .deep-think [-m <model>]
python scripts/deep_think.py end-phase 04-verification -w .deep-think
```

### Finalize & Deliver

```bash
python scripts/deep_think.py finalize -w .deep-think
```

Then present to the user:
1. Read and show the content of `06-answer/answer.md`
2. Mention the full thinking trace is available in `.deep-think/`
3. Offer to show `REPORT.md` for the session timeline

### Quick Mode (run_session.py)

For fully autonomous execution (orchestrator writes no analysis — sub-agents figure it out):

```bash
python scripts/run_session.py "Your question" -c high -n 4
```

This is simpler but produces slightly lower quality since sub-agents don't get orchestrator analysis.

## Important Rules

1. **Always write Phase 1-2 before launching sub-agents.** The quality of analysis and decomposition directly determines the quality of sub-agent output.
2. **Sub-agents are independent.** They share NO context with each other. Any shared info must be passed via the workspace files.
3. **The verifier is fresh.** It has never seen the paths before — this is a feature, not a bug. Fresh eyes catch what the path agents missed.
4. **Scale to complexity.** 2 agents for simple tasks, 5 for extreme. Don't over-invest.
5. **Read the final answer yourself** before presenting to the user. Sanity-check it.