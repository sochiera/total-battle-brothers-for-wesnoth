import json
import re
import shlex
import sys
from pathlib import Path

import pytest

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
CLIENT_SCRIPT = GAME / "scripts" / "bridge_client.gd"
MAIN_SCRIPT = GAME / "scripts" / "main.gd"
PROBE = GAME / "tests" / "bridge_order_probe.gd"
PREFIX = "BRIDGE_ORDER "
FAILURE_PROBE = GAME / "tests" / "bridge_order_failure_probe.gd"
FAILURE_PREFIX = "BRIDGE_ORDER_FAILURE "


def test_main_reads_the_last_order_result_through_the_named_client_api():
    client_source = CLIENT_SCRIPT.read_text(encoding="utf-8")
    main_source = MAIN_SCRIPT.read_text(encoding="utf-8")

    assert re.search(
        r"^func last_order_result\(\) -> Variant:", client_source, flags=re.MULTILINE
    ), "BridgeClient must expose last_order_result() as the scene-facing API"
    assert "get_property_list" not in main_source


def test_persistent_bridge_send_order_persists_and_returns_the_post_order_model(tmp_path):
    assert PROBE.is_file(), "missing res://tests/bridge_order_probe.gd"
    state_path = tmp_path / "campaign-state.json"
    request_path = tmp_path / "bridge-request.jsonl"
    command = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"

    result = run_godot_script(
        GAME,
        "res://tests/bridge_order_probe.gd",
        command,
        str(state_path),
        str(request_path),
        "73",
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    payload = json.loads(lines[0][len(PREFIX) :])
    assert payload["has_send_order"] is True
    assert payload["order"] is not None
    assert payload["has_last_order_result_api"] is True
    assert payload["last_order_result"] == {"order": "develop", "changed": True}

    assert payload["unchanged_order"] is not None
    assert payload["unchanged_order_result"] == {"order": "develop", "changed": False}
    assert payload["rejected_order_is_null"] is True
    assert payload["rejected_order_result"] is None

    assert payload["order"]["calendar"] == {"year": 1, "month": 1}
    assert payload["order"]["regions"]
    assert payload["order"]["player_result"] == "ongoing"
    assert payload["order"]["player_duchy_status"] == {
        "morale": 0,
        "settlements": 1,
        "parties": 0,
    }
    assert payload["unchanged_order"] == payload["resumed"]
    assert payload["state_exists"] is True
    assert payload["requests"] == [
        {"type": "order", "order": "develop"},
        {"type": "save", "path": str(state_path)},
    ]


@pytest.mark.parametrize(
    "program",
    [
        "print('{\"ok\": false}'); print('{\"ok\": true}')",
        "print('{\"ok\": true}'); print('{\"ok\": false}')",
        "print('{\"ok\": true}')",
        "print('{\"ok\": true}'); print('{\"ok\": true}')",
        "print('not json'); print('{\"ok\": true}')",
        "import sys; sys.exit(3)",
    ],
    ids=["order_rejected", "save_rejected", "missing_response", "unusable_order_snapshot", "malformed_response", "process_fails"],
)
def test_persistent_bridge_send_order_discards_all_failed_batches(tmp_path, program):
    assert FAILURE_PROBE.is_file(), "missing res://tests/bridge_order_failure_probe.gd"
    command = f"{shlex.quote(sys.executable)} -c {shlex.quote(program)}"

    result = run_godot_script(
        GAME,
        "res://tests/bridge_order_failure_probe.gd",
        command,
        str(tmp_path / "campaign-state.json"),
        str(tmp_path / "bridge-request.jsonl"),
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(FAILURE_PREFIX)]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len(FAILURE_PREFIX) :]) == {"model_is_null": True}


def test_non_persistent_bridge_send_order_returns_null_without_running_the_bridge(tmp_path):
    assert FAILURE_PROBE.is_file(), "missing res://tests/bridge_order_failure_probe.gd"
    marker = tmp_path / "bridge-ran"
    result = run_godot_script(
        GAME,
        "res://tests/bridge_order_failure_probe.gd",
        f"touch {shlex.quote(str(marker))}",
        str(tmp_path / "campaign-state.json"),
        str(tmp_path / "bridge-request.jsonl"),
        "--non-persistent",
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(FAILURE_PREFIX)]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len(FAILURE_PREFIX) :]) == {"model_is_null": True}
    assert not marker.exists()


def test_persistent_bridge_send_order_returns_null_when_the_real_bridge_rejects_it(tmp_path):
    assert FAILURE_PROBE.is_file(), "missing res://tests/bridge_order_failure_probe.gd"
    command = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    result = run_godot_script(
        GAME,
        "res://tests/bridge_order_failure_probe.gd",
        command,
        str(tmp_path / "campaign-state.json"),
        str(tmp_path / "bridge-request.jsonl"),
        "--unknown-order",
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(FAILURE_PREFIX)]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len(FAILURE_PREFIX) :]) == {"model_is_null": True}
