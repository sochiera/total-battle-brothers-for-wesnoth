import json
import shlex
from pathlib import Path

from godot_runner import run_godot_script
from tbbbridge.session import new_session


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/persistent_next_turn_e2e_probe.gd"
PREFIX = "PERSISTENT_NEXT_TURN "
SEED = 73


def _expected_snapshot(turns: int) -> dict:
    session = new_session(SEED)
    for _ in range(turns):
        session = session.next_turn()
    return session.snapshot()


def _controls(snapshot: dict) -> dict:
    player_status = next(
        duchy
        for duchy in snapshot["duchies"]
        if duchy["id"] == snapshot["player_duchy"]
    )
    return {
        "date": (
            f"Rok {snapshot['calendar']['year']}, "
            f"miesiąc {snapshot['calendar']['month']}"
        ),
        "result": f"Wynik: {snapshot['result']['player_result']}",
        "duchy_status": (
            f"Morale: {player_status['morale']}, "
            f"osady: {player_status['settlements']}, "
            f"oddziały: {player_status['parties']}"
        ),
        "regions": [region["name"] for region in snapshot["map"]["regions"]],
    }


def test_next_turn_button_persists_the_game_across_two_bridge_processes(tmp_path):
    state_path = tmp_path / "persistent-session.json"
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

    assert payload == {
        "state_exists_after_first_press": True,
        "first": _controls(_expected_snapshot(1)),
        "second": _controls(_expected_snapshot(2)),
    }


def test_next_turn_button_keeps_controls_empty_when_persistent_bridge_fails(tmp_path):
    result = run_godot_script(
        GAME,
        PROBE,
        "false",
        str(tmp_path / "persistent-session.json"),
        str(tmp_path / "bridge-request.jsonl"),
        str(SEED),
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len(PREFIX) :]) == {
        "state_exists_after_first_press": False,
        "first": {"date": "", "result": "", "duchy_status": "", "regions": []},
        "second": {"date": "", "result": "", "duchy_status": "", "regions": []},
    }
