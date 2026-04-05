<!-- Status: placeholder -->
<!-- Confidence: low -->
<!-- doc_type: architecture-context -->

# Architecture Context: <TITLE>

## Scope Boundary

[QUESTION][must-answer] What is inside this design's boundary, and what is
outside?

- **Inside**:
- **Outside**:

## System Context (C4 Level 1)

[ASSUMPTION][candidate] The relevant external actors and systems are:

- **Users / Actors**:
- **External systems called**:
- **External systems calling us**:

```
(ASCII or Mermaid diagram sketch — populated during flesh)
```

## Container View (C4 Level 2)

[QUESTION][must-answer] What deployable/runtime units exist inside this
boundary?

- **Container 1**: <name, tech, responsibility>
- **Container 2**:

```
(Container diagram sketch)
```

## Data Flow

[ASSUMPTION][candidate] Data flows:

1. **Source → Transform → Sink**: ...
2. ...

## Ownership Boundaries

Which team or module owns each part.

- <component>: <owner>

## Invariants

[QUESTION][must-answer] What must always be true about this system, from
the outside?

- Invariant 1:
- Invariant 2:

## Decision Candidates

(Elevated to ADRs during refine.)

[DECISION-CANDIDATE] <choice that needs an ADR>

## Dependencies

- **Inbound**:
- **Outbound**:
- **Runtime**:
- **Build-time**:

## Extension Points

[QUESTION][nice-to-have] Where is this designed to grow next?

## Open Questions

(Moved here during refine.)

## References

- PRD: `../PRD.md`
- ADRs: `../adr/`
