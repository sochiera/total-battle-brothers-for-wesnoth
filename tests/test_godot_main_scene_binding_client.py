import json
from pathlib import Path

from godot_runner import PLAYER_RESULT_PL, run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/bind_client_probe.gd"
PREFIX = "BIND_CLIENT "


def probe_payload(result):
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def test_bind_client_advances_once_per_press_rebinds_without_duplicate_connections_and_preserves_controls_on_failure():
    result = run_godot_script(GAME, PROBE, timeout=30)

    assert probe_payload(result) == {
        "available": True,
        "before_bind": {"date": "", "result": "", "regions": []},
        "after_unbound_press": {"date": "", "result": "", "regions": []},
        "first_calls": 2,
        "after_first_press": {
            "date": "Rok 2, miesiąc 3",
            "result": PLAYER_RESULT_PL["ongoing"],
            "regions": ["Pierwsza"],
        },
        "after_second_press": {
            "date": "Rok 2, miesiąc 4",
            "result": PLAYER_RESULT_PL["victory"],
            "regions": ["Druga"],
        },
        "second_calls": 2,
        "after_rebind_press": {
            "date": "Rok 7, miesiąc 8",
            "result": PLAYER_RESULT_PL["draw"],
            "regions": ["Nowa"],
        },
        "after_failed_press": {
            "date": "Rok 7, miesiąc 8",
            "result": PLAYER_RESULT_PL["draw"],
            "regions": ["Nowa"],
        },
    }


def test_bind_client_probe_reports_a_reliable_nonzero_exit_on_failure():
    result = run_godot_script(GAME, PROBE, "--force-failure", timeout=30)

    assert result.returncode != 0
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    assert "bind_client_probe: forced failure" in result.stderr
