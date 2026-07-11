#!/usr/bin/env bash
# Uruchamia pełny pakiet testów z katalogu projektu.
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 -m pytest
