import json
from pathlib import Path

from godot_runner import run_godot_script

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
FIXTURE = GAME / "tests" / "fixtures" / "session_snapshot.json"
PREFIX = "SNAPSHOT_MODEL_TEST "
STATUS_KEYS = ("morale", "settlements", "parties")


def test_snapshot_model_projects_player_duchy_status_and_preserves_base_fields():
    result = run_godot_script(GAME, "res://tests/test_snapshot_model.gd")
    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    payload = json.loads(lines[0][len(PREFIX) :])
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    expected_base = {
        "year": fixture["calendar"]["year"],
        "month": fixture["calendar"]["month"],
        "regions": fixture["map"]["regions"],
        "player_result": fixture["result"]["player_result"],
    }
    expected_status = {
        key: fixture["duchies"][0][key]
        for key in STATUS_KEYS
    }

    assert payload["matched"] == {
        **expected_base,
        "player_duchy_status": expected_status,
    }
    for case in ("no_player", "no_match", "empty_duchies", "missing_duchies"):
        assert payload[case] == {**expected_base, "player_duchy_status": None}
    assert payload["float_status"] == {
        **expected_base,
        "player_duchy_status": {"morale": 0.5, "settlements": 1.5, "parties": 2.5},
    }
    for leaf in STATUS_KEYS:
        assert payload["malformed_statuses"][f"missing_{leaf}"] == {
            **expected_base,
            "player_duchy_status": None,
        }
        assert payload["malformed_statuses"][f"invalid_{leaf}"] == {
            **expected_base,
            "player_duchy_status": None,
        }
