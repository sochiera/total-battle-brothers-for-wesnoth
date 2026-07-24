import json
from pathlib import Path

from tbbbridge.session import new_session


def test_session_snapshot_fixture_is_valid_and_matches_fresh_public_snapshot():
    """G71.1a1: fixture jest kanonicznym snapshotem świeżej sesji."""
    fixture_path = (
        Path(__file__).resolve().parents[1]
        / "game"
        / "tests"
        / "fixtures"
        / "session_snapshot.json"
    )

    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

    assert fixture == new_session().snapshot()
    assert fixture["calendar"]["year"] == 1
    assert fixture["calendar"]["month"] == 1
    assert fixture["map"]["regions"]
    assert "player_result" in fixture["result"]
