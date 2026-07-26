import json
from pathlib import Path

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/develop_button_binding_probe.gd"
PREFIX = "DEVELOP_BUTTON_BINDING "


def test_develop_button_is_a_single_safe_binding_and_renders_the_post_order_snapshot():
    result = run_godot_script(GAME, PROBE, timeout=30)

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len(PREFIX) :]) == {
        "before_bind": {"date": "", "duchy_status": ""},
        "after_unbound_press": {"date": "", "duchy_status": ""},
        "orders": ["develop", "develop", "develop"],
        "after_first_press": {
            "date": "Rok 1, miesiąc 1",
            "duchy_status": "Morale: 4, osady: 2, oddziały: 1",
        },
        "after_second_press": {
            "date": "Rok 1, miesiąc 1",
            "duchy_status": "Morale: 5, osady: 3, oddziały: 1",
        },
        "after_failed_press": {
            "date": "Rok 1, miesiąc 1",
            "duchy_status": "Morale: 5, osady: 3, oddziały: 1",
        },
    }
