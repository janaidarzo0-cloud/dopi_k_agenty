# Adaptive Depth Policy

The agent should not maximize analysis volume. It should maximize decision value per unit of time.

## Minimum pass

- data dictionary,
- profile and quality issues,
- objective-aligned frequencies/crosstabs,
- at least one synthesis checkpoint.

## Deepen only when

- signal is relevant to objective,
- base is sufficient,
- effect is meaningful,
- result could affect a recommendation,
- uncertainty can be reduced by one targeted check.

## Do not deepen when

- the signal is irrelevant,
- base is too small,
- the difference is tiny,
- another recent check already answered the question,
- runtime budget is close to limit.

## Stop when

- top findings are stable,
- new evidence does not alter recommendations,
- remaining branches are low value,
- critic has no high-priority unresolved challenge.
