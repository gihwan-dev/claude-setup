# React State Anti-Patterns

## Common Smells

- Re-storing derivable values via `useEffect` + `setState`
- Expressing impossible states through combinations of boolean flags
- Routing event responses through effect chains
- Letting multiple `setState` calls collapse into implicit chained transitions
- Managing complex transitions implicitly without a `discriminated union`
- Letting new states disappear silently because `exhaustive` checks are missing

## Better Defaults

- Compute values during render when possible instead of storing them.
- Make state transitions explicit, and consider a reducer or state model when transitions multiply.
- Treat effects with suspicion unless they synchronize with an external system.
