# Mermaid Patterns for Architecture Docs

Choose and use at least two of the patterns below based on the current context.

## 1) Flowchart: Layers / Boundaries

```mermaid
flowchart TB
  subgraph Presentation
    Web["Web UI"]
    Admin["Admin UI"]
  end

  subgraph Application
    Facade["UseCase Facade"]
    Orchestrator["Workflow Orchestrator"]
  end

  subgraph Domain
    Policy["Domain Policy"]
    Model["Aggregate Model"]
  end

  subgraph Infrastructure
    Repo["Repository"]
    Queue["Event Bus"]
    External["External API"]
  end

  Web --> Facade
  Admin --> Facade
  Facade --> Orchestrator
  Orchestrator --> Policy
  Policy --> Model
  Orchestrator --> Repo
  Orchestrator --> Queue
  Queue --> External
```

## 2) Sequence: Request / Event Flow

```mermaid
sequenceDiagram
  actor User
  participant UI
  participant API
  participant Service
  participant Bus
  participant Worker

  User->>UI: Trigger action
  UI->>API: Submit payload
  API->>Service: Execute use case
  Service->>Bus: Publish domain event
  Bus-->>Worker: Consume event
  Worker-->>API: Async status update
  API-->>UI: Return response
```

## 3) C4-style Component: Responsibility Split

```mermaid
flowchart LR
  subgraph System["System Boundary"]
    C1["Web App"]
    C2["API Gateway"]
    C3["Core Service"]
    C4["Scheduler"]
  end

  Ext1["Identity Provider"]
  Ext2["Analytics Platform"]

  C1 --> C2
  C2 --> C3
  C4 --> C3
  C3 --> Ext1
  C3 --> Ext2
```

## 4) Dependency Graph: Package / Module Dependencies

```mermaid
flowchart LR
  UI["packages/ui"] --> Feature["packages/feature"]
  Feature --> Domain["packages/domain"]
  Domain --> Shared["packages/shared"]
  Feature --> Api["packages/api-client"]
```

## Selection Guide

- Include `Sequence` when user-facing request/data flow matters.
- Include `Flowchart` when hierarchy and boundaries are the main story.
- Include `Dependency Graph` when package structure changed significantly.
- Include `C4-style Component` when you need to explain system responsibility splits.
