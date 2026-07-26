import json
import shlex
from pathlib import Path

from godot_runner import run_godot_script
from tbbbridge.session import new_session


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = GAME / "tests" / "bridge_model_status_probe.gd"
PREFIX = "BRIDGE_MODEL_STATUS "
SEED = 7
STATUS_KEYS = ("morale", "settlements", "parties")


def test_snapshot_model_projects_player_duchy_status_from_live_bridge(tmp_path):
    assert PROBE.is_file(), "missing test probe for player-duchy status"
    request_path = tmp_path / "bridge-request.jsonl"
    command = (
        f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} "
        f"python3 -m tbbbridge serve {SEED}"
    )
    result = run_godot_script(
        GAME,
        "res://tests/bridge_model_status_probe.gd",
        command,
        str(request_path),
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    snapshot = new_session(SEED).snapshot()
    player_duchy = next(
        duchy for duchy in snapshot["duchies"] if duchy["id"] == snapshot["player_duchy"]
    )
    assert json.loads(lines[0][len(PREFIX) :]) == {
        key: player_duchy[key] for key in STATUS_KEYS
    }
    assert json.loads(request_path.read_text(encoding="utf-8").splitlines()[0]) == {
        "type": "snapshot"
    }
