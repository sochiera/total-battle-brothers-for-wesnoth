"""Client-side battle move selection gate for G121.1d (task-688)."""

from __future__ import annotations

import json
from pathlib import Path

from godot_runner import run_godot_script


PREFIX = "BATTLE_MOVE_SELECTION "
ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/battle_move_selection_probe.gd"


def test_battle_view_selects_move_destination_and_keeps_attack_path():
    """G121.1d AC1-3: reveal legal move hexes, send battle_move, keep attack.

    Realistic defect: BattleView only wires battle_target for an enemy hex, so
    an empty neighbour never becomes clickable and BridgeClient has no
    battle_move path. Existing target-selection and bridge pause tests never
    exercise click-own-unit then click-free-neighbour through Main.
    """
    result = run_godot_script(GAME, PROBE, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    payload = json.loads(lines[0][len(PREFIX) :])

    # AC1: selecting the active own unit reveals every free axial neighbour,
    # and clicking one sends battle_move with the public mover/destination pair
    # while the battle stays pending.
    assert payload["destinations_before_select"] == [], payload
    assert payload["destinations_after_select"] == [
        "HexTile_-1_0",
        "HexTile_-1_1",
        "HexTile_0_-1",
        "HexTile_0_1",
        "HexTile_1_-1",
        "HexTile_1_0",
    ], payload
    assert payload["valid_move_calls"] == [
        {"mover": {"q": 0, "r": 0}, "destination": {"q": 0, "r": 1}}
    ], payload
    assert payload["confirmed_moves"] == [
        {"mover": {"q": 0, "r": 0}, "destination": {"q": 0, "r": 1}}
    ], payload
    assert payload["pending_after_valid"] is None, payload
    assert payload["battle_visible_after_valid"] is True, payload

    # AC2: bridge-returned model confirms the intent; a refused move keeps the
    # board and surfaces a readable Polish status instead of applying targets.
    assert payload["hexes_after_valid"] == payload["hexes_before_refuse"], payload
    assert payload["refused_move_calls"] == [
        {"mover": {"q": 0, "r": 0}, "destination": {"q": 1, "r": 0}}
    ], payload
    assert payload["refused_hexes"] == payload["hexes_before_refuse"], payload
    assert payload["refused_moves"] == [], payload
    assert payload["refused_status"] == "Pole docelowe jest niedostępne.", payload
    assert payload["battle_visible_after_refuse"] is True, payload

    # AC3: enemy click after own unit still issues battle_target, never move;
    # empty non-destination and enemy-first clicks send no command.
    assert payload["attack_move_calls"] == [], payload
    assert payload["attack_target_calls"] == [
        {"attacker": {"q": 0, "r": 0}, "target": {"q": 2, "r": 0}}
    ], payload
    assert payload["empty_miss_move_calls"] == [], payload
    assert payload["empty_miss_target_calls"] == [], payload
    assert payload["empty_miss_status"] == (
        "Wybierz aktywną jednostkę wroga."
    ), payload
    assert payload["enemy_first_move_calls"] == [], payload
    assert payload["enemy_first_target_calls"] == [], payload
    assert payload["enemy_first_status"] == (
        "Najpierw wybierz aktywną własną jednostkę."
    ), payload
