#!/usr/bin/env bash
# Uruchamia headless runner rdzenia (placeholder na teraz).
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="src${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m tbb
