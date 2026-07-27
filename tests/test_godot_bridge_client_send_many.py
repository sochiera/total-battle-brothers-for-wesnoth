import json
import shlex
from pathlib import Path

import pytest

from godot_runner import run_godot_script
from tbbbridge.session import new_session


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = GAME / "tests" / "bridge_many_probe.gd"
PREFIX = "BRIDGE_MANY "
SEED = 7
ONE_RESPONSE_COMMAND = "echo eyJvayI6IHRydWV9 | base64 -d"
VALID_THEN_INVALID_RESPONSE_COMMAND = "echo eyJvayI6IHRydWV9Cm5vdCBqc29uCg== | base64 -d"


def _command() -> str:
    return (
        f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} "
        f"python3 -m tbbbridge serve {SEED}"
    )


def _payload(result) -> dict:
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def _run(tmp_path, command: str, *options: str):
    return run_godot_script(
        GAME,
        "res://tests/bridge_many_probe.gd",
        command,
        str(tmp_path / "bridge-request.jsonl"),
        *options,
        timeout=30,
    )


def test_bridge_many_probe_sends_ordered_turn_batch_to_the_real_bridge(tmp_path):
    assert PROBE.is_file(), "missing res://tests/bridge_many_probe.gd"

    payload = _payload(_run(tmp_path, _command()))
    session = new_session(SEED)
    first = session.next_turn()
    second = first.next_turn()

    assert [response["result"]["date"] for response in payload["responses"]] == [
        {"year": first.calendar.year, "month": first.calendar.month},
        {"year": second.calendar.year, "month": second.calendar.month},
    ]
    assert [response["snapshot"] for response in payload["responses"]] == [
        first.snapshot(),
        second.snapshot(),
    ]
    assert [json.loads(line) for line in (tmp_path / "bridge-request.jsonl").read_text().splitlines()] == [
        {"type": "next_turn"},
        {"type": "next_turn"},
    ]


def test_bridge_many_single_request_matches_send(tmp_path):
    payload = _payload(_run(tmp_path, _command(), "--single"))

    assert payload["send"] == payload["send_many"][0]
    assert len(payload["send_many"]) == 1


@pytest.mark.parametrize("command", ["exit 3", "true"])
def test_bridge_many_returns_empty_list_for_process_failure_or_empty_stdout(tmp_path, command):
    assert _payload(_run(tmp_path, command, "--allow-empty")) == {"responses": []}


def test_bridge_many_returns_empty_list_when_request_file_cannot_be_written(tmp_path):
    result = run_godot_script(
        GAME,
        "res://tests/bridge_many_probe.gd",
        _command(),
        str(tmp_path / "missing-directory" / "bridge-request.jsonl"),
        "--allow-empty",
        timeout=30,
    )

    assert _payload(result) == {"responses": []}


@pytest.mark.parametrize(
    "command",
    [
        ONE_RESPONSE_COMMAND,
        VALID_THEN_INVALID_RESPONSE_COMMAND,
    ],
)
def test_bridge_many_returns_empty_list_for_incomplete_or_malformed_output(tmp_path, command):
    assert _payload(_run(tmp_path, command, "--allow-empty")) == {"responses": []}


def test_bridge_many_empty_list_does_not_run_the_bridge_process(tmp_path):
    marker = tmp_path / "bridge-ran"
    payload = _payload(_run(tmp_path, f"touch {shlex.quote(str(marker))}", "--empty"))

    assert payload == {"responses": []}
    assert not marker.exists()


def test_bridge_many_probe_rejects_an_incomplete_batch_by_default(tmp_path):
    result = _run(tmp_path, ONE_RESPONSE_COMMAND)

    assert result.returncode != 0
    assert PREFIX not in result.stdout
    assert "bridge_many_probe: responses are not complete and ordered" in result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr


def test_bridge_many_probe_returns_nonzero_for_a_corrupted_result(tmp_path):
    result = _run(tmp_path, _command(), "--corrupt")

    assert result.returncode != 0
    assert PREFIX not in result.stdout
    assert "bridge_many_probe: responses are not complete and ordered" in result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
