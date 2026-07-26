import json
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
    result = run_godot_script(
        GAME,
        INVALID_CONFIG_PROBE,
        str(tmp_path / "session.json"),
        str(tmp_path / "bridge-started"),
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [
        line for line in result.stdout.splitlines() if line.startswith(INVALID_PREFIX)
    ]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len(INVALID_PREFIX) :]) == {
        "available": True,
        "results": [False, False, False, False],
        "controls_unchanged": True,
        "bridge_started": False,
    }
