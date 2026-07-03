#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Support both:
#   python eval_pack/synthetic_factory/factory.py build-suite ...
# and:
#   python -m eval_pack.synthetic_factory.factory build-suite ...
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from eval_pack.synthetic_factory.agent_api_runner import main as run_api_main
from eval_pack.synthetic_factory.build_case import main as build_case_main
from eval_pack.synthetic_factory.build_suite import main as build_suite_main
from eval_pack.synthetic_factory.score_synthetic_case import main as score_case_main


def main() -> int:
    parser = argparse.ArgumentParser(description="Synthetic factory command wrapper")
    parser.add_argument("command", choices=["build-case", "build-suite", "score-case", "run-api"])
    args, rest = parser.parse_known_args()
    sys.argv = [sys.argv[0], *rest]
    if args.command == "build-case":
        return build_case_main()
    if args.command == "build-suite":
        return build_suite_main()
    if args.command == "score-case":
        return score_case_main()
    if args.command == "run-api":
        return run_api_main()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
