---
name: commit
description: >
  Generate conventional commit messages with logical diff splitting. Use when the
  user asks to commit changes, save work, "커밋해줘", or create a conventional commit.
  Do not use for amending, rebasing, or cherry-picking operations.
allowed-tools: Bash, Read, Grep, Glob
---

# Commit

Use this skill to create structured commits with conventional commit messages. Husky hooks run at commit time, so extra pre-commit verification steps are not required here.

1. If the user specifies `--no-verify`, pass it through and skip hook execution.
2. Check staged files with `git status`.
3. If nothing is staged, automatically stage all modified and new files with `git add`.
4. Run `git diff` to understand what will be committed.
5. Analyze the diff and decide whether it contains multiple logically distinct changes.
6. If multiple distinct changes are present, suggest splitting them into separate commits.
7. For each commit, or for the single combined commit when no split is needed, generate a conventional commit message.

## Commit Best Practices

- **Pre-commit validation**: confirm the code is linted and passes type checks.
- **Atomic commits**: each commit should contain only related changes with a single purpose.
- **Split large changes**: separate changes that cover multiple concerns into different commits.
- **Conventional commit format**: use `<type>(<scope>): [#issue] <description>`, where `type` is one of:
  - `feat`: new feature
  - `fix`: bug fix
  - `docs`: documentation change
  - `style`: code style change such as formatting
  - `refactor`: code change that is neither a bug fix nor a new feature
  - `perf`: performance improvement
  - `test`: test addition or update
  - `chore`: build process, tooling, or maintenance work
  - `ci`: CI/CD related change
  - `revert`: revert a previous change
- **Write commit titles in Korean**: keep the description clear and specific.
- **Keep the first line concise**: target 72 characters or fewer.
- **Do not use emoji**: stick to the `type(scope):` format only.

## Commit Splitting Guidelines

When analyzing the diff, consider splitting commits using these criteria:

1. **Different concerns**: unrelated areas of the codebase changed together.
2. **Different change types**: features, fixes, refactors, and docs are mixed together.
3. **File patterns**: different categories of files changed, such as source code and docs.
4. **Logical grouping**: changes are easier to review or understand as separate units.
5. **Size**: the change set is large enough that splitting would make intent clearer.

## Examples

Example commit messages shown in English for structure reference. In actual use, keep the final commit message in Korean:

- `feat(react): [#52] Add user authentication system`
- `fix(react): [#63] Resolve memory leak in rendering pipeline`
- `docs(docs): Update API documentation for the new endpoint`
- `refactor(react): [#45] Simplify parser error handling`
- `test(react): [#52] Add unit tests for RowClick feature`
- `chore(root): Improve developer tooling setup flow`
- `perf(react): [#45] Improve grouped header performance`

Commit split example:

- First commit: `feat(react): [#52] Add type definitions for the new solc version`
- Second commit: `docs(docs): Update documentation for the new solc version`
- Third commit: `chore(deps): Update package.json dependencies`
- Fourth commit: `test(react): [#52] Add unit tests for the new feature`

## Command Option

- `--no-verify`: skip commit-time validation hooks such as lint and typecheck.

## Important Notes

- By default, commit-time validation such as `pnpm lint` and `pnpm typecheck` runs to protect code quality.
- If validation fails, ask whether to proceed with the commit or fix the issues first.
- If specific files are already staged, commit only those files.
- If no files are staged, automatically stage all modified and new files.
- Generate the commit message from the detected changes.
- Review the diff before committing to decide whether multiple commits would be better.
- If multiple commits are recommended, help the user stage and commit them separately.
- Always review the commit diff so the message matches the actual change.
- **Commit messages must be written in Korean.**
- **Never use emoji.**
- **Keep each body line at 100 characters or fewer.**
