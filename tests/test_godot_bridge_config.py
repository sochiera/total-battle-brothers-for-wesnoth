import json
import os
from pathlib import Path

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/bridge_config_probe.gd"
PREFIX = "BRIDGE_CONFIG "
ENVIRONMENT_PROBE = "res://tests/bridge_config_environment_probe.gd"
ENVIRONMENT_PREFIX = "BRIDGE_CONFIG_ENVIRONMENT "


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
