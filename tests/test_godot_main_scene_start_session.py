import json
import os
import shlex
from pathlib import Path

from godot_runner import run_godot_script
from tbbbridge.session import new_session


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/start_session_probe.gd"
INVALID_CONFIG_PROBE = "res://tests/start_session_invalid_config_probe.gd"
PREFIX = "START_SESSION "
INVALID_PREFIX = "START_SESSION_INVALID "
ENVIRONMENT_AUTOSTART_PROBE = "res://tests/environment_autostart_probe.gd"
ENVIRONMENT_AUTOSTART_PREFIX = "ENVIRONMENT_AUTOSTART "
SEED = 73


def _controls(snapshot: dict) -> dict:
    return {
        "date": (
            f"Rok {snapshot['calendar']['year']}, "
            f"miesiąc {snapshot['calendar']['month']}"
        ),
        "result": f"Wynik: {snapshot['result']['player_result']}",
        "regions": [region["name"] for region in snapshot["map"]["regions"]],
    }


def test_start_session_renders_fresh_game_without_advancing_then_binds_next_turn(tmp_path):
    command_prefix = (
        f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    )
    state_path = tmp_path / "session.json"
    result = run_godot_script(
        GAME, PROBE, command_prefix, str(state_path), str(SEED), timeout=30
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout

    session = new_session(SEED)
    assert json.loads(lines[0][len(PREFIX) :]) == {
        "available": True,
        "started": True,
        "state_exists_after_start": False,
        "after_start": _controls(session.snapshot()),
        "after_first_press": _controls(session.next_turn().snapshot()),
    }


def test_start_session_rejects_invalid_config_without_changing_scene_or_starting_bridge(tmp_path):
    environment = os.environ.copy()
    environment["XDG_DATA_HOME"] = str(tmp_path / "xdg-data")
    result = run_godot_script(
        GAME,
        INVALID_CONFIG_PROBE,
        str(tmp_path / "session.json"),
        str(tmp_path / "bridge-started"),
        timeout=30,
        env=environment,
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [
        line for line in result.stdout.splitlines() if line.startswith(INVALID_PREFIX)
    ]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len(INVALID_PREFIX) :]) == {
        "available": True,
        "results": [False] * 11,
        "controls_unchanged": True,
        "bridge_started": False,
        "state_exists": False,
        "request_exists": False,
    }


def test_scene_autostarts_from_environment_and_resumes_after_next_turn(tmp_path):
    state_path = tmp_path / "autostart-session.json"
    environment = os.environ.copy()
    environment.update(
        {
            "TBB_BRIDGE_COMMAND": (
                f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
            ),
            "TBB_STATE_PATH": str(state_path),
            "TBB_SEED": str(SEED),
        }
    )

    first = run_godot_script(
        GAME,
        ENVIRONMENT_AUTOSTART_PROBE,
        "--press",
        timeout=30,
        env=environment,
    )
    second = run_godot_script(
        GAME, ENVIRONMENT_AUTOSTART_PROBE, timeout=30, env=environment
    )

    for result in (first, second):
        assert result.returncode == 0, result.stderr
        assert "SCRIPT ERROR" not in result.stderr, result.stderr

    def payload(result):
        lines = [
            line
            for line in result.stdout.splitlines()
            if line.startswith(ENVIRONMENT_AUTOSTART_PREFIX)
        ]
        assert len(lines) == 1, result.stdout
        return json.loads(lines[0][len(ENVIRONMENT_AUTOSTART_PREFIX) :])

    fresh = new_session(SEED)
    after_turn = fresh.next_turn()
    assert payload(first) == {
        "after_start": _controls(fresh.snapshot()),
        "after_press": _controls(after_turn.snapshot()),
        "state_exists": True,
    }
    assert payload(second) == {
        "after_start": _controls(after_turn.snapshot()),
        "after_press": _controls(after_turn.snapshot()),
        "state_exists": True,
    }


def test_scene_entry_without_environment_is_a_noop():
    environment = os.environ.copy()
    for variable in ("TBB_BRIDGE_COMMAND", "TBB_STATE_PATH", "TBB_SEED"):
        environment.pop(variable, None)

    result = run_godot_script(
        GAME, ENVIRONMENT_AUTOSTART_PROBE, timeout=30, env=environment
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [
        line
        for line in result.stdout.splitlines()
        if line.startswith(ENVIRONMENT_AUTOSTART_PREFIX)
    ]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len(ENVIRONMENT_AUTOSTART_PREFIX) :]) == {
        "after_start": {"date": "", "result": "", "regions": []},
        "after_press": {"date": "", "result": "", "regions": []},
        "state_exists": False,
    }
