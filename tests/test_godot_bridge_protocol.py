import json
from pathlib import Path

import pytest

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "game" / "scripts"
GAME = ROOT / "game"
PREFIX = "BRIDGE_PARSE "


def test_bridge_protocol_exposes_the_required_public_entrypoints():
    """G71.2a1: Godot receives a protocol client and a parse probe."""
    client_path = SCRIPTS / "bridge_client.gd"
    probe_path = SCRIPTS / "bridge_parse_probe.gd"

    assert client_path.is_file(), "missing res://scripts/bridge_client.gd"
    assert probe_path.is_file(), "missing res://scripts/bridge_parse_probe.gd"

    client = client_path.read_text(encoding="utf-8")
    assert "extends RefCounted" in client
    assert "static func request_line(command: Dictionary) -> String" in client
    assert "static func first_response(output: String) -> Variant" in client


def run_parse_probe(tmp_path, output: str):
    output_path = tmp_path / "bridge-output.txt"
    output_path.write_text(output, encoding="utf-8")
    result = run_godot_script(
        GAME, "res://scripts/bridge_parse_probe.gd", str(output_path), timeout=30
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
        GAME, "res://scripts/bridge_parse_probe.gd", *args, timeout=30
    )

    assert result.returncode == 2
    assert PREFIX not in result.stdout
    assert result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
