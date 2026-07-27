import json
from pathlib import Path

import pytest

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "game" / "scripts"
GAME = ROOT / "game"
PREFIX = "BRIDGE_PARSE "
BATCH_PREFIX = "BRIDGE_BATCH "


def test_bridge_protocol_exposes_the_required_public_entrypoints():
    """G71.2a1: Godot receives a protocol client and a parse probe."""
    client_path = SCRIPTS / "bridge_client.gd"
    probe_path = GAME / "tests" / "bridge_parse_probe.gd"

    assert client_path.is_file(), "missing res://scripts/bridge_client.gd"
    assert probe_path.is_file(), "missing res://tests/bridge_parse_probe.gd"

    client = client_path.read_text(encoding="utf-8")
    assert "extends RefCounted" in client
    assert "static func request_line(command: Dictionary) -> String" in client
    assert "static func first_response(output: String) -> Variant" in client


def test_bridge_protocol_exposes_json_lines_batch_entrypoints():
    """G72.1a: the pure batch JSON Lines API is publicly callable."""
    client = (SCRIPTS / "bridge_client.gd").read_text(encoding="utf-8")

    assert "static func request_lines(commands: Array) -> String" in client
    assert "static func all_responses(output: String) -> Array" in client


def test_bridge_protocol_exposes_send_many_entrypoint():
    """G72.1b: the live batch API is publicly callable."""
    client = (SCRIPTS / "bridge_client.gd").read_text(encoding="utf-8")

    assert "func send_many(requests: Array) -> Array" in client


def run_batch_probe(*args: str):
    return run_godot_script(
        GAME, "res://tests/bridge_batch_probe.gd", *args, timeout=30
    )


def test_bridge_batch_probe_validates_json_lines_batch_semantics():
    result = run_batch_probe()

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(BATCH_PREFIX)]
    assert len(lines) == 1, result.stdout
    payload = json.loads(lines[0][len(BATCH_PREFIX) :])

    assert payload["empty_request"] == ""
    assert payload["request"].endswith("\n")
    assert [json.loads(line) for line in payload["request"].splitlines()] == [
        {"type": "next_turn", "turn": 1},
        {"type": "save", "path": "user://slot.json"},
        {"type": "snapshot", "options": {"verbose": True}},
    ]
    assert payload["responses"] == [
        {"sequence": 1},
        {"sequence": 2},
        {"sequence": 3},
    ]


def test_bridge_batch_probe_returns_nonzero_when_result_is_corrupted():
    result = run_batch_probe("--corrupt")

    assert result.returncode != 0
    assert BATCH_PREFIX not in result.stdout
    assert "bridge_batch_probe: responses are not complete and ordered" in result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr


def run_parse_probe(tmp_path, output: str):
    output_path = tmp_path / "bridge-output.txt"
    output_path.write_text(output, encoding="utf-8")
    result = run_godot_script(
        GAME, "res://tests/bridge_parse_probe.gd", str(output_path), timeout=30
    )

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    return json.loads(lines[0][len(PREFIX) :])


@pytest.mark.parametrize(
    ("output", "expected_response"),
    [
        ('{"ok": true, "turn": 1}', {"ok": True, "turn": 1}),
        ('\n  \n {"ok": true, "turn": 2} \n', {"ok": True, "turn": 2}),
        ('{"turn": 3}\n{"turn": 4}\n', {"turn": 3}),
        ("", None),
        ("not json\n{\"turn\": 5}\n", None),
        ("[1, 2, 3]\n", None),
        ('"not a dictionary"\n', None),
        ("42\n", None),
    ],
)
def test_bridge_parse_probe_serializes_request_and_first_dictionary_response(
    tmp_path, output, expected_response
):
    payload = run_parse_probe(tmp_path, output)

    assert json.loads(payload["request"]) == {"type": "snapshot"}
    assert "\n" not in payload["request"]
    assert payload["response"] == expected_response


@pytest.mark.parametrize("args", [(), ("/definitely/missing/bridge-output.txt",)])
def test_bridge_parse_probe_reports_missing_or_unreadable_input(args):
    result = run_godot_script(
        GAME, "res://tests/bridge_parse_probe.gd", *args, timeout=30
    )

    assert result.returncode == 2
    assert PREFIX not in result.stdout
    assert result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
