# Analytical Quality Policy

This policy defines what the eval suite rewards. It can later be copied into system prompts or critic prompts, but for now it is a standalone contract.

## 1. Research framing

The agent must first infer the research type:

- descriptive survey,
- KPI/driver study,
- segmentation study,
- wave comparison,
- open-text exploration,
- mixed study.

It must not force a KPI when the study is descriptive.

## 2. Evidence discipline

Every final finding must be linked to computed evidence. Unsupported findings are allowed only as explicitly marked hypotheses, not as conclusions.

Required fields for a strong finding:

- claim,
- evidence_ids,
- base or sample size,
- metric and comparison,
- uncertainty/significance status,
- implication,
- caution if needed.

## 3. Statistical restraint

The agent must downgrade conclusions when:

- base n is small,
- p-value is not significant,
- effect size is tiny,
- weights reduce effective sample size,
- a plausible confounder is untested,
- the signal appears only in one unstable slice.

## 4. Senior analyst behavior

Good analysis is not a table dump. It must produce:

- a through-line,
- 3-6 meaningful themes,
- segment roles,
- implication for decisions,
- limitations and next research questions.

## 5. Adaptive depth

The agent should deepen only when needed. It should not spend expensive iterations on weak or irrelevant branches.

Depth ladder:

1. broad profile,
2. target-relevant first pass,
3. signal ranking,
4. robustness checks for candidate executive-summary claims,
5. synthesis and stop.

## 6. Safety and privacy

Respondent-level rows and raw open answers should stay local. LLM-facing summaries should be aggregate, redacted, or thematic.

## 7. Evaluation principle

A change is accepted only if it improves measured quality without unacceptable runtime or cost regression.
