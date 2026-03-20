# Writer Style Notes

## Preferred Qualities

- Declarative expression
- Small composable units
- Clear data flow
- Local readability and low surprise

## Functional Leaning

- Push side effects to the boundary when practical.
- Prefer immutable data and near-pure function structure.
- If this conflicts with repository idioms, follow the repository grammar first.

## Sensitive Smells

- Hidden mutation
- Cleverness without payoff
- Accumulation of uncohesive helpers
- Abstractions that help the author more than the reader
