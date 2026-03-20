# Korean Naming Playbook

## Purpose

Provide Korean aliases that improve understanding without removing the original identifiers.

## Alias Writing Rules

- Always show the original identifier alongside the alias. Example: `calculateAdjustedPrice` plus a Korean alias meaning "adjusted price calculation".
- Preserve the functional meaning and do not encode the implementation method into the alias.
- Expand abbreviations when possible. Example: `ctx` should become a Korean alias meaning "execution context".
- Keep a verb + object shape when the original name uses it. Example: `fetchUserProfile` should become a Korean alias meaning "fetch user profile".

## Recommended Translation Patterns

| Pattern | Example Original | Recommended Korean Alias Meaning |
| --- | --- | --- |
| `get*` | `getSession` | session lookup |
| `fetch*` | `fetchOrders` | fetch order list |
| `load*` | `loadConfig` | load configuration |
| `build*` | `buildPayload` | build payload |
| `create*` | `createInvoice` | create invoice |
| `update*` | `updateProfile` | update profile |
| `delete*` | `deleteComment` | delete comment |
| `validate*` | `validateInput` | validate input |
| `handle*` | `handleSubmit` | handle submission |
| `is*`/`has*` | `isExpired` | whether it is expired |

## Translations To Avoid

- Do not use a broad generic word alone. Example: an alias meaning only "process data" gives no context.
- Do not encode implementation detail. Example: an alias meaning "sort with quicksort" is too specific.
- Do not use slang or team-internal jargon.

## Explanation Table Template

```md
| Original | Korean Alias | Role | Notes |
| --- | --- | --- | --- |
| `calculateFee` | [natural Korean alias meaning fee calculation] | computes order fees | depends on tax policy |
```
