# Question Flow

Ask in two rounds. Use at most three questions per round.

## Round A: Goal Alignment

1. What exactly is the final deliverable? For example: a code change, document, report, or test.
2. How should completion be judged? For example: passing tests, a specific UX outcome, or a performance metric.
3. What is the scope boundary? For example: included and excluded targets, or editable paths.

## Round B: Risk And Exceptions

1. Which condition is most likely to cause problems?
2. What fallback is acceptable if the task fails? For example: a partial result or alternate path.
3. What compatibility requirements must hold with the current behavior?

## Optional Deepening (only when needed)

- Are there data quality issues such as missing values, duplicates, or format mismatches?
- Are there policy or compliance constraints such as security, privacy, or licensing?
- Are there time or cost limits such as a deadline in minutes or API call limits?

## Stop Rule

Stop asking questions and move to prompt generation when these conditions are satisfied:

- the goal, completion criteria, and scope boundary are clear
- at least one key risk and its response rule are defined
- the context access boundary is specified
