#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__:
    from .generator import generate_case, load_blueprint
else:
    from generator import generate_case, load_blueprint  # type: ignore


def main() -> int:
    parser = argparse.ArgumentParser(description="Build one synthetic survey eval case.")
    parser.add_argument("blueprint", type=Path, help="Path to a blueprint JSON file")
    parser.add_argument("--out", type=Path, default=Path("eval_pack/synthetic_factory/generated"))
    parser.add_argument("--sav-mode", choices=["require", "fallback"], default="fallback")
    args = parser.parse_args()
    generated = generate_case(load_blueprint(args.blueprint), args.out, sav_mode=args.sav_mode)
    print(json.dumps({
        "case_id": generated.case_id,
        "research_type": generated.research_type,
        "root": str(generated.paths.root),
        "rows": generated.row_count,
        "notes": generated.notes,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
