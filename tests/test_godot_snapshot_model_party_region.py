import json
from pathlib import Path

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PREFIX = "SNAPSHOT_MODEL_PARTY_REGION_TEST "


def test_snapshot_model_projects_only_the_players_party_region():
    result = run_godot_script(GAME, "res://tests/test_snapshot_model_party_region.gd")

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    payload = json.loads(lines[0][len(PREFIX) :])
    assert payload == {
        "no_party": None,
        "player_party": "player lands",
        "missing_player": None,
        "foreign_party": None,
        "empty_name": "",
        "invalid_player": None,
        "invalid_region": None,
        "invalid_party": None,
        "party_without_owner": None,
    }
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
