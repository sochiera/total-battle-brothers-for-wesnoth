import json
from pathlib import Path

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
SCRIPT = GAME / "scripts" / "order_result.gd"
PROBE = GAME / "tests" / "order_result_probe.gd"
PREFIX = "ORDER_RESULT "


def test_godot_order_result_projects_only_complete_successful_order_results():
    assert SCRIPT.is_file(), "missing res://scripts/order_result.gd"
    assert PROBE.is_file(), "missing res://tests/order_result_probe.gd"

    result = run_godot_script(GAME, "res://tests/order_result_probe.gd", timeout=30)

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    payload = json.loads(lines[0][len(PREFIX) :])

    assert payload["changed"] == {"order": "develop", "changed": True}
    assert payload["unchanged"] == {"order": "develop", "changed": False}
    for case in (
        "missing_ok",
        "not_ok",
        "missing_result",
        "turn_result",
        "save_result",
        "missing_order",
        "invalid_order",
        "missing_changed",
        "invalid_changed",
    ):
        assert payload[case] is None
