"""G86.2a: main scene exposes Save/Load party buttons with Polish labels."""

import json
from pathlib import Path

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/save_load_buttons_probe.gd"
PREFIX = "SAVE_LOAD_BUTTONS "


def test_main_scene_exposes_save_and_load_party_buttons():
    """Player-facing Save/Load controls must exist, be labeled and enabled.

    Realistic defect this catches: main.tscn still has only order buttons
    (NextTurn…Assault), so the player cannot invoke save/load without a
    terminal. Existing scene probes pin the old control set and do not require
    %SaveGameButton / %LoadGameButton or Polish labels.

    Binding, status text and round-trip live in
    test_godot_main_scene_save_load_binding (G86.2b). This gate only pins
    presence/labels; pressed_connections may be 0 or more depending on session
    autostart. Visibility of the flag `visible` is asserted here. Non-zero
    laid-out size and pairwise-disjoint rects (K83) are pinned by
    test_godot_main_scene_layout.
    """
    result = run_godot_script(GAME, PROBE, timeout=30)

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    payload = json.loads(lines[0][len(PREFIX) :])
    assert payload["save"]["name"] == "SaveGameButton"
    assert payload["save"]["text"] == "Zapisz partię"
    assert payload["save"]["disabled"] is False
    assert payload["save"]["visible"] is True
    assert payload["load"]["name"] == "LoadGameButton"
    assert payload["load"]["text"] == "Wczytaj partię"
    assert payload["load"]["disabled"] is False
    assert payload["load"]["visible"] is True
