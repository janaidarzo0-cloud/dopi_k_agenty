#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from build_case import main as build_case_main
from build_suite import main as build_suite_main
from score_synthetic_case import main as score_case_main
from agent_api_runner import main as run_api_main


def main() -> int:
    parser = argparse.ArgumentParser(description="Synthetic factory command wrapper")
    parser.add_argument("command", choices=["build-case", "build-suite", "score-case", "run-api"])
    args, rest = parser.parse_known_args()

    # Re-dispatch by replacing argv for the underlying command modules.
    import sys
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
