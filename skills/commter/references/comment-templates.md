# Comment Templates

## 1) JSDoc for a TS exported function (minimal type repetition)

```ts
/**
 * Normalizes user input and builds the final runtime config according to policy priority.
 * CLI arguments override environment variables and defaults.
 *
 * @param input Raw input object.
 * @returns Executable runtime config.
 * @throws Throws when configuration values conflict with each other.
 */
export function buildRuntimeConfig(input: RawConfig): RuntimeConfig {
  // ...
}
```

## 2) JSDoc for a JS function (with type annotations)

```js
/**
 * Build a retry plan from network error metadata.
 * @param {{code: string, attempt: number}} errorInfo Retry input.
 * @returns {{shouldRetry: boolean, waitMs: number}} Retry decision.
 */
function createRetryPlan(errorInfo) {
  // ...
}
```

## 3) Inline comments for branches and exception handling

```ts
// Do not retry immediately after a cache miss.
// Retrying in the same event loop tends to trigger the external API rate limit more often.
if (!cached && justFailed) {
  return BACKOFF_REQUIRED;
}
```

## 4) Order-dependent logic comments

```ts
// Order matters: sanitize -> validate -> persist.
// Calling validate first creates false negatives on fields removed by sanitize.
const sanitized = sanitize(payload);
validate(sanitized);
persist(sanitized);
```

## 5) Call-site parameter name comments

```ts
scheduleJob(userId, /* shouldNotify= */ false, /* delayMs= */ 30_000);
```

## Quick Anti-pattern Check

- repeats the code verbatim: remove it
- says only "temporary" with no reason: rewrite it
- no longer matches the current logic: update immediately
- long but missing the decision rationale: compress it
