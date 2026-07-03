from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def write_sav_or_fallback(df: pd.DataFrame, path: Path, metadata: dict[str, Any], *, mode: str = "fallback") -> Path:
    """Write SPSS .sav when pyreadstat is available, otherwise write CSV.

    mode:
      - require: raise if pyreadstat is unavailable.
      - fallback: write CSV and a metadata sidecar when pyreadstat is unavailable.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import pyreadstat  # type: ignore
    except Exception as exc:
        if mode == "require":
            raise RuntimeError("pyreadstat is required to write .sav files") from exc
        fallback_path = path.with_suffix(".csv")
        df.to_csv(fallback_path, index=False, encoding="utf-8")
        fallback_path.with_suffix(".metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        return fallback_path

    kwargs: dict[str, Any] = {
        "column_labels": metadata.get("column_labels") or {},
        "variable_value_labels": metadata.get("value_labels") or {},
    }
    for key in ["missing_ranges", "variable_measure", "variable_format"]:
        if metadata.get(key):
            kwargs[key] = metadata[key]
    pyreadstat.write_sav(df, str(path), **kwargs)
    return path
