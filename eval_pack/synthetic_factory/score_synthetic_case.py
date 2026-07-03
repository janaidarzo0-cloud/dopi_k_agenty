#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def read_json(path: Path, default: Any = None) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            rows.append({"_bad_json": line[:200]})
    return rows


def blob(value: Any) -> str:
    if isinstance(value, dict):
        return "\n".join(blob(v) for v in value.values())
    if isinstance(value, list):
        return "\n".join(blob(v) for v in value)
    return str(value or "")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def hit(text: str, phrase: str) -> bool:
    parts = [p for p in re.split(r"[^a-zа-я0-9_]+", norm(phrase)) if len(p) >= 3]
    if not parts:
        return norm(phrase) in text
    return sum(1 for p in parts if p in text) >= max(1, round(len(parts) * 0.6))


def score(case_root: Path, output_dir: Path) -> dict[str, Any]:
    truth = read_json(case_root / "oracle" / "truth.json", {}) or {}
    summary = read_json(output_dir / "analysis_summary.json", {}) or {}
    insights = read_json(output_dir / "insights.json", []) or []
    evidence = read_jsonl(output_dir / "evidence.jsonl")
    text = norm(blob(summary) + "\n" + blob(insights))

    must_detect = truth.get("must_detect") or []
    must_not = truth.get("must_not_claim") or []
    expected_tools = set(truth.get("expected_tools") or [])
    actual_tools = {str(e.get("tool")) for e in evidence if e.get("tool")}

    detected = [x for x in must_detect if hit(text, str(x))]
    forbidden = [x for x in must_not if hit(text, str(x))]
    tool_hits = sorted(expected_tools & actual_tools)
    evidence_ids = {e.get("evidence_id") for e in evidence if e.get("evidence_id")}

    recall = 100.0 * len(detected) / max(1, len(must_detect))
    tool_strategy = 100.0 * len(tool_hits) / max(1, len(expected_tools))
    forbidden_score = 100.0 if not forbidden else max(0.0, 100.0 - 35.0 * len(forbidden))
    evidence_grounding = 100.0 if evidence_ids else 0.0
    caution_score = 100.0
    if truth.get("requires_caution"):
        caution_score = 100.0 if any(w in text for w in ["осторож", "мал", "weak", "незнач", "огранич", "развед"]) else 30.0
    total = round(0.35 * recall + 0.20 * tool_strategy + 0.20 * forbidden_score + 0.15 * evidence_grounding + 0.10 * caution_score, 2)
    return {
        "case_id": truth.get("case_id") or case_root.name,
        "total_score": total,
        "dimensions": {
            "oracle_recall": round(recall, 2),
            "tool_strategy": round(tool_strategy, 2),
            "forbidden_claim_control": round(forbidden_score, 2),
            "evidence_grounding": round(evidence_grounding, 2),
            "caveat_honesty": round(caution_score, 2),
        },
        "detected": detected,
        "missed": [x for x in must_detect if x not in detected],
        "forbidden_hits": forbidden,
        "expected_tools": sorted(expected_tools),
        "actual_tools": sorted(actual_tools),
        "tool_hits": tool_hits,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = score(args.case_root, args.output_dir)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload)
    return 0 if result["total_score"] >= 70 else 1


if __name__ == "__main__":
    raise SystemExit(main())
