import json
from pathlib import Path

import pytest

from godot_runner import run_godot_script

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
FIXTURE = GAME / "tests" / "fixtures" / "session_snapshot.json"

PREFIX = "SNAPSHOT_MODEL "


def assert_null_probe_result(result):
    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len(PREFIX) :]) is None
    assert "SCRIPT ERROR" not in result.stderr, result.stderr


def test_snapshot_probe_prints_projection_of_bridge_response(tmp_path):
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    response_path = tmp_path / "response.json"
    response_path.write_text(
        json.dumps({"ok": True, "snapshot": fixture}), encoding="utf-8"
    )

    result = run_godot_script(
        GAME, "res://tests/snapshot_probe.gd", str(response_path), timeout=30
    )

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout

    payload = json.loads(lines[0][len(PREFIX) :])
    assert payload["year"] == fixture["calendar"]["year"]
    assert payload["month"] == fixture["calendar"]["month"]
    assert payload["regions"] == fixture["map"]["regions"]
    assert payload["player_result"] == fixture["result"]["player_result"]


def test_snapshot_probe_prints_null_for_error_response(tmp_path):
    response_path = tmp_path / "response.json"
    response_path.write_text(
        json.dumps({"ok": False, "error": "boom"}), encoding="utf-8"
    )

    result = run_godot_script(
        GAME, "res://tests/snapshot_probe.gd", str(response_path), timeout=30
    )

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len(PREFIX) :]) is None


def test_snapshot_probe_prints_null_when_snapshot_key_missing(tmp_path):
    response_path = tmp_path / "response.json"
    response_path.write_text(json.dumps({"ok": True}), encoding="utf-8")

    result = run_godot_script(
        GAME, "res://tests/snapshot_probe.gd", str(response_path), timeout=30
    )

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len(PREFIX) :]) is None


@pytest.mark.parametrize("section", ["calendar", "map", "result"])
def test_snapshot_probe_prints_null_when_snapshot_section_missing(tmp_path, section):
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    snapshot = {key: value for key, value in fixture.items() if key != section}
    response_path = tmp_path / "response.json"
    response_path.write_text(
        json.dumps({"ok": True, "snapshot": snapshot}), encoding="utf-8"
    )

    result = run_godot_script(
        GAME, "res://tests/snapshot_probe.gd", str(response_path), timeout=30
    )

    assert_null_probe_result(result)


@pytest.mark.parametrize(
    ("section", "leaf"),
    [
        ("calendar", "year"),
        ("calendar", "month"),
        ("map", "regions"),
        ("result", "player_result"),
    ],
)
def test_snapshot_probe_prints_null_when_required_leaf_missing(
    tmp_path, section, leaf
):
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    snapshot = fixture.copy()
    section_copy = snapshot[section].copy()
    del section_copy[leaf]
    snapshot[section] = section_copy
    response_path = tmp_path / "response.json"
    response_path.write_text(
        json.dumps({"ok": True, "snapshot": snapshot}), encoding="utf-8"
    )

    result = run_godot_script(
        GAME, "res://tests/snapshot_probe.gd", str(response_path), timeout=30
    )

    assert_null_probe_result(result)


@pytest.mark.parametrize(
    ("section", "leaf", "invalid_value"),
    [
        ("calendar", "year", "1"),
        ("calendar", "month", None),
        ("map", "regions", "nie-lista"),
        ("result", "player_result", 5),
    ],
)
def test_snapshot_probe_prints_null_when_required_leaf_has_invalid_type(
    tmp_path, section, leaf, invalid_value
):
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    snapshot = fixture.copy()
    section_copy = snapshot[section].copy()
    section_copy[leaf] = invalid_value
    snapshot[section] = section_copy
    response_path = tmp_path / "response.json"
    response_path.write_text(
        json.dumps({"ok": True, "snapshot": snapshot}), encoding="utf-8"
    )

    result = run_godot_script(
        GAME, "res://tests/snapshot_probe.gd", str(response_path), timeout=30
    )

    assert_null_probe_result(result)


def test_snapshot_probe_prints_null_when_snapshot_map_is_not_dictionary(tmp_path):
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    snapshot = dict(fixture)
    snapshot["map"] = "nie-slownik"
    response_path = tmp_path / "response.json"
    response_path.write_text(
        json.dumps({"ok": True, "snapshot": snapshot}), encoding="utf-8"
    )

    result = run_godot_script(
        GAME, "res://tests/snapshot_probe.gd", str(response_path), timeout=30
    )

    assert_null_probe_result(result)


def test_snapshot_probe_prints_null_when_snapshot_is_not_dictionary(tmp_path):
    response_path = tmp_path / "response.json"
    response_path.write_text(
        json.dumps({"ok": True, "snapshot": "nie-slownik"}), encoding="utf-8"
    )

    result = run_godot_script(
        GAME, "res://tests/snapshot_probe.gd", str(response_path), timeout=30
    )

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len(PREFIX) :]) is None
