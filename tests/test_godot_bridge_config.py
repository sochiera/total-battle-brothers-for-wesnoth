import json
import os
import shutil
from pathlib import Path

import pytest

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/bridge_config_probe.gd"
PREFIX = "BRIDGE_CONFIG "
VALIDITY_PREFIX = "BRIDGE_CONFIG_VALIDITY "
ENVIRONMENT_PROBE = "res://tests/bridge_config_environment_probe.gd"
ENVIRONMENT_PREFIX = "BRIDGE_CONFIG_ENVIRONMENT "
DEFAULT_PROBE = "res://tests/bridge_config_default_probe.gd"
DEFAULT_PREFIX = "BRIDGE_CONFIG_DEFAULT "
DEFAULT_LIVE_PROBE = "res://tests/bridge_config_default_live_probe.gd"
DEFAULT_LIVE_PREFIX = "BRIDGE_CONFIG_DEFAULT_LIVE "


def test_bridge_config_from_values_trims_valid_values_and_rejects_invalid_ones():
    result = run_godot_script(GAME, PROBE, timeout=30)

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert "SCRIPT ERROR" not in result.stderr, result.stderr

    assert json.loads(lines[0][len(PREFIX) :]) == [
        {
            "command": "python3 -m tbbbridge serve 73",
            "state_path": "/tmp/tbb-state.jsonl",
            "seed": 73,
        },
        {
            "command": "bridge --serve",
            "state_path": "state.jsonl",
            "seed": -5,
        },
        None,
        None,
        None,
        None,
        None,
    ]


def test_bridge_config_exposes_single_public_validity_predicate_for_ready_configs():
    result = run_godot_script(GAME, PROBE, timeout=30)

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [
        line for line in result.stdout.splitlines() if line.startswith(VALIDITY_PREFIX)
    ]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len(VALIDITY_PREFIX) :]) == {
        "available": True,
        "results": [True, False, False, False],
    }


def test_bridge_config_from_environment_delegates_environment_values_to_from_values():
    cases = [
        (
            {
                "TBB_BRIDGE_COMMAND": " python -m tbbbridge ",
                "TBB_STATE_PATH": " /tmp/tbb-state.jsonl ",
                "TBB_SEED": "-73",
            },
            {
                "command": "python -m tbbbridge",
                "state_path": "/tmp/tbb-state.jsonl",
                "seed": -73,
            },
        ),
        (
            {
                "TBB_BRIDGE_COMMAND": "bridge",
                "TBB_STATE_PATH": "state.jsonl",
            },
            None,
        ),
        (
            {
                "TBB_BRIDGE_COMMAND": "bridge",
                "TBB_STATE_PATH": "state.jsonl",
                "TBB_SEED": "not-an-integer",
            },
            None,
        ),
    ]

    for overrides, expected in cases:
        environment = dict(os.environ)
        for variable in ("TBB_BRIDGE_COMMAND", "TBB_STATE_PATH", "TBB_SEED"):
            environment.pop(variable, None)
        environment.update(overrides)
        result = run_godot_script(
            GAME, ENVIRONMENT_PROBE, timeout=30, env=environment
        )

        assert result.returncode == 0, result.stderr
        lines = [
            line
            for line in result.stdout.splitlines()
            if line.startswith(ENVIRONMENT_PREFIX)
        ]
        assert len(lines) == 1, result.stdout
        assert "SCRIPT ERROR" not in result.stderr, result.stderr
        assert json.loads(lines[0][len(ENVIRONMENT_PREFIX) :]) == expected


def test_bridge_config_default_values_are_valid_deterministic_and_stay_in_user_data(
    tmp_path,
):
    environment = dict(os.environ)
    for variable in ("TBB_BRIDGE_COMMAND", "TBB_STATE_PATH", "TBB_SEED"):
        environment.pop(variable, None)
    environment["XDG_DATA_HOME"] = str(tmp_path / "xdg-data")

    result = run_godot_script(GAME, DEFAULT_PROBE, timeout=30, env=environment)

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(DEFAULT_PREFIX)]
    assert len(lines) == 1, result.stdout
    payload = json.loads(lines[0][len(DEFAULT_PREFIX) :])

    assert payload["available"] is True
    assert payload["valid"] is True
    assert payload["first"] == payload["second"]
    assert payload["first"]["command"]
    assert Path(payload["first"]["state_path"]).is_absolute()
    assert Path(payload["first"]["state_path"]).is_relative_to(
        Path(payload["user_directory"])
    )
    assert payload["state_file_exists"] is False


@pytest.mark.parametrize("project_with_spaces", [False, True], ids=["plain", "spaces"])
def test_default_config_starts_and_resumes_the_bridge_without_terminal_environment(
    tmp_path, project_with_spaces
):
    environment = dict(os.environ)
    for variable in ("TBB_BRIDGE_COMMAND", "TBB_STATE_PATH", "TBB_SEED", "PYTHONPATH"):
        environment.pop(variable, None)
    environment["XDG_DATA_HOME"] = str(tmp_path / "xdg-data")
    project = GAME
    if project_with_spaces:
        project_root = tmp_path / "project with spaces"
        project = project_root / "game"
        shutil.copytree(GAME, project)
        (project_root / "src").symlink_to(ROOT / "src", target_is_directory=True)
    working_directory = tmp_path / "unrelated working directory"
    working_directory.mkdir()

    result = run_godot_script(
        project,
        DEFAULT_LIVE_PROBE,
        timeout=30,
        env=environment,
        cwd=working_directory,
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [
        line
        for line in result.stdout.splitlines()
        if line.startswith(DEFAULT_LIVE_PREFIX)
    ]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len(DEFAULT_LIVE_PREFIX) :]) == {
        "initial": {"year": 1, "month": 1},
        "advanced": {"year": 1, "month": 2},
        "resumed": {"year": 1, "month": 2},
        "state_exists": True,
    }
