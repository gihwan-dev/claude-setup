---
name: complexity-refactor
description: >
  Refactor high cyclomatic complexity functions into human-readable, maintainable code.
  Use for "clean up this complex function", "this function is hard to read", "reduce
  cyclomatic complexity", or "please refactor this". Prioritizes logical reconstruction
  and readability over simple extraction or raw performance. Do not use for cosmetic
  formatting, renaming, or moving code between files.
allowed-tools: Read, Grep, Glob, Edit
---

# Complexity Refactor

Restructure highly complex functions into code that is **easy for humans to understand and modify**.

## Core Philosophy

### 1. No blind extraction

```text
❌ Don't: Cut 10 lines of code and paste them into a new function as-is
✅ Goal: Reconstruct logical units so the split feels obviously justified
```

### 2. Prioritize human reading flow

Code should be predictable as a reader moves from top to bottom.

```typescript
// ❌ A common AI output: abstract and hard to predict
processDataWithValidationAndTransformation(data, config, options)

// ✅ Human-friendly: concrete and sequential
const validated = validateUserInput(data)
const normalized = normalizePhoneNumber(validated.phone)
const saved = saveToDatabase({ ...validated, phone: normalized })
```

### 3. Names should be easy to explain

```typescript
// ❌ Bad names: unclear meaning
handleDataProcessingWithContext()
executeOperationWithFallback()
processEntityBatch()

// ✅ Good names: easy to explain in one phrase
filterExpiredUsers()      // function that filters expired users
calculateShippingFee()    // function that calculates shipping cost
sendWelcomeEmail()        // function that sends a welcome email
```

### 4. Readability > performance

Ignore the cost of looping one extra time if it makes the code easier to read. Readability comes first.

## Refactoring Procedure

### Step 1: Measure complexity

Calculate cyclomatic complexity for the target function:

```text
Complexity = 1 + (number of branch points)

Branch points: if, else if, case, while, for, catch, &&, ||, ? (ternary)
```

| Score | State | Action |
|------|------|------|
| 1-10 | Healthy | Keep |
| 11-20 | Warning | Improvement recommended |
| 21+ | Risky | Must improve |

### Step 2: Understand the logical flow

Read the code and split it by **human reasoning units**:

1. **Preparation**: data validation, initialization
2. **Core logic**: real business processing
3. **Wrap-up**: return values, cleanup

### Step 3: Choose a restructuring pattern

Apply the pattern that matches the situation. See `references/patterns.md` for details.

- **Early Return**: handle exceptional cases first to remove nesting
- **Step-by-Step**: split the logic into sequential stages
- **Strategy**: replace conditional branching with an object / map

### Step 4: Write the code

Always preserve the following while refactoring:

1. **Function names**: verb + object
2. **Flow**: the logic should be understandable by reading top to bottom
3. **Nesting**: maximum depth of 2 (no `if` inside `if` inside `if`)
4. **Length**: recommend keeping one function within 30 lines

### Step 5: Verify

- Re-measure complexity after the refactor (target: 10 or below)
- Confirm that the overall flow is understandable from function names alone
- Guarantee identical behavior to the original

## References

- Detailed refactoring patterns: `references/patterns.md`
- Anti-pattern examples: `references/antipatterns.md`
