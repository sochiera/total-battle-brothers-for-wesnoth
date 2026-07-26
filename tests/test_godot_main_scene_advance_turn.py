import json
from pathlib import Path

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/advance_turn_from_bridge_probe.gd"
PREFIX = "ADVANCE_TURN_FROM_BRIDGE "


def probe_payload(result):
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def test_advance_turn_from_bridge_applies_post_turn_model_once_and_preserves_scene_on_failure():
    result = run_godot_script(GAME, PROBE, timeout=30)

    assert probe_payload(result) == {
        "available": True,
        "refreshed": True,
        "success_calls": 1,
        "success_snapshot_calls": 0,
        "after_success": {
            "date": "Rok 8, miesiąc 4",
            "result": "Wynik: after-turn",
            "regions": ["Po turze"],
        },
        "rejected": False,
        "failure_calls": 1,
        "failure_snapshot_calls": 0,
        "after_failure": {
            "date": "Rok 8, miesiąc 4",
            "result": "Wynik: after-turn",
            "regions": ["Po turze"],
        },
    }


def test_advance_turn_from_bridge_probe_reports_a_reliable_nonzero_exit_on_failure():
    result = run_godot_script(GAME, PROBE, "--force-failure", timeout=30)

    assert result.returncode != 0
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    assert "advance_turn_from_bridge_probe: forced failure" in result.stderr
