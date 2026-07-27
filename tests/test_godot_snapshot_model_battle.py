"""G85.1a: SnapshotModel projects last battle or unambiguous absence."""

import json
from pathlib import Path

from godot_runner import run_godot_script

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PREFIX = "SNAPSHOT_MODEL_BATTLE_TEST "


def test_snapshot_model_projects_battle_or_null():
    """Model exposes battle result+hexes when present; null when absent/invalid.

    Realistic defect: SnapshotModel never projects snapshot['battle'], so the
    consumer cannot read last-battle hexes/result after assault, and cannot
    distinguish pre-battle absence from an empty battle payload.
    """
    result = run_godot_script(GAME, "res://tests/test_snapshot_model_battle.gd")

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    payload = json.loads(lines[0][len(PREFIX) :])

    assert payload["no_battle"] is None
    assert payload["with_battle"] == {
        "result": "defender_win",
        "hexes": [
            {"q": 1, "r": 0, "terrain": "Plains", "side": "attacker", "hp": 0},
            {"q": 2, "r": 0, "terrain": "Plains", "side": "defender", "hp": 15},
        ],
    }
    assert payload["float_coords"] == {
        "result": "attacker_win",
        "hexes": [
            {"q": 1, "r": 0, "terrain": "Forest", "side": "attacker", "hp": 3},
        ],
    }
    assert payload["skips_bad_hexes"] == {
        "result": "draw",
        "hexes": [
            {"q": 1, "r": 0, "terrain": "Plains", "side": "attacker", "hp": 5},
            {"q": 3, "r": 1, "terrain": "Hills", "side": "defender", "hp": 7},
        ],
    }
    # Empty hex list still is a battle (result present) — not "absence".
    assert payload["empty_hexes"] == {"result": "draw", "hexes": []}
    # Missing/invalid battle → unambiguous null, model stays valid.
    assert payload["missing_result"] is None
    assert payload["bad_battle_type"] is None
    assert payload["missing_hexes"] is None
    assert payload["bad_battle_keeps_model"] is True
    assert payload["missing_hexes_keeps_model"] is True
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
