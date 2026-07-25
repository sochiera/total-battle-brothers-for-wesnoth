import json
from pathlib import Path

from godot_runner import run_godot_script

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
FIXTURE = GAME / "tests" / "fixtures" / "session_snapshot.json"

PREFIX = "SNAPSHOT_MODEL "


def test_snapshot_probe_prints_projection_of_bridge_response(tmp_path):
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    response_path = tmp_path / "response.json"
    response_path.write_text(
        json.dumps({"ok": True, "snapshot": fixture}), encoding="utf-8"
    )

    result = run_godot_script(
        GAME, "res://scripts/snapshot_probe.gd", str(response_path), timeout=30
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
        GAME, "res://scripts/snapshot_probe.gd", str(response_path), timeout=30
    )

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len(PREFIX) :]) is None


def test_snapshot_probe_prints_null_when_snapshot_key_missing(tmp_path):
    response_path = tmp_path / "response.json"
    response_path.write_text(json.dumps({"ok": True}), encoding="utf-8")

    result = run_godot_script(
        GAME, "res://scripts/snapshot_probe.gd", str(response_path), timeout=30
    )

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len(PREFIX) :]) is None


def test_snapshot_probe_prints_null_when_snapshot_is_not_dictionary(tmp_path):
    response_path = tmp_path / "response.json"
    response_path.write_text(
        json.dumps({"ok": True, "snapshot": "nie-slownik"}), encoding="utf-8"
    )

    result = run_godot_script(
        GAME, "res://scripts/snapshot_probe.gd", str(response_path), timeout=30
    )

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len(PREFIX) :]) is None
