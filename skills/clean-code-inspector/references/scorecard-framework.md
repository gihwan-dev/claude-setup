# React Clean Code Scorecard Framework

This file defines the quantitative evaluation framework referenced by the clean-code-inspector agent.

## 1. Structural Complexity
- **Cyclomatic Complexity (CC)**: Count every branch point (`if`, `else`, `&&`, `||`, `?:`, `??`, `switch case`, `catch`).
  - Nested ternaries inside JSX are counted as multiplicative complexity.
  - 1-10: healthy | 11-20: warning | 21-50: risky | >50: unacceptable
- **Cognitive Complexity**: Watch nesting depth (`max-depth > 3-4` is a warning), hook dependency array size (`>5` is risky), and callback nesting.

## 2. Component Responsibility Score (CRS)
- CRS = w1(LoC) + w2(CC) + w3(SC) + w4(DC)
- **LoC**: >200 lines is risky, <100 is recommended
- **State Count (SC)**: Number of `useState` / `useReducer` calls. 0-3: healthy | 4-6: warning | >6: risky
- **Dependency Count (DC)**: Number of import statements. >10 is a warning
- CRS bands: <50 (Atomic) | 50-100 (Boundary) | >100 (God Component - Refactor Alert)

## 3. Cohesion and Coupling
- **LCOM4 (React Hook Cohesion)**: Connection graph between internal state (`useState`) and methods (`Effect` / `Callback` / `Handler`).
  - Number of disconnected subgraphs = LCOM4. 1: healthy | >1: should be split
  - If LCOM4 > 1, each disconnected graph is a custom-hook candidate.
- **Props Drilling**: Delivery depth from origin to consumer. >3 implies unnecessary coupling.

## 4. Component Interface Quality
- **Prop Count**: <5 (ideal) | 5-7 (acceptable) | >7 (code smell)
- **Boolean Props**: Multiple booleans should usually be consolidated into an enum/union type. Check for mutually exclusive boolean combinations.
- **Naming Rules**: Prop event handlers use the `on*` prefix, implementation handlers use `handle*`. Booleans use `is*` / `has*` / `should*`.

## 5. Static Analysis Metrics (ESLint)
- `react-hooks/rules-of-hooks`: 0 violations
- `max-lines-per-function`: <100
- `no-console`: 0 violations
- `TypeScript noImplicitAny`: 0%

## 6. Testability
- Target Mutation Score > 80% for business-logic hooks and utilities.
- Inspect side-effect isolation and whether the component can be tested independently.

## 7. State Architecture
- **State Colocation**: How close state lives to where it is used.
- **Global State Density**: Whether global state truly needs to be global.

## 8. Consolidated Scorecard Format

| Category | Evaluation item | Measured / observed value | Status (healthy / warning / risky) | Notes |
|---------|---------|------------|-------------------|------|
| Complexity | Cyclomatic Complexity (CC) | ... | ... | ... |
| Complexity | Cognitive Complexity | ... | ... | ... |
| Size | Lines of Code (LoC) | ... | ... | ... |
| Responsibility | CRS | ... | ... | ... |
| Interface | Prop Count | ... | ... | ... |
| Interface | Boolean Props | ... | ... | ... |
| Interface | Naming Rules | ... | ... | ... |
| Coupling | Props Drilling Depth | ... | ... | ... |
| Cohesion | LCOM4 (estimated) | ... | ... | ... |
| State | State Colocation | ... | ... | ... |
| State | Global State Density | ... | ... | ... |
| Hygiene | ESLint Violations | ... | ... | ... |
| Testing | Testability | ... | ... | ... |

## 9. Auto-Fix Eligibility

An issue is auto-fixable only when it satisfies **all three** conditions below:
1. **Deterministic transformation**: There is exactly one correct fix with no design judgment required
2. **Local scope**: The fix is fully contained within the file itself, with no cross-file impact
3. **Behavior preservation**: Runtime behavior does not change (pure refactor)

Auto-fixable examples: naming rule violations, unused imports, `console.log`, inferable explicit `any`
Not auto-fixable: component splitting, hook extraction, boolean-to-enum changes, state architecture changes, memoization changes
