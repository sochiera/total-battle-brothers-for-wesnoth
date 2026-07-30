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

EXPECTED_VIEWPORT = {"w": 1152.0, "h": 648.0, "scene_w": 1152.0, "scene_h": 648.0}


def _run(tmp_path: Path, *extra: str, state_name: str = "legal-targeted-move.json") -> dict:
    state_path = tmp_path / state_name
    request_path = tmp_path / "bridge-request.jsonl"
    command_prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    result = run_godot_script(
        GAME,
        PROBE,
        command_prefix,
        str(state_path),
        str(request_path),
        str(SEED),
        *extra,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def _player_party_region_and_calendar(state_path: Path) -> tuple[str, dict]:
    """Semantic resume gate: region of the player party + calendar from save JSON."""
    data = json.loads(state_path.read_text(encoding="utf-8"))
    calendar = data["calendar"]
    regions = [entry["name"] for entry in data["world"]["regions"]]
    player_regions = [
        regions[index]
        for index, party in data["world"]["parties"]
        if party.get("owner_id") == "player"
    ]
    assert len(player_regions) == 1, (
        f"expected exactly one player party in state, got {player_regions!r} "
        f"from {state_path}"
    )
    return player_regions[0], calendar


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


def test_legal_targeted_move_resumes_with_unit_on_destination(tmp_path):
    """Cold resume after legal targeted step paints the unit on the saved region.

    Realistic defect existing gates miss: in-session legal targeted-move e2e
    (same process) and bridge-level ``send_order(move, target)`` resume pin the
    model ``player_party_region``, while ``persistent_party_map_mark`` resumes
    only after untargeted muster→march. None of them run the unique boundary
    MapView select → MarchButton (order=move+target) → auto-save → **new**
    Godot process + bridge ``serve --resume`` → first Main render. A client that
    reloads the label from the snapshot but leaves MapView on the seed/source
    tile, drops the silhouette until another order, or advances the calendar on
    resume keeps those green gates while this AC fails.

    Resume phase issues no march/move press — position must already be correct.
    Measured viewport stays 1152×648 for human screenshot review of the resumed party.
    """
    state_name = "legal-targeted-move-resume.json"
    state_path = tmp_path / state_name

    first = _run(tmp_path, state_name=state_name)
    assert first["state_exists"] is True
    party_region_after_move, calendar_after_move = _player_party_region_and_calendar(
        state_path
    )

    second = _run(tmp_path, "resume", state_name=state_name)

    source = first["source_region"]
    target = first["target_region"]
    assert source == "player lands"
    assert target == "player outpost"
    assert second["state_exists"] is True
    # Resume fact only — do not pin private shell-quoting of bridge_client.gd.
    assert "--resume" in second["session_command"], second["session_command"]
    assert str(state_path) in second["session_command"], second["session_command"]
    assert first["viewport"] == EXPECTED_VIEWPORT, first["viewport"]
    assert second["viewport"] == EXPECTED_VIEWPORT, second["viewport"]

    after_move = first["after_move"]
    resumed = second["after_resume"]

    # In-session after the targeted step: one mark on destination, calendar fixed.
    assert after_move["marker_count"] == 1, after_move
    assert after_move["marked_regions"] == [target], after_move
    assert target in after_move["position_label"], after_move
    assert source not in after_move["marked_regions"], after_move
    assert after_move["order_status"] == SUCCESS_STATUS, after_move
    move_date = after_move["date"]
    assert move_date, after_move

    # Semantic save: party on destination, calendar frozen across resume process.
    assert party_region_after_move == target, party_region_after_move
    party_region_resumed, calendar_resumed = _player_party_region_and_calendar(
        state_path
    )
    assert party_region_resumed == party_region_after_move, (
        f"resume must not re-apply move: before={party_region_after_move!r} "
        f"after={party_region_resumed!r}"
    )
    assert calendar_resumed == calendar_after_move, (
        f"resume must not advance calendar in state file: "
        f"before={calendar_after_move!r} after={calendar_resumed!r}"
    )

    # First paint after resume: same destination mark + matching label, no re-order.
    assert resumed["marker_count"] == 1, resumed
    assert resumed["marked_regions"] == [target], resumed
    assert target in resumed["position_label"], resumed
    assert source not in resumed["marked_regions"], resumed
    assert resumed["date"] == move_date, (
        f"resume must not advance DateLabel: after_move={move_date!r} "
        f"resumed={resumed['date']!r}"
    )
