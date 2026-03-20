# Cognitive Principles for Code Explanation

## Core Principles

1. Protect working memory
- Limit how many elements the reader must process at once.
- Do not treat a long chain as one block; break it into groups of 3-5.

2. Prefer chunking
- Group by units of intent, not by raw lines of code.
- Give chunks role names such as `validation`, `decision`, `execution`, and `cleanup`.

3. Activate schemas
- Before the explanation starts, state the problem this code is trying to solve.
- Connect it to familiar patterns such as a pipeline or a state machine.

4. Externalize the model
- Use tables and diagrams to reduce mental tracking load.
- Do not explain branching, state, and data movement with text alone.

5. Reveal progressively
- Present the whole picture first, then the main path, then the exception paths.
- Do not dump every exception at the beginning.

6. Reinforce recall
- End with a check question or debugging checkpoint.
- Help the reader reconstruct the logic on their own.

## Links To How Programmers Think

- Code comprehension difficulty is often more sensitive to "how many states must be tracked at once" than to raw line count.
- Ambiguous variable names increase the cost of reconstructing meaning.
- Translating an unfamiliar structure into a familiar pattern speeds up understanding.
- A summary-first, detail-later order reduces early cognitive load significantly.

## Practical Checklist

- Does the explanation introduce no more than five new concepts at once?
- Are the branching criteria clearly expressed in sentences?
- Did you connect cause and effect with a diagram when they are far apart in the code?
- Did you provide aliases for identifiers that require interpretation?
- Does the ending include a self-check the reader can use?
