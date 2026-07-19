#!/usr/bin/env bash
# Dymny bieg produktu: uruchamia headless runner rdzenia i sprawdza rc==0.
# rc==0 = produkt startuje i kończy się czysto.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="src${PYTHONPATH:+:$PYTHONPATH}"
python3 -m tbb
echo "smoke: OK"
