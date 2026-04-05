# Question Taxonomy

Every question the main agent asks the user during refine mode, and every
question embedded in an ADR's "questions considered" section, is tagged with
one of these six types. The type determines the question's purpose and the
expected response pattern.

## Types

### `clarify`

Purpose: Reduce ambiguity. Make the implicit explicit.

When to use:
- The user's description has undefined terms.
- Success criteria are vague.
- Scope boundaries are unclear.

Examples:
- "When you say 'fast', what latency threshold are you targeting?"
- "Does 'user' here mean the end-user or the internal API consumer?"
- "What happens to in-flight requests when this change deploys?"

### `falsify`

Purpose: Find conditions under which the current assumption breaks.

When to use:
- A claim has been accepted without evidence.
- An `[ASSUMPTION][candidate]` has survived without challenge.
- An alternative has been dismissed too quickly.

Examples:
- "If the database connection drops mid-transaction, does this invariant still hold?"
- "What happens when this function receives an empty collection instead of null?"
- "You assumed read-after-write consistency. What if the replica has a 2-second lag?"

### `constrain`

Purpose: Narrow the solution space by surfacing hard limits.

When to use:
- Multiple approaches seem equally valid in an ADR.
- Non-functional requirements haven't been stated.
- Deployment or operational context is missing.

Examples:
- "Is there a memory budget for this service?"
- "Can we break backward compatibility, or must old clients keep working?"
- "What's the maximum acceptable downtime during migration?"

### `compare`

Purpose: Force explicit trade-off evaluation between alternatives.

When to use:
- A `[DECISION-CANDIDATE]` has 2+ options.
- The user gravitates toward one option without articulating why.
- Trade-offs haven't been stated in an ADR.

Examples:
- "Option A is simpler but requires downtime. Option B is zero-downtime but adds a new dependency. Which constraint matters more?"
- "Both approaches handle the happy path. How do they differ on the error path?"
- "If you had to roll back Option A vs Option B, which recovery is faster?"

### `validate`

Purpose: Confirm that a resolved question or decision still holds under the
current model.

When to use:
- A prior decision was made and new context has emerged.
- A new constraint was introduced that may invalidate prior ADRs.
- Moving from refine to done.

Examples:
- "Earlier we decided X because of assumption Y. We've since learned Z. Does X still hold?"
- "The success criterion says P. Does the chosen approach actually deliver P?"
- "We agreed the rollback plan is R. Given the new data flow, is R still viable?"

### `risk`

Purpose: Surface failure modes, operational hazards, and second-order effects.

When to use:
- Refining a doc whose axis is sensitivity, scale, or architecture.
- The design involves distributed systems, migrations, or user-facing changes.
- An `[ASSUMPTION][candidate]` is marked "likely true but unverified".

Examples:
- "If this migration fails halfway, what state is the data in?"
- "What monitoring would detect this failure before users do?"
- "Who gets paged at 3am if this breaks, and do they have the context to fix it?"

## Usage Rules

1. Tag every must-answer question in brackets when asking the user:
   `[clarify] ...`, `[falsify] ...`, etc.
2. Prefer `clarify` early (during flesh interview), `falsify` and `risk`
   late (during refine adversarial pass).
3. When dispatching `design-skeptic` in refine, ≥50% of the attacks the
   skeptic surfaces should be `falsify` or `risk` shaped.
4. If the same type has been used 3 turns in a row, consider whether a
   different type would surface new information.
5. `compare` is mandatory for every `[DECISION-CANDIDATE]` elevated to the
   user. Do not let the user pick without the trade-off on the table.
