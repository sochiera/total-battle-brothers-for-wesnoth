import json
from pathlib import Path

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/recruit_button_probe.gd"
PREFIX = "RECRUIT_BUTTON "


def test_main_scene_exposes_a_safe_unbound_recruit_button():
    result = run_godot_script(GAME, PROBE, timeout=30)

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len(PREFIX) :]) == {
        "button": {
            "name": "RecruitButton",
            "text": "Rekrutuj jednostkę",
            "disabled": False,
            "pressed_connections": 0,
        },
        "controls_unchanged": True,
    }
