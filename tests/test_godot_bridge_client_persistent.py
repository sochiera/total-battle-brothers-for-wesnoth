import json
import shlex
from pathlib import Path

from godot_runner import run_godot_script
from tbbbridge.persist import save_session
from tbbbridge.session import new_session


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = GAME / "scripts" / "bridge_persistent_api_probe.gd"
PERSISTENT_PROBE = GAME / "scripts" / "bridge_persistent_probe.gd"


def test_persistent_bridge_client_exposes_command_selection_api():
    assert PROBE.is_file(), "missing res://scripts/bridge_persistent_api_probe.gd"

    result = run_godot_script(
        GAME, "res://scripts/bridge_persistent_api_probe.gd", timeout=30
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr


def test_persistent_bridge_switches_to_a_quoted_resume_command_and_executes_it(tmp_path):
    assert PERSISTENT_PROBE.is_file(), "missing res://scripts/bridge_persistent_probe.gd"
    saved_state = tmp_path / "saved-session.json"
    save_session(new_session(seed=73), saved_state)
    state_path = tmp_path / "state file's copy.json"
    prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"

    result = run_godot_script(
        GAME,
        "res://scripts/bridge_persistent_probe.gd",
        prefix,
        str(state_path),
        str(saved_state),
        "73",
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith("PERSISTENT_BRIDGE ")]
    assert len(lines) == 1, result.stdout
    payload = json.loads(lines[0][len("PERSISTENT_BRIDGE ") :])
    assert payload["fresh"] == f"{prefix} serve 73"
    assert "serve --resume" in payload["resumed"]
