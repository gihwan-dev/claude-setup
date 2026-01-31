---
name: survey
description: 아키텍처 설계를 위한 설문 생성. "요구사항 분석", "아키텍처 질문", "설문 만들어" 등의 요청 시 사용
disable-model-invocation: false
argument-hint: 분석할 요구사항 또는 기능 설명
---

argument: $1

1.  **Analyze Request**: specific requirements provided by the user in the slash command arguments.
2.  **Generate Survey Content**: Create a comprehensive markdown document **in Korean** that asks clarifying questions to help define the architecture. Use the **Knowledge Base** below to formulate relevant questions.
    *   The output should be a structured questionnaire (Markdown).
    *   It should guide the user to provide necessary details for architectural decision making.
    *   **CRITICAL**: The generated content MUST be in Korean.
3.  **Write File**: Save the generated content to a file named `survey.md` in the project root.

# Knowledge Base: React Architecture Strategy

## 1. General Project Scope & Constraints (Pre-implementation)
*   **Team & Timeline**: What is the team structure (size, squads)? What is the maintenance lifecycle?
*   **Business Drivers**: What is the core value?
*   **Scale**: Is this a small MVP or a large enterprise app? (Determines FSD vs Bulletproof React).

## 2. Domain Modeling (DDD)
*   **Entities**: What are the core immutable data structures (e.g., User, Product) identified?
*   **Features**: What are the functional scenarios (e.g., "Checkout", "ProductSearch")?
*   **Ubiquitous Language**: Are there discrepancies between Design/Biz/Dev terms?

## 3. Non-Functional Requirements (NFR Checklist)
*   **Scalability**: Module boundaries, repo structure (Monorepo?).
*   **Maintainability**: Dependency rules.
*   **Performance**: Core Web Vitals targets (LCP, INP). SSR or CSR?
*   **Testability**: Logic isolation strategies. Custom Hooks vs Logic classes.
*   **Accessibility**: Compliance levels (WCAG). Headless UI needs.
*   **Security**: Auth patterns, Token storage.

## 4. Architectural Methodology Selection
*   **FSD (Feature-Sliced Design)**: strict layering, unidirectional flow. Good for complex, long-term projects.
*   **Bulletproof React**: Feature-based folders, pragmatic. Good for startups/medium scale.
*   **Clean Architecture**: Strict separation of UI and Domain (Adapters/Ports). High boilerplate, high testability.

## 5. Data & State Strategy
*   **Server State**: React Query / SWR.
*   **URL State**: Search params for filters/pagination?
*   **Client Global State**: Zustand/Redux (Minimize this).
*   **Local UI State**: Colocation.
*   **Data Fetching**: Render-then-Fetch vs Render-as-you-fetch (Loaders/Actions).

## 6. Testing & Quality
*   **Static Analysis**: ESLint boundaries.
*   **Integration**: MSW + RTL (The "Trophy" model).
*   **E2E**: Cypress/Playwright for critical paths.

---
**Output Format for `survey.md`**:
```markdown
# Architectural Survey for [Requirement Name]

## 1. Project Context
- [Question 1]
- [Question 2]

## 2. Domain Analysis
...
```
