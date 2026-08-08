"""G112.1d: reinforce UI → JSON Lines → core → panel, across processes."""

from __future__ import annotations

import json
import re
import shlex
from pathlib import Path

from godot_runner import run_godot_script

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/persistent_reinforce_process_probe.gd"
PREFIX = "PERSISTENT_REINFORCE_PROCESS "
SEED = 73
TARGET_REGION = "player outpost"
TARGET_LABEL = "Posterunek gracza"
SUCCESS_STATUS = "Oddział został wzmocniony."


def _run_process(
    command_prefix: str, state_path: Path, request_path: Path, phase: str
) -> dict:
    result = run_godot_script(
        GAME,
        PROBE,
        command_prefix,
        str(state_path),
        str(request_path),
        str(SEED),
        phase,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def _row(panel_text: str, prefix: str) -> str:
    rows = [line for line in panel_text.splitlines() if line.startswith(prefix)]
    assert len(rows) == 1, f"expected one {prefix!r} row, got {panel_text!r}"
    return rows[0]


def test_reinforce_ui_round_trips_through_two_bridge_processes(tmp_path):
    """A real client click must render the changed party and resume it cold.

    Realistic defect existing synthetic gates miss: Main can pass a hand-written
    SnapshotModel through a fake client while the live ReinforceButton sends no
    JSONL order, applies no post-order snapshot, or the next process paints the
    pre-reinforcement state. The request-file assertion also pins the public
    BridgeClient batch (order + save), rather than merely testing a mock call.
    """
    state_path = tmp_path / "persistent-reinforce-session.json"
    request_path = tmp_path / "bridge-request.jsonl"
    command_prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"

    first = _run_process(command_prefix, state_path, request_path, "first")
    second = _run_process(command_prefix, state_path, request_path, "resume")

    assert first["state_exists"] is True
    assert second["state_exists"] is True
    assert first["session_command"] == f"{command_prefix} serve --resume '{state_path}'"
    assert second["session_command"] == f"{command_prefix} serve --resume '{state_path}'"

    before = first["before"]
    after = first["after"]
    resumed = second["resumed"]
    for observation in (before, after, resumed):
        assert observation["selected_region_name"] == TARGET_REGION, observation
        assert TARGET_LABEL in observation["selected_panel_text"], observation

    assert re.search(r"(?<!\d)5(?!\d)", _row(before["selected_panel_text"], "Armia:"))
    assert re.search(r"(?<!\d)5(?!\d)", _row(before["selected_panel_text"], "Osada:"))
    assert re.search(r"(?<!\d)10(?!\d)", _row(after["selected_panel_text"], "Armia:"))
    assert re.search(r"(?<!\d)0(?!\d)", _row(after["selected_panel_text"], "Osada:"))
    assert after["order_status"] == SUCCESS_STATUS, after

    resumed_army = _row(resumed["selected_panel_text"], "Armia:")
    resumed_settlement = _row(resumed["selected_panel_text"], "Osada:")
    assert re.search(r"(?<!\d)10(?!\d)", resumed_army), resumed
    assert re.search(r"(?<!\d)0(?!\d)", resumed_settlement), resumed

    assert first["requests"] == [
        {"type": "order", "order": "reinforce"},
        {"type": "save", "path": str(state_path)},
    ], first
