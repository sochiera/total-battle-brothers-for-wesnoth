import json
from pathlib import Path

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/develop_from_bridge_probe.gd"
PREFIX = "DEVELOP_FROM_BRIDGE "
SEND_ORDER_PROBE = "res://tests/send_order_from_bridge_probe.gd"
SEND_ORDER_PREFIX = "SEND_ORDER_FROM_BRIDGE "


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
            "order_status": "Rozkaz rozwoju zmienił stan.",
        },
        "refreshed_without_change": True,
        "unchanged_orders": ["develop"],
        "after_unchanged": {
            "date": "Rok 1, miesiąc 1",
            "result": "Wynik: unchanged",
            "regions": ["Bez zmiany"],
            "order_status": "Rozkaz rozwoju nie zmienił stanu.",
        },
        "rejected": False,
        "failure_orders": ["develop"],
        "after_failure": {
            "date": "Rok 1, miesiąc 1",
            "result": "Wynik: unchanged",
            "regions": ["Bez zmiany"],
            "order_status": "Rozkaz nie powiódł się.",
        },
        "refreshed_without_order_result": True,
        "missing_order_result_orders": ["develop"],
        "after_missing_order_result": {
            "date": "Rok 1, miesiąc 1",
            "result": "Wynik: missing result",
            "regions": ["Bez wyniku"],
            "order_status": "",
        },
    }


def test_send_order_from_bridge_uses_the_order_result_status_for_recruitment():
    result = run_godot_script(GAME, SEND_ORDER_PROBE, timeout=30)

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [
        line for line in result.stdout.splitlines() if line.startswith(SEND_ORDER_PREFIX)
    ]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len(SEND_ORDER_PREFIX) :]) == {
        "available": True,
        "refreshed": True,
        "recruit_orders": ["recruit"],
        "after_recruit": {
            "date": "Rok 2, miesiąc 3",
            "result": "Wynik: recruited",
            "regions": ["Po rekrutacji"],
            "order_status": "Rozkaz rekrutacji zmienił stan.",
        },
        "rejected": False,
        "failure_orders": ["recruit"],
        "after_failure": {
            "date": "Rok 2, miesiąc 3",
            "result": "Wynik: recruited",
            "regions": ["Po rekrutacji"],
            "order_status": "Rozkaz nie powiódł się.",
        },
    }
