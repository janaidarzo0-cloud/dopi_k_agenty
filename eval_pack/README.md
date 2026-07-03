# AI Survey Analyst Eval Pack

This repository contains a standalone eval pack for `janaidarzo0-cloud/Analytic_AI_agent`.

It is designed as a non-invasive quality layer: no production files from the agent are changed here. The pack contains eval cases, scoring code, rubrics, policy files, prompt templates, synthetic research generators, and CI examples for measuring analytical quality before changing the agent.

## Quick start

```bash
bash eval_pack/run_eval.sh --self-test
bash eval_pack/run_eval.sh --results-root projects_eval/latest
```

Expected result folders:

```text
projects_eval/latest/<case_id>/output/analysis_summary.json
projects_eval/latest/<case_id>/output/evidence.jsonl
```

## Synthetic research factory

Generate a full diagnostic benchmark suite for the AI agent located in a neighboring directory:

```bash
python3 eval_pack/synthetic_factory/factory.py build-suite \
  --out ../Analytic_AI_agent/projects_eval/generated_cases \
  --sav-mode require
```

Use `--sav-mode fallback` when `pyreadstat` is unavailable. Each generated case includes:

```text
case_id/
  input/survey.sav or input/survey.csv
  input/questionnaire.txt
  input/codebook.json
  input/user_prompt.txt
  oracle/truth.json
  oracle/exact_stats.json
  agent_input_manifest.json
```

Run one generated case through a locally running agent API:

```bash
python3 eval_pack/synthetic_factory/factory.py run-api \
  --case-root ../Analytic_AI_agent/projects_eval/generated_cases/kpi_confounder_001
```

Score the output against the oracle:

```bash
python3 eval_pack/synthetic_factory/factory.py score-case \
  --case-root ../Analytic_AI_agent/projects_eval/generated_cases/kpi_confounder_001 \
  --output-dir ../Analytic_AI_agent/projects_eval/synthetic_results/kpi_confounder_001/output
```

## Main files

- `EVAL_UPGRADE_BLUEPRINT.md` — roadmap and design proposal.
- `policy.md` — quality contract for analytical reasoning.
- `eval_suite/manifest.json` — case registry and thresholds.
- `scoring_scripts/evaluate_outputs.py` — stdlib-only scorer.
- `scoring_scripts/make_synthetic_data.py` — simple synthetic dataset generator.
- `synthetic_factory/` — full diagnostic `.sav + questionnaire + prompt + oracle` case factory.
- `prompt_templates/` — policies for future prompt upgrades.
- `ci/eval_quality.yml` — optional GitHub Actions workflow template.

## Core acceptance rule

A change is only an improvement if it raises analytical quality while preserving evidence grounding, numeric faithfulness, caveat honesty, reproducibility, and runtime discipline.
