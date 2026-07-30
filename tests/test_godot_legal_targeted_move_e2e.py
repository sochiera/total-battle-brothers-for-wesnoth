"""G97.1f e2e: legal targeted move shows unit, panel, frame and PL status."""

from __future__ import annotations

import json
import shlex
from pathlib import Path

from godot_runner import run_godot_script

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/legal_targeted_move_e2e_probe.gd"
PREFIX = "LEGAL_TARGETED_MOVE_E2E "
SEED = 73

SUCCESS_STATUS = "Oddział przemieścił się."
ARMY_PLAYER = "Armia: własny (gracz)"
ARMY_NONE = "Armia: brak armii"


def _run(tmp_path: Path) -> dict:
    state_path = tmp_path / "legal-targeted-move.json"
    request_path = tmp_path / "bridge-request.jsonl"
    command_prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    result = run_godot_script(
        GAME,
        PROBE,
        command_prefix,
        str(state_path),
        str(request_path),
        str(SEED),
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def test_legal_targeted_move_shows_unit_panel_frame_and_polish_status(tmp_path):
    """After select+MarchButton on a live bridge the step is visible end-to-end.

    Realistic defect existing gates miss: contextual MarchButton already sends
    ``move`` with the selected target (G97.1f contextual button) and the bridge
    already applies ``move`` + persists party region (G97.1a/b), but
    ``OrderResult.status_text`` has no branch for ``order=move`` (falls through
    to empty string) and no live UI sequence pins the full path
    MapView select → MarchButton → JSONL → core → re-render. Automatic
    muster→march e2e stays green while a legal targeted step leaves empty
    status and/or fails to re-render silhouette, single frame and panel army
    for the same ``changed=true`` result.

    Panel army line must refresh: a weak ``gracz|własn`` match also hits
    ``Właściciel: własny (gracz)`` on a player-owned settlement before the
    party arrives, so only an exact ``Armia:`` line plus before/after contrast
    gates the AC "panel shows refreshed state including the player army".
    """
    payload = _run(tmp_path)
    source = payload["source_region"]
    target = payload["target_region"]
    assert source == "player lands"
    assert target == "player outpost"
    assert payload["state_exists"] is True

    after_muster = payload["after_muster"]
    after_select = payload["after_select"]
    after_move = payload["after_move"]

    # Precondition: muster places one party mark on the source region.
    assert after_muster["marker_count"] == 1, after_muster
    assert after_muster["marked_regions"] == [source], after_muster

    # Selection targets the legal neighbour; contextual label follows.
    assert after_select["selected_region_name"] == target, after_select
    assert after_select["march_label"] == f"Wyrusz: {target}", after_select
    assert after_select["frame_count"] == 1, after_select
    assert after_select["framed_regions"] == [target], after_select
    # Before the step the selected neighbour has no party yet.
    assert ARMY_NONE in after_select["panel_text"], after_select

    # After legal move: one silhouette on target only (equality implies not on source).
    assert after_move["marker_count"] == 1, after_move
    assert after_move["marked_regions"] == [target], after_move
    assert target in after_move["position_label"], after_move

    # Selection chrome survives re-render exactly once on the same region.
    assert after_move["selected_region_name"] == target, after_move
    assert after_move["frame_count"] == 1, after_move
    assert after_move["framed_regions"] == [target], after_move

    # Panel for the still-selected target shows the player army after the step.
    panel = after_move["panel_text"]
    assert target in panel, after_move
    assert ARMY_PLAYER in panel, (
        f"panel must show {ARMY_PLAYER!r} on {target!r} after legal move, got {panel!r}"
    )

    # Public PL confirmation — not empty, not march/assault wording.
    assert after_move["order_status"] == SUCCESS_STATUS, (
        "after legal targeted move LastOrderStatusLabel must be "
        f"{SUCCESS_STATUS!r}, got {after_move['order_status']!r}"
    )
    assert "marsz" not in after_move["order_status"].lower()
    assert "szturm" not in after_move["order_status"].lower()
