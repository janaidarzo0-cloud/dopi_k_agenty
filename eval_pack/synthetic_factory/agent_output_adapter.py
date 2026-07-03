#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

OUTPUT_FILES = [
    "analysis_summary.json",
    "insights.json",
    "evidence.jsonl",
    "critic_assessment.json",
    "skeptic_review.json",
    "research_memory.json",
    "analyst_brief.json",
]
LOG_FILES = ["events.jsonl"]


def copy_agent_project(agent_project_dir: Path, case_id: str, results_root: Path) -> Path:
    target = results_root / case_id / "output"
    target.mkdir(parents=True, exist_ok=True)
    for name in OUTPUT_FILES:
        src = agent_project_dir / "output" / name
        if src.exists():
            shutil.copy2(src, target / name)
    for name in LOG_FILES:
        src = agent_project_dir / "logs" / name
        if src.exists():
            shutil.copy2(src, target / name)
    state = agent_project_dir / "state.json"
    if state.exists():
        shutil.copy2(state, target / "project_state.json")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy outputs from Analytic_AI_agent/projects/<project_id> into eval results layout.")
    parser.add_argument("--agent-project-dir", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--results-root", type=Path, default=Path("projects_eval/synthetic"))
    args = parser.parse_args()
    out = copy_agent_project(args.agent_project_dir, args.case_id, args.results_root)
    print(json.dumps({"case_id": args.case_id, "output_dir": str(out)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
