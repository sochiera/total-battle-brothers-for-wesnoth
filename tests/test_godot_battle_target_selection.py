"""Client-side target selection gate for G120.1d (task-682)."""

from __future__ import annotations

import json
from pathlib import Path

from godot_runner import run_godot_script


PREFIX = "BATTLE_TARGET_SELECTION "
ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/battle_target_selection_probe.gd"


def test_battle_view_selects_target_confirms_it_and_keeps_round_controls_working():
    """G120.1d AC1-4: click pair, bridge confirmation, and round controls.

    Realistic defect: BattleView can render a pending deployment while its
    tiles ignore mouse input, or the client can keep the selection local and
    never apply the bridge-returned target snapshot. Existing BattleView
    rendering and bridge pause tests do not exercise this click-to-command
    path. The named assertions cover the valid pair, the returned state,
    advance/auto controls, a readable invalid-pair refusal, and no target mode
    outside an in-progress battle.
    """
    result = run_godot_script(GAME, PROBE, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    payload = json.loads(lines[0][len(PREFIX) :])

    # AC1: the real click sequence must send the selected attacker/defender pair.
    assert payload["valid_target_calls"] == [
        {"attacker": {"q": 0, "r": 0}, "target": {"q": 2, "r": 0}}
    ], payload

    # AC2: the bridge-returned model, not just a local highlight, confirms it.
    assert payload["confirmed_targets"] == [
        {"attacker": {"q": 0, "r": 0}, "target": {"q": 2, "r": 0}}
    ], payload
    assert payload["invalid_target_calls"] == [], payload
    assert payload["invalid_status"] == "Wybierz aktywną jednostkę wroga.", payload

    # Review regression: a second active friendly click replaces the pending
    # attacker instead of being mistaken for the enemy target.
    assert payload["replacement_target_calls"] == [
        {"attacker": {"q": 0, "r": 1}, "target": {"q": 2, "r": 0}}
    ], payload

    # AC3: the selected target is consumed by the next round and the no-target
    # auto path remains usable.
    assert payload["advance_calls"] == 1, payload
    assert payload["before_advance"] != payload["after_advance"], payload
    assert payload["advance_target_state"] == [], payload
    assert payload["auto_calls"] == 1, payload
    assert payload["auto_result"] in {"attacker_win", "defender_win", "draw"}, payload

    # AC4: a result board and the hidden no-battle state must not enter target mode.
    assert payload["result_board_visible"] is True, payload
    assert payload["result_board_target_calls"] == [], payload
    assert payload["no_battle_visible"] is False, payload
    assert payload["no_battle_target_calls"] == [], payload
