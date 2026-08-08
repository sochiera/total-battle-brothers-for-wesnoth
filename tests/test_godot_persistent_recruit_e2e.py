import json
import shlex
from pathlib import Path

from godot_runner import map_player_result, run_godot_script
from tbbbridge.session import apply_command, new_session


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/persistent_recruit_e2e_probe.gd"
PREFIX = "PERSISTENT_RECRUIT "
SEED = 73


def _expected_controls(recruits: int) -> dict:
    session = new_session(SEED)
    for _ in range(recruits):
        session = apply_command(session, {"type": "order", "order": "recruit"})
    snapshot = session.snapshot()
    return {
        "date": (
            f"Rok {snapshot['calendar']['year']}, "
            f"miesiąc {snapshot['calendar']['month']}"
        ),
        "result": map_player_result(snapshot['result']['player_result']),
        "order_status": (
            "Rozkaz rekrutacji zmienił stan."
            # G92.2a: two keeps × four free garrison slots = eight productive recruits.
            if recruits <= 8
            # G114.1c (task-637): no-op recruit carries the transient population
            # reason through the bridge → status names what was lacking.
            else "Brak wolnych mieszkańców — ludność przybędzie w kolejnej turze."
        ),
    }


def test_recruit_button_persists_five_changes_then_resumes_with_no_change(tmp_path):
    state_path = tmp_path / "persistent-recruit-session.json"
    command_prefix = (
        f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    )
    result = run_godot_script(
        GAME,
        PROBE,
        command_prefix,
        str(state_path),
        str(tmp_path / "bridge-request.jsonl"),
        str(SEED),
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    payload = json.loads(lines[0][len(PREFIX) :])

    # First process: eight changes + one no-op; resume: still no-op.
    assert payload == {
        "state_exists_after_first_process": True,
        "first": [_expected_controls(recruits) for recruits in range(1, 10)],
        "resumed_command": f"{command_prefix} serve --resume '{state_path}'",
        "resumed": _expected_controls(10),
    }
