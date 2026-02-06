---
name: deep-think
description: >
  Structured deep reasoning skill using Claude Code's native Agent Teams.
  Spawns multiple independent Claude instances with different personas to explore
  solution paths in parallel, then synthesizes the best answer.
  Use when the user prefixes a question with "deep think", "딥씽크", "깊게 생각해",
  or requests thorough/exhaustive analysis. Also trigger for complex architecture,
  debugging, algorithmic, or multi-domain questions where highest quality is needed.
  NOT for simple factual lookups or casual conversation.
  Requires: CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
---

# Deep Think (Agent Teams)

Multi-phase reasoning using Claude Code's **native Agent Teams**. Each reasoning path is explored by a separate teammate with its own context window and persona. Teammates can challenge each other's findings. A verifier teammate then synthesizes the best answer.

## Prerequisites

Enable Agent Teams (experimental):
```bash
# In shell
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

# Or in ~/.claude/settings.json
{ "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" } }
```

## Architecture

```
You (Team Lead)
├── Phase 1-2: Analysis & Decomposition (you)
├── Phase 3: Parallel Paths (Agent Team)
│   ├── 🧠 first-principles — derives from fundamentals
│   ├── 🔧 pragmatist — focuses on real-world practicality
│   ├── 😈 adversarial — finds failure modes and edge cases
│   ├── 💡 innovator — proposes unconventional solutions
│   └── ⚡ optimizer — maximizes performance
├── Phase 4: Verification (verifier teammate reads all paths fresh)
└── Phase 5-6: Synthesis & Final Answer
```

## Workflow

### Phase 1-2: Analysis & Decomposition (You)

Before spawning the team, write foundational analysis that all teammates will read.

1. Create workspace and analysis:
   ```
   mkdir -p .deep-think/01-analysis .deep-think/02-decomposition
   ```

2. Write `.deep-think/01-analysis/analysis.md`:
    - Precise problem restatement
    - Problem type: coding / debugging / math / analysis / creative
    - Key constraints and implicit assumptions
    - What a perfect answer looks like
    - Complexity: low (2 paths) / medium (3) / high (4) / extreme (5)

3. Write `.deep-think/02-decomposition/decomposition.md`:
    - Sub-problems and dependencies
    - Knowledge gaps to investigate
    - Attack plan

### Phase 3: Spawn Agent Team

Create the team with natural language. Adjust teammate count based on complexity.

**Standard (high complexity, 4 teammates + verifier):**

```
Create an agent team called "deep-think" to analyze this problem from multiple angles:

The problem: [paste from analysis.md]

Spawn these teammates:
1. "first-principles" - Derive everything from fundamentals. Question all assumptions.
   Challenge best practices. Focus on correctness and logical soundness.
2. "pragmatist" - Focus on what works in production. Consider maintenance,
   team velocity, and real-world constraints. Prefer battle-tested over novel.
3. "adversarial" - Find worst-case scenarios, edge cases, failure modes.
   Assume Murphy's Law. Propose the most defensive approach.
4. "optimizer" - Think in complexity, cache behavior, resource utilization.
   Quantify performance claims.

Each teammate should:
- Read .deep-think/01-analysis/analysis.md and .deep-think/02-decomposition/decomposition.md
- Write their solution to .deep-think/03-paths/path-{their-name}.md
- Include: approach summary, detailed reasoning, concrete solution, weaknesses, confidence level
- When done, send a summary to team-lead inbox

After all paths are written, spawn a "verifier" teammate who:
- Reads ALL path files with fresh eyes
- Evaluates each for correctness, completeness, practicality
- Finds contradictions between paths
- Identifies blind spots ALL paths missed
- Plays devil's advocate against the best approach
- Writes synthesis to .deep-think/05-synthesis/synthesis.md
- Writes final answer to .deep-think/06-answer/answer.md
```

**Lightweight (medium complexity, 3 teammates):**

```
Create an agent team "deep-think" with 3 teammates:
1. "analyst" - Thorough, methodical approach
2. "critic" - Find problems and edge cases
3. "synthesizer" - Combine best elements into final answer

[same task structure as above]
```

### Phase 4-6: Monitor and Collect

1. **Switch between teammates** with `Shift+Up/Down` to monitor progress
2. **Check your inbox** for teammate summaries:
   ```bash
   cat ~/.claude/teams/deep-think/inboxes/team-lead.json | jq '.'
   ```
3. After verifier finishes, **read the final answer**:
   ```bash
   cat .deep-think/06-answer/answer.md
   ```

### Shutdown

When complete:
```
Shutdown the deep-think team. All teammates should finish their current work and exit.
```

## Personas Reference

| Persona | System Prompt Summary |
|---------|----------------------|
| first-principles | Break every assumption down. Derive from scratch. Question "best practices". |
| pragmatist | What works in production? Maintenance burden? Will this make sense in 6 months? |
| adversarial | Worst case, edge cases, failure modes. Murphy's Law everywhere. |
| innovator | Unconventional solutions. Analogies from other domains. "What if we did the opposite?" |
| optimizer | Time/space complexity, cache behavior, network trips, rendering cycles. Quantify everything. |

See `references/reasoning-patterns.md` for problem-type-specific strategies.

## Output Structure

```
.deep-think/
├── 01-analysis/analysis.md       # Your problem analysis
├── 02-decomposition/decomposition.md  # Sub-problems breakdown
├── 03-paths/
│   ├── path-first-principles.md  # Each teammate's solution
│   ├── path-pragmatist.md
│   ├── path-adversarial.md
│   └── path-optimizer.md
├── 04-verification/verification.md  # Verifier's critique
├── 05-synthesis/synthesis.md     # Combined best elements
└── 06-answer/answer.md           # Final polished answer
```

## Important Rules

1. **Write Phase 1-2 BEFORE spawning team.** Teammates need this context.
2. **Each teammate has independent context.** They share info via files and inbox messages.
3. **Verifier must be spawned AFTER paths are done.** Fresh eyes = no anchoring bias.
4. **Scale to complexity.** 2-3 teammates for medium, 4-5 for high/extreme.
5. **Read the final answer yourself.** Sanity-check before presenting to user.

## Opus 4.6 Tips

- **Effort levels**: Use `/effort max` for deep think tasks. The model will use extended thinking when useful.
- **Adaptive thinking**: Opus 4.6 automatically decides when deeper reasoning helps. Deep Think benefits from this.
- **Context compaction**: For very long sessions, enable compaction to avoid hitting context limits.

## Comparison: Agent Teams vs Subagents

| Aspect | Agent Teams | Subagents |
|--------|-------------|-----------|
| Communication | Teammates message each other | Report back to parent only |
| Context | Each has own window | Shares parent context |
| Coordination | Self-organize via task list | Parent orchestrates |
| Best for | Deep parallel exploration | Quick focused tasks |

Deep Think uses Agent Teams because we need teammates to challenge each other's findings.