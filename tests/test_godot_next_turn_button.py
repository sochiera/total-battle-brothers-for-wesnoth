import json
from pathlib import Path

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/next_turn_button_probe.gd"
PREFIX = "NEXT_TURN_BUTTON "


def test_main_scene_exposes_an_enabled_next_turn_button():
    result = run_godot_script(GAME, PROBE, timeout=30)

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    assert json.loads(lines[0][len(PREFIX) :]) == {
        "name": "NextTurnButton",
        "text": "Następna tura",
        "disabled": False,
    }


def test_next_turn_button_probe_fails_for_an_incorrect_label_expectation():
    result = run_godot_script(GAME, PROBE, "Zła etykieta", timeout=30)

    assert result.returncode != 0
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
