# Mermaid Patterns for Architecture Docs

아래 패턴 중 문맥에 맞는 2개 이상을 선택해 사용한다.

## 1) Flowchart: 레이어/경계

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

## 2) Sequence: 요청/이벤트 흐름

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

## 3) C4-style Component: 책임 분리

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

## 4) Dependency Graph: 패키지/모듈 의존성

```mermaid
flowchart LR
  UI["packages/ui"] --> Feature["packages/feature"]
  Feature --> Domain["packages/domain"]
  Domain --> Shared["packages/shared"]
  Feature --> Api["packages/api-client"]
```

## 선택 가이드

- 사용자 요청/데이터 흐름이 중요하면 `Sequence`를 포함한다.
- 계층 구조와 경계 설명이 중요하면 `Flowchart`를 포함한다.
- 패키지 구조 변동이 크면 `Dependency Graph`를 포함한다.
- 시스템 책임 분리 설명이 필요하면 `C4-style Component`를 포함한다.
