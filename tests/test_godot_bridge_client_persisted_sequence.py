import json
import shlex
import sys
from pathlib import Path

import pytest

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = GAME / "tests" / "bridge_persisted_sequence_probe.gd"
PREFIX = "BRIDGE_PERSISTED_SEQUENCE "


@pytest.mark.parametrize(
    "program, expected_models",
    [
        ("print('{\"ok\": false}'); print('{\"ok\": true}')", [True, True]),
        ("print('{\"ok\": true}'); print('{\"ok\": false}')", [True, True]),
        ("print('{\"ok\": true}')", [True, True]),
        (
            "print('{\"ok\": true, \"snapshot\": {\"calendar\": {\"year\": 1, \"month\": 2}, \"map\": {\"regions\": []}, \"result\": {\"player_result\": \"ongoing\"}}}'); print('{\"ok\": true}')",
            [False, False],
        ),
    ],
    ids=["command_rejected", "save_rejected", "missing_save", "success"],
)
def test_persisted_commands_share_rejection_rules_and_save_request(tmp_path, program, expected_models):
    assert PROBE.is_file(), "missing res://tests/bridge_persisted_sequence_probe.gd"
    state_path = tmp_path / "campaign-state.json"
    bridge_script = tmp_path / "bridge.py"
    bridge_script.write_text(program, encoding="utf-8")
    command = f"{shlex.quote(sys.executable)} {shlex.quote(str(bridge_script))}"

    result = run_godot_script(
        GAME,
        "res://tests/bridge_persisted_sequence_probe.gd",
        command,
        str(state_path),
        str(tmp_path / "advance-request.jsonl"),
        str(tmp_path / "order-request.jsonl"),
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    payload = json.loads(lines[0][len(PREFIX) :])
    assert payload["model_is_null"] == expected_models
    assert payload["requests"] == [
        [
            {"type": "next_turn"},
            {"type": "save", "path": str(state_path)},
        ],
        [
            {"type": "order", "order": "develop"},
            {"type": "save", "path": str(state_path)},
        ],
    ]
