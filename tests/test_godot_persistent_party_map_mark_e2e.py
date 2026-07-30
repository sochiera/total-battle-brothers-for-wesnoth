"""G84.1c e2e: player-party map mark follows muster→march across processes."""

from __future__ import annotations

import json
import shlex
from pathlib import Path

from godot_runner import run_godot_script

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/persistent_party_map_mark_probe.gd"
PREFIX = "PERSISTENT_PARTY_MAP_MARK "
SEED = 73
EXPECTED_MARKED_REGION = "player outpost"
EXPECTED_POSITION_NAME = "Posterunek gracza"


def _run_process(command_prefix: str, state_path: Path, request_path: Path, phase: str) -> dict:
    result = run_godot_script(
        GAME,
        PROBE,
        command_prefix,
        str(state_path),
        str(request_path),
        str(SEED),
        phase,
        timeout=45,
    )
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def test_party_map_mark_moves_after_muster_and_march_across_two_processes(tmp_path):
    """After fresh start the map has no party mark; after muster→march a different
    tile is marked, and resume reloads that mark without scene hand-wiring.

    Realistic defect: MapView marks from synthetic apply_model tests but bridge
    refresh / order paths leave the mark stale or absent while PlayerPartyPositionLabel
    already tracks the party — player cannot see the army after real orders.
    """
    state_path = tmp_path / "persistent-party-map-mark.json"
    request_path = tmp_path / "bridge-request.jsonl"
    command_prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"

    first = _run_process(command_prefix, state_path, request_path, "orders")
    second = _run_process(command_prefix, state_path, request_path, "resume")

    assert first["state_exists"] is True
    assert second["session_command"] == f"{command_prefix} serve --resume '{state_path}'"

    start = first["after_start"]
    after = first["after_orders"]
    resumed = second["after_orders"]

    # Fresh seed-73 party: no player army on the map.
    assert start["marker_count"] == 0, start
    assert start["marked_regions"] == [], start
    assert "brak" in start["position_label"].lower(), start

    # After muster→march the mark follows the party (player outpost for seed 73).
    assert after["marker_count"] == 1, after
    assert len(after["marked_regions"]) == 1, after
    marked = after["marked_regions"][0]
    assert marked == EXPECTED_MARKED_REGION, after
    assert EXPECTED_POSITION_NAME in after["position_label"], after
    assert after["marked_regions"] != start["marked_regions"], (
        f"mark must change after muster+march: start={start} after={after}"
    )

    # Resume process shows the same mark without re-issuing orders.
    assert resumed["marker_count"] == 1, resumed
    assert resumed["marked_regions"] == after["marked_regions"], resumed
    assert EXPECTED_POSITION_NAME in resumed["position_label"], resumed
