#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CaseResult:
    case_id: str
    total_score: float
    dimensions: dict[str, float]
    failures: list[str]
    notes: list[str]


def read_json(path: Path, default: Any = None) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            rows.append({"_parse_error": line[:200]})
    return rows


def find_output_dir(case_dir: Path) -> Path:
    if (case_dir / "output" / "analysis_summary.json").exists():
        return case_dir / "output"
    return case_dir


def text_blob(value: Any) -> str:
    if isinstance(value, dict):
        return "\n".join(text_blob(v) for v in value.values())
    if isinstance(value, list):
        return "\n".join(text_blob(v) for v in value)
    return str(value or "")


def numbers_in_text(text: str) -> set[float]:
    out: set[float] = set()
    for raw in re.findall(r"-?\d+(?:[\.,]\d+)?", text):
        try:
            out.add(round(float(raw.replace(",", ".")), 4))
        except ValueError:
            pass
    return out


def numbers_in_obj(value: Any) -> set[float]:
    out: set[float] = set()
    if isinstance(value, bool) or value is None:
        return out
    if isinstance(value, (int, float)):
        out.add(round(float(value), 4))
        return out
    if isinstance(value, str):
        return numbers_in_text(value)
    if isinstance(value, dict):
        for v in value.values():
            out |= numbers_in_obj(v)
    elif isinstance(value, list):
        for v in value:
            out |= numbers_in_obj(v)
    return out


def clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def score_case(case_file: Path, results_root: Path) -> CaseResult:
    spec = read_json(case_file, {}) or {}
    case_id = spec.get("case_id") or case_file.stem
    out_dir = find_output_dir(results_root / case_id)
    summary = read_json(out_dir / "analysis_summary.json", {}) or {}
    insights = read_json(out_dir / "insights.json", []) or []
    evidence = read_jsonl(out_dir / "evidence.jsonl")
    failures: list[str] = []
    notes: list[str] = []

    report = summary.get("report") or {}
    findings = report.get("findings") or summary.get("findings") or insights or []
    summary_text = text_blob(report) + "\n" + text_blob(findings)
    evidence_ids = {e.get("evidence_id") for e in evidence if e.get("evidence_id")}

    required_artifacts = spec.get("required_artifacts") or ["analysis_summary.json", "evidence.jsonl"]
    present = sum(1 for name in required_artifacts if (out_dir / name).exists())
    artifact_score = 100.0 * present / max(1, len(required_artifacts))
    if present < len(required_artifacts):
        failures.append("missing_required_artifacts")

    evidence_count = len([e for e in evidence if e.get("evidence_id")])
    min_evidence = int(spec.get("min_evidence_count", 3))
    evidence_volume = clamp(100.0 * evidence_count / max(1, min_evidence))
    if evidence_count < min_evidence:
        failures.append("low_evidence_count")

    cited = []
    for f in findings if isinstance(findings, list) else []:
        if isinstance(f, dict):
            cited.extend(str(x) for x in (f.get("evidence_ids") or []) if str(x).strip())
    valid_cited = [x for x in cited if x in evidence_ids]
    evidence_grounding = 100.0 if not findings else 100.0 * len(valid_cited) / max(1, len(cited) or len(findings))
    if findings and not valid_cited:
        failures.append("findings_without_valid_evidence")

    unsupported_numbers = summary.get("unsupported_numbers") or []
    if unsupported_numbers:
        numeric_faithfulness = 60.0
        failures.append("unsupported_numbers_present")
    else:
        allowed = set()
        for e in evidence:
            allowed |= numbers_in_obj(e.get("result"))
        narrative_nums = numbers_in_text(summary_text)
        important_nums = {n for n in narrative_nums if abs(n) >= 1 and n not in {2024, 2025, 2026}}
        if not important_nums:
            numeric_faithfulness = 80.0
            notes.append("no_substantive_numbers_in_narrative")
        else:
            matched = 0
            for n in important_nums:
                if any(abs(n - a) <= 0.51 for a in allowed) or any(abs(n / 100 - a) <= 0.01 for a in allowed):
                    matched += 1
            numeric_faithfulness = 100.0 * matched / max(1, len(important_nums))
            if numeric_faithfulness < 80:
                failures.append("numbers_not_traceable")

    expected_terms = [str(x).lower() for x in spec.get("expected_terms", [])]
    forbidden_terms = [str(x).lower() for x in spec.get("forbidden_terms", [])]
    low_text = summary_text.lower()
    objective_fit = 100.0
    if expected_terms:
        hits = sum(1 for term in expected_terms if term in low_text)
        objective_fit = 100.0 * hits / len(expected_terms)
        if hits < max(1, len(expected_terms) // 2):
            failures.append("weak_objective_fit")
    if any(term in low_text for term in forbidden_terms):
        objective_fit = min(objective_fit, 40.0)
        failures.append("forbidden_behavior_detected")

    caution_terms = ["осторож", "мал", "n<", "незнач", "развед", "weak", "огранич"]
    requires_caution = bool(spec.get("requires_caution"))
    caveat_honesty = 100.0 if not requires_caution else (100.0 if any(t in low_text for t in caution_terms) else 35.0)
    if requires_caution and caveat_honesty < 60:
        failures.append("missing_required_caution")

    critic = summary.get("critic_assessment") or read_json(out_dir / "critic_assessment.json", {}) or {}
    skeptic = summary.get("skeptic_review") or read_json(out_dir / "skeptic_review.json", {}) or {}
    critic_coverage = 0.0
    if critic:
        critic_coverage += 50.0
    if skeptic:
        critic_coverage += 30.0
    if summary.get("research_backlog") or read_json(out_dir / "research_backlog.json", {}):
        critic_coverage += 20.0

    insight_quality = 50.0
    if isinstance(findings, list) and findings:
        claims = [text_blob(f) for f in findings if isinstance(f, dict)]
        avg_len = statistics.mean([len(c) for c in claims]) if claims else 0
        insight_quality = clamp(45 + min(35, avg_len / 12) + (20 if len(findings) >= 3 else 0))
    else:
        failures.append("no_findings")

    dimensions = {
        "artifact_completeness": round(artifact_score, 2),
        "evidence_volume": round(evidence_volume, 2),
        "evidence_grounding": round(evidence_grounding, 2),
        "numeric_faithfulness": round(numeric_faithfulness, 2),
        "objective_fit": round(objective_fit, 2),
        "caveat_honesty": round(caveat_honesty, 2),
        "critic_coverage": round(clamp(critic_coverage), 2),
        "insight_quality": round(insight_quality, 2),
    }
    weights = spec.get("scoring_weights") or {
        "artifact_completeness": 0.10,
        "evidence_volume": 0.10,
        "evidence_grounding": 0.20,
        "numeric_faithfulness": 0.20,
        "objective_fit": 0.15,
        "caveat_honesty": 0.10,
        "critic_coverage": 0.10,
        "insight_quality": 0.05,
    }
    total = sum(dimensions.get(k, 0.0) * float(w) for k, w in weights.items())
    return CaseResult(case_id, round(total, 2), dimensions, failures, notes)


def load_cases(manifest_path: Path) -> list[Path]:
    manifest = read_json(manifest_path, {}) or {}
    base = manifest_path.parent
    return [base / str(item["path"]) for item in manifest.get("cases", [])]


def self_test(tmp_root: Path) -> None:
    case_dir = tmp_root / "demo_descriptive" / "output"
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "evidence.jsonl").write_text(json.dumps({
        "evidence_id": "ev_001",
        "tool": "frequencies",
        "result": {"rows": [{"column": "region", "percent": 0.62, "n": 120}]},
    }, ensure_ascii=False) + "\n", encoding="utf-8")
    (case_dir / "analysis_summary.json").write_text(json.dumps({
        "report": {"findings": [{"title": "Регион", "narrative": "Москва даёт 62% базы", "evidence_ids": ["ev_001"]}]},
        "unsupported_numbers": [],
        "critic_assessment": {"checks": ["base"]},
        "skeptic_review": {"reviews": []},
        "research_backlog": {"coverage": {"checked": 1, "total": 1}},
    }, ensure_ascii=False), encoding="utf-8")
    case_file = tmp_root / "case.json"
    case_file.write_text(json.dumps({
        "case_id": "demo_descriptive",
        "expected_terms": ["москва"],
        "min_evidence_count": 1,
        "required_artifacts": ["analysis_summary.json", "evidence.jsonl"],
    }, ensure_ascii=False), encoding="utf-8")
    result = score_case(case_file, tmp_root)
    assert result.total_score >= 80, result
    print("self-test ok", result.total_score)


def write_reports(results: list[CaseResult], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "cases": [r.__dict__ for r in results],
        "average_total_score": round(statistics.mean([r.total_score for r in results]) if results else 0.0, 2),
        "failed_cases": [r.case_id for r in results if r.failures],
    }
    (out_dir / "summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Eval Summary", "", f"Average score: **{payload['average_total_score']}**", ""]
    for r in results:
        lines.append(f"## {r.case_id} — {r.total_score}")
        if r.failures:
            lines.append("Failures: " + ", ".join(r.failures))
        for k, v in r.dimensions.items():
            lines.append(f"- {k}: {v}")
        lines.append("")
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="eval_pack/eval_suite/manifest.json")
    parser.add_argument("--results-root", default="projects_eval/latest")
    parser.add_argument("--out-dir", default="eval_pack/results/latest")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test(Path("/tmp/eval_pack_self_test"))
        return 0

    manifest_path = Path(args.manifest)
    results_root = Path(args.results_root)
    cases = load_cases(manifest_path)
    results = [score_case(path, results_root) for path in cases]
    write_reports(results, Path(args.out_dir))
    avg = statistics.mean([r.total_score for r in results]) if results else 0.0
    print(f"eval complete: {len(results)} cases, average={avg:.2f}")
    return 0 if avg >= 70 else 1


if __name__ == "__main__":
    raise SystemExit(main())
