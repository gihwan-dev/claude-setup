# Decision Catalog

This is the classification table used by `bootstrap-project-rules` when locking implementation rules.
Fill in facts that can be confirmed by exploration first, then ask only for the items that are truly necessary.

## Locked now

These are the items that would destabilize the implementation surface, directory structure,
or validation path if left undecided now.

- runtime / language (`node`, `python`, `typescript`)
- framework / app shell (`next`, `react`, `fastapi`, `django`, `cli`)
- package manager / workspace model
- lint / format / typecheck / test stack
- default state/data-fetching strategy
- default styling / design-system direction
- module boundary / folder ownership
- validation commands / definition of done

## Deferred

These are optional libraries that are hard to judge well before a concrete feature slice exists.
In the document, record `Decision`, `Why deferred`, `Trigger`, and `Needed input` together.

- rich table / chart / editor / animation libraries
- analytics / monitoring / experiment SDK
- optional utilities such as form helpers, cache helpers, and image helpers
- specific auth adapter / payment SDK / vendor SDK

## Banned/Avoid

These options conflict with the current architecture, validation contract, or maintenance cost profile.

- tooling that conflicts with the existing package manager
- a duplicate state/data layer that overlaps an existing responsibility
- a second styling stack that conflicts with the design system
- bypass patterns that weaken the validation command

## Question Filter

Ask questions only when one of the following is true.

- It belongs in `Locked now`, but exploration alone cannot confirm it.
- Deferring it would prevent the current blocker from being resolved.

Limit questions to 1-3 items, and ask only about choices that would actually change the resulting documents.
