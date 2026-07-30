"""G97.1f e2e: blocked move into enemy settlement stays put with PL status."""

from __future__ import annotations

import json
import shlex
from pathlib import Path

from godot_png_assets import assert_asset_credited
from godot_runner import run_godot_script

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/blocked_enemy_settlement_move_e2e_probe.gd"
PREFIX = "BLOCKED_ENEMY_SETTLEMENT_MOVE_E2E "
SEED = 73

BLOCKED_STATUS = "Ruch nie nastąpił."
SUCCESS_STATUS = "Oddział przemieścił się."
TRANSPORT_FAILURE_STATUS = "Rozkaz nie powiódł się."
OWNER_AI = "Właściciel: AI (wróg)"
ARMY_NONE = "Armia: brak armii"

CREDITED_ASSETS = (
    "party_player_unit.png",
    "settlement_outpost.png",
    "map_target_frame.png",
    "icon_march.png",
)


def _run(tmp_path: Path) -> dict:
    state_path = tmp_path / "blocked-enemy-settlement-move.json"
    request_path = tmp_path / "bridge-request.jsonl"
    command_prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    result = run_godot_script(
        GAME,
        PROBE,
        command_prefix,
        str(state_path),
        str(request_path),
        str(SEED),
        timeout=90,
    )
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def test_blocked_move_into_enemy_settlement_keeps_unit_and_polish_status(tmp_path):
    """Select+MarchButton on adjacent enemy settlement: no move, clear PL status.

    Realistic defect existing gates miss: legal targeted-move e2e (task-555) and
    OrderResult unit status pin only the successful ``changed=true`` step and the
    obsolete / generic unchanged wording. Bridge core already returns
    ``move`` + ``changed=false`` for enemy settlements (G97.1a), and contextual
    MarchButton already sends targeted ``move`` (G97.1f button) — but no live
    UI→JSONL→block-rule→re-render sequence pins that the silhouette stays only
    on the source region, the selection frame/panel still name the hostile
    settlement, and LastOrderStatusLabel reads exactly ``Ruch nie nastąpił.``
    (distinct from the legal-step status and from transport failure). A client
    that re-renders a ghost unit on the target, clears selection chrome, or
    shows ``Oddział nie przemieścił się.`` / empty / ``Rozkaz nie powiódł się.``
    keeps those green gates while this AC fails.
    """
    payload = _run(tmp_path)
    source_start = payload["source_start"]
    step_own = payload["step_own"]
    source = payload["source_region"]
    target = payload["target_region"]
    assert source_start == "player lands"
    assert step_own == "player outpost"
    assert source == "border"
    assert target == "ai outpost"
    assert payload["state_exists"] is True

    after_muster = payload["after_muster"]
    after_step_own = payload["after_step_own"]
    after_border = payload["after_step_border"]
    after_select = payload["after_select"]
    after_blocked = payload["after_blocked"]

    # Seed topology: muster on player lands, then legal step through own outpost.
    assert after_muster["marker_count"] == 1, after_muster
    assert after_muster["marked_regions"] == [source_start], after_muster
    assert after_step_own["marker_count"] == 1, after_step_own
    assert after_step_own["marked_regions"] == [step_own], after_step_own

    # Precondition: party stands on border next to the enemy outpost.
    assert after_border["marker_count"] == 1, after_border
    assert after_border["marked_regions"] == [source], after_border

    # Selection names the hostile neighbour; contextual label follows.
    assert after_select["selected_region_name"] == target, after_select
    assert after_select["march_label"] == f"Wyrusz: {target}", after_select
    assert after_select["frame_count"] == 1, after_select
    assert after_select["framed_regions"] == [target], after_select
    assert OWNER_AI in after_select["panel_text"], after_select
    assert ARMY_NONE in after_select["panel_text"], after_select

    # After blocked move: one silhouette still only on source (equality ⇒ not target).
    assert after_blocked["marker_count"] == 1, after_blocked
    assert after_blocked["marked_regions"] == [source], after_blocked
    assert source in after_blocked["position_label"], after_blocked

    # Selection chrome survives re-render on the blocked enemy settlement.
    assert after_blocked["selected_region_name"] == target, after_blocked
    assert after_blocked["frame_count"] == 1, after_blocked
    assert after_blocked["framed_regions"] == [target], after_blocked

    # Panel still describes the hostile settlement (owner + no army there).
    panel = after_blocked["panel_text"]
    assert target in panel, after_blocked
    assert OWNER_AI in panel, (
        f"panel must keep {OWNER_AI!r} on blocked {target!r}, got {panel!r}"
    )
    assert ARMY_NONE in panel, (
        f"panel must keep {ARMY_NONE!r} on blocked target (no ghost army), got {panel!r}"
    )

    # Public PL status for changed=false move — exact AC wording.
    assert after_blocked["order_status"] == BLOCKED_STATUS, (
        "after blocked move into enemy settlement LastOrderStatusLabel must be "
        f"{BLOCKED_STATUS!r}, got {after_blocked['order_status']!r}"
    )
    assert after_blocked["order_status"] != SUCCESS_STATUS
    assert after_blocked["order_status"] != TRANSPORT_FAILURE_STATUS
    assert "marsz" not in after_blocked["order_status"].lower()
    assert "szturm" not in after_blocked["order_status"].lower()


def test_blocked_enemy_settlement_move_assets_remain_credited():
    """AC: used map/order assets keep complete per-file CREDITS rows."""
    credits = GAME / "assets" / "CREDITS.md"
    for name in CREDITED_ASSETS:
        assert_asset_credited(credits, name)
