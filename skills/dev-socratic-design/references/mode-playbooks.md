# Mode Playbooks

Each mode shares the same FSM skeleton but emphasizes different concerns and question banks.

## Architecture Mode

Focus: Boundaries, responsibilities, state transitions, operational resilience.

### Key concerns by state

| State | Primary concern |
|-------|----------------|
| frame | What are the quality attributes (latency, availability, consistency)? What are the non-goals? |
| evidence-gap | Which module boundaries are unclear? What coupling exists? |
| system-model | Component diagram, data flow, ownership boundaries, invariants |
| alternatives | Structural options: monolith vs service split, sync vs async, push vs pull |
| adversarial-review | Single points of failure, cascading failures, deployment coupling, observability gaps |
| plan | ADR format, migration path, rollback, monitoring requirements |

### Priority questions

- `[constrain]` What quality attributes are non-negotiable?
- `[clarify]` Where does ownership end for this service?
- `[falsify]` If service B is down for 5 minutes, what happens to service A?
- `[risk]` What does the on-call engineer need to diagnose this at 3am?
- `[compare]` Sync call vs event: which failure mode is more acceptable?

## Bugfix Strategy Mode

Focus: Reproduction, root cause isolation, invariant restoration, regression prevention.

### Key concerns by state

| State | Primary concern |
|-------|----------------|
| frame | Exact reproduction conditions, affected users/flows, severity |
| evidence-gap | Logs, traces, and data that haven't been examined |
| system-model | The specific code path, state transitions, and data flow involved in the bug |
| alternatives | Fix strategies: patch vs refactor, data migration vs graceful handling |
| adversarial-review | Regression risk, fix side effects, incomplete root cause |
| plan | Regression test, verification steps, monitoring for recurrence |

### Priority questions

- `[clarify]` What is the exact sequence of actions that reproduces this?
- `[clarify]` When did this start? What changed around that time?
- `[falsify]` Is this the root cause, or a symptom of something deeper?
- `[falsify]` If we apply this fix, does the original invariant actually restore?
- `[risk]` What other code paths share this assumption and could break the same way?
- `[validate]` Does the regression test cover the exact reproduction scenario?

## Refactor Mode

Focus: Behavior preservation, migration safety, backward compatibility, rollback.

### Key concerns by state

| State | Primary concern |
|-------|----------------|
| frame | What behavior must be preserved? What is the migration window? |
| evidence-gap | Which callers exist? What implicit contracts are in play? |
| system-model | Dependency graph, public API surface, implicit coupling |
| alternatives | Strangler fig vs big-bang, adapter layer vs direct rewrite |
| adversarial-review | Behavioral drift, missed callers, performance regression |
| plan | Migration steps, compatibility shim lifespan, rollback trigger |

### Priority questions

- `[constrain]` Can we break any existing callers, or is full backward compatibility required?
- `[clarify]` What implicit behavior do callers depend on beyond the documented API?
- `[compare]` Incremental strangler fig vs clean rewrite: what's the risk/effort trade-off?
- `[falsify]` If we change this internal structure, does the public behavior actually stay identical?
- `[risk]` What happens if we need to roll back after 50% of callers have migrated?
- `[validate]` Does the existing test suite cover the behavior we claim to preserve?

## Feature Mode

Focus: User value, domain model, interface design, validation, rollout strategy.

### Key concerns by state

| State | Primary concern |
|-------|----------------|
| frame | User problem, success metrics, scope boundary, MVP definition |
| evidence-gap | Domain terms, user journeys, edge cases not yet explored |
| system-model | Domain model, entity relationships, state lifecycle |
| alternatives | UX approaches, data model options, integration strategies |
| adversarial-review | Edge cases, abuse scenarios, performance under load, accessibility |
| plan | Rollout strategy (feature flag, canary, full), acceptance criteria, monitoring |

### Priority questions

- `[clarify]` What user problem does this solve? How will we know it's solved?
- `[constrain]` What is explicitly out of scope for the first release?
- `[clarify]` Walk through the user journey step by step. What happens at each decision point?
- `[falsify]` What happens when the user does the unexpected thing?
- `[compare]` Approach A is simpler for the user but harder to extend. Approach B is the reverse. Which trade-off aligns with the product direction?
- `[risk]` If this feature is used 10x more than expected, what breaks first?
- `[validate]` Do the acceptance criteria actually cover the user problem we stated?
