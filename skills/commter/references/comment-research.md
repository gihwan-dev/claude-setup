# Good Comment Research Summary

This document captures the evidence behind the comment standards used by the `commter` skill.

## Key Conclusions

1. Comments should communicate intent, not translate the implementation.
- The Google TypeScript Style Guide recommends documentation that explains design and intent rather than comments that restate the code.

2. Public APIs and complex logic should be documented with JSDoc or comments.
- The Google guide expects top-level exports and complex functions to be documented.
- Prioritize constraints, side effects, and exceptions that the caller needs to understand.

3. JSDoc tags should focus on describing the contract.
- The official JSDoc docs use `@param` and `@returns` to clarify argument meaning and return meaning.
- TypeScript documents which JSDoc tags are supported, so documentation should center on supported tags.

4. Good comment quality is judged by consistency, completeness, and readability.
- A systematic literature review identifies consistency, completeness, and readability as core attributes of comment quality.
- In practice, that means the comment should match the latest code, include the missing context, and stay easy to read.

5. Unnecessary comments raise maintenance cost.
- The Linux kernel coding style warns that bad comments create confusion and recommends explaining why the code works this way, not just what it does.

## Actionable Rules

- Before adding a comment: improve naming or extract a function first if code structure can explain the idea on its own.
- When adding a comment: include at least one of these items, `why`, `constraint`, `side effect`, or `decision rationale`.
- When updating a comment: if a change inside the diff makes it inaccurate, fix it immediately.
- When removing a comment: delete repeated code narration, stale TODOs, or misleading explanations.

## Reference Links

- Google TypeScript Style Guide (Comments & Documentation):
  [https://google.github.io/styleguide/tsguide.html#comments-and-documentation](https://google.github.io/styleguide/tsguide.html#comments-and-documentation)
- JSDoc `@param`:
  [https://jsdoc.app/tags-param](https://jsdoc.app/tags-param)
- JSDoc `@returns`:
  [https://jsdoc.app/tags-returns](https://jsdoc.app/tags-returns)
- TypeScript Handbook - JSDoc Reference:
  [https://www.typescriptlang.org/docs/handbook/jsdoc-supported-types.html](https://www.typescriptlang.org/docs/handbook/jsdoc-supported-types.html)
- SLR: Software Code Comment Quality Assessment (2024):
  [https://www.sciencedirect.com/science/article/pii/S0950584924001580](https://www.sciencedirect.com/science/article/pii/S0950584924001580)
- Linux kernel coding style (Commenting):
  [https://docs.kernel.org/process/coding-style.html#commenting](https://docs.kernel.org/process/coding-style.html#commenting)
