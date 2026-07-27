"""G86.2b: klik Zapisz/Wczytaj przywraca stan na ekranie i pokazuje skutek."""

import json
import os
import shlex
from pathlib import Path

from godot_runner import run_godot_script
from tbbbridge.session import new_session


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/save_load_binding_probe.gd"
PREFIX = "SAVE_LOAD_BINDING "
SEED = 73

# Publiczny kontrakt komunikatów zapisu/wczytania — widoczne dla gracza po kliku.
SAVE_OK_STATUS = "Partia została zapisana."
LOAD_OK_STATUS = "Partia została wczytana."
LOAD_FAIL_STATUS = "Nie udało się wczytać partii."


def _controls(snapshot: dict, status: str = "") -> dict:
    player_status = next(
        duchy
        for duchy in snapshot["duchies"]
        if duchy["id"] == snapshot["player_duchy"]
    )
    return {
        "date": (
            f"Rok {snapshot['calendar']['year']}, "
            f"miesiąc {snapshot['calendar']['month']}"
        ),
        "duchy_status": (
            f"Morale: {player_status['morale']}, "
            f"osady: {player_status['settlements']}, "
            f"oddziały: {player_status['parties']}"
        ),
        "status": status,
    }


def _date_and_duchy(snapshot: dict) -> dict:
    """Date/duchy only — NextTurn may leave or clear LastOrderStatusLabel (UX)."""
    controls = _controls(snapshot)
    return {"date": controls["date"], "duchy_status": controls["duchy_status"]}


def test_save_load_buttons_round_trip_restores_screen_and_report_polish_status(tmp_path):
    """Defekt: przyciski istnieją, ale nie wołają save/load ani nie odświeżają widoku.

    Istniejące bramki pinują tylko niepowiązane %SaveGameButton/%LoadGameButton
    (pressed_connections: 0) oraz API BridgeClient.save_party/load_party poza
    sceną. Klik w scenie nie tworzy slotu, nie przywraca daty po turze i nie
    pokazuje polskiego skutku — gracz nie domyka K86 bez terminala.

    Trwałość wczytania (drugi proces mostu na TBB_STATE_PATH) jest pinowana
    tutaj po kliku Load w scenie — nie tylko w test_godot_bridge_client_save_load.
    """
    state_path = tmp_path / "campaign-state.json"
    save_path = tmp_path / "party-slot.json"
    environment = os.environ.copy()
    environment.update(
        {
            "TBB_BRIDGE_COMMAND": (
                f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
            ),
            "TBB_STATE_PATH": str(state_path),
            "TBB_SAVE_PATH": str(save_path),
            "TBB_SEED": str(SEED),
            "XDG_DATA_HOME": str(tmp_path / "xdg-data"),
        }
    )

    result = run_godot_script(GAME, PROBE, timeout=60, env=environment)

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    payload = json.loads(lines[0][len(PREFIX) :])

    fresh = new_session(SEED)
    after_turn = fresh.next_turn()

    assert payload["slot_exists_after_save"] is True
    assert payload["after_start"] == _controls(fresh.snapshot())
    assert payload["after_save"] == _controls(fresh.snapshot(), SAVE_OK_STATUS)
    # after_turn: tura działa; dokładny status save nie jest wymogiem AC (UX).
    assert _date_and_duchy_from_payload(payload["after_turn"]) == _date_and_duchy(
        after_turn.snapshot()
    )
    assert payload["after_load"] == _controls(fresh.snapshot(), LOAD_OK_STATUS)
    # Drugi proces mostu na tym samym pliku stanu widzi partię po load (1/1).
    assert payload["resumed_after_load"] == {"year": 1, "month": 1}
    assert payload["after_failed_load"] == _controls(fresh.snapshot(), LOAD_FAIL_STATUS)
    # Po błędzie load NextTurn nadal działa; status fail nie jest pinowany.
    assert _date_and_duchy_from_payload(payload["after_turn_after_fail"]) == _date_and_duchy(
        after_turn.snapshot()
    )


def _date_and_duchy_from_payload(controls: dict) -> dict:
    return {"date": controls["date"], "duchy_status": controls["duchy_status"]}
