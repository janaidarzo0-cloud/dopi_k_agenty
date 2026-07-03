# Eval Upgrade Blueprint for AI Survey Analyst

## Goal

Build a measurable quality system for `Analytic_AI_agent` that raises the agent from a tool-using survey runner to a senior research analyst. The target is not only higher factual correctness, but better research judgment: goal framing, hypothesis selection, robustness checks, insight quality, caveat honesty, and client-ready synthesis.

This package deliberately lives outside production code. It lets the team evaluate changes before touching prompts, tools, models, or orchestration.

## North Star

The agent should produce conclusions that a senior marketing research consultant would accept after checking the base, questionnaire, significance, alternative explanations, and business implication.

A run is good only when it satisfies all of these:

1. The answer follows the user's research objective.
2. The agent chooses a sensible analysis plan before calculating.
3. Claims cite real evidence artifacts.
4. Numbers in the narrative are traceable to computed evidence.
5. Small bases, non-significant differences, and weak signals are clearly downgraded.
6. The report contains a coherent story, not a list of tables.
7. Runtime stays bounded by an adaptive-depth policy.

## Highest-leverage upgrades

### P0 — Eval harness before agent changes

Add structured eval cases and score existing outputs. This is the cheapest improvement because it makes every future prompt/tool change measurable.

Expected effect: high.  
Latency effect: none.  
Implementation cost: low.  
Success criterion: scorer produces stable JSON/Markdown summaries for at least 5 cases.

### P1 — Analyst quality rubric

Judge final outputs on eight dimensions:

- objective fit,
- evidence grounding,
- statistical discipline,
- robustness and alternative explanations,
- insight depth,
- business implication,
- caveat honesty,
- structure and synthesis.

Expected effect: high.  
Latency effect: none for offline scoring; optional judge pass later.  
Implementation cost: low.

### P2 — Golden synthetic cases

Use compact synthetic datasets where the true story is known. These cases should include:

- descriptive survey with no KPI,
- KPI survey with a true driver and a confounder,
- multi-response block,
- weak/noisy signal where the correct answer is caution,
- adversarial questionnaire text containing misleading instructions that must be ignored.

Expected effect: high.  
Latency effect: low because datasets are small.  
Implementation cost: medium.

### P3 — Adaptive depth policy

Replace fixed deep analysis with a budgeted decision ladder:

1. Always profile and map.
2. Always run minimum descriptive coverage.
3. Deepen only when the first pass finds a strong, relevant, sufficiently based signal.
4. Run robustness only for candidate insights that may enter the executive summary.
5. Stop when new evidence no longer changes the answer.

Expected effect: high.  
Latency effect: positive to neutral.  
Implementation cost: medium.

### P4 — Evidence-to-claim contract

Every final finding should expose:

- claim,
- evidence_ids,
- base n,
- metric,
- comparison group,
- significance/uncertainty,
- business implication,
- caution label.

Expected effect: very high.  
Latency effect: none.  
Implementation cost: medium.

### P5 — Critic and skeptic specialization

The current project already has critic and skeptic artifacts. The next upgrade is to make them scoreable:

- critic checks coverage: did it test the strongest claims?
- skeptic checks validity: did it weaken/remove claims with weak evidence?
- presentation QA checks delivery: are slides client-ready and supported?

Expected effect: medium-high.  
Latency effect: low if critic uses deterministic checks first and LLM only on flagged findings.  
Implementation cost: medium.

## Eval case design

Each eval case has:

- case_id,
- dataset path,
- optional questionnaire/codebook path,
- user_goal,
- expected_behavior,
- forbidden_behavior,
- golden_signals,
- required_artifacts,
- max_runtime_seconds,
- scoring_weights.

The current pack includes machine-readable case files under `eval_suite/cases/`.

## Scoring model

Use two layers.

### Layer 1: deterministic artifact scoring

This is implemented in `scoring_scripts/evaluate_outputs.py` and checks:

- artifacts present,
- evidence count,
- findings cite evidence,
- unsupported number warnings,
- critic/skeptic artifacts present,
- privacy memory exists,
- caution terms appear when expected,
- forbidden terms are absent.

### Layer 2: optional expert judge

Later, add a model-as-judge or human review using `prompt_templates/judge_rubric.md`. Do not rely only on a judge; it must sit on top of deterministic checks.

## Runtime discipline

Do not reward the agent for simply doing more work. The suite should track:

- evidence count,
- number of tool calls if available,
- elapsed time if available,
- whether extra checks changed final findings,
- whether the run stopped after convergence.

Target: most synthetic evals should complete in minutes, not hours.

## Recommended acceptance thresholds

Initial gate:

- total_score >= 70,
- evidence_grounding >= 80,
- numeric_faithfulness >= 90,
- caveat_honesty >= 70,
- no critical forbidden behavior.

Strong gate:

- total_score >= 82,
- evidence_grounding >= 90,
- numeric_faithfulness >= 95,
- insight_quality >= 75,
- critic_coverage >= 75.

## Roadmap

### Week 1

- Run this pack against current outputs.
- Add 3-5 real anonymized historical studies as private evals.
- Tune deterministic scorer weights.

### Week 2

- Add benchmark dashboards.
- Introduce failure taxonomy.
- Require every agent prompt/tool change to include before/after eval results.

### Week 3

- Add model judge only for qualitative dimensions.
- Add pairwise comparison between old and new agent outputs.
- Add latency/cost regression gates.

## Failure taxonomy

Use these labels in eval reports:

- `unsupported_claim`: finding lacks evidence id.
- `number_not_in_evidence`: narrative number not traceable.
- `forced_kpi`: agent invented KPI in descriptive study.
- `overclaims_small_base`: small n treated as stable fact.
- `missed_confounded_signal`: top-line pattern not checked against confounder.
- `table_dump`: report lists tables without synthesis.
- `weak_caveat`: uncertainty hidden or softened too much.
- `wrong_business_frame`: technically correct analysis that misses the client question.
- `slow_overanalysis`: many tools without material improvement.

## What not to do

- Do not optimize only for more tool calls.
- Do not let the LLM judge replace deterministic checks.
- Do not accept a prettier report if evidence discipline gets worse.
- Do not change production prompts before there is a baseline.

## Implementation note

This pack is intentionally stdlib-first. It should run without OpenAI keys and without the app running. It scores exported project artifacts. That makes it safe for CI and for local regression checks.
