import json
import shlex
from pathlib import Path

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = GAME / "scripts" / "bridge_call_probe.gd"
PREFIX = "BRIDGE_CALL "


def _bridge_call_payload(result) -> dict:
    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    return json.loads(lines[0][len(PREFIX) :])


def _assert_null_call(result) -> None:
    assert _bridge_call_payload(result) == {
        "is_null": True,
        "keys": [],
        "ok": False,
    }


def test_bridge_call_probe_sends_snapshot_to_the_real_bridge(tmp_path):
    assert PROBE.is_file(), "missing res://scripts/bridge_call_probe.gd"

    request_path = tmp_path / "bridge-request.jsonl"
    command = (
        f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} "
        "python3 -m tbbbridge serve 7"
    )

    result = run_godot_script(
        GAME,
        "res://scripts/bridge_call_probe.gd",
        command,
        str(request_path),
        timeout=30,
    )

    payload = _bridge_call_payload(result)
    assert payload["is_null"] is False
    assert payload["ok"] is True
    assert "snapshot" in payload["keys"]
    assert json.loads(request_path.read_text(encoding="utf-8").splitlines()[0]) == {
        "type": "snapshot"
    }

    for failed_command in ("exit 3", "missing-tbbbridge-command"):
        failed_result = run_godot_script(
            GAME,
            "res://scripts/bridge_call_probe.gd",
            failed_command,
            str(tmp_path / (failed_command + ".jsonl")),
            timeout=30,
        )
        _assert_null_call(failed_result)

    empty_stdout = run_godot_script(
        GAME,
        "res://scripts/bridge_call_probe.gd",
        "true",
        str(tmp_path / "empty-stdout-request.jsonl"),
        timeout=30,
    )
    _assert_null_call(empty_stdout)

    unopenable_request = run_godot_script(
        GAME,
        "res://scripts/bridge_call_probe.gd",
        "true",
        str(tmp_path / "missing-directory" / "request.jsonl"),
        timeout=30,
    )
    _assert_null_call(unopenable_request)

    default_request_path = run_godot_script(
        GAME,
        "res://scripts/bridge_call_probe.gd",
        command,
        timeout=30,
    )
    default_payload = _bridge_call_payload(default_request_path)
    assert default_payload["is_null"] is False
    assert default_payload["ok"] is True
    assert "snapshot" in default_payload["keys"]

    missing_command = run_godot_script(
        GAME,
        "res://scripts/bridge_call_probe.gd",
        timeout=30,
    )
    assert missing_command.returncode == 2
    assert "bridge_call_probe: missing bridge command" in missing_command.stderr
    assert PREFIX not in missing_command.stdout
