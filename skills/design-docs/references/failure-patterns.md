# Common Failure Patterns

Consult this document when a design-docs session shows signs of stalling,
drifting, or degrading.

## 1. Premature implementation jump

**Signal**: Conversation shifts to specific code changes, file names, or
syntax before `phase: done`.

**Fix**: Redirect to current phase. Say: "We're still in [phase]. Let's
resolve [specific unresolved tag] before discussing implementation."

## 2. Sycophantic agreement loop

**Signal**: Three consecutive turns where the main agent agrees with the
user without adding new information, challenging an assumption, or surfacing
a risk.

**Fix**: Force a `falsify` question. Find the weakest unchallenged
`[ASSUMPTION][candidate]` and attack it. Frame as: "I want to stress-test
this before we commit to it."

## 3. Question fatigue

**Signal**: User gives increasingly short answers, says "just decide", or
expresses frustration with the questioning pace.

**Fix**: Acknowledge the pace. Summarize the current state. Compress: "Here's
where we are. I see [N] must-answer questions. The most critical one is [X].
Can we resolve that and move forward?" Batch limit is already ≤3 — tighten
to ≤2 or 1 if fatigue persists.

## 4. Scope creep during flesh

**Signal**: New requirements or features keep appearing during flesh or
refine that weren't in the plan-mode frozen bundle.

**Fix**: Add each new item to the PRD `## Assumptions` as "new scope". At
the end of the current turn, ask: "This wasn't in our plan-mode bundle.
Should we update scope (rerun plan for this doc) or keep it out?"

## 5. False consensus

**Signal**: A `[DECISION-CANDIDATE]` was resolved quickly with no dissent.
`design-skeptic` dispatch found no real challenges.

**Fix**: Explicitly adopt a devil's advocate stance. Ask: "If I had to argue
against this choice, the strongest argument would be [X]. How do we counter
that?" Add the counterargument to the ADR's Consequences section.

## 6. Evidence-free reasoning

**Signal**: Claims about system behavior, performance, or user needs are
stated in a doc without referencing code, data, logs, or documentation.

**Fix**: Dispatch `docs-researcher` to verify the claim. Frame as: "Let's
check this against the actual code/data before building on it." Promote the
claim to `[ASSUMPTION][candidate]` until verified.

## 7. Alternatives theater

**Signal**: An ADR lists alternatives but one is clearly a strawman. The
comparison is not genuine.

**Fix**: Challenge the weaker alternative: "Is there a context where
Alternative B would actually be better? If not, what would a genuinely
different approach look like?" Rewrite the ADR with real alternatives or
collapse it to a single-option decision with reasoning.

## 8. Phase oscillation

**Signal**: The session keeps flipping between flesh and refine without
resolving the blocking issue.

**Fix**: Identify the specific blocker. If external dependency, mark the
session as `phase: blocked` with the dependency noted in `_state.log`. If
internal disagreement, frame it as a `[DECISION-CANDIDATE]` and ask the user
to pick with trade-off visible.

## 9. Bundle drift

**Signal**: Docs haven't been updated in 3+ turns. Verbal agreements during
refine aren't recorded in the doc bodies.

**Fix**: Pause and synchronize. Update affected docs + `_state.yaml` with
findings from the last few turns before asking the next question or
dispatching new agents.

## 10. Infinite depth

**Signal**: Questions keep drilling deeper into a subtopic well beyond what
any doc's decision requires.

**Fix**: Apply the "decision relevance" test: "Does the answer change
anything in any doc? If not, note it as an `[QUESTION][nice-to-have]` in
the relevant Open Questions and move on."

## 11. Premature refine

**Signal**: User invokes `$design-docs refine` before flesh has drafted all
bundle docs.

**Fix**: Warn. Report which docs are still `status: placeholder`. Offer:
"Run flesh first? Or skip the missing docs for this refine pass?" Respect
user override but log the forced refine in `_state.log`.

## 12. Signal starvation

**Signal**: In plan mode, 5+ signals remain `unknown` after docs-researcher
dispatch, and the user can't easily answer them.

**Fix**: Drop to conservative defaults: include `prd-lite` + `adr` + any
doc with at least one `true` signal. Mark unresolved axes in
`_state.yaml.signals` and return to plan mode later when more is known.
