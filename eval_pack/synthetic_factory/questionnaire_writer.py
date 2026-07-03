from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_questionnaire(path: Path, blueprint: dict[str, Any], metadata: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append(f"# Questionnaire for {blueprint['case_id']}")
    lines.append("")
    lines.append(f"Research type: {blueprint.get('kind', 'unknown')}")
    lines.append("")
    lines.append("## Questions")
    for name, label in (metadata.get("column_labels") or {}).items():
        if name == "respondent_id":
            continue
        lines.append(f"- {name}: {label}")
        value_labels = (metadata.get("value_labels") or {}).get(name)
        if value_labels:
            parts = [f"{k}={v}" for k, v in value_labels.items()]
            lines.append(f"  Values: {', '.join(parts)}")
    if blueprint.get("questionnaire_note"):
        lines.append("")
        lines.append("## Embedded questionnaire note")
        lines.append(str(blueprint["questionnaire_note"]))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_codebook(path: Path, metadata: dict[str, Any], oracle: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "variables": [
            {
                "name": name,
                "label": label,
                "value_labels": (metadata.get("value_labels") or {}).get(name, {}),
                "measure": (metadata.get("variable_measure") or {}).get(name),
                "role": oracle.get("variable_roles", {}).get(name),
            }
            for name, label in (metadata.get("column_labels") or {}).items()
        ],
        "multi_response_sets": oracle.get("multi_response_sets", {}),
        "technical_columns": oracle.get("technical_columns", []),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
