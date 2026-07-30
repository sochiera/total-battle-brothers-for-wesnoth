"""Layout contract for the Godot main scene: controls must not stack on one point."""

from __future__ import annotations

import json
import re
from pathlib import Path

from godot_png_assets import assert_asset_credited
from godot_runner import run_godot_script
from test_godot_assets import _import_game_assets

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PREFIX = "SCENE_LAYOUT "

# Public contract names from task-471 / main scene.
STATUS_CONTROLS = (
    "DateLabel",
    "StartStatusLabel",
    "RegionList",
    "ResultLabel",
    "PlayerDuchyStatusLabel",
    "LastOrderStatusLabel",
    "PlayerPartyPositionLabel",
)
ORDER_CONTROLS = (
    "NextTurnButton",
    "DevelopButton",
    "RecruitButton",
    "MusterButton",
    "MarchButton",
    "AssaultButton",
    "SaveGameButton",
    "LoadGameButton",
)
ALL_CONTROLS = STATUS_CONTROLS + ORDER_CONTROLS

# G94.1d review resolution and strategic map panel background path.
VIEWPORT_W = 1152.0
VIEWPORT_H = 648.0
STRATEGIC_BACKGROUND = "strategic_map_background.png"
STRATEGIC_BACKGROUND_RES = f"res://assets/{STRATEGIC_BACKGROUND}"


def _load_layout_payload() -> dict:
    result = run_godot_script(GAME, "res://tests/scene_layout_probe.gd", timeout=30)
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def _load_layout() -> dict[str, dict[str, float] | None]:
    payload = _load_layout_payload()
    controls = payload["controls"]
    assert set(controls) == set(ALL_CONTROLS), controls
    return controls


def _rects_share_a_point(a: dict[str, float], b: dict[str, float]) -> bool:
    """Closed axis-aligned rects: true if any screen point lies in both."""
    a_right = a["x"] + a["w"]
    a_bottom = a["y"] + a["h"]
    b_right = b["x"] + b["w"]
    b_bottom = b["y"] + b["h"]
    # Strict separation on an axis ⇒ no shared point (edges may touch).
    if a_right <= b["x"] or b_right <= a["x"]:
        return False
    if a_bottom <= b["y"] or b_bottom <= a["y"]:
        return False
    return True


def _union_bbox(rects: list[dict[str, float]]) -> dict[str, float]:
    left = min(r["x"] for r in rects)
    top = min(r["y"] for r in rects)
    right = max(r["x"] + r["w"] for r in rects)
    bottom = max(r["y"] + r["h"] for r in rects)
    return {"x": left, "y": top, "w": right - left, "h": bottom - top}


def _rect_fully_inside_viewport(
    rect: dict[str, float], *, w: float = VIEWPORT_W, h: float = VIEWPORT_H, tol: float = 1.0
) -> bool:
    """True when rect lies fully inside [0,0]–[w,h] (edges may touch, tol for snap)."""
    return (
        float(rect["x"]) >= -tol
        and float(rect["y"]) >= -tol
        and float(rect["x"]) + float(rect["w"]) <= w + tol
        and float(rect["y"]) + float(rect["h"]) <= h + tol
    )


def _battle_view_takes_layout_space(state: dict) -> bool:
    """BattleView contributes vertical space when visible with non-trivial height."""
    if not state.get("found"):
        return False
    if state.get("visible") is False:
        return False
    return float(state.get("h") or 0) > 1.0


def test_main_scene_controls_have_disjoint_layout_and_visible_region_list():
    """Controls must not share screen points; RegionList must be visible area.

    Realistic defect this catches: main.tscn still parents every control at the
    same origin with default zero sizes (empirically all global_position==(0,0),
    RegionList 0×0). Existing scene probes only assert names/classes/text and
    bridge behaviour, so a stacked, unreadable UI stays green.
    """
    controls = _load_layout()

    for name in ALL_CONTROLS:
        rect = controls[name]
        assert rect is not None, f"missing control {name}"
        assert rect["w"] > 0 and rect["h"] > 0, (
            f"{name} must have non-zero size after layout, got {rect}"
        )

    # Beyond ALL_CONTROLS non-zero size: list must be tall enough to show several rows.
    # Default ItemList row ~24px; main.tscn min height is 180 — require at least ~3 rows.
    region = controls["RegionList"]
    assert region["w"] >= 100, f"RegionList width too small for names: {region}"
    assert region["h"] >= 72, f"RegionList height must fit several items, got {region}"

    for i, left_name in enumerate(ALL_CONTROLS):
        for right_name in ALL_CONTROLS[i + 1 :]:
            left = controls[left_name]
            right = controls[right_name]
            assert not _rects_share_a_point(left, right), (
                f"{left_name} and {right_name} share screen area: "
                f"{left} vs {right}"
            )

    status_rects = [controls[name] for name in STATUS_CONTROLS]
    order_rects = [controls[name] for name in ORDER_CONTROLS]
    status_box = _union_bbox(status_rects)
    order_box = _union_bbox(order_rects)
    assert not _rects_share_a_point(status_box, order_box), (
        "status controls and order buttons must form separate groups, "
        f"got status={status_box} orders={order_box}"
    )


def test_strategic_composition_fits_review_viewport_collapses_empty_battle_and_uses_background():
    """G94.1d: 1152×648 composition, empty BattleView free, map panel background.

    Realistic defect existing gates miss: main.tscn always reserves BattleView
    ``custom_minimum_size`` 420×240 even when the snapshot has no battle, so a
    fresh party at the review resolution 1152×648 pushes order buttons past the
    bottom edge and leaves a large grey empty strip. Layout only checks pairwise
    disjointness of status/order controls and never looks at BattleView height,
    viewport fit, or a map-panel background. Asset gates do not require
    ``strategic_map_background.png`` or its CREDITS row, so the strategic screen
    stays green while still looking like a prototype.
    """
    assets_dir = GAME / "assets"
    background_path = assets_dir / STRATEGIC_BACKGROUND
    assert background_path.is_file(), (
        f"required strategic background missing on disk: {background_path}"
    )
    # License and source URL must sit on the asset row (or adjacent prose), not
    # merely elsewhere in the pack credits (e.g. Kenney CC0 alone must not pass).
    assert_asset_credited(
        assets_dir / "CREDITS.md",
        STRATEGIC_BACKGROUND,
        source_re=re.compile(r"https?://\S+"),
    )

    # Headless import so Texture2D path can resolve when MapView wires the asset.
    # Shared with tests/test_godot_assets.py (single place for godot --import).
    imported = _import_game_assets()
    assert imported.returncode == 0, (
        f"godot --import failed rc={imported.returncode} "
        f"stderr={imported.stderr!r} stdout={imported.stdout!r}"
    )

    payload = _load_layout_payload()
    viewport = payload.get("viewport") or {}
    assert float(viewport.get("w", 0)) == VIEWPORT_W, payload
    assert float(viewport.get("h", 0)) == VIEWPORT_H, payload
    assert payload.get("apply_model") is True, (
        "scene_layout_probe must drive Main.apply_model for no/with-battle "
        f"composition; missing method would self-satisfy on bridge residue, "
        f"got apply_model={payload.get('apply_model')!r}"
    )

    # No-battle layout lives under the single key "controls" (same as disjoint).
    controls = payload["controls"]
    assert set(controls) == set(ALL_CONTROLS), controls
    for name in ALL_CONTROLS:
        rect = controls[name]
        assert rect is not None, f"missing control {name}"
        assert rect["w"] > 0 and rect["h"] > 0, (
            f"{name} must have non-zero size after no-battle layout, got {rect}"
        )
        assert _rect_fully_inside_viewport(rect), (
            f"{name} must fit fully inside {VIEWPORT_W:.0f}×{VIEWPORT_H:.0f} "
            f"with no battle (no scroll / no buttons below fold), got {rect}"
        )

    map_view = payload.get("map_view") or {}
    assert map_view.get("found") is True, f"MapView required, got {map_view!r}"
    assert float(map_view["w"]) > 0 and float(map_view["h"]) > 0, map_view
    assert _rect_fully_inside_viewport(map_view), (
        f"MapView must fit inside review viewport, got {map_view!r}"
    )
    # Observable: panel has the strategic texture covering its rect — not a
    # fixed child name/parent (node may move under MapAndBattle / panel root).
    assert map_view.get("background_path") == STRATEGIC_BACKGROUND_RES, (
        f"map panel must show textured strategic background "
        f"{STRATEGIC_BACKGROUND_RES}, got {map_view.get('background_path')!r}"
    )
    assert map_view.get("background_covers_panel") is True, (
        "strategic background texture must cover the MapView panel rect, "
        f"got {map_view!r}"
    )

    battle_empty = payload.get("battle_view_no_battle") or {}
    assert battle_empty.get("found") is True, battle_empty
    assert not _battle_view_takes_layout_space(battle_empty), (
        "when snapshot has no battle, BattleView must not reserve layout space "
        f"(hide or collapse height), got {battle_empty!r}"
    )

    battle_present = payload.get("battle_view_with_battle") or {}
    assert battle_present.get("found") is True, battle_present
    assert _battle_view_takes_layout_space(battle_present), (
        "when snapshot carries a battle, BattleView must be visible and take "
        f"layout space so the fight remains available, got {battle_present!r}"
    )
    result_text = str(payload.get("battle_result_text_with_battle") or "")
    assert result_text.strip(), (
        "with battle present, BattleResultLabel must still show a non-empty "
        f"outcome (hide-empty must not drop last battle result), got {result_text!r}"
    )

    controls_battle = payload["controls_with_battle"]
    assert isinstance(controls_battle, dict), (
        "controls_with_battle must be a control map when apply_model is available, "
        f"got {controls_battle!r}"
    )
    assert set(controls_battle) == set(ALL_CONTROLS), controls_battle
    for name in ALL_CONTROLS:
        rect = controls_battle[name]
        assert rect is not None and rect["w"] > 0 and rect["h"] > 0, rect
        # With battle, status + orders must remain on-screen (may be tighter).
        assert _rect_fully_inside_viewport(rect), (
            f"{name} must remain inside {VIEWPORT_W:.0f}×{VIEWPORT_H:.0f} "
            f"even when BattleView is shown, got {rect}"
        )

