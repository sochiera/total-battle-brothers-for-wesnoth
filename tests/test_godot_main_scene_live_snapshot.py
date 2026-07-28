import json
from pathlib import Path

from godot_runner import map_player_result, run_godot_script
from tbbbridge.session import new_session


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
FIXTURE = GAME / "tests" / "fixtures" / "session_snapshot.json"
PREFIX = "SCENE_TEXT "


def test_scene_bind_probe_applies_live_snapshot_after_three_turns(tmp_path, monkeypatch):
    session = new_session()
    for _ in range(3):
        session = session.next_turn()
    snapshot = session.snapshot()
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert snapshot != fixture
    assert (snapshot["calendar"]["year"], snapshot["calendar"]["month"]) != (
        fixture["calendar"]["year"],
        fixture["calendar"]["month"],
    )

    response_path = tmp_path / "response.json"
    response_path.write_text(
        json.dumps({"ok": True, "snapshot": snapshot}), encoding="utf-8"
    )
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg_data"))
    result = run_godot_script(
        GAME, "res://tests/scene_bind_probe.gd", str(response_path), timeout=30
    )

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert "SCRIPT ERROR" not in result.stderr, result.stderr

    payload = json.loads(lines[0][len(PREFIX) :])
    assert payload["date"] == (
        f"Rok {snapshot['calendar']['year']}, miesiąc {snapshot['calendar']['month']}"
    )
    assert payload["result"] == map_player_result(snapshot['result']['player_result'])
    player_status = next(
        duchy
        for duchy in snapshot["duchies"]
        if duchy["id"] == snapshot["player_duchy"]
    )
    assert payload["duchy_status"] == (
        f"Morale: {player_status['morale']}, "
        f"osady: {player_status['settlements']}, "
        f"oddziały: {player_status['parties']}"
    )
    assert payload["regions"] == len(snapshot["map"]["regions"])
    assert payload["region_names"] == [
        region["name"] for region in snapshot["map"]["regions"]
    ]


def test_scene_bind_probe_clears_status_when_the_next_model_has_no_player_duchy(
    tmp_path,
):
    snapshot = json.loads(FIXTURE.read_text(encoding="utf-8"))
    response_path = tmp_path / "response.json"
    response_path.write_text(
        json.dumps({"ok": True, "snapshot": snapshot}), encoding="utf-8"
    )

    result = run_godot_script(
        GAME,
        "res://tests/scene_bind_probe.gd",
        str(response_path),
        "1",
        "clear_status",
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert "SCRIPT ERROR" not in result.stderr, result.stderr

    payload = json.loads(lines[0][len(PREFIX) :])
    assert payload["duchy_status_before_clear"] == "Morale: 0, osady: 1, oddziały: 0"
    assert payload["duchy_status"] == ""
