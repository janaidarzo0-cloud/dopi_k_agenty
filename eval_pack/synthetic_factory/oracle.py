from __future__ import annotations

from typing import Any

import pandas as pd


def _safe_pct(num: float, den: float) -> float:
    return round(float(num) / float(den), 4) if den else 0.0


def frequencies(df: pd.DataFrame, column: str) -> list[dict[str, Any]]:
    total = len(df)
    return [{"value": str(v), "n": int(n), "pct": _safe_pct(n, total)} for v, n in df[column].value_counts(dropna=False).sort_index().items()]


def mean_by(df: pd.DataFrame, metric: str, by: str) -> list[dict[str, Any]]:
    return sorted([
        {"group": str(k), "n": int(len(g)), "mean": round(float(g[metric].mean()), 4)}
        for k, g in df.groupby(by, dropna=False)
    ], key=lambda x: x["group"])


def nps_by(df: pd.DataFrame, metric: str, by: str | None = None) -> list[dict[str, Any]]:
    def calc(group_name: str, grp: pd.DataFrame) -> dict[str, Any]:
        n = len(grp)
        promoters = int((grp[metric] >= 9).sum())
        detractors = int((grp[metric] <= 6).sum())
        return {
            "group": group_name,
            "n": n,
            "promoters_pct": _safe_pct(promoters, n),
            "detractors_pct": _safe_pct(detractors, n),
            "nps": round(100 * _safe_pct(promoters - detractors, n), 2),
        }
    if by is None:
        return [calc("total", df)]
    return sorted([calc(str(k), g) for k, g in df.groupby(by, dropna=False)], key=lambda x: x["group"])


def pearson_corrs(df: pd.DataFrame, metric: str, candidates: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for col in candidates:
        if col not in df.columns:
            continue
        try:
            corr = df[[metric, col]].corr().iloc[0, 1]
            if pd.notna(corr):
                rows.append({"variable": col, "corr": round(float(corr), 4)})
        except Exception:
            continue
    return sorted(rows, key=lambda x: abs(x["corr"]), reverse=True)


def multiselect_penetration(df: pd.DataFrame, columns: list[str], by: str | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    groups = [("total", df)] if by is None else [(str(k), g) for k, g in df.groupby(by, dropna=False)]
    for group, grp in groups:
        n = len(grp)
        for col in columns:
            if col in grp.columns:
                rows.append({"option": col, "group": group, "n": n, "pct": _safe_pct((grp[col] == 1).sum(), n)})
    return rows


def build_exact_stats(df: pd.DataFrame, oracle: dict[str, Any]) -> dict[str, Any]:
    stats: dict[str, Any] = {"n": int(len(df)), "frequencies": {}, "means": {}, "nps": {}, "correlations": {}, "multiselect": {}}
    for col in oracle.get("oracle_frequencies", []):
        if col in df.columns:
            stats["frequencies"][col] = frequencies(df, col)
    for item in oracle.get("oracle_means", []):
        metric, by = item.get("metric"), item.get("by")
        if metric in df.columns and by in df.columns:
            stats["means"][f"{metric}_by_{by}"] = mean_by(df, metric, by)
    for item in oracle.get("oracle_nps", []):
        metric, by = item.get("metric"), item.get("by")
        if metric in df.columns:
            stats["nps"][f"{metric}_by_{by or 'total'}"] = nps_by(df, metric, by if by in df.columns else None)
    for item in oracle.get("oracle_correlations", []):
        metric = item.get("metric")
        if metric in df.columns:
            stats["correlations"][metric] = pearson_corrs(df, metric, item.get("candidates") or [])
    for name, item in oracle.get("multi_response_sets", {}).items():
        by = item.get("by")
        stats["multiselect"][name] = multiselect_penetration(df, item.get("columns") or [], by if by in df.columns else None)
    return stats
