#!/usr/bin/env bash
# Uruchamia pełną deterministyczną partię headless.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="src${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m tbb
