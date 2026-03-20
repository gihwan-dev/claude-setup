# Anti-Patterns to Avoid

Common mistakes AI makes when refactoring code.

## 1. Meaningless abstraction

This happens when the code is merely cut into a new function, but the new function name does not explain what it does.

### ❌ Bad example

```typescript
// Original code
if (user.age >= 18 && user.country === 'KR') {
  price = price * 1.1
}

// AI-generated "refactor"
function processUserPriceLogic(user: User, price: number) {
  if (user.age >= 18 && user.country === 'KR') {
    price = price * 1.1
  }
  return price
}
```

### ✅ Good example

```typescript
function applyKoreanAdultTax(price: number): number {
  return price * 1.1
}

// Usage
if (isKoreanAdult(user)) {
  price = applyKoreanAdultTax(price)
}
```

## 2. Excessive parameterization

Trying to make the code too generic by adding too many parameters, which makes it harder to understand.

### ❌ Bad example

```typescript
function processData(
  data: any,
  config: ProcessConfig,
  options: ProcessOptions,
  context: ProcessContext,
  handlers: ProcessHandlers,
  validators: ProcessValidators,
) {
  // ...
}
```

### ✅ Good example

```typescript
// Functions tuned to a specific purpose
function validateUserInput(input: UserInput): ValidatedInput { ... }
function formatPhoneNumber(phone: string): string { ... }
function saveUser(user: User): SaveResult { ... }
```

## 3. Mechanical splitting

Splitting code mechanically by line count instead of by logical units.

### ❌ Bad example

```typescript
// Split every 30 lines no matter what
function processPart1(data) {
  // lines 1-30
}

function processPart2(data) {
  // lines 31-60
}

function processPart3(data) {
  // lines 61-90
}
```

### ✅ Good example

```typescript
// Split by logical unit (line counts may differ)
function validateInput(data) { ... }      // 15 lines
function transformData(data) { ... }      // 45 lines (still OK if it is one concept)
function saveResult(data) { ... }         // 20 lines
```

## 4. Over-decorated names

Trying to stuff too much information into the name until it becomes harder to read.

### ❌ Bad example

```typescript
function validateAndProcessUserInputDataWithErrorHandling()
function handleUserRegistrationFormSubmissionWithValidation()
function executeAsyncDatabaseQueryWithRetryAndTimeout()
```

### ✅ Good example

```typescript
function validateUserInput()
function submitRegistration()
function queryWithRetry()
```

## 5. Too many abstraction layers

Adding multiple wrapper functions for a single call.

### ❌ Bad example

```typescript
function handleRequest(req) {
  return processRequest(req)
}

function processRequest(req) {
  return executeRequest(req)
}

function executeRequest(req) {
  return runRequest(req)
}

function runRequest(req) {
  // The real logic only exists here
}
```

### ✅ Good example

```typescript
function handleRequest(req) {
  const validated = validateRequest(req)
  const result = executeQuery(validated)
  return formatResponse(result)
}
```

## 6. Context-free helper functions

Creating a "utility" that could be used anywhere even though it is actually used in only one place.

### ❌ Bad example

```typescript
// utils/helpers.ts
function processArrayWithCondition(arr, condition, transformer) {
  return arr.filter(condition).map(transformer)
}

// Usage
const adults = processArrayWithCondition(
  users,
  u => u.age >= 18,
  u => u.name
)
```

### ✅ Good example

```typescript
// Clear and local at the call site
const adultNames = users
  .filter(user => user.age >= 18)
  .map(user => user.name)
```

## Self-Review Checklist

After refactoring, check the following:

1. [ ] Can you tell what the function does from its name alone?
2. [ ] Are there 3 parameters or fewer?
3. [ ] Does each function do one thing?
4. [ ] Is the calling code easier to read now?
5. [ ] Can you understand the overall flow by reading top to bottom?
