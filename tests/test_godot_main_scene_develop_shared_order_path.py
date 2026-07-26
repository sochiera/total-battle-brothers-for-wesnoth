import json
from pathlib import Path

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/develop_button_shared_order_path_probe.gd"
PREFIX = "DEVELOP_BUTTON_SHARED_ORDER_PATH "


def test_develop_button_delegates_to_the_shared_bound_order_path():
    result = run_godot_script(GAME, PROBE, timeout=30)

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len(PREFIX) :]) == {
        "calls": ["send_order_from_bridge:develop"]
    }
