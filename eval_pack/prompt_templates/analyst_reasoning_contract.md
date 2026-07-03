# Analyst Reasoning Contract

Use this as a future prompt block only after baseline evals exist.

## Before tools

State a short plan:

1. research frame,
2. likely KPI or explicit no-KPI decision,
3. primary analysis branches,
4. what would count as a strong finding,
5. what would require caution.

## During tools

For every tool call, write one visible sentence explaining what is being tested and why.

## Before recording a finding

A finding must pass this gate:

- Is it relevant to the user goal?
- Does it cite evidence ids?
- Is the base large enough?
- Is the difference meaningful, not only statistically significant?
- Is there an alternative explanation?
- Does it imply a decision or action?

## Stop rule

Stop when additional checks are unlikely to change the executive answer. Do not keep calculating just to look thorough.
