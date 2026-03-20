# Qualitative Overlay Rubric (v2)

Qualitative evaluation does not replace quantitative results. Scoring must use only the rubric below.

## Common Rules

- Target: files in the top 20% of quantitative hotspots
- Score range per criterion: `0~4`
- Evidence requirement: at least two file+line evidence points per criterion
- If evidence is insufficient: `N/A`
- Do not write praise or criticism without evidence

## 1) Intent Clarity

Does the business intent or behavior rule become clear from the code alone?

- 4: Function/variable names and branch structure reveal the core rule immediately.
- 3: Mostly clear, but some branches still require contextual inference.
- 2: Key rules are scattered across the code and require back-and-forth reading.
- 1: Intent is hard to infer, and names/branches conflict with each other.
- 0: The intent cannot be meaningfully understood from the code.

## 2) Local Reasoning

Can state and data flow be traced within a single file or function?

- 4: Data flow is linear and understandable from local context alone.
- 3: Some external dependencies exist, but the main flow is still understandable locally.
- 2: The reader must repeatedly jump between local and external context.
- 1: Tracing the flow frequently crosses multiple abstraction boundaries.
- 0: The flow is practically impossible to follow.

## 3) Failure Semantics

Are the intentions around errors, empty states, timeouts, and fallbacks clear?

- 4: Failure modes are clearly defined and handled comprehensively.
- 3: Major failure modes are covered, but some edge cases remain open.
- 2: Failure handling is inconsistent and visibly incomplete.
- 1: Failure branches are rare and mostly implicit.
- 0: Failure handling intent is nearly absent.

> If the score is 0 and evidence is sufficient, add the `missing_failure_semantics` flag.

## 4) Boundary Discipline

Are separation-of-concerns and boundary rules preserved?

- 4: Boundaries are clear and layers do not leak into each other.
- 3: Boundaries mostly hold, with limited leakage.
- 2: Boundary mixing appears repeatedly.
- 1: Multiple boundary violations create broad change impact.
- 0: Boundary discipline has effectively collapsed.

> If the score is 0 and evidence is sufficient, add the `boundary_discipline_violation` flag.

## 5) Test Oracle Quality

Do tests verify behavior rules rather than merely executing code?

- 4: The tests explicitly assert the core business rules.
- 3: Most core rules are verified, but some assertions are still close to execution checks.
- 2: Assertion quality is uneven, and important rules are missing.
- 1: Many tests focus mainly on execution confirmation.
- 0: There is almost no meaningful rule verification.

## Recommended Output Format (JSON)

```json
{
  "evaluations": [
    {
      "file": "src/example.ts",
      "criteria": [
        {
          "id": "intent_clarity",
          "score": 3,
          "evidence": [
            { "file": "src/example.ts", "line": 12, "detail": "domain-rule branch" },
            { "file": "src/example.ts", "line": 28, "detail": "intent-revealing function name" }
          ],
          "comment": "The core flow is clear, but some terms remain vague."
        }
      ],
      "criticalFlags": []
    }
  ]
}
```
