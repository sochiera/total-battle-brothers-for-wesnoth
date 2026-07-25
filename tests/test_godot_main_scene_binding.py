import json
from pathlib import Path

import pytest

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
FIXTURE = GAME / "tests" / "fixtures" / "session_snapshot.json"
PREFIX = "SCENE_TEXT "


def test_scene_bind_probe_applies_model_date_regions_and_result(tmp_path):
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    response_path = tmp_path / "response.json"
    response_path.write_text(
        json.dumps({"ok": True, "snapshot": fixture}), encoding="utf-8"
    )

    result = run_godot_script(
        GAME, "res://scripts/scene_bind_probe.gd", str(response_path), timeout=30
    )

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert "SCRIPT ERROR" not in result.stderr, result.stderr

    payload = json.loads(lines[0][len(PREFIX) :])
    assert payload["date"] == (
        f"Rok {fixture['calendar']['year']}, miesiąc {fixture['calendar']['month']}"
    )
    assert payload["result"] == f"Wynik: {fixture['result']['player_result']}"
    assert payload["regions"] == len(fixture["map"]["regions"])
    assert payload["region_names"] == [
        region["name"] for region in fixture["map"]["regions"]
    ]


def test_scene_bind_probe_uses_result_from_model_not_constant(tmp_path):
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    response_fixture = fixture.copy()
    response_result = fixture["result"].copy()
    response_result["player_result"] = "won"
    response_fixture["result"] = response_result
    response_path = tmp_path / "response.json"
    response_path.write_text(
        json.dumps({"ok": True, "snapshot": response_fixture}), encoding="utf-8"
    )

    result = run_godot_script(
        GAME, "res://scripts/scene_bind_probe.gd", str(response_path), timeout=30
    )

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert "SCRIPT ERROR" not in result.stderr, result.stderr

    payload = json.loads(lines[0][len(PREFIX) :])
    assert payload["date"] == (
        f"Rok {fixture['calendar']['year']}, miesiąc {fixture['calendar']['month']}"
    )
    assert payload["result"] == "Wynik: won"
    assert payload["regions"] == len(fixture["map"]["regions"])


def test_scene_bind_probe_skips_regions_without_string_name(tmp_path):
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    response_fixture = fixture.copy()
    response_map = fixture["map"].copy()
    response_regions = fixture["map"]["regions"].copy()
    response_regions.extend(["nie-region", {"col": 9}])
    response_map["regions"] = response_regions
    response_fixture["map"] = response_map
    response_path = tmp_path / "response.json"
    response_path.write_text(
        json.dumps({"ok": True, "snapshot": response_fixture}), encoding="utf-8"
    )

    result = run_godot_script(
        GAME, "res://scripts/scene_bind_probe.gd", str(response_path), timeout=30
    )

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert "SCRIPT ERROR" not in result.stderr, result.stderr

    payload = json.loads(lines[0][len(PREFIX) :])
    assert payload["region_names"] == [
        region["name"] for region in fixture["map"]["regions"]
    ]


def test_scene_bind_probe_is_idempotent_for_repeated_model_application(tmp_path):
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    response_path = tmp_path / "response.json"
    response_path.write_text(
        json.dumps({"ok": True, "snapshot": fixture}), encoding="utf-8"
    )

    single = run_godot_script(
        GAME, "res://scripts/scene_bind_probe.gd", str(response_path), timeout=30
    )
    repeated = run_godot_script(
        GAME,
        "res://scripts/scene_bind_probe.gd",
        str(response_path),
        "3",
        timeout=30,
    )

    assert repeated.returncode == 0, repeated.stderr
    lines = [line for line in repeated.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, repeated.stdout
    assert "SCRIPT ERROR" not in repeated.stderr, repeated.stderr

    single_lines = [line for line in single.stdout.splitlines() if line.startswith(PREFIX)]
    assert single.returncode == 0, single.stderr
    assert len(single_lines) == 1, single.stdout
    payload = json.loads(lines[0][len(PREFIX) :])
    assert payload == json.loads(single_lines[0][len(PREFIX) :])
    assert payload["regions"] == len(fixture["map"]["regions"])
    assert payload["region_names"] == [
        region["name"] for region in fixture["map"]["regions"]
    ]


@pytest.mark.parametrize("applications", ["0", "nie-liczba"])
def test_scene_bind_probe_rejects_invalid_application_count(tmp_path, applications):
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    response_path = tmp_path / "response.json"
    response_path.write_text(
        json.dumps({"ok": True, "snapshot": fixture}), encoding="utf-8"
    )

    result = run_godot_script(
        GAME,
        "res://scripts/scene_bind_probe.gd",
        str(response_path),
        applications,
        timeout=30,
    )

    assert result.returncode == 2
    assert not any(line.startswith(PREFIX) for line in result.stdout.splitlines())
