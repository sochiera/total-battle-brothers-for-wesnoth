"""Layout contract for the Godot main scene: controls must not stack on one point."""

from __future__ import annotations

import json
import re
import struct
import zlib
from pathlib import Path

from godot_png_assets import assert_asset_credited, png_rgba8
from godot_runner import run_godot_script
from test_godot_assets import _import_game_assets

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PREFIX = "SCENE_LAYOUT "

# Public contract names from task-471 / main scene.
STATUS_CONTROLS = (
    "DateLabel",
    "StartStatusLabel",
    "ResultLabel",
    "PlayerDuchyStatusLabel",
    "LastOrderStatusLabel",
    "PlayerPartyPositionLabel",
    "SelectedRegionPanel",
)
HIDDEN_CONTROLS = ("RegionList",)
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
ALL_CONTROLS = STATUS_CONTROLS + HIDDEN_CONTROLS + ORDER_CONTROLS

# G94.1d review resolution and strategic map panel background path.
VIEWPORT_W = 1152.0
VIEWPORT_H = 648.0
STRATEGIC_BACKGROUND = "strategic_map_background.png"
STRATEGIC_BACKGROUND_RES = f"res://assets/{STRATEGIC_BACKGROUND}"
STATUS_BACKGROUND = "strategic_status_background.png"
STATUS_BACKGROUND_RES = f"res://assets/{STATUS_BACKGROUND}"
ORDER_BAR_BACKGROUND = "order_bar_background.png"
ORDER_BAR_BACKGROUND_RES = f"res://assets/{ORDER_BAR_BACKGROUND}"
WINDOW_BACKGROUND_RESOURCES = {
    "res://assets/strategic_window_background.png",
    STRATEGIC_BACKGROUND_RES,
    STATUS_BACKGROUND_RES,
    ORDER_BAR_BACKGROUND_RES,
}
ORDER_BAR_SCREENSHOTS = (
    GAME / "screenshots" / "task-565-fresh-order-states-1152x648.png",
    GAME / "screenshots" / "task-565-visible-battle-1152x648.png",
)
WINDOW_BACKGROUND_SCREENSHOTS = (
    GAME / "screenshots" / "task-569-fresh-1152x648.png",
    GAME / "screenshots" / "task-569-selected-region-1152x648.png",
    GAME / "screenshots" / "task-569-visible-battle-1152x648.png",
)
ORDER_ICON_FILES = {
    "NextTurnButton": "icon_next_turn.png",
    "DevelopButton": "icon_develop.png",
    "RecruitButton": "icon_recruit.png",
    "MusterButton": "icon_muster.png",
    "MarchButton": "icon_march.png",
    "AssaultButton": "icon_assault.png",
    "SaveGameButton": "icon_save.png",
    "LoadGameButton": "icon_load.png",
}


def _load_layout_payload() -> dict:
    result = run_godot_script(GAME, "res://tests/scene_layout_probe.gd", timeout=30)
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    # Runtime call/deferred argument failures use the plain ``ERROR:`` prefix
    # and can leave the probe's JSON and exit status looking successful.
    assert "ERROR:" not in result.stderr, result.stderr
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


def _relative_luminance(rgb: tuple[float, float, float]) -> float:
    linear = tuple(
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in rgb
    )
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _median_opaque_icon_luminance(
    path: Path, modulate_rgb: tuple[float, float, float] = (1.0, 1.0, 1.0)
) -> float:
    _width, _height, rgba = png_rgba8(path)
    luminances = sorted(
        _relative_luminance(
            (
                rgba[i] / 255 * modulate_rgb[0],
                rgba[i + 1] / 255 * modulate_rgb[1],
                rgba[i + 2] / 255 * modulate_rgb[2],
            )
        )
        for i in range(0, len(rgba), 4)
        if rgba[i + 3] >= 192
    )
    assert luminances, f"icon must contain visible pixels: {path}"
    return luminances[len(luminances) // 2]


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"not a PNG: {path}"
    pos = 8
    dimensions = None
    saw_iend = False
    while pos + 12 <= len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_end = pos + 12 + length
        assert chunk_end <= len(data), f"truncated PNG chunk: {path}"
        chunk_type = data[pos + 4 : pos + 8]
        chunk = data[pos + 8 : pos + 8 + length]
        expected_crc = struct.unpack(">I", data[pos + 8 + length : chunk_end])[0]
        assert zlib.crc32(chunk_type + chunk) & 0xFFFFFFFF == expected_crc, (
            f"invalid PNG chunk CRC: {path}"
        )
        if chunk_type == b"IHDR":
            assert length == 13 and dimensions is None, f"invalid PNG IHDR: {path}"
            dimensions = struct.unpack(">II", chunk[:8])
        if chunk_type == b"IEND":
            assert length == 0, f"invalid PNG IEND: {path}"
            saw_iend = True
            pos = chunk_end
            break
        pos = chunk_end
    assert dimensions is not None and saw_iend and pos == len(data), (
        f"incomplete PNG structure: {path}"
    )
    return dimensions


def test_main_scene_controls_have_disjoint_layout_and_hidden_region_list():
    """Visible controls must not overlap; the map replaces the hidden RegionList.

    Realistic defect this catches: main.tscn still parents every control at the
    same origin with default zero sizes (empirically all global_position==(0,0),
    RegionList 0×0). Existing scene probes only assert names/classes/text and
    bridge behaviour, so a stacked, unreadable UI stays green.
    """
    controls = _load_layout()

    for name in STATUS_CONTROLS + ORDER_CONTROLS:
        rect = controls[name]
        assert rect is not None, f"missing control {name}"
        assert rect["w"] > 0 and rect["h"] > 0, (
            f"{name} must have non-zero size after layout, got {rect}"
        )

    region = controls["RegionList"]
    assert region is not None, "RegionList must remain findable for bridge/probe compatibility"
    assert region["visible"] is False, (
        f"duplicated RegionList must not be presented beside the map, got {region}"
    )

    visible_controls = STATUS_CONTROLS + ORDER_CONTROLS
    for i, left_name in enumerate(visible_controls):
        for right_name in visible_controls[i + 1 :]:
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


def test_order_bar_uses_credited_background_covering_all_order_controls():
    """G99.1d: the complete order bar is visibly backed by its public texture.

    Realistic defect existing gates miss: ``OrderControls`` remains a transparent
    VBox containing otherwise functional buttons. Layout and icon tests stay
    green because they only check control rectangles, labels and icon paths;
    they do not require the named, credited bar artwork or verify that it is
    actually rendered behind the full group. A copied ``.import`` may also retain
    the status background's UID, making Godot treat two public textures as the
    same resource identity even though both PNG paths exist and load.
    """
    assets_dir = GAME / "assets"
    background_path = assets_dir / ORDER_BAR_BACKGROUND
    assert background_path.is_file(), (
        f"required order-bar background missing on disk: {background_path}"
    )
    assert_asset_credited(
        assets_dir / "CREDITS.md",
        ORDER_BAR_BACKGROUND,
        source_re=re.compile(r"https?://\S+"),
    )
    order_import = (background_path.with_suffix(".png.import")).read_text(
        encoding="utf-8"
    )
    status_import = (
        assets_dir / f"{STATUS_BACKGROUND}.import"
    ).read_text(encoding="utf-8")
    order_uid = re.search(r'^uid="([^"]+)"$', order_import, re.MULTILINE)
    status_uid = re.search(r'^uid="([^"]+)"$', status_import, re.MULTILINE)
    assert order_uid and status_uid, "both background imports must declare a UID"
    assert order_uid.group(1) != status_uid.group(1), (
        "order-bar and strategic-status backgrounds must have distinct Godot UIDs"
    )

    payload = _load_layout_payload()
    order_bar = payload.get("order_bar") or {}
    assert order_bar.get("found") is True, order_bar
    assert order_bar.get("background_path") == ORDER_BAR_BACKGROUND_RES, order_bar
    assert order_bar.get("background_covers_panel") is True, (
        "order-bar background must cover the complete OrderControls rect, "
        f"got {order_bar!r}"
    )


def test_order_buttons_expose_distinct_states_and_review_screenshots():
    """G99.1d: button-state styling and both human-review frames are observable.

    Realistic defect existing gates miss: functional buttons can retain one
    indistinguishable/default-looking surface in every interaction state, and
    no 1152×648 evidence may exist for reviewing those states or the battle
    composition. Geometry, icon-path and background gates all remain green.

    Pixel-level artistic approval intentionally remains human-owned. This gate
    requires explicit public theme states with distinct background colours and
    registers the two required, correctly sized PNG review artifacts.
    """
    payload = _load_layout_payload()
    states = (payload.get("order_bar") or {}).get("button_states") or {}
    assert set(states) == set(ORDER_CONTROLS), states
    for button_name, button in states.items():
        assert button.get("found") is True, (button_name, button)
        colors = []
        for state_name in ("normal", "hover", "pressed"):
            state = button.get(state_name) or {}
            assert state.get("explicit") is True, (
                f"{button_name} must explicitly style {state_name}, got {state!r}"
            )
            rgba = state.get("background_rgba")
            assert isinstance(rgba, list) and len(rgba) == 4, (
                f"{button_name} {state_name} needs a measurable flat background, "
                f"got {rgba!r}"
            )
            colors.append(tuple(round(float(channel), 3) for channel in rgba))
        assert len(set(colors)) == 3, (
            f"{button_name} normal/hover/pressed backgrounds must be distinct, "
            f"got {colors!r}"
        )
        icon_modulate = button.get("icon_modulate_rgba")
        assert isinstance(icon_modulate, list) and len(icon_modulate) == 4, (
            f"{button_name} needs a measurable normal icon modulate, "
            f"got {icon_modulate!r}"
        )
        assert float(icon_modulate[3]) >= 0.95, (
            f"{button_name} icon modulate must remain effectively opaque, "
            f"got {icon_modulate!r}"
        )
        icon_luminance = _median_opaque_icon_luminance(
            GAME / "assets" / ORDER_ICON_FILES[button_name],
            tuple(float(channel) for channel in icon_modulate[:3]),
        )
        for state_name, rgba in zip(("normal", "hover", "pressed"), colors):
            background_luminance = _relative_luminance(rgba[:3])
            contrast = (
                max(icon_luminance, background_luminance) + 0.05
            ) / (
                min(icon_luminance, background_luminance) + 0.05
            )
            assert contrast >= 3.0, (
                f"{button_name} icon needs >=3:1 median-pixel contrast in "
                f"{state_name}, got {contrast:.2f}:1"
            )

    for screenshot in ORDER_BAR_SCREENSHOTS:
        assert screenshot.is_file(), f"required human-review screenshot missing: {screenshot}"
        width, height = _png_dimensions(screenshot)
        assert (width, height) == (int(VIEWPORT_W), int(VIEWPORT_H)), (
            f"{screenshot} must be 1152×648, got {width}×{height}"
        )
        assert screenshot.stat().st_size >= 100_000, (
            f"{screenshot} must contain a detailed live-game review frame, "
            "not a tiny flat-colour placeholder"
        )

def test_window_background_review_screenshots_exist_at_target_resolution():
    """G100.1d: review artifacts cover fresh, selected, and battle states."""
    # Older task-565/task-568 captures predate the full-window parchment and
    # cannot demonstrate that root gaps no longer expose default grey chrome.
    for screenshot in WINDOW_BACKGROUND_SCREENSHOTS:
        assert screenshot.is_file(), (
            f"required post-G100.1d human-review screenshot missing: {screenshot}"
        )
        width, height = _png_dimensions(screenshot)
        assert (width, height) == (int(VIEWPORT_W), int(VIEWPORT_H)), (
            f"{screenshot} must be 1152×648, got {width}×{height}"
        )
        assert screenshot.stat().st_size >= 100_000, (
            f"{screenshot} must contain a detailed live-game review frame, "
            "not a tiny flat-colour placeholder"
        )


def test_strategic_composition_fits_review_viewport_collapses_empty_battle_and_uses_background():
    """G94.1d/G100.1d: fitted composition with panel and window backgrounds.

    Realistic defect existing gates miss: main.tscn always reserves BattleView
    ``custom_minimum_size`` 420×240 even when the snapshot has no battle, so a
    fresh party at the review resolution 1152×648 pushes order buttons past the
    bottom edge and leaves a large grey empty strip. Layout only checks pairwise
    disjointness of status/order controls and never looks at BattleView height,
    viewport fit, or a map-panel background. Asset gates do not require
    ``strategic_map_background.png`` or its CREDITS row, so the strategic screen
    stays green while still looking like a prototype. G100.1d additionally
    requires an allowed parchment texture to cover the complete viewport so
    root gaps and container separators cannot expose default grey chrome.
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
    status_background_path = assets_dir / STATUS_BACKGROUND
    assert status_background_path.is_file(), (
        f"required status-card background missing on disk: {status_background_path}"
    )
    assert_asset_credited(
        assets_dir / "CREDITS.md",
        STATUS_BACKGROUND,
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
    window_background = payload.get("window_background") or {}
    assert window_background.get("found") is True, window_background
    assert window_background.get("background_path") in WINDOW_BACKGROUND_RESOURCES, (
        "the complete strategic window must use the dedicated artwork or an "
        "explicit extension of an existing parchment texture, "
        f"got {window_background!r}"
    )
    assert window_background.get("background_covers_window") is True, (
        "a medieval background must cover the complete 1152×648 window so "
        "container separators and empty root areas cannot expose default grey "
        f"chrome, got {window_background!r}"
    )
    assert window_background.get("visible") is True, window_background
    assert window_background.get("covered_stretch") is True, (
        "the full-window texture must crop-to-cover rather than letterbox, "
        f"got {window_background!r}"
    )
    assert window_background.get("below_main_layout") is True, (
        "the window background must be a sibling drawn below MainLayout, "
        f"got {window_background!r}"
    )

    # No-battle layout lives under the single key "controls" (same as disjoint).
    controls = payload["controls"]
    assert set(controls) == set(ALL_CONTROLS), controls
    assert controls["RegionList"] is not None
    assert controls["RegionList"]["visible"] is False
    for name in STATUS_CONTROLS + ORDER_CONTROLS:
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
    # Observable: the MapView subtree itself has the strategic texture covering
    # its rect. A full-window sibling using the same asset cannot satisfy this.
    assert map_view.get("background_path") == STRATEGIC_BACKGROUND_RES, (
        f"map panel must show textured strategic background "
        f"{STRATEGIC_BACKGROUND_RES}, got {map_view.get('background_path')!r}"
    )
    assert map_view.get("background_covers_panel") is True, (
        "strategic background texture must cover the MapView panel rect, "
        f"got {map_view!r}"
    )
    status_card = payload.get("status_card") or {}
    assert status_card.get("found") is True, status_card
    assert status_card.get("background_path") == STATUS_BACKGROUND_RES, status_card
    assert status_card.get("background_covers_panel") is True, status_card

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
    assert controls_battle["RegionList"] is not None
    assert controls_battle["RegionList"]["visible"] is False
    for name in STATUS_CONTROLS + ORDER_CONTROLS:
        rect = controls_battle[name]
        assert rect is not None and rect["w"] > 0 and rect["h"] > 0, rect
        # With battle, status + orders must remain on-screen (may be tighter).
        assert _rect_fully_inside_viewport(rect), (
            f"{name} must remain inside {VIEWPORT_W:.0f}×{VIEWPORT_H:.0f} "
            f"even when BattleView is shown, got {rect}"
        )
