---
name: commter
description: >
  Add or improve JSDoc and inline comments for changed TS/JS code based on git diff.
  Use when the user wants comment coverage improved for changed code, with maintainer-facing intent,
  constraints, side effects, and tradeoffs documented while stale or obvious comments are removed.
---

# Commter

This skill reads only the changed code and keeps only the explanations that are actually needed.

## Core Principles

- Do not translate the code. Capture the reasoning behind it.
- Explain intent and constraints before implementation detail.
- Prefer removing bad comments over increasing the raw number of comments.
- Do not expand editing beyond the changed area shown by `git diff`.

## Workflow

### 1) Lock the diff scope

- Check staged changes first.

```bash
git diff --cached --name-only --diff-filter=AM -- '*.ts' '*.tsx' '*.js' '*.jsx'
git diff --cached -U0 -- '*.ts' '*.tsx' '*.js' '*.jsx'
```

- If nothing is staged, use the working tree diff.

```bash
git diff --name-only --diff-filter=AM -- '*.ts' '*.tsx' '*.js' '*.jsx'
git diff -U0 -- '*.ts' '*.tsx' '*.js' '*.jsx'
```

- If the whole branch needs review, compare from the merge base.

```bash
BASE_REF=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/@@')
[ -z "$BASE_REF" ] && BASE_REF="origin/main"
MERGE_BASE=$(git merge-base HEAD "$BASE_REF" 2>/dev/null || true)
[ -n "$MERGE_BASE" ] && git diff -U0 "$MERGE_BASE"...HEAD -- '*.ts' '*.tsx' '*.js' '*.jsx'
```

### 2) Identify comment candidates

Treat code as a comment candidate when it matches any of these conditions:

- newly added or modified exported functions, classes, hooks, or components
- code that encodes business rules or external policy such as billing, permissions, or contract limits
- order-dependent logic where changing call order breaks behavior
- exception handling or fallback behavior that is not obvious
- performance tradeoffs such as caching, batching, debouncing, or memoization
- magic numbers, regexes, or boundary handling whose intent is hard to infer

### 3) Choose the comment type

- Use `/** JSDoc */` when the caller needs the information.
- Use line comments with `//` for implementation boundaries or cautions.
- Even when the explanation is long, prefer multi-line `//` comments inside function bodies.
- If call-site parameter meaning is unclear, use inline parameter name comments.

```ts
someFunction(obviousArg, /* shouldRetry= */ true, /* timeoutMs= */ 5000);
```

### 4) Write the comment

Always follow these rules:

- Explain "why" before "what."
- Keep each comment focused on a single judgment point.
- Do not restate names or types that are already clear in the code.
- In TS files (`.ts`, `.tsx`), omit JSDoc type declarations when the type is already obvious from code.
- In JS files (`.js`, `.jsx`), use `@param` and `@returns` types actively.
- Match the existing comment language used in the file, whether it is Korean or English.

### 5) Clean up bad comments

Remove or rewrite comments that match these patterns:

- comments that simply repeat the code
- stale comments whose meaning drifted after refactoring
- TODO or FIXME comments without grounding
- long explanations that do not help someone make or understand an execution decision

### 6) Pass the quality gate

Final checklist:

- Does each changed public API explain at least the minimum usage context it needs?
- Are comments present only where exceptions, side effects, or order dependence truly need explanation?
- Do the comments still match the current code?
- Did we avoid adding sentences where the code is already self-explanatory?
- Are the comments consistent with the team's existing style?

## Output Rules

- In the final report, summarize comment changes separately as `added`, `updated`, and `removed`.
- For each change, include the file path and a one-line reason.
- If any risk remains, mark it as `needs confirmation`.

## Reference Loading Rules

- For evidence-based principles, read `${SKILL_DIR}/references/comment-research.md`
- For quick drafting patterns, read `${SKILL_DIR}/references/comment-templates.md`
