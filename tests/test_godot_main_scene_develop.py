import json
from pathlib import Path

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/develop_from_bridge_probe.gd"
PREFIX = "DEVELOP_FROM_BRIDGE "


def test_develop_from_bridge_applies_post_order_model_and_preserves_scene_on_failure():
    result = run_godot_script(GAME, PROBE, timeout=30)

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len(PREFIX) :]) == {
        "available": True,
        "refreshed": True,
        "success_orders": ["develop"],
        "after_success": {
            "date": "Rok 1, miesiąc 1",
            "result": "Wynik: developed",
            "regions": ["Po rozkazie"],
        },
        "rejected": False,
        "failure_orders": ["develop"],
        "after_failure": {
            "date": "Rok 1, miesiąc 1",
            "result": "Wynik: developed",
            "regions": ["Po rozkazie"],
        },
    }
