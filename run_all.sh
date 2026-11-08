#!/usr/bin/env bash
# Rebuild every output from the raw Kaggle file, in order.
# Usage (from the project folder):  ./run_all.sh
set -euo pipefail   # stop at the first error
cd "$(dirname "$0")"

if [ ! -f data/raw/DataCoSupplyChainDataset.csv ]; then
  echo "Missing data/raw/DataCoSupplyChainDataset.csv (see README: Reproduce)" >&2
  exit 1
fi

PY=.venv/bin/python
echo "== 1/7 First look";  $PY scripts/01_first_look.py > /dev/null
echo "== 2/7 Clean";       $PY scripts/02_clean.py      > /dev/null
echo "== 3/7 Analysis";    $PY scripts/03_analysis.py
echo "== 4/7 Prioritize";  $PY scripts/04_prioritize.py > /dev/null
echo "== 5/7 Test plan";   $PY scripts/05_test_plan.py > /dev/null
echo "== 6/7 Dashboard";   $PY scripts/06_build_dashboard.py
echo "== 7/7 Tableau CSV"; $PY scripts/07_export_tableau.py
echo "Done. Tables in outputs/tables/, charts in outputs/figures/, dashboard in dashboard/index.html."
