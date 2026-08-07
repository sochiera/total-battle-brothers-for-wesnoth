"""G113.1b e2e: the region panel tells two measured armies apart on a live bridge."""

from __future__ import annotations

import json
import re
import shlex
from pathlib import Path

import pytest

from godot_runner import run_godot_script

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/party_strength_e2e_probe.gd"
PREFIX = "PARTY_STRENGTH_E2E "
SEED = 73

# Measured at planning (task-626): recruit×10 → muster = 5 units,
# develop×10 → recruit×10 → muster = 1 unit.
EXPECTED_SIZE = {"plain": 5, "developed": 1}


def _run(tmp_path: Path, mode: str) -> dict:
    state_path = tmp_path / f"party-strength-{mode}.json"
    request_path = tmp_path / "bridge-request.jsonl"
    command_prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    result = run_godot_script(
        GAME,
        PROBE,
        command_prefix,
        str(state_path),
        str(request_path),
        str(SEED),
        mode,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def _army_row(payload: dict) -> str:
    panel = str(payload["after_select"]["panel_text"])
    rows = [row for row in panel.splitlines() if row.startswith("Armia:")]
    assert len(rows) == 1, f"expected exactly one army row, got panel={panel!r}"
    return rows[0]


@pytest.mark.parametrize("mode", sorted(EXPECTED_SIZE))
def test_panel_shows_measured_party_size_on_live_bridge(tmp_path, mode):
    """AC5: the same click on the same seed reads out the army the core built.

    Realistic defect the headless panel probe misses: that gate feeds Main a
    hand-written SnapshotModel, so a panel wired to a key the live bridge
    snapshot never sends (``count`` instead of ``size``, strength nested under
    a different dict) stays green there while every real session renders the
    bare „Armia: własny (gracz)". Driving orders through JSONL → core → render
    and contrasting the two measured runs (5 units vs 1 unit) pins the number
    to what the player actually commanded.
    """
    payload = _run(tmp_path, mode)
    assert payload["state_exists"] is True
    assert payload["after_select"]["selected_region_name"] == payload["party_region"]

    row = _army_row(payload)
    size = EXPECTED_SIZE[mode]
    assert re.search(rf"(?<!\d){size}(?!\d)", row), (
        f"{mode}: panel must show the measured {size}-unit party, got {row!r}"
    )
    other = EXPECTED_SIZE["developed" if mode == "plain" else "plain"]
    assert not re.search(rf"(?<!\d){other}(?!\d)", row), (
        f"{mode}: panel must not show the other run's size {other}, got {row!r}"
    )
