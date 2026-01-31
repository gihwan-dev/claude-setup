---
name: planner
description: FSD 기반 구현 계획 생성. survey.md를 읽고 plan.md 작성. "계획 세워", "구현 계획" 등의 요청 시 사용
disable-model-invocation: false
---

1.  **Analyze Request**: Understand the user's intent for the architectural plan.
2.  **Read Survey**: Read the content of `survey.md` in the project root to understand the architectural context and decisions.
3.  **Generate Plan**: Create a comprehensive implementation plan (`plan.md`) **in Korean**.
    *   **Context**: Use the information from `survey.md` as the foundation.
    *   **Architecture**: The plan MUST adhere to **Feature-Sliced Design (FSD)** principles.
    *   **Quality**: Prioritize "High Cohesion", "Low Coupling", "Abstraction", and "SOLID" principles.
    *   **Format**: The output should be a high-level design document (architecture), not just detailed code snippets. Focus on the macro structure and future extensibility.
    *   **CRITICAL**: The generated content MUST be in Korean.
4.  **Write File**: Save the generated content to a file named `plan.md` in the project root.

# Knowledge Base: Architectural Principles for plan.md

## 1. Feature-Sliced Design (FSD) Application
*   **Layers**: app -> pages -> widgets -> features -> entities -> shared.
*   **Slices**: Group code by business domain (e.g., `user`, `cart`, `product`).
*   **Segments**: ui, model (store/types), lib (utils), api.
*   **Rule**: Upper layers can import lower layers. Lower layers cannot import upper layers. Slices in the same layer cannot import each other (use Composition in Widget/Page).

## 2. Design Principles
*   **SOLID**:
    *   *SRP*: Each component/hook should have one reason to change.
    *   *OCP*: Open for extension, closed for modification (use props/strategy pattern).
    *   *LSP*: Subtypes must be substitutable.
    *   *ISP*: Small, specific interfaces.
    *   *DIP*: Depend on abstractions (interfaces), not concretions.
*   **Cohesion & Coupling**:
    *   Keep related things together (Colocation).
    *   Minimize dependencies between distinct features.

## 3. Plan Structure (plan.md)
*   **Objective**: Clear statement of what is being built.
*   **Architecture Overview**: Diagram or text description of layers and slices involved.
*   **Directory Structure**: Proposed folder structure following FSD.
*   **Key Components/Modules**: Description of core units and their responsibilities.
*   **Data Flow**: How state moves (Server -> Client -> UI).
*   **Extensibility Strategy**: How to add new features later without rewriting this code.
