# Visualization Playbook

## Diagram Selection Rules

- Use `flowchart` when you need to break down execution flow.
- Use `sequenceDiagram` for async calls or interaction between actors.
- Use `stateDiagram-v2` when state transitions are the core story.
- Use `classDiagram` or a simple C4 style for module responsibilities and dependencies.

## Template 1: Flowchart

```mermaid
flowchart TD
  A[Receive Input] --> B{Valid?}
  B -->|Yes| C[Run Core Logic]
  B -->|No| D[Return Error]
  C --> E[Store Result]
  E --> F[Return Response]
```

## Template 2: Sequence

```mermaid
sequenceDiagram
  participant U as User
  participant C as Controller
  participant S as Service
  participant R as Repository

  U->>C: Send request
  C->>S: Pass input
  S->>R: Query data
  R-->>S: Query result
  S-->>C: Processing result
  C-->>U: Return response
```

## Template 3: State Transition

```mermaid
stateDiagram-v2
  [*] --> Idle
  Idle --> Validating: Request received
  Validating --> Running: Validation passed
  Validating --> Failed: Validation failed
  Running --> Completed: Processing succeeded
  Running --> Failed: Exception occurred
  Completed --> [*]
  Failed --> [*]
```

## Quality Checklist

- Are node labels role-centered?
- Does each branching label include both the condition and the outcome?
- Do arrow directions match the real execution order?
- Do the text explanation and the diagram use the same terms?
- Are the happy path and exception path clearly separated?
