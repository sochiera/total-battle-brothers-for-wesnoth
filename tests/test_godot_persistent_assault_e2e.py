import json
import shlex
from pathlib import Path

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/persistent_assault_process_probe.gd"
PREFIX = "PERSISTENT_ASSAULT_PROCESS "
SEED = 73


def _run_process(command_prefix: str, state_path: Path, request_path: Path, phase: str) -> dict:
    result = run_godot_script(
        GAME,
        PROBE,
        command_prefix,
        str(state_path),
        str(request_path),
        str(SEED),
        phase,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def test_assault_button_persists_battle_then_no_change_across_godot_processes(tmp_path):
    state_path = tmp_path / "persistent-assault-session.json"
    request_path = tmp_path / "bridge-request.jsonl"
    command_prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"

    prepared = _run_process(command_prefix, state_path, request_path, "prepare")
    battle = _run_process(command_prefix, state_path, request_path, "battle")
    unchanged = _run_process(command_prefix, state_path, request_path, "unchanged")

    assert prepared["state_exists"] is True
    assert battle["session_command"] == f"{command_prefix} serve --resume '{state_path}'"
    assert unchanged["session_command"] == f"{command_prefix} serve --resume '{state_path}'"
    assert prepared["controls_after_muster"]["party_position"] == "Położenie oddziału: player lands"
    assert prepared["controls"]["party_position"] == "Położenie oddziału: border"
    assert battle["controls_before_order"]["party_position"] == "Położenie oddziału: border"
    assert battle["controls"]["party_position"] == "Położenie oddziału: brak"
    assert battle["controls"]["order_status"] == "Szturm: porażka (straty: 0, wróg: 0)."
    assert unchanged["controls"]["order_status"] == "Rozkaz szturmu nie zmienił stanu."
    assert prepared["controls"]["date"] == prepared["controls_before_order"]["date"]
    assert battle["controls"]["date"] == prepared["controls"]["date"]
    assert unchanged["controls"]["date"] == battle["controls"]["date"]
