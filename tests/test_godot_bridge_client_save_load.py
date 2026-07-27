"""BridgeClient: zapis i wczytanie partii gracza (slot ≠ plik stanu)."""

import json
import shlex
from pathlib import Path

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = GAME / "tests" / "bridge_save_load_probe.gd"
PREFIX = "BRIDGE_SAVE_LOAD "


def test_persistent_bridge_save_and_load_party_round_trip(tmp_path):
    """Zapis slotu, tura, wczytanie przywraca datę; load jest trwały w pliku stanu.

    Defekt, którego nie łapią istniejące testy: klient ma tylko zapis ciągłości
    sesji po next_turn/order; nie ma operacji na slocie partii gracza ani
    sekwencji load+save stanu, więc wczytanie nie przetrwałoby kolejnego procesu.
    """
    assert PROBE.is_file(), "missing res://tests/bridge_save_load_probe.gd"

    seed = 73
    state_path = tmp_path / "campaign-state.json"
    request_path = tmp_path / "bridge-request.jsonl"
    slot_path = tmp_path / "party-slot.json"
    prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"

    result = run_godot_script(
        GAME,
        "res://tests/bridge_save_load_probe.gd",
        prefix,
        str(state_path),
        str(request_path),
        str(seed),
        str(slot_path),
        timeout=60,
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    payload = json.loads(lines[0][len(PREFIX) :])

    assert payload["has_save_party"] is True
    assert payload["has_load_party"] is True
    assert payload["saved"] == {"year": 1, "month": 1}
    assert payload["after_save"] == {"year": 1, "month": 1}
    assert payload["advanced"] == {"year": 1, "month": 2}
    assert payload["loaded"] == {"year": 1, "month": 1}
    assert payload["missing_load_is_null"] is True
    assert payload["after_missing"] == {"year": 1, "month": 1}
    assert payload["resumed"] == {"year": 1, "month": 1}
    assert payload["slot_exists"] is True
    assert payload["non_persistent_save_is_null"] is True
    assert payload["non_persistent_load_is_null"] is True
