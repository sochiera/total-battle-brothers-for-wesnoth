"""Layout contract for the Godot main scene: controls must not stack on one point."""

from __future__ import annotations

import json
import re
import struct
import zlib
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
    "ResultLabel",
    "MoraleValueLabel",
    "SettlementsValueLabel",
    "PartiesValueLabel",
    "LastOrderStatusLabel",
    "PlayerPartyPositionLabel",
    "SelectedRegionPanel",
)
HIDDEN_CONTROLS = (
    "RegionList",
    "ResultContractLabel",
    "PlayerDuchyStatusLabel",
    "PartyPositionContractLabel",
)
COMMAND_CONTROLS = (
    "NextTurnButton",
    "DevelopButton",
    "RecruitButton",
    "MusterButton",
    "MarchButton",
    "AssaultButton",
    "EngageButton",
)
SAVE_LOAD_CONTROLS = (
    "SaveGameButton",
    "LoadGameButton",
    "NewGameButton",
)
ORDER_CONTROLS = COMMAND_CONTROLS + SAVE_LOAD_CONTROLS
ALL_CONTROLS = STATUS_CONTROLS + HIDDEN_CONTROLS + ORDER_CONTROLS

# G94.1d review resolution and strategic map panel background path.
VIEWPORT_W = 1152.0
VIEWPORT_H = 648.0
# Public MapView base hex height (game/scripts/map_view.gd BASE_TILE_SIZE.y).
# With-battle fit may shrink the map column, but region tiles must keep a
# readable fraction of that base — not a ~24px sliver under multi-hex battle.
MAP_VIEW_BASE_TILE_H = 48.0
MIN_READABLE_REGION_TILE_H_WITH_BATTLE = MAP_VIEW_BASE_TILE_H * 0.75
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
    GAME / "screenshots" / "task-579-fresh-order-states-1152x648.png",
    GAME / "screenshots" / "task-579-visible-battle-1152x648.png",
    # G107.1d: full-screen proof of the expanded bar with "Nowa partia".
    GAME / "screenshots" / "task-598-new-game-order-bar-1152x648.png",
)
WINDOW_BACKGROUND_SCREENSHOTS = (
    GAME / "screenshots" / "task-569-fresh-1152x648.png",
    GAME / "screenshots" / "task-569-selected-region-1152x648.png",
    GAME / "screenshots" / "task-569-visible-battle-1152x648.png",
    # G106.1a: scripted capture on a synthetic five-region model
    # (game/tests/capture_fresh_post_k105_review.gd; not a raw new_session).
    GAME / "screenshots" / "task-591-fresh-post-k105-1152x648.png",
    # G106.1b: empty → selected pair after K105; same synthetic model via
    # game/tests/capture_selected_region_post_k105_review.gd (task-568 pair
    # predates K105 chrome). Empty frame is intentionally identical to G106.1a.
    GAME / "screenshots" / "task-592-selected-region-empty-1152x648.png",
    GAME / "screenshots" / "task-592-selected-region-selected-1152x648.png",
    # G106.1c: visible battle after K105 — iso/¾ sides, PŻ, terrain decor,
    # PL result banner, centered occupied cluster; map + order bar still
    # readable. Pre-K105 task-569/579/585 battle frames are not this proof.
    GAME / "screenshots" / "task-593-visible-battle-post-k105-1152x648.png",
    # G108.1d: live seed-73 bridge session after passive turns; the AI army
    # stands on the strategic map rather than disappearing on its spawn turn.
    GAME / "screenshots" / "task-606-live-enemy-army-1152x648.png",
    # G108.1d / task-607: a second live seed-73 frame, after the player
    # presses Engage against that army; it must preserve the full strategic
    # chrome alongside the resolved battle.
    GAME / "screenshots" / "task-607-live-engage-battle-1152x648.png",
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
    "NewGameButton": "icon_new_game.png",
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


def _assert_review_screenshot(path: Path, *, frame_description: str = "review") -> None:
    assert path.is_file(), f"required human-review screenshot missing: {path}"
    width, height = _png_dimensions(path)
    assert (width, height) == (int(VIEWPORT_W), int(VIEWPORT_H)), (
        f"{path} must be 1152×648, got {width}×{height}"
    )
    assert path.stat().st_size >= 100_000, (
        f"{path} must contain a detailed {frame_description} frame, "
        "not a tiny flat-colour placeholder"
    )


def test_main_scene_controls_have_disjoint_layout_and_hidden_contract_controls():
    """Visible controls do not overlap; compatibility controls remain hidden.

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

    for name in HIDDEN_CONTROLS:
        rect = controls[name]
        assert rect is not None, f"{name} must remain findable for probe compatibility"
        assert rect["visible"] is False, (
            f"compatibility control {name} must not be presented, got {rect}"
        )

    visible_controls = STATUS_CONTROLS + ORDER_CONTROLS
    for name in ORDER_CONTROLS:
        rect = controls[name]
        assert rect["disabled"] is False, f"{name} must remain clickable, got {rect}"
        assert rect["visible"] is True, f"{name} must be visible, got {rect}"
        assert rect["clip_text"] is False, f"{name} must not clip its label, got {rect}"
        assert rect["w"] >= rect["minimum_w"], (
            f"{name} must fit its icon/label minimum width, got {rect}"
        )
        assert rect["h"] >= rect["minimum_h"], (
            f"{name} must fit its icon/label minimum height, got {rect}"
        )
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

    command_rows = {round(float(controls[name]["y"]), 3) for name in COMMAND_CONTROLS}
    save_load_rows = {
        round(float(controls[name]["y"]), 3) for name in SAVE_LOAD_CONTROLS
    }
    assert 1 <= len(command_rows) <= 2, (
        "the seven order buttons may use one row or a 5+2 command layout, "
        f"got rows={command_rows}"
    )
    assert len(save_load_rows) == 1, (
        "save/load/new-game buttons must remain on one separate row, "
        f"got rows={save_load_rows}"
    )
    assert command_rows.isdisjoint(save_load_rows), (
        "command and save/load rows must remain visually separate, "
        f"got commands={command_rows} save_load={save_load_rows}"
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
    """G103.1a/G107.1d: textured button states and the current bar proof.

    Realistic defect existing gates miss: functional buttons can keep three
    distinguishable StyleBoxFlat colours. Geometry, icon-path, contrast and
    order-bar background gates then remain green even though the interactive
    carriers are still the residual flat surfaces forbidden by G103.1a.

    G107.1d adds a separate failure mode: all order controls can be present and
    laid out correctly while the required post-G107 full-screen proof with
    ``NewGameButton`` is missing or is not a detailed 1152×648 frame.

    Pixel-level artistic approval intentionally remains human-owned. This gate
    observes each resolved public theme state and requires texture-backed,
    credited carriers with three distinct rendered texture/modulation signatures.
    """
    payload = _load_layout_payload()
    states = (payload.get("order_bar") or {}).get("button_states") or {}
    assert set(states) == set(ORDER_CONTROLS), states
    style_textures: set[str] = set()
    for button_name, button in states.items():
        assert button.get("found") is True, (button_name, button)
        signatures = []
        for state_name in ("normal", "hover", "pressed"):
            state = button.get(state_name) or {}
            assert state.get("explicit") is True, (
                f"{button_name} must explicitly style {state_name}, got {state!r}"
            )
            assert state.get("carrier") == "StyleBoxTexture", (
                f"{button_name} {state_name} must resolve to StyleBoxTexture, "
                f"got {state!r}"
            )
            texture_path = state.get("texture_path")
            assert isinstance(texture_path, str) and texture_path.startswith(
                "res://assets/"
            ), f"{button_name} {state_name} needs an asset texture, got {state!r}"
            texture_file = GAME / texture_path.removeprefix("res://")
            assert texture_file.is_file(), (
                f"{button_name} {state_name} texture missing: {texture_file}"
            )
            assert_asset_credited(
                GAME / "assets" / "CREDITS.md",
                texture_file.name,
                source_re=re.compile(r"https?://\S+|oryginał projektu"),
            )
            style_textures.add(texture_path)
            modulate = state.get("modulate_rgba")
            assert isinstance(modulate, list) and len(modulate) == 4, (
                f"{button_name} {state_name} needs measurable modulation, "
                f"got {state!r}"
            )
            signatures.append(
                (
                    texture_path,
                    tuple(round(float(channel), 3) for channel in modulate),
                )
            )
        assert len(set(signatures)) == 3, (
            f"{button_name} normal/hover/pressed texture looks must be distinct, "
            f"got {signatures!r}"
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

    assert len(style_textures) == 1, (
        "all order-bar buttons must share the same textured frame, "
        f"got {sorted(style_textures)!r}"
    )

    for screenshot in ORDER_BAR_SCREENSHOTS:
        _assert_review_screenshot(screenshot, frame_description="live-game review")


def test_window_background_review_screenshots_exist_at_target_resolution():
    """G100.1d (+ G106.1a/b/c, G108.1d): review PNGs exist at 1152×648.

    Covers post-G100.1d window-background states, the G106.1a fresh-party
    frame, the G106.1b empty→selected region pair, the G106.1c visible battle
    after K105, and G108.1d's two live-session frames (enemy army, then its
    resolved engage battle). **Scope: file presence, IHDR 1152×648, and size
    floor only** — visual inspection still owns whether the G108.1d images
    show the live bridge state, AI army, resolved battle, and Polish chrome.

    Realistic defect existing gates miss: BattleView geometry/sides/PŻ/PL
    result and K105.1c cluster centering can stay green, while no committed
    1152×648 frame proves either that an enemy army remains on the strategic
    map after passive live-bridge turns or that pressing Engage renders its
    resolved battle without losing the strategic chrome.
    """
    # Older task-565/task-568 captures predate the full-window parchment and
    # cannot demonstrate that root gaps no longer expose default grey chrome.
    for screenshot in WINDOW_BACKGROUND_SCREENSHOTS:
        _assert_review_screenshot(screenshot)


def test_strategic_composition_fits_review_viewport_collapses_empty_battle_and_uses_background():
    """G94.1d/G100.1d (+ G106.1c chrome): fitted composition with panel/window backgrounds.

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

    G106.1c residual: a 2-hex with-battle payload keeps BattleView short enough
    that status + order bar still fit, while the multi-hex G104/G105/G106 field
    (r∈{0,1,2}) grows the panel and clips the status card top and both order
    rows — the proof PNG can still be 1152×648. The probe's with-battle model
    is that multi-hex field so chrome-fit assertions catch the overflow.

    G106.1c residual (map readability): chrome-fit that only clamps MapView to
    h>1px (or floors near ~96px) can leave region tiles as a ~24px top sliver
    with crushed/overlapping PL labels while viewport fit and legend/tile
    disjointness stay green. The with-battle probe must report legend + region
    tile rects; the legend must not be clipped by MapView, legend and tiles
    must not share screen area, and each region tile must keep a readable
    minimum height (¾ of MapView base tile height) under the multi-hex fit
    that the proof PNG uses.
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
    for name in HIDDEN_CONTROLS:
        assert controls[name] is not None
        assert controls[name]["visible"] is False
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
    assert _rect_fully_inside_viewport(battle_present), (
        f"BattleView must fit fully inside {VIEWPORT_W:.0f}×{VIEWPORT_H:.0f} "
        f"with multi-hex battle (no clip of fight panel), got {battle_present!r}"
    )
    result_text = str(payload.get("battle_result_text_with_battle") or "")
    assert result_text.strip(), (
        "with battle present, BattleResultLabel must still show a non-empty "
        f"outcome (hide-empty must not drop last battle result), got {result_text!r}"
    )

    # map_view alone is the no-battle sample; after fit, MapView may shrink —
    # still must remain on-screen so strategic map stays readable with the fight.
    map_with_battle = payload.get("map_view_with_battle") or {}
    assert map_with_battle.get("found") is True, (
        "probe must report MapView after with-battle apply_model, "
        f"got {map_with_battle!r}"
    )
    assert float(map_with_battle.get("w") or 0) > 1.0 and float(
        map_with_battle.get("h") or 0
    ) > 1.0, (
        "with multi-hex battle, MapView must keep non-zero layout size "
        f"(chrome fit must not collapse the strategic map), got {map_with_battle!r}"
    )
    assert _rect_fully_inside_viewport(map_with_battle), (
        f"MapView must remain inside {VIEWPORT_W:.0f}×{VIEWPORT_H:.0f} "
        f"when BattleView is shown, got {map_with_battle!r}"
    )
    assert float(map_with_battle["y"]) >= 4.0, (
        "with BattleView shown, MapView must keep at least a 4px upper rim "
        "instead of being effectively pinned to the viewport edge and clipping "
        "its strategic frame; "
        f"got {map_with_battle!r}"
    )

    # Readable strategic map with battle: OwnerLegend must not cover region tiles,
    # and tiles must keep enough height for PL labels / party marks (not a sliver).
    # Legend/tile disjoint + map_h>1 alone is green at map_h≈96 with tile_h≈24.
    map_readability = payload.get("map_readability_with_battle") or {}
    assert map_readability.get("found") is True, (
        "probe must report MapView readability after with-battle apply_model, "
        f"got {map_readability!r}"
    )
    legend = map_readability.get("legend")
    assert isinstance(legend, dict), (
        "OwnerLegend must be present on MapView with multi-hex battle, "
        f"got {map_readability!r}"
    )
    assert float(legend.get("w") or 0) > 0 and float(legend.get("h") or 0) > 0, (
        f"OwnerLegend must have non-zero size, got {legend!r}"
    )
    assert (
        float(legend["x"]) >= float(map_with_battle["x"]) - 1.0
        and float(legend["y"]) >= float(map_with_battle["y"]) - 1.0
        and float(legend["x"]) + float(legend["w"])
        <= float(map_with_battle["x"]) + float(map_with_battle["w"]) + 1.0
        and float(legend["y"]) + float(legend["h"])
        <= float(map_with_battle["y"]) + float(map_with_battle["h"]) + 1.0
    ), (
        "with multi-hex battle, OwnerLegend must fit fully inside MapView; "
        "otherwise MapView.clip_contents cuts the strategic legend even though "
        f"the panel itself is on-screen. legend={legend!r} map={map_with_battle!r}"
    )
    region_tiles = map_readability.get("region_tiles") or []
    assert len(region_tiles) >= 1, (
        "MapView with battle must expose region tiles for readability check, "
        f"got {map_readability!r}"
    )
    for tile in region_tiles:
        assert not _rects_share_a_point(legend, tile), (
            "with multi-hex battle, OwnerLegend must not cover region tiles "
            f"(strategic map must stay readable beside BattleView); "
            f"legend={legend!r} tile={tile!r} map_h={map_readability.get('map_h')!r}"
        )
        tile_h = float(tile.get("h") or 0)
        assert tile_h >= MIN_READABLE_REGION_TILE_H_WITH_BATTLE, (
            "with multi-hex battle, each region tile must keep a readable height "
            f"(≥{MIN_READABLE_REGION_TILE_H_WITH_BATTLE:.0f}px = ¾ of MapView "
            f"base tile {MAP_VIEW_BASE_TILE_H:.0f}px); chrome fit must not crush "
            f"the strategic strip to an unreadable sliver. "
            f"tile={tile!r} map_h={map_readability.get('map_h')!r} "
            f"legend={legend!r}"
        )

    controls_battle = payload["controls_with_battle"]
    assert isinstance(controls_battle, dict), (
        "controls_with_battle must be a control map when apply_model is available, "
        f"got {controls_battle!r}"
    )
    assert set(controls_battle) == set(ALL_CONTROLS), controls_battle
    for name in HIDDEN_CONTROLS:
        assert controls_battle[name] is not None
        assert controls_battle[name]["visible"] is False
    for name in STATUS_CONTROLS + ORDER_CONTROLS:
        rect = controls_battle[name]
        assert rect is not None and rect["w"] > 0 and rect["h"] > 0, rect
        # With battle, status + orders must remain on-screen (may be tighter).
        assert _rect_fully_inside_viewport(rect), (
            f"{name} must remain inside {VIEWPORT_W:.0f}×{VIEWPORT_H:.0f} "
            f"even when BattleView is shown, got {rect}"
        )
