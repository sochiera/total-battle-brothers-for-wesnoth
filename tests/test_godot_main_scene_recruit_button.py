import json
from pathlib import Path

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/recruit_button_binding_probe.gd"
PREFIX = "RECRUIT_BUTTON_BINDING "


def test_recruit_button_is_a_single_safe_binding_and_renders_the_post_order_snapshot():
    result = run_godot_script(GAME, PROBE, timeout=30)

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len(PREFIX) :]) == {
        "before_bind": {
            "date": "",
            "result": "",
            "regions": [],
            "duchy_status": "",
            "order_status": "",
        },
        "after_unbound_press": {
            "date": "",
            "result": "",
            "regions": [],
            "duchy_status": "",
            "order_status": "",
        },
        "orders": ["recruit", "recruit"],
        "after_changed_press": {
            "date": "Rok 3, miesiąc 4",
            "result": "Wynik: zrekrutowano",
            "regions": ["Północ"],
            "duchy_status": "Morale: 2, osady: 3, oddziały: 1",
            "order_status": "Rozkaz rekrutacji zmienił stan.",
        },
        "after_unchanged_press": {
            "date": "Rok 3, miesiąc 4",
            "result": "Wynik: brak rekrutów",
            "regions": ["Północ"],
            "duchy_status": "Morale: 2, osady: 3, oddziały: 1",
            "order_status": "Rozkaz rekrutacji nie zmienił stanu.",
        },
    }
