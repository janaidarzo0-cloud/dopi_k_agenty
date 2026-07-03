# AI Survey Analyst Eval Pack

This repository contains a standalone eval pack for `janaidarzo0-cloud/Analytic_AI_agent`.

It is designed as a non-invasive quality layer: no production files from the agent are changed here. The pack contains eval cases, scoring code, rubrics, policy files, prompt templates, and CI examples for measuring analytical quality before changing the agent.

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

## Main files

- `EVAL_UPGRADE_BLUEPRINT.md` — roadmap and design proposal.
- `policy.md` — quality contract for analytical reasoning.
- `eval_suite/manifest.json` — case registry and thresholds.
- `scoring_scripts/evaluate_outputs.py` — stdlib-only scorer.
- `scoring_scripts/make_synthetic_data.py` — synthetic dataset generator.
- `prompt_templates/` — policies for future prompt upgrades.
- `ci/eval_quality.yml` — optional GitHub Actions workflow template.

## Core acceptance rule

A change is only an improvement if it raises analytical quality while preserving evidence grounding, numeric faithfulness, caveat honesty, reproducibility, and runtime discipline.
