# Question Taxonomy

Every question in the session must be tagged with one of these types. The type determines the question's purpose and the expected response pattern.

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
- The assumption ledger has unchallenged entries.
- An alternative has been dismissed too quickly.

Examples:
- "If the database connection drops mid-transaction, does this invariant still hold?"
- "What happens when this function receives an empty collection instead of null?"
- "You assumed read-after-write consistency. What if the replica has a 2-second lag?"

### `constrain`

Purpose: Narrow the solution space by surfacing hard limits.

When to use:
- Multiple approaches seem equally valid.
- Non-functional requirements haven't been stated.
- Deployment or operational context is missing.

Examples:
- "Is there a memory budget for this service?"
- "Can we break backward compatibility, or must old clients keep working?"
- "What's the maximum acceptable downtime during migration?"

### `compare`

Purpose: Force explicit trade-off evaluation between alternatives.

When to use:
- The `alternatives` state has 2+ options.
- The user gravitates toward one option without articulating why.
- Trade-offs haven't been stated.

Examples:
- "Option A is simpler but requires downtime. Option B is zero-downtime but adds a new dependency. Which constraint matters more?"
- "Both approaches handle the happy path. How do they differ on the error path?"
- "If you had to roll back Option A vs Option B, which recovery is faster?"

### `validate`

Purpose: Confirm that a resolved question or decision still holds under the current model.

When to use:
- The system model has changed since the original decision.
- A new constraint was introduced that may invalidate prior choices.
- Moving from `decision` to `plan`.

Examples:
- "Earlier we decided X because of assumption Y. We've since learned Z. Does X still hold?"
- "The success criterion says P. Does the chosen approach actually deliver P?"
- "We agreed the rollback plan is R. Given the new data flow, is R still viable?"

### `risk`

Purpose: Surface failure modes, operational hazards, and second-order effects.

When to use:
- Entering `adversarial-review`.
- The design involves distributed systems, migrations, or user-facing changes.
- The assumption ledger has items marked "likely true but unverified."

Examples:
- "If this migration fails halfway, what state is the data in?"
- "What monitoring would detect this failure before users do?"
- "Who gets paged at 3am if this breaks, and do they have the context to fix it?"

## Usage Rules

1. Tag every question with its type in brackets: `[clarify]`, `[falsify]`, etc.
2. Prefer `clarify` early, `falsify` and `risk` late.
3. In `adversarial-review`, at least 50% of questions must be `falsify` or `risk`.
4. If the same type has been used 3 turns in a row, consider whether a different type would surface new information.
5. `compare` is mandatory in the `alternatives` state. Do not skip it.
