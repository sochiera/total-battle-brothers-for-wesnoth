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
    """G117.1c AC1: a real muster remains visible across a cold resume.

    Realistic defect existing status-only coverage misses: ``MusterButton``
    can receive a successful bridge result while the selected-region panel or
    map marker remains stale, and a second process can paint the pre-order
    snapshot.  The probe uses the public panel text and map observation after
    two real recruit clicks and the live muster button.
    """
    state_path = tmp_path / "persistent-muster-session.json"
    request_path = tmp_path / "bridge-request.jsonl"
    command_prefix = (
        f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    )

    first = _run_process(command_prefix, state_path, request_path)
    second = _run_process(command_prefix, state_path, request_path)

    assert first["state_exists"] is True
    assert first["before"]["selected_region_name"] == "player lands", first
    assert "garnizon: 3" in first["before"]["panel_text"], first
    assert "brak armii" in first["before"]["panel_text"], first
    assert first["after"]["selected_region_name"] == "player lands", first
    assert "garnizon: 1" in first["after"]["panel_text"], first
    assert "Armia: własny (gracz)" in first["after"]["panel_text"], first
    assert first["after"]["marker_count"] == 1, first
    assert first["after"]["marked_regions"] == ["player lands"], first
    assert first["controls"]["order_status"] == "Rozkaz zbiórki zmienił stan."
    assert second["before"]["selected_region_name"] == "player lands", second
    assert "garnizon: 1" in second["before"]["panel_text"], second
    assert "Armia: własny (gracz)" in second["before"]["panel_text"], second
    assert second["before"]["marker_count"] == 1, second
    assert second["before"]["marked_regions"] == ["player lands"], second
    assert second["controls"]["order_status"] == "Rozkaz zbiórki nie zmienił stanu."
    assert second["controls"]["date"] == first["controls"]["date"]
    assert second["session_command"] == (
        f"{command_prefix} serve --resume '{state_path}'"
    )
