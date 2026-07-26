import json
from pathlib import Path

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = GAME / "tests" / "order_result_march_status_probe.gd"
PREFIX = "ORDER_MARCH_STATUS_TEXT "


def test_godot_order_result_returns_distinct_polish_status_text_for_march():
    assert PROBE.is_file(), "missing res://tests/order_result_march_status_probe.gd"

    result = run_godot_script(GAME, "res://tests/order_result_march_status_probe.gd", timeout=30)

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    payload = json.loads(lines[0][len(PREFIX) :])

    assert payload == {
        "march_changed": "Rozkaz marszu zmienił stan.",
        "march_unchanged": "Rozkaz marszu nie zmienił stanu.",
        "unknown_order": "",
        "missing_changed": "",
        "invalid_changed": "",
    }
