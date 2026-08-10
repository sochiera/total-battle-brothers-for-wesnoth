"""G119.1c: pending battles are visible and own the order-bar state."""

from __future__ import annotations

import json
import shlex
import struct
from pathlib import Path

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/battle_pending_controls_probe.gd"
PREFIX = "BATTLE_PENDING_CONTROLS "
SEED = 73
VISUAL_PROOFS = (
    GAME / "screenshots" / "task-674-battle-pending-1152x648.png",
    GAME / "screenshots" / "task-674-battle-advance-1152x648.png",
)


def _probe_payload(*args: str) -> dict:
    result = run_godot_script(GAME, PROBE, *args, timeout=60)

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def _run_live_probe(tmp_path: Path, phase: str) -> dict:
    command = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    return _probe_payload(
        command,
        str(tmp_path / "battle-state.json"),
        str(tmp_path / f"bridge-{phase}.jsonl"),
        str(SEED),
        phase,
    )


def test_battle_pending_renders_deployment_without_result_banner():
    payload = _probe_payload()

    assert payload["pending_model_has_battle"] is True, (
        "battle_pending snapshot with result=null must reach SnapshotModel.battle"
    )
    assert payload["battle_view_visible"] is True, payload
    assert payload["battle_tile_count"] >= 2, payload
    assert payload["battle_result_text"] == "", payload
    assert payload["pending_model_battle_hexes"] == [
        {
            "q": 0,
            "r": 0,
            "terrain": "Plains",
            "side": "attacker",
            "hp": 10,
            "stunned": True,
        },
        {
            "q": 1,
            "r": 0,
            "terrain": "Forest",
            "side": "defender",
            "hp": 8,
            "stunned": False,
        },
    ], payload


def test_pending_battle_order_bar_exposes_round_and_auto_commands_in_polish():
    payload = _probe_payload()
    round_buttons = payload["round_buttons"]

    assert round_buttons["battle_advance"] == {
        "found": True,
        "disabled": False,
        "text": "Następna runda",
        "order_name": "battle_advance",
    }, round_buttons
    assert round_buttons["battle_auto"] == {
        "found": True,
        "disabled": False,
        "text": "Rozstrzygnij od razu",
        "order_name": "battle_auto",
    }, round_buttons


def test_pending_battle_blocks_other_order_buttons_or_explains_polish_status():
    payload = _probe_payload()
    regular_buttons = payload["regular_order_buttons"]
    status = payload["order_status"].casefold()

    blocked = all(
        button["disabled"] or "bitwa" in status
        for button in regular_buttons.values()
    )
    assert blocked, {
        "regular_order_buttons": regular_buttons,
        "order_status": payload["order_status"],
    }


def test_battle_round_buttons_are_disabled_without_pending_battle():
    payload = _probe_payload()

    assert all(
        button["found"] and button["disabled"]
        for button in payload["outside_round_buttons"].values()
    ), payload["outside_round_buttons"]


def test_live_bridge_round_sequence_updates_board_resolves_and_survives_restart(tmp_path):
    payload = _run_live_probe(tmp_path, "play")

    assert payload["setup_ok"] is True, (
        f"live setup stopped at {payload['setup_failed_button']!r}: {payload}"
    )
    assert payload["state_exists"] is True, payload

    pending = payload["pending"]
    assert pending["visible"] is True, pending
    assert pending["tile_count"] >= 2, pending
    assert pending["result_text"] == "", pending
    assert pending["model_hexes"], pending
    assert all(isinstance(hex_data.get("stunned"), bool) for hex_data in pending["model_hexes"]), pending

    assert (
        all(button["disabled"] for button in payload["regular_buttons"].values())
        or "bitwa" in payload["pending_status"].casefold()
    ), payload
    assert all(
        not button["disabled"] for button in payload["persistence_buttons"].values()
    ), payload
    assert payload["round_buttons"]["battle_advance"] == {
        "found": True,
        "disabled": False,
        "text": "Następna runda",
        "order_name": "battle_advance",
    }, payload
    assert payload["round_buttons"]["battle_auto"] == {
        "found": True,
        "disabled": False,
        "text": "Rozstrzygnij od razu",
        "order_name": "battle_auto",
    }, payload

    after_advance = payload["after_advance"]
    assert payload["advance_pressed"] is True, payload
    assert payload["advance_request_types"] == ["battle_advance", "save"], payload
    assert after_advance["visible"] is True, after_advance
    assert after_advance["tile_count"] >= 2, after_advance
    assert after_advance["result_text"] == "", after_advance
    assert after_advance["tiles"] != pending["tiles"], {
        "pending": pending,
        "after_advance": after_advance,
        "status": payload["advance_status"],
    }
    assert all(isinstance(hex_data.get("stunned"), bool) for hex_data in after_advance["model_hexes"]), after_advance

    after_auto = payload["after_auto"]
    assert payload["auto_pressed"] is True, payload
    assert payload["auto_request_types"] == ["battle_auto", "save"], payload
    assert after_auto["visible"] is True, after_auto
    assert after_auto["tile_count"] >= 2, after_auto
    assert after_auto["result_text"].casefold() in {"zwycięstwo", "porażka", "remis"}, after_auto
    assert payload["next_turn_pressed"] is True, payload
    assert payload["next_turn_request_types"] == ["next_turn", "save"], payload
    assert payload["after_next_turn"]["visible"] is False, payload
    assert payload["after_next_turn"]["result_text"] == "", payload
    assert payload["after_next_turn"]["tile_count"] == 0, payload

    resumed = _run_live_probe(tmp_path, "resume")["resumed"]
    assert resumed["visible"] is False, resumed
    assert resumed["result_text"] == "", resumed
    assert resumed["tile_count"] == 0, resumed


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", path
    return struct.unpack(">II", data[16:24])


def test_pending_and_advanced_battle_have_committed_1152x648_visual_proofs():
    for path in VISUAL_PROOFS:
        assert path.is_file(), f"missing human-review screenshot: {path}"
        assert _png_dimensions(path) == (1152, 648), path
        assert path.stat().st_size >= 100_000, path
