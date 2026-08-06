import json
import shlex
import sys
from pathlib import Path

import pytest

from godot_runner import run_godot_script
from tbbbridge.persist import save_session
from tbbbridge.session import new_session


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = GAME / "tests" / "bridge_persistent_api_probe.gd"
PERSISTENT_PROBE = GAME / "tests" / "bridge_persistent_probe.gd"
ADVANCE_PROBE = GAME / "tests" / "bridge_advance_turn_probe.gd"
ADVANCE_FAILURE_PROBE = GAME / "tests" / "bridge_advance_turn_failure_probe.gd"
NEW_GAME_PROBE = GAME / "tests" / "bridge_new_game_probe.gd"


def test_persistent_bridge_client_exposes_command_selection_api():
    assert PROBE.is_file(), "missing res://tests/bridge_persistent_api_probe.gd"

    result = run_godot_script(
        GAME, "res://tests/bridge_persistent_api_probe.gd", timeout=30
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr


def test_persistent_bridge_switches_to_a_quoted_resume_command_and_executes_it(tmp_path):
    assert PERSISTENT_PROBE.is_file(), "missing res://tests/bridge_persistent_probe.gd"
    saved_state = tmp_path / "saved-session.json"
    save_session(new_session(seed=73), saved_state)
    state_path = tmp_path / "state file's copy.json"
    prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"

    result = run_godot_script(
        GAME,
        "res://tests/bridge_persistent_probe.gd",
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


def test_persistent_bridge_advance_turn_persists_across_bridge_processes(tmp_path):
    assert ADVANCE_PROBE.is_file(), "missing res://tests/bridge_advance_turn_probe.gd"

    seed = 73
    state_path = tmp_path / "campaign-state.json"
    request_path = tmp_path / "bridge-request.jsonl"
    prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    result = run_godot_script(
        GAME,
        "res://tests/bridge_advance_turn_probe.gd",
        prefix,
        str(state_path),
        str(request_path),
        str(seed),
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith("BRIDGE_ADVANCE ")]
    assert len(lines) == 1, result.stdout
    payload = json.loads(lines[0][len("BRIDGE_ADVANCE ") :])

    first = new_session(seed).next_turn().snapshot()["calendar"]
    second = new_session(seed).next_turn().next_turn().snapshot()["calendar"]
    assert payload == {
        "first": first,
        "after_first_snapshot": first,
        "second": second,
        "after_second_snapshot": second,
        "state_exists": True,
    }


def test_persistent_bridge_start_new_game_resets_and_persists_across_processes(tmp_path):
    """A new game must replace, rather than merely reset in memory, a campaign.

    Realistic defect missed by the existing turn/order persistence gates:
    ``new_game`` can be sent without a following session-state ``save``.  Its
    immediate response then looks fresh, while the next bridge process resumes
    the pre-reset campaign.
    """
    assert NEW_GAME_PROBE.is_file(), "missing res://tests/bridge_new_game_probe.gd"

    state_path = tmp_path / "campaign-state.json"
    request_path = tmp_path / "bridge-request.jsonl"
    prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    result = run_godot_script(
        GAME,
        "res://tests/bridge_new_game_probe.gd",
        prefix,
        str(state_path),
        str(request_path),
        "73",
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith("BRIDGE_NEW_GAME ")]
    assert len(lines) == 1, result.stdout
    payload = json.loads(lines[0][len("BRIDGE_NEW_GAME ") :])

    assert payload["before"] == {"year": 1, "month": 3}
    assert payload["fresh"] == {"year": 1, "month": 1}
    assert payload["fresh_is_ongoing"] is True
    assert payload["had_order_result"] is True
    assert payload["last_order_result_is_null"] is True
    assert payload["resumed"] == {"year": 1, "month": 1}
    assert payload["resumed_is_ongoing"] is True
    assert payload["state_exists"] is True
    assert payload["requests"] == [
        {"type": "new_game"},
        {"type": "save", "path": str(state_path)},
    ]


def test_persistent_bridge_advance_turn_probe_returns_nonzero_when_corrupted(tmp_path):
    assert ADVANCE_PROBE.is_file(), "missing res://tests/bridge_advance_turn_probe.gd"

    prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    result = run_godot_script(
        GAME,
        "res://tests/bridge_advance_turn_probe.gd",
        prefix,
        str(tmp_path / "campaign-state.json"),
        str(tmp_path / "bridge-request.jsonl"),
        "73",
        "--corrupt",
        timeout=30,
    )

    assert result.returncode != 0
    assert "BRIDGE_ADVANCE " not in result.stdout
    assert "bridge_advance_turn_probe: inconsistent advance result" in result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr


@pytest.mark.parametrize(
    "program",
    [
        "print('{\"ok\": false}'); print('{\"ok\": true}')",
        (
            "print('{\"ok\": true, \"snapshot\": {\"calendar\": {\"year\": 1, \"month\": 2}, "
            "\"map\": {\"regions\": []}, \"result\": {\"player_result\": \"ongoing\"}}}'); "
            "print('{\"ok\": false}')"
        ),
        "print('{\"ok\": true}')",
        "import sys; sys.exit(3)",
    ],
    ids=[
        "turn_response_not_ok",
        "save_response_not_ok_after_usable_turn_snapshot",
        "missing_response",
        "bridge_process_fails",
    ],
)
@pytest.mark.parametrize(
    "operation_args", [(), ("--new-game",)], ids=["advance_turn", "start_new_game"]
)
def test_persistent_bridge_persisted_operations_discard_partial_failures(
    tmp_path, program, operation_args
):
    assert ADVANCE_FAILURE_PROBE.is_file(), (
        "missing res://tests/bridge_advance_turn_failure_probe.gd"
    )

    command = f"{shlex.quote(sys.executable)} -c {shlex.quote(program)}"
    result = run_godot_script(
        GAME,
        "res://tests/bridge_advance_turn_failure_probe.gd",
        command,
        str(tmp_path / "campaign-state.json"),
        str(tmp_path / "bridge-request.jsonl"),
        *operation_args,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [
        line
        for line in result.stdout.splitlines()
        if line.startswith("BRIDGE_ADVANCE_FAILURE ")
    ]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len("BRIDGE_ADVANCE_FAILURE ") :]) == {"model_is_null": True}


@pytest.mark.parametrize(
    "operation_args", [(), ("--new-game",)], ids=["advance_turn", "start_new_game"]
)
def test_non_persistent_bridge_persisted_operations_return_null_without_running_the_bridge(
    tmp_path, operation_args
):
    assert ADVANCE_FAILURE_PROBE.is_file(), (
        "missing res://tests/bridge_advance_turn_failure_probe.gd"
    )

    marker = tmp_path / "bridge-ran"
    command = f"touch {shlex.quote(str(marker))}"
    result = run_godot_script(
        GAME,
        "res://tests/bridge_advance_turn_failure_probe.gd",
        command,
        str(tmp_path / "campaign-state.json"),
        str(tmp_path / "bridge-request.jsonl"),
        "--non-persistent",
        *operation_args,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [
        line
        for line in result.stdout.splitlines()
        if line.startswith("BRIDGE_ADVANCE_FAILURE ")
    ]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len("BRIDGE_ADVANCE_FAILURE ") :]) == {"model_is_null": True}
    assert not marker.exists()
