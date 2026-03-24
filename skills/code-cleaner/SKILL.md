---
name: code-cleaner
description: >
  Remove unused code (dead exports, functions, types, console.log) from changed
  TS/JS files via git diff analysis. Use for "unused-code cleanup", "dead code",
  "code cleanup", or post-AI cleanup requests. Do not use on non-TS/JS files,
  for full-codebase analysis without git changes, or for logic refactoring.
allowed-tools: Bash, Read, Grep, Glob, Edit
---

# Unused Code Cleaner

Automatically clean up unnecessary code that often appears after AI-generated changes.

## Workflow

### 1. Identify changed files

```bash
git diff --name-only HEAD
```

Including staged files:
```bash
git diff --name-only HEAD --staged
```

Comparing a specific commit or branch:
```bash
git diff --name-only <base>..<target>
```

### 2. Filter TS/JS files

Extension filter: `.ts`, `.tsx`, `.js`, `.jsx`

Exclude:
- `node_modules/`
- `.d.ts` files (type declarations)
- config files (`*.config.ts`, `*.config.js`)

### 3. Analyze and edit per file (adaptive parallelization)

**Analysis strategy by changed file count:**

#### 2 files or fewer: sequential analysis

Read each file directly and remove the patterns below.

#### 3 files or more: parallel analysis -> sequential edits

**3-A: parallel analysis**

Analyze unused code in each file as independent parallel analysis tasks.

```text
Analyze the following file for unused code. DO NOT modify any files.
Only report what you find.

File to analyze: [file path]

Check for these patterns:
1. Unused exports: Run `git diff HEAD -- [file]` to find newly added exports,
   then search the project for imports of each export name.
2. Unused functions: Functions defined but never called within the file or project.
3. Unused types/interfaces: Type declarations not referenced anywhere.
4. Commented code blocks: Code blocks that are commented out (preserve TODO/FIXME/NOTE comments).
5. Orphan console.log: Debugging console.log statements.

For unused exports, verify by searching the project:
- Check for dynamic imports: import() patterns
- Check barrel files (index.ts) for re-exports
- Check if used in test files

Output a JSON-like report:
{
  "file": "[file path]",
  "findings": [
    {"type": "unused_export", "name": "...", "line": N, "confidence": "high/medium"},
    {"type": "unused_function", "name": "...", "line": N, "confidence": "high/medium"},
    ...
  ]
}

Only report findings with medium or high confidence.
```

Wait until analysis is complete for all files.

**3-B: sequential edits**

After the orchestrator collects all analysis results:

1. Review each finding and remove false positives, especially cross-file dependency mistakes
2. Edit files sequentially starting with `high` confidence findings
3. Re-check `medium` confidence findings once more before editing

**The orchestrator must perform the actual edits directly** to avoid concurrent file-edit conflicts.

#### Removal targets (things lint / TS may miss)

| Pattern | Description |
|------|------|
| Unused exports | Newly added exports that are not imported anywhere in the project |
| Unused functions | Functions that are defined but never called |
| Unused types/interfaces | Type declarations that are never referenced |
| Commented code blocks | Commented-out code blocks (keep explanatory comments) |
| Orphan console.log | `console.log` added only for debugging |

#### How to detect unused exports

1. Identify newly added exports with `git diff`:
```bash
git diff HEAD -- <file> | grep "^+" | grep -E "export (const|function|class|type|interface|enum)"
```

2. Check whether each export is imported anywhere in the project:
```bash
grep -r --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" "import.*<export_name>.*from" .
grep -r --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" "{ <export_name>" .
```

3. If it is not imported anywhere, delete it

#### Cautions

- Search for dynamic import usage patterns such as `import()`
- Trace cases where the symbol is re-exported from a barrel file (`index.ts`)
- Keep TODO, FIXME, NOTE, and explanatory comments

### 4. Apply the edits

After editing, print a summary of the changes:
- Number of removed imports
- Number of removed variables / functions
- Number of removed lines of code
- For parallel analysis, a summary of the analysis mode: file count and parallel agent count

## Example usage

```text
User: clean up the unused code from what I just changed
User: look at git diff and remove unnecessary code
User: dead code cleanup
```
