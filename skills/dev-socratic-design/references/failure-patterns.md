# Common Failure Patterns

Consult this document when the session shows signs of stalling, drifting, or degrading.

## 1. Premature implementation jump

**Signal**: The conversation shifts to specific code changes, file names, or syntax before `alternatives` state.

**Fix**: Redirect to the current state's question. Say: "We're still in [state]. Let's resolve [specific unknown] before discussing implementation."

## 2. Sycophantic agreement loop

**Signal**: Three consecutive turns where the response agrees with the user without adding new information, challenging an assumption, or surfacing a risk.

**Fix**: Force a `falsify` question. Find the weakest assumption in the ledger and attack it. Frame as: "I want to stress-test this before we commit to it."

## 3. Question fatigue

**Signal**: User gives increasingly short answers, says "just decide", or expresses frustration with the questioning pace.

**Fix**: Acknowledge the pace. Summarize the current state. Offer to compress: "Here's where we are. I see [N] open questions. The most critical one is [X]. Can we resolve that and move forward?"

## 4. Scope creep during design

**Signal**: New requirements or features keep appearing in later states that weren't in the original `frame`.

**Fix**: Add each new item to the assumption ledger as "new scope". At the end of the current turn, ask: "This wasn't in our original frame. Should we update the scope, or is this out of scope for this design?"

## 5. False consensus

**Signal**: A decision was reached quickly with no dissent. The adversarial-review found no real challenges.

**Fix**: Explicitly adopt a devil's advocate stance. Ask: "If I had to argue against this choice, the strongest argument would be [X]. How do we counter that?"

## 6. Evidence-free reasoning

**Signal**: Claims about system behavior, performance, or user needs are stated without referencing code, data, logs, or documentation.

**Fix**: Dispatch an `Explore` agent to verify the claim. Frame as: "Let's check this against the actual code/data before building on it."

## 7. Alternatives theater

**Signal**: Alternatives were generated but one was clearly a strawman. The comparison was not genuine.

**Fix**: Challenge the weaker alternative: "Is there a context where Alternative B would actually be better? If not, what would a genuinely different approach look like?"

## 8. State oscillation

**Signal**: The session keeps returning to the same state without resolving the blocking issue.

**Fix**: Identify the specific blocker. If it's an external dependency, mark the session as `blocked` with the dependency noted. If it's an internal disagreement, frame it as a decision: "We have two views on [X]. Let's decide and document the trade-off."

## 9. Design document drift

**Signal**: The living document hasn't been updated in 3+ turns. Verbal agreements aren't recorded.

**Fix**: Pause and synchronize. Update the document with all findings from the last few turns before asking the next question.

## 10. Infinite depth

**Signal**: Questions keep drilling deeper into a subtopic well beyond what the design decision requires.

**Fix**: Apply the "decision relevance" test: "Does the answer to this question change our design choice? If not, note it as an open question and move on."
