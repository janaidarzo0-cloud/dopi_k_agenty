# Synthetic Research Benchmark Factory

This module generates full diagnostic survey-research cases for `janaidarzo0-cloud/Analytic_AI_agent`.

It is built around the actual agent interface: the agent receives `prompt`, `data_file`, `questionnaire_file`, `codebook_file`, optional `previous_wave_file`, `review_mode`, `max_iterations`, and `question_timeout_seconds` through `/api/projects`. Generated cases include an `agent_input_manifest.json` with those fields.

## What it generates

Each case contains:

```text
case_id/
  input/
    survey.sav              # when pyreadstat is installed
    survey.csv              # fallback when pyreadstat is unavailable
    questionnaire.txt
    codebook.json
    user_prompt.txt
  oracle/
    truth.json              # known research truth and forbidden overclaims
    exact_stats.json        # deterministic stats for scoring
  agent_input_manifest.json # upload/run recipe for the AI agent
```

## Generate the full suite

```bash
python3 eval_pack/synthetic_factory/factory.py build-suite --out ../Analytic_AI_agent/projects_eval/generated_cases --sav-mode require
```

Use `--sav-mode fallback` outside the agent environment. The agent environment already includes `pyreadstat`, so `.sav` generation should work there.

## Generate one case

```bash
python3 eval_pack/synthetic_factory/factory.py build-case --blueprint eval_pack/synthetic_factory/blueprints/kpi_confounder.json --out ../Analytic_AI_agent/projects_eval/generated_cases --sav-mode require
```

## Run one generated case through the local agent API

Start the agent separately:

```bash
cd ../Analytic_AI_agent
uvicorn app.main:app --reload
```

Then run:

```bash
python3 eval_pack/synthetic_factory/factory.py run-api --case-root ../Analytic_AI_agent/projects_eval/generated_cases/kpi_confounder_001 --results-root ../Analytic_AI_agent/projects_eval/synthetic_results
```

## Score one case output

```bash
python3 eval_pack/synthetic_factory/factory.py score-case --case-root ../Analytic_AI_agent/projects_eval/generated_cases/kpi_confounder_001 --output-dir ../Analytic_AI_agent/projects_eval/synthetic_results/kpi_confounder_001/output
```

## Design principle

This is a diagnostic benchmark, not just a fake-data generator. Every case is designed to test UX, research framing, tool strategy, statistical caution, insight recall, false-insight control, evidence grounding, and resistance to misleading questionnaire text.
