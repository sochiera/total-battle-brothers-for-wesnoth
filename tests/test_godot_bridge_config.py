import json
from pathlib import Path

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/bridge_config_probe.gd"
PREFIX = "BRIDGE_CONFIG "


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
