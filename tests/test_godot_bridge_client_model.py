import json
import shlex
from pathlib import Path

from godot_runner import run_godot_script
from tbbbridge.session import new_session


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = GAME / "scripts" / "bridge_model_probe.gd"
PREFIX = "BRIDGE_MODEL "
SEED = 7


def _model_output(result):
    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    return lines[0][len(PREFIX) :]


def test_bridge_model_probe_projects_snapshot_from_the_real_bridge(tmp_path):
    assert PROBE.is_file(), "missing res://scripts/bridge_model_probe.gd"

    request_path = tmp_path / "bridge-request.jsonl"
    command = (
        f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} "
        f"python3 -m tbbbridge serve {SEED}"
    )
    result = run_godot_script(
        GAME,
        "res://scripts/bridge_model_probe.gd",
        command,
        str(request_path),
        timeout=30,
    )

    snapshot = new_session(SEED).snapshot()
    payload = json.loads(_model_output(result))
    assert payload == {
        "year": snapshot["calendar"]["year"],
        "month": snapshot["calendar"]["month"],
        "regions": len(snapshot["map"]["regions"]),
        "region_names": [
            region["name"]
            for region in snapshot["map"]["regions"]
            if isinstance(region, dict) and isinstance(region.get("name"), str)
        ],
        "player_result": snapshot["result"]["player_result"],
    }
    assert json.loads(request_path.read_text(encoding="utf-8").splitlines()[0]) == {
        "type": "snapshot"
    }


def test_bridge_model_probe_returns_null_for_unusable_responses(tmp_path):
    assert PROBE.is_file(), "missing res://scripts/bridge_model_probe.gd"

    for command in ("exit 3", "printf '%s\\n' '{\"ok\": false, \"error\": \"boom\"}'"):
        result = run_godot_script(
            GAME,
            "res://scripts/bridge_model_probe.gd",
            command,
            str(tmp_path / "bridge-request.jsonl"),
            timeout=30,
        )
        assert _model_output(result) == "null"


def test_bridge_model_probe_reports_a_missing_command():
    assert PROBE.is_file(), "missing res://scripts/bridge_model_probe.gd"

    result = run_godot_script(
        GAME, "res://scripts/bridge_model_probe.gd", timeout=30
    )

    assert result.returncode == 2
    assert PREFIX not in result.stdout
    assert result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
