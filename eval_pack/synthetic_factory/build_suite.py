#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__:
    from .generator import generate_case, load_blueprint
else:
    from generator import generate_case, load_blueprint  # type: ignore


def default_blueprint_dir() -> Path:
    return Path(__file__).resolve().parent / "blueprints"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a full synthetic benchmark suite.")
    parser.add_argument("--blueprints", type=Path, default=default_blueprint_dir())
    parser.add_argument("--out", type=Path, default=Path("eval_pack/synthetic_factory/generated"))
    parser.add_argument("--sav-mode", choices=["require", "fallback"], default="fallback")
    args = parser.parse_args()
    cases = []
    for path in sorted(args.blueprints.glob("*.json")):
        generated = generate_case(load_blueprint(path), args.out, sav_mode=args.sav_mode)
        cases.append({
            "case_id": generated.case_id,
            "research_type": generated.research_type,
            "root": str(generated.paths.root),
            "rows": generated.row_count,
            "notes": generated.notes,
        })
    manifest = {"suite": "synthetic_research_benchmark", "cases": cases}
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "suite_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
