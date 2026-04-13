# Interview Axes

The flesh-mode interview surfaces domain context before per-doc drafting. The
main agent asks one axis question per turn, recording answers in
`_state.yaml.interview_answers`. These answers then feed every doc writer's
dispatch payload.

The axes are **abstract**, not UI-level. "What color should the submit button
be" is out of scope. "Who is the primary user and what job do they hire this
for" is in scope.

## 8 Interview Axes

### 1. Users and Jobs

**Question**: Who is the primary user, and what job are they hiring this
system to do?

**Why**: Grounds the PRD problem statement, user scenarios, and UX flow.
Without this, every other answer drifts.

**Good answers look like**: "Internal PMs running weekly ops reviews — they
want to see blocked work in ≤30 seconds."

**Stop condition**: A concrete user segment + a concrete job is stated.

### 2. Success Criteria

**Question**: How will you know this worked, and over what time window?

**Why**: Forces measurable outcomes into the PRD. Distinguishes success
metrics from vanity metrics.

**Good answers look like**: "Median time-to-find-blocker drops from 4m to
<1m within 2 weeks of launch."

**Stop condition**: Measurable outcome + timebox named.

### 3. Scope and Non-scope

**Question**: What is explicitly in scope this round, and what is
deliberately out of scope?

**Why**: Prevents scope creep during flesh. Populates PRD non-goals.

**Good answers look like**: "In: dashboard + single saved filter. Out:
multi-tenant RBAC, mobile."

**Stop condition**: Both in-scope and out-of-scope are named.

### 4. Constraints and Deadlines

**Question**: What hard constraints or deadlines shape this work?

**Why**: Surfaces non-functional requirements, compliance, timeline pressure,
headcount limits.

**Good answers look like**: "Must ship before Q3 board meeting (2026-06-15);
cannot add a new database."

**Stop condition**: At least one hard constraint is named.

### 5. Reuse Surface

**Question**: What existing components, libraries, or design-system parts
should this build on?

**Why**: Anchors architecture-context + api-contract to real reuse, not
greenfield invention.

**Good answers look like**: "Reuse the existing `QueryBuilder` component and
the `/internal/v2/tasks` API. Follow Polaris design tokens."

**Stop condition**: At least one concrete reusable asset is named, OR user
confirms greenfield.

### 6. Data and Integrations

**Question**: What data does this touch, and what external systems does it
talk to?

**Why**: Drives architecture-context data flow, api-contract, and
security-privacy scope.

**Good answers look like**: "Reads from task_events (Postgres), calls Slack
webhook for notifications, writes audit log to S3."

**Stop condition**: Data sources + external integrations named, OR user
confirms none.

### 7. Quality Attributes

**Question**: Which quality attributes are non-negotiable — latency,
availability, accessibility, privacy, cost?

**Why**: Drives nfr-checklist, security-privacy, accessibility docs. Without
explicit quality attributes, trade-offs collapse.

**Good answers look like**: "p95 < 300ms; accessibility must meet WCAG 2.2
AA; PII must never leave the VPC."

**Stop condition**: At least two quality attributes with thresholds OR
explicit acknowledgment that no hard threshold exists.

### 8. Future Direction

**Question**: What's likely to come next after this ships, that we should
not preclude?

**Why**: Shapes ADR "consequences" sections and architecture-context
extension points. Distinguishes "design for now" from "paint into corner".

**Good answers look like**: "Next quarter we'll add per-team dashboards and
external API access — so multi-tenancy and authz are likely reopens."

**Stop condition**: User names at least one likely follow-up OR explicitly
says none are known.

### 9. Technical Risk (Spike Candidates)

**Question**: What is the single biggest technical bet in this design — the
assumption that, if wrong, would invalidate the entire approach? How would
you verify it in under 30 minutes with a minimal test?

**Why**: Surfaces runtime-only assumptions that cannot be validated by
reading code or documentation. These become `[SPIKE][required]` entries
that must be tested before full document production begins. Prevents
building an elaborate design on an unverified foundation.

**Good answers look like**: "We assume the Claude Code Stop hook fires
once per session exit, not per-turn. Verify: register a Stop hook that
appends a timestamp to a log file, run one session with 3 turns, check
if the log has 1 line or 3."

**Stop condition**: User names at least one runtime-verifiable assumption
with a concrete test, OR explicitly confirms all technical assumptions
are already verified or verifiable via code reading.

**When to ask**: Always ask this axis. It is the most important axis for
architecture and feature work modes. Even if the user says "none", record
that as an explicit acknowledgment in `_state.yaml`.

## Conduct Rules

1. **One axis per turn.** Do not bundle axis questions together. Give the
   user space to answer each.
2. **Prefer axes that unblock the most docs.** Users+Jobs and Constraints
   unblock nearly every doc; ask them first. **Technical Risk (Axis 9)
   should be asked early for architecture/feature work modes** — it can
   invalidate the entire design direction.
3. **Stop asking when answered.** If the user's answer to Axis 1 already
   implied Axis 3 (scope), skip Axis 3's explicit question and record the
   inferred answer with `[ASSUMPTION][candidate]` marker.
4. **Never ask UI-level questions here.** Button color, spacing, copy — those
   are filled inside `ux-flow` drafts in flesh, not in the interview.
5. **Close the interview explicitly.** After 6-9 axes are answered, summarize
   the domain context to the user and ask "is this accurate before I
   dispatch the writers?"

## Early Exit

If the user has a `docs/design/<slug>.md` from a prior Socratic session, the
interview can be shortened:

- Read the prior doc's Problem Framing, Constraints, Non-goals, Success
  Criteria, Chosen Direction.
- Skip axes already covered there.
- Confirm the mapping with the user in a single turn before proceeding.

Log the reused answers in `_state.yaml.interview_answers` with source
`from_socratic_design`.
