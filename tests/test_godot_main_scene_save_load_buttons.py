"""G86.2a: main scene exposes unbound Save/Load party buttons (no bridge wire)."""

import json
from pathlib import Path

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/save_load_buttons_probe.gd"
PREFIX = "SAVE_LOAD_BUTTONS "


def test_main_scene_exposes_safe_unbound_save_and_load_party_buttons():
    """Player-facing Save/Load controls must exist, be labeled, and stay inert.

    Realistic defect this catches: main.tscn still has only order buttons
    (NextTurn…Assault), so the player cannot invoke save/load without a
    terminal. Existing scene probes pin the old control set and do not require
    %SaveGameButton / %LoadGameButton, Polish labels, or unbound pressed.
    Binding and e2e stay out of scope (task-484).

    Visibility of the flag `visible` is asserted here. Non-zero laid-out size and
    pairwise-disjoint rects (K83) are pinned by test_godot_main_scene_layout
    (ORDER_CONTROLS includes SaveGameButton/LoadGameButton) — not re-measured in
    this headless probe without process_frame.
    """
    result = run_godot_script(GAME, PROBE, timeout=30)

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len(PREFIX) :]) == {
        "save": {
            "name": "SaveGameButton",
            "text": "Zapisz partię",
            "disabled": False,
            "visible": True,
            "pressed_connections": 0,
        },
        "load": {
            "name": "LoadGameButton",
            "text": "Wczytaj partię",
            "disabled": False,
            "visible": True,
            "pressed_connections": 0,
        },
        "controls_unchanged": True,
    }
