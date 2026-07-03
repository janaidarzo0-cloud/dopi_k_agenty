from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CasePaths:
    root: Path
    input_dir: Path
    oracle_dir: Path
    data_file: Path
    questionnaire_file: Path
    codebook_file: Path
    user_prompt_file: Path
    truth_file: Path
    exact_stats_file: Path
    agent_manifest_file: Path


@dataclass
class GeneratedCase:
    case_id: str
    research_type: str
    paths: CasePaths
    oracle: dict[str, Any]
    exact_stats: dict[str, Any]
    row_count: int
    notes: list[str] = field(default_factory=list)


def build_case_paths(root: Path, case_id: str, data_ext: str = ".sav") -> CasePaths:
    case_root = root / case_id
    input_dir = case_root / "input"
    oracle_dir = case_root / "oracle"
    return CasePaths(
        root=case_root,
        input_dir=input_dir,
        oracle_dir=oracle_dir,
        data_file=input_dir / f"survey{data_ext}",
        questionnaire_file=input_dir / "questionnaire.txt",
        codebook_file=input_dir / "codebook.json",
        user_prompt_file=input_dir / "user_prompt.txt",
        truth_file=oracle_dir / "truth.json",
        exact_stats_file=oracle_dir / "exact_stats.json",
        agent_manifest_file=case_root / "agent_input_manifest.json",
    )
