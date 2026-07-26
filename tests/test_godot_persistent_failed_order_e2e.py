import json
import shlex
from pathlib import Path

from godot_runner import run_godot_script
from tbbbridge.session import apply_command, new_session


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/persistent_failed_order_e2e_probe.gd"
PREFIX = "PERSISTENT_FAILED_ORDER "
SEED = 73


def _controls(develops: int, status: str) -> dict:
    session = new_session(SEED)
    for _ in range(develops):
        session = apply_command(session, {"type": "order", "order": "develop"})
    snapshot = session.snapshot()
    player = next(
        duchy for duchy in snapshot["duchies"] if duchy["id"] == snapshot["player_duchy"]
    )
    return {
        "date": f"Rok {snapshot['calendar']['year']}, miesiąc {snapshot['calendar']['month']}",
        "result": f"Wynik: {snapshot['result']['player_result']}",
        "duchy_status": (
            f"Morale: {player['morale']}, osady: {player['settlements']}, "
            f"oddziały: {player['parties']}"
        ),
        "regions": [region["name"] for region in snapshot["map"]["regions"]],
        "order_status": status,
    }


def test_failed_order_reports_status_without_corrupting_the_resumed_campaign(tmp_path):
    state_path = tmp_path / "persistent-failed-order.json"
    command_prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
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

    before_failure = _controls(1, "Rozkaz rozwoju zmienił stan.")
    after_resume = _controls(2, "Rozkaz rozwoju zmienił stan.")
    assert payload == {
        "rejected": False,
        "before_failure": before_failure,
        "after_failure": {
            **before_failure,
            "order_status": "Rozkaz nie powiódł się.",
        },
        "state_exists_after_failure": True,
        "resumed_command": f"{command_prefix} serve --resume '{state_path}'",
        "resumed": True,
        "after_resume": after_resume,
    }
