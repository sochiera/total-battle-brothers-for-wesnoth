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
    # G92.2a AC4: fresh public snapshot carries five regions and two keeps/side
    # without adding snapshot fields (shape stays calendar/player_duchy/duchies/map/result).
    assert list(fixture.keys()) == [
        "calendar",
        "player_duchy",
        "duchies",
        "map",
        "result",
    ]
    assert [region["name"] for region in fixture["map"]["regions"]] == [
        "player lands",
        "player outpost",
        "border",
        "ai outpost",
        "ai lands",
    ]
    by_id = {duchy["id"]: duchy for duchy in fixture["duchies"]}
    assert by_id["player"]["settlements"] == 2
    assert by_id["ai"]["settlements"] == 2
    assert "player_result" in fixture["result"]
