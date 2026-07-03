#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SELF_TEST=0
GENERATE_SYNTHETIC=0
SYNTHETIC_OUT="eval_pack/synthetic_factory/generated"
SAV_MODE="fallback"
RESULTS_ROOT="projects_eval/latest"
OUT_DIR="eval_pack/results/latest"
MANIFEST="eval_pack/eval_suite/manifest.json"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --self-test)
      SELF_TEST=1
      shift
      ;;
    --generate-synthetic)
      GENERATE_SYNTHETIC=1
      shift
      ;;
    --synthetic-out)
      SYNTHETIC_OUT="$2"
      shift 2
      ;;
    --sav-mode)
      SAV_MODE="$2"
      shift 2
      ;;
    --results-root)
      RESULTS_ROOT="$2"
      shift 2
      ;;
    --out-dir)
      OUT_DIR="$2"
      shift 2
      ;;
    --manifest)
      MANIFEST="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

cd "$ROOT_DIR"

if [[ "$SELF_TEST" == "1" ]]; then
  python3 eval_pack/scoring_scripts/evaluate_outputs.py --self-test
  exit $?
fi

if [[ "$GENERATE_SYNTHETIC" == "1" ]]; then
  python3 eval_pack/synthetic_factory/factory.py build-suite --out "$SYNTHETIC_OUT" --sav-mode "$SAV_MODE"
  echo "Synthetic cases: $SYNTHETIC_OUT"
  exit 0
fi

python3 eval_pack/scoring_scripts/evaluate_outputs.py \
  --manifest "$MANIFEST" \
  --results-root "$RESULTS_ROOT" \
  --out-dir "$OUT_DIR"

echo "Report: $OUT_DIR/summary.md"
