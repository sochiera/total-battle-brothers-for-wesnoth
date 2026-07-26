import json
import shlex
import shutil
from pathlib import Path

from godot_runner import run_godot_script
from tbbbridge.session import new_session


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = GAME / "scripts" / "scene_live_probe.gd"
PREFIX = "SCENE_LIVE "
SEED = 7


def scene_live_payload(result):
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    return json.loads(lines[0][len(PREFIX) :])


def assert_probe_failure(result, message):
    assert result.returncode == 2
    assert message in result.stderr
    assert PREFIX not in result.stdout


def test_scene_live_probe_renders_snapshot_from_real_bridge(tmp_path):
    assert PROBE.is_file(), "missing res://scripts/scene_live_probe.gd"

    command = (
        f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} "
        f"python3 -m tbbbridge serve {SEED}"
    )
    result = run_godot_script(
        GAME,
        "res://scripts/scene_live_probe.gd",
        command,
        str(tmp_path / "bridge-request.jsonl"),
        timeout=30,
    )

    assert result.returncode == 0, result.stderr

    snapshot = new_session(SEED).snapshot()
    payload = scene_live_payload(result)
    assert payload == {
        "refreshed": True,
        "date": (
            f"Rok {snapshot['calendar']['year']}, "
            f"miesiąc {snapshot['calendar']['month']}"
        ),
        "result": f"Wynik: {snapshot['result']['player_result']}",
        "regions": len(snapshot["map"]["regions"]),
        "region_names": [
            region["name"] for region in snapshot["map"]["regions"]
        ],
    }


def test_scene_live_probe_leaves_controls_empty_when_bridge_fails(tmp_path):
    result = run_godot_script(
        GAME,
        "res://scripts/scene_live_probe.gd",
        "false",
        str(tmp_path / "bridge-request.jsonl"),
        timeout=30,
    )

    assert result.returncode == 0, result.stderr

    payload = scene_live_payload(result)
    assert payload == {
        "refreshed": False,
        "date": "",
        "result": "",
        "regions": 0,
        "region_names": [],
    }


def test_scene_live_probe_rejects_missing_bridge_command():
    result = run_godot_script(
        GAME, "res://scripts/scene_live_probe.gd", timeout=30
    )

    assert_probe_failure(result, "scene_live_probe: missing bridge command")


def test_scene_live_probe_reports_missing_main_scene(tmp_path):
    project = tmp_path / "game"
    project.mkdir()
    shutil.copy2(GAME / "project.godot", project / "project.godot")
    shutil.copytree(GAME / "scripts", project / "scripts")

    result = run_godot_script(
        project,
        "res://scripts/scene_live_probe.gd",
        "false",
        timeout=30,
    )

    assert_probe_failure(result, "scene_live_probe: cannot load main scene")
