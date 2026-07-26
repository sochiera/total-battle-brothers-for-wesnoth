import json
import shlex
from pathlib import Path

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/persistent_muster_process_probe.gd"
PREFIX = "PERSISTENT_MUSTER_PROCESS "
SEED = 73


def _run_process(command_prefix: str, state_path: Path, request_path: Path) -> dict:
    result = run_godot_script(
        GAME,
        PROBE,
        command_prefix,
        str(state_path),
        str(request_path),
        str(SEED),
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def test_muster_button_persists_across_two_godot_processes(tmp_path):
    state_path = tmp_path / "persistent-muster-session.json"
    request_path = tmp_path / "bridge-request.jsonl"
    command_prefix = (
        f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    )

    first = _run_process(command_prefix, state_path, request_path)
    second = _run_process(command_prefix, state_path, request_path)

    assert first["state_exists"] is True
    assert first["controls"]["order_status"] == "Rozkaz zbiórki zmienił stan."
    assert second["controls"]["order_status"] == "Rozkaz zbiórki nie zmienił stanu."
    assert second["controls"]["date"] == first["controls"]["date"]
    assert second["session_command"] == (
        f"{command_prefix} serve --resume '{state_path}'"
    )
