"""BattleView contract: one axial hex tile per battle hex, side paint, Polish result."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from godot_runner import run_godot_script
from godot_tile_layer import MOUSE_FILTER_IGNORE, layer_fills_tile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PREFIX = "BATTLE_VIEW "

# Public asset paths for battle terrain (G87.1a / G87.1c-1).
TERRAIN_ASSETS: dict[str, str] = {
    "Plains": "res://assets/terrain_plains.png",
    "Forest": "res://assets/terrain_forest.png",
    "Hills": "res://assets/terrain_hills.png",
}

# Native base hex from terrain_plains.png (G98.1a public visual contract).
PLAINS_ASSET = TERRAIN_ASSETS["Plains"]
FOREST_ASSET = TERRAIN_ASSETS["Forest"]
HILLS_ASSET = TERRAIN_ASSETS["Hills"]
BASE_HEX_W = 120
BASE_HEX_H = 140
_LAYOUT_TOL_PX = 1.0

# Native decoration pixel sizes (public contract from audited PNGs, G98.1b).
# Forest = tree 26×40, Hills = rock 74×92 — proportions, not stretch-to-hex.
DECORATION_NATIVE: dict[str, tuple[float, float]] = {
    "Forest": (26.0, 40.0),
    "Hills": (74.0, 92.0),
}
_ENGLISH_TERRAIN_LABELS = frozenset({"Plains", "Forest", "Hills"})
# TextureRect.STRETCH_SCALE — full-rect scaled fill (forbidden for decorations).
_STRETCH_SCALE = 0

# Public side silhouette paths (G87.1a / G87.1c-2).
SIDE_ATTACKER = "res://assets/side_attacker.png"
SIDE_DEFENDER = "res://assets/side_defender.png"
SIDE_ASSETS = (SIDE_ATTACKER, SIDE_DEFENDER)


def _import_game_assets() -> subprocess.CompletedProcess[str]:
    """Headless import so res://assets/*.png resolve to Texture2D."""
    return subprocess.run(
        ["godot", "--headless", "--path", str(GAME), "--import"],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def _load_battle_view() -> dict:
    result = run_godot_script(GAME, "res://tests/battle_view_probe.gd", timeout=30)
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def _by_qr(tiles: list[dict]) -> dict[tuple[int, int], dict]:
    return {(int(t["q"]), int(t["r"])): t for t in tiles}


def _rects_overlap(a: dict, b: dict) -> bool:
    a_right = a["x"] + a["w"]
    a_bottom = a["y"] + a["h"]
    b_right = b["x"] + b["w"]
    b_bottom = b["y"] + b["h"]
    if a_right <= b["x"] or b_right <= a["x"]:
        return False
    if a_bottom <= b["y"] or b_bottom <= a["y"]:
        return False
    return True


def _polish_mentions_result(text: str, *keywords: str) -> bool:
    lowered = text.casefold()
    return any(keyword.casefold() in lowered for keyword in keywords)


def _rect_of(node: dict) -> dict:
    return {"x": node["x"], "y": node["y"], "w": node["w"], "h": node["h"]}


def _terrain_layers(tile: dict, terrain_path: str) -> list[dict]:
    layers = tile.get("texture_layers") or []
    return [
        layer
        for layer in layers
        if isinstance(layer, dict) and layer.get("path") == terrain_path
    ]


def _assert_credits_table_row(asset_name: str) -> None:
    """Complete per-file CREDITS.md row: file | source | author | license."""
    credits = (GAME / "assets" / "CREDITS.md").read_text(encoding="utf-8")
    assert asset_name in credits, (
        f"CREDITS.md must keep a per-file attribution for {asset_name}"
    )
    credits_row = next(
        (
            line
            for line in credits.splitlines()
            if line.strip().startswith("|") and asset_name in line
        ),
        "",
    )
    assert credits_row, f"CREDITS.md must have a table row for {asset_name}"
    cells = [c.strip() for c in credits_row.strip("|").split("|")]
    assert len(cells) >= 4 and cells[0] == asset_name and all(cells[:4]), (
        f"CREDITS row for {asset_name} must list file|source|author|license, "
        f"got {credits_row!r}"
    )


def _fully_inside(outer: dict, inner: dict) -> bool:
    """True if inner's closed rectangle lies entirely within outer (edges may touch)."""
    return (
        inner["x"] >= outer["x"]
        and inner["y"] >= outer["y"]
        and inner["x"] + inner["w"] <= outer["x"] + outer["w"]
        and inner["y"] + inner["h"] <= outer["y"] + outer["h"]
    )


def _gap_between_axis_aligned(a: dict, b: dict, *, axis: str) -> float:
    """Non-negative gap between two AABBs along one axis ('x' or 'y').

    Zero means edges touch or rects overlap on that axis. Positive means a
    visible separation (card-style spacing).
    """
    if axis == "x":
        a0, a1 = float(a["x"]), float(a["x"]) + float(a["w"])
        b0, b1 = float(b["x"]), float(b["x"]) + float(b["w"])
    else:
        a0, a1 = float(a["y"]), float(a["y"]) + float(a["h"])
        b0, b1 = float(b["y"]), float(b["y"]) + float(b["h"])
    if a1 <= b0:
        return b0 - a1
    if b1 <= a0:
        return a0 - b1
    return 0.0


def _canvas_draw_order_key(tile: dict) -> tuple[int, int]:
    """Godot sibling draw order: higher z_index wins; ties → later child_index on top."""
    return (int(tile.get("z_index", 0)), int(tile.get("child_index", -1)))


def _assert_pointy_top_cross_row_paint_order(by_qr: dict[tuple[int, int], dict]) -> None:
    """Higher axial r must paint above lower r wherever HexTile AABBs overlap.

    Pointy-top rows interpenetrate (~0.25·h) with transparent plains corners; the
    stack must follow geometry (z_index / sibling index), not battle.hexes order.
    Named pair (1,0)/(0,1) is the R3 RED case (unsorted probe places (1,0) late).
    """
    assert (1, 0) in by_qr and (0, 1) in by_qr, (
        f"probe must include inter-row overlap pair (1,0)/(0,1), got {sorted(by_qr)}"
    )
    upper, lower = by_qr[(1, 0)], by_qr[(0, 1)]
    assert _rects_overlap(upper, lower), (
        "pointy-top inter-row pair (1,0)/(0,1) must overlap AABBs so stack "
        f"order is observable; tiles={upper!r} {lower!r}"
    )
    for key in ("z_index", "child_index"):
        assert key in upper and key in lower, (
            f"probe must expose {key} for paint-order checks, "
            f"got keys upper={sorted(upper)} lower={sorted(lower)}"
        )
    assert _canvas_draw_order_key(lower) > _canvas_draw_order_key(upper), (
        "pointy-top: higher-r hex (0,1) must draw above lower-r neighbour (1,0) "
        "in the AABB overlap band (stable geometry paint order via z_index "
        "and/or sibling index, not raw battle.hexes order). "
        f"upper(1,0) key={_canvas_draw_order_key(upper)} tile={upper!r}; "
        f"lower(0,1) key={_canvas_draw_order_key(lower)} tile={lower!r}"
    )
    for i, left_qr in enumerate(by_qr):
        for right_qr in list(by_qr)[i + 1 :]:
            _, lr = left_qr
            _, rr = right_qr
            if lr == rr:
                continue
            a, b = by_qr[left_qr], by_qr[right_qr]
            if not _rects_overlap(a, b):
                continue
            top_qr, bot_qr = (left_qr, right_qr) if lr > rr else (right_qr, left_qr)
            top, bot = by_qr[top_qr], by_qr[bot_qr]
            assert _canvas_draw_order_key(top) > _canvas_draw_order_key(bot), (
                f"cross-row overlap: higher-r {top_qr} must paint above {bot_qr}; "
                f"top_key={_canvas_draw_order_key(top)} bot_key={_canvas_draw_order_key(bot)}; "
                f"tiles={top!r} {bot!r}"
            )


def test_battle_view_shows_one_axial_tile_per_hex_with_side_paint_and_polish_result():
    """BattleView must place one tile per battle hex on axial axes with side paint.

    Geometry detail (native 120×140 plains base, pointy-top packing, no card
    gaps) is owned by G98.1a; this gate keeps count/idempotence, side paint,
    Polish result, and tile/label layout non-clip. Cross-row AABB interpenetration
    is expected under hex packing — do not reintroduce global non-overlap here.

    Realistic defects this catches:
    1) SnapshotModel already exposes battle hexes (G85.1a) but main has no
       BattleView — pure-text assault status stays green while the fight is
       invisible. map_view / snapshot_model_battle / order_result never look
       for BattleView or axial tile geometry.
    2) Fixed BattleResultLabel at y≈136 with axial step 68 and settlement
       rows r∈{0,1,2}: r=2 tiles sit on y=136 and are clipped / covered by
       the result label. A probe limited to r=0,1 stays green while a real
       three-row battle is unreadable.
    """
    payload = _load_battle_view()

    assert payload["battle_view_found"] is True, (
        "main scene must expose BattleView findable from the root by name"
    )
    assert payload["has_render_model"] is True, (
        "BattleView must expose public render_model(model)"
    )

    hexes = payload["hexes"]
    assert isinstance(hexes, list) and len(hexes) >= 2, (
        f"probe must emit the synthetic hexes it used, got {hexes!r}"
    )
    n = len(hexes)
    coords = {(int(h["q"]), int(h["r"])) for h in hexes}
    assert len(coords) == n, f"probe hexes must have unique (q,r), got {hexes!r}"
    rows = {int(h["r"]) for h in hexes}
    assert max(rows) >= 2, (
        "probe must include settlement-like r=2 so result/tile layout is checked, "
        f"got rows {sorted(rows)}"
    )

    first = payload["tiles_after_first"]
    second = payload["tiles_after_second"]
    empty = payload["tiles_after_empty"]
    direct = payload["tiles_after_direct_render"]
    null_render = payload["tiles_after_null_render"]

    assert payload["tile_count_after_first"] == n, payload
    assert payload["tile_count_after_second"] == n, (
        "re-render must not accumulate hex tiles, got count "
        f"{payload['tile_count_after_second']}"
    )
    assert payload["tile_count_after_empty"] == 0, payload
    assert payload["tile_count_after_direct_render"] == n, payload
    assert payload["tile_count_after_null_render"] == 0, payload

    assert len(first) == n, (
        f"exactly one tile per battle hex after apply_model, got {first!r}"
    )
    by_qr = _by_qr(first)
    assert set(by_qr) == coords, first

    for hex_row in hexes:
        tile = by_qr[(int(hex_row["q"]), int(hex_row["r"]))]
        assert tile["visible"] is True, tile
        assert tile["w"] > 0 and tile["h"] > 0, (
            f"hex ({hex_row['q']},{hex_row['r']}) must have non-zero size, got {tile}"
        )
        assert tile["name"] == f"HexTile_{hex_row['q']}_{hex_row['r']}", tile

    # Axial placement (pointy-top compatible): same-r higher q → further right;
    # higher r → further down. Cross-row AABBs may interpenetrate under hex packing,
    # so global non-overlap is intentionally not required here (see G98.1a gate).
    qr_list = list(coords)
    for left in qr_list:
        for right in qr_list:
            if left == right:
                continue
            lq, lr = left
            rq, rr = right
            if rr == lr and rq > lq:
                assert by_qr[right]["x"] > by_qr[left]["x"], (
                    f"same-r q {rq} must sit right of q {lq}: "
                    f"{by_qr[left]} vs {by_qr[right]}"
                )
            if rr > lr:
                assert by_qr[right]["y"] > by_qr[left]["y"], (
                    f"r {rr} must sit below r {lr}: "
                    f"{by_qr[left]} vs {by_qr[right]}"
                )

    # Side is machine-readable via distinct silhouettes (G98.1b removes whole-ground
    # side tint; G87.1c-2 / silhouette gate owns figure paint). Do not require
    # modulate colour keys on the terrain base.
    sides = {h["side"]: (int(h["q"]), int(h["r"])) for h in hexes}
    assert "attacker" in sides and "defender" in sides, hexes
    attacker_paths = set(by_qr[sides["attacker"]].get("texture_paths") or [])
    defender_paths = set(by_qr[sides["defender"]].get("texture_paths") or [])
    assert SIDE_ATTACKER in attacker_paths and SIDE_DEFENDER not in attacker_paths, (
        f"attacker tile must carry attacker silhouette only, paths={attacker_paths!r}"
    )
    assert SIDE_DEFENDER in defender_paths and SIDE_ATTACKER not in defender_paths, (
        f"defender tile must carry defender silhouette only, paths={defender_paths!r}"
    )

    # Idempotent re-render; no-battle and null clear tiles.
    assert len(second) == n, second
    assert set(_by_qr(second)) == coords
    assert empty == [], f"model without battle must clear tiles, got {empty!r}"
    assert null_render == [], (
        f"render_model(null) must clear tiles, got {null_render!r}"
    )
    assert len(direct) == n, direct
    assert set(_by_qr(direct)) == coords

    # Polish result text distinguishes player win / loss / draw (player = attacker).
    assert _polish_mentions_result(
        payload["result_text_attacker_win"], "zwycięstwo", "zwyciestwo"
    ), payload["result_text_attacker_win"]
    assert _polish_mentions_result(
        payload["result_text_defender_win"], "porażka", "porazka"
    ), payload["result_text_defender_win"]
    assert _polish_mentions_result(
        payload["result_text_draw"], "remis"
    ), payload["result_text_draw"]
    # No battle → no leftover Polish outcome claiming a fight result.
    no_battle = payload["result_text_no_battle"]
    assert not _polish_mentions_result(
        no_battle, "zwycięstwo", "zwyciestwo", "porażka", "porazka", "remis"
    ), no_battle

    # Result label + all hex tiles fully inside BattleView; pairwise non-overlapping
    # with the outcome text (r=2 must not sit under a fixed-y result strip).
    view = payload["view_rect"]
    result_rect = payload["result_label_rect"]
    assert isinstance(view, dict) and view["w"] > 0 and view["h"] > 0, view
    assert isinstance(result_rect, dict) and result_rect["w"] > 0 and result_rect["h"] > 0, (
        f"BattleResultLabel must be present with non-zero size after battle render, "
        f"got {result_rect!r}"
    )
    assert _fully_inside(view, result_rect), (
        f"Polish result label must fit fully inside BattleView: "
        f"label={result_rect} view={view}"
    )
    for qr, tile in by_qr.items():
        tile_rect = _rect_of(tile)
        assert _fully_inside(view, tile_rect), (
            f"hex tile {qr} must fit fully inside BattleView (no clip_contents cut): "
            f"tile={tile_rect} view={view}"
        )
        assert not _rects_overlap(tile_rect, result_rect), (
            f"battle result label must not cover hex tile {qr}: "
            f"tile={tile_rect} label={result_rect}"
        )


def _layer_rect(layer: dict) -> dict:
    return {
        "x": float(layer.get("x", 0.0)),
        "y": float(layer.get("y", 0.0)),
        "w": float(layer["w"]),
        "h": float(layer["h"]),
    }


def _modulate_is_neutral(mod: object, *, tol: float = 0.02) -> bool:
    """True when modulate is identity white (no side tint on the ground)."""
    if not isinstance(mod, (list, tuple)) or len(mod) < 3:
        return False
    r, g, b = float(mod[0]), float(mod[1]), float(mod[2])
    a = float(mod[3]) if len(mod) > 3 else 1.0
    return (
        abs(r - 1.0) <= tol
        and abs(g - 1.0) <= tol
        and abs(b - 1.0) <= tol
        and abs(a - 1.0) <= tol
    )


def _assert_native_decoration(layer: dict, tile: dict, *, terrain: str, qr: tuple) -> None:
    """G98.1b: decoration keeps audited PNG proportions and stays inside the hex."""
    native_w, native_h = DECORATION_NATIVE[terrain]
    lw, lh = float(layer["w"]), float(layer["h"])
    assert lw > 0 and lh > 0, f"hex {qr} {terrain} decoration must have size, {layer!r}"
    # Must not be stretched to the shared hex body (full-rect 120×140).
    assert not layer_fills_tile(layer, tile), (
        f"hex {qr} terrain={terrain!r} decoration must not fill the hex bounds "
        f"(tree/rock is not a stretched ground tile), layer={layer!r} "
        f"tile_w={tile['w']} tile_h={tile['h']}"
    )
    assert lw < float(tile["w"]) and lh < float(tile["h"]), (
        f"hex {qr} terrain={terrain!r} decoration must be smaller than the hex "
        f"in both axes, layer={layer!r} tile={tile!r}"
    )
    # Proportions of the audited PNG (scale may differ; aspect must match).
    expected_aspect = native_w / native_h
    actual_aspect = lw / lh
    assert abs(actual_aspect - expected_aspect) <= 0.05, (
        f"hex {qr} terrain={terrain!r} decoration must keep native aspect "
        f"{native_w}×{native_h} (ratio {expected_aspect:.4f}), "
        f"got {lw}×{lh} (ratio {actual_aspect:.4f}), layer={layer!r}"
    )
    # Prefer near-native control size so small art stays readable; allow ≤1px tol.
    assert abs(lw - native_w) <= _LAYOUT_TOL_PX, (
        f"hex {qr} terrain={terrain!r} decoration width should match native "
        f"{native_w}px (not scaled to hex), got w={lw}, layer={layer!r}"
    )
    assert abs(lh - native_h) <= _LAYOUT_TOL_PX, (
        f"hex {qr} terrain={terrain!r} decoration height should match native "
        f"{native_h}px (not scaled to hex), got h={lh}, layer={layer!r}"
    )
    # STRETCH_SCALE on a decoration control would distort even if size were fixed.
    stretch = layer.get("stretch_mode")
    if stretch is not None and int(stretch) >= 0:
        assert int(stretch) != _STRETCH_SCALE, (
            f"hex {qr} terrain={terrain!r} decoration must not use STRETCH_SCALE "
            f"(distorts tree/rock), stretch_mode={stretch}, layer={layer!r}"
        )
    assert layer.get("mouse_filter") == MOUSE_FILTER_IGNORE, (
        f"hex {qr} terrain={terrain!r} decoration must not capture mouse, "
        f"layer={layer!r}"
    )
    # Anchored inside the shared hex AABB (readable, not clipped outside).
    if "x" in layer and "y" in layer:
        assert _fully_inside(_rect_of(tile), _layer_rect(layer)), (
            f"hex {qr} terrain={terrain!r} decoration must sit inside the hex, "
            f"layer={layer!r} tile={tile!r}"
        )


def test_battle_view_hex_tiles_carry_terrain_textures_from_assets():
    """G98.1b: shared plains base + unstretched Forest/Hills decorations.

    Realistic defect existing gates miss: BattleView already paints a shared
    plains body (G98.1a geometry green) and still includes Forest/Hills asset
    paths, but stretches those PNGs with ``TileTextureLayer.full_rect`` to the
    120×140 hex, tints the whole base with side colour, and overlays English
    ``Plains``/``Forest``/``Hills`` Labels. The old R87.1 full-rect ground rule
    greened that defect. Missing PNGs must still fail at the disk gate.
    Unknown / empty / missing terrain must still paint the plains base only.
    """
    assets_dir = GAME / "assets"
    for asset_name in (
        "terrain_plains.png",
        "terrain_forest.png",
        "terrain_hills.png",
    ):
        asset_path = assets_dir / asset_name
        assert asset_path.is_file(), (
            f"required battle terrain asset missing on disk: {asset_path} "
            "(missing file must red-gate, not paint an empty color tile)"
        )
        _assert_credits_table_row(asset_name)

    imported = _import_game_assets()
    assert imported.returncode == 0, (
        f"godot --import failed rc={imported.returncode} "
        f"stderr={imported.stderr!r} stdout={imported.stdout!r}"
    )

    payload = _load_battle_view()
    assert payload["battle_view_found"] is True, payload
    assert payload["has_render_model"] is True, payload

    hexes = payload["hexes"]
    terrains = {str(h.get("terrain", "")) for h in hexes}
    assert terrains >= set(TERRAIN_ASSETS), (
        f"probe must include Plains/Forest/Hills hexes for texture mapping, "
        f"got terrains {sorted(terrains)}"
    )

    first = payload["tiles_after_first"]
    assert len(first) == len(hexes), first
    by_qr = _by_qr(first)

    for hex_row in hexes:
        qr = (int(hex_row["q"]), int(hex_row["r"]))
        tile = by_qr[qr]
        terrain = str(hex_row["terrain"])
        paths = list(tile.get("texture_paths") or [])
        assert tile["has_texture"] is True, (
            f"hex {qr} terrain={terrain!r} must carry Texture2D from assets, "
            f"got {tile!r}"
        )
        assert paths, tile
        for path in paths:
            assert isinstance(path, str) and path.startswith("res://assets/"), (
                f"hex {qr} texture must come from res://assets/, got {path!r} "
                f"in {tile!r}"
            )
        assert tile.get("tile_mouse_filter") == MOUSE_FILTER_IGNORE, (
            f"hex {qr} root must ignore mouse, got {tile!r}"
        )

        # Shared plains base fills the hex; never side-tinted as whole ground.
        assert PLAINS_ASSET in paths, (
            f"hex {qr} terrain={terrain!r} must paint shared base {PLAINS_ASSET}, "
            f"got paths={paths!r}"
        )
        base_layers = _terrain_layers(tile, PLAINS_ASSET)
        assert base_layers, (
            f"hex {qr} must expose a sized plains base layer, got {tile!r}"
        )
        for layer in base_layers:
            assert layer_fills_tile(layer, tile), (
                f"hex {qr} plains base must fill the hex bounds undistorted "
                f"(120×140), layer={layer!r} tile_w={tile['w']} tile_h={tile['h']}"
            )
            assert layer.get("mouse_filter") == MOUSE_FILTER_IGNORE, (
                f"hex {qr} plains base must not capture mouse, got layer={layer!r}"
            )
            assert "modulate" in layer, (
                f"hex {qr} plains base probe must expose modulate for side-tint "
                f"checks (G98.1b), layer={layer!r}"
            )
            assert _modulate_is_neutral(layer["modulate"]), (
                f"hex {qr} plains base must not carry side-colour tint on the "
                f"whole ground (G98.1b), modulate={layer.get('modulate')!r}, "
                f"layer={layer!r}"
            )

        # Role mapping: Plains = base only; Forest/Hills overlay native decoration.
        forest_layers = _terrain_layers(tile, FOREST_ASSET)
        hills_layers = _terrain_layers(tile, HILLS_ASSET)
        if terrain == "Plains":
            assert FOREST_ASSET not in paths and HILLS_ASSET not in paths, (
                f"hex {qr} Plains must leave only the base (no tree/rock overlay), "
                f"got paths={paths!r}"
            )
            assert forest_layers == [] and hills_layers == [], (
                f"hex {qr} Plains must not report decoration layers, "
                f"forest={forest_layers!r} hills={hills_layers!r}"
            )
        elif terrain == "Forest":
            assert FOREST_ASSET in paths, (
                f"hex {qr} Forest must include {FOREST_ASSET}, got paths={paths!r}"
            )
            assert HILLS_ASSET not in paths, (
                f"hex {qr} Forest must not also paint Hills rock, paths={paths!r}"
            )
            assert forest_layers, (
                f"hex {qr} Forest must expose a sized tree decoration layer, "
                f"got {tile!r}"
            )
            assert paths.index(PLAINS_ASSET) < paths.index(FOREST_ASSET), (
                f"hex {qr} Forest must draw tree over plains base "
                f"(base path before decoration in tree order), paths={paths!r}"
            )
            for layer in forest_layers:
                _assert_native_decoration(layer, tile, terrain="Forest", qr=qr)
        elif terrain == "Hills":
            assert HILLS_ASSET in paths, (
                f"hex {qr} Hills must include {HILLS_ASSET}, got paths={paths!r}"
            )
            assert FOREST_ASSET not in paths, (
                f"hex {qr} Hills must not also paint Forest tree, paths={paths!r}"
            )
            assert hills_layers, (
                f"hex {qr} Hills must expose a sized rock decoration layer, "
                f"got {tile!r}"
            )
            assert paths.index(PLAINS_ASSET) < paths.index(HILLS_ASSET), (
                f"hex {qr} Hills must draw rock over plains base "
                f"(base path before decoration in tree order), paths={paths!r}"
            )
            for layer in hills_layers:
                _assert_native_decoration(layer, tile, terrain="Hills", qr=qr)
        else:
            # Named terrains outside the three roles still keep the base only.
            assert FOREST_ASSET not in paths and HILLS_ASSET not in paths, (
                f"hex {qr} terrain={terrain!r} must not invent decorations, "
                f"paths={paths!r}"
            )

        # English terrain names must not sit on the hex face.
        surface_labels = [
            str(t).strip() for t in (tile.get("surface_labels") or []) if str(t).strip()
        ]
        for label in surface_labels:
            assert label not in _ENGLISH_TERRAIN_LABELS, (
                f"hex {qr} must not show English terrain label {label!r} on the "
                f"tile surface (G98.1b), labels={surface_labels!r}"
            )

    # Three core terrains remain three distinct mapped images (roles differ).
    path_sets = {
        name: {
            p
            for t in first
            if t.get("terrain") == name
            for p in t["texture_paths"]
            if p == TERRAIN_ASSETS[name]
        }
        for name in TERRAIN_ASSETS
    }
    assert len({frozenset(s) for s in path_sets.values()}) == 3, (
        f"Plains/Forest/Hills must map to three distinct terrain textures, "
        f"got {path_sets!r}"
    )

    # Fallback: unknown, empty string, and missing terrain key still paint tiles
    # with the default plains base only — no drop, no script error, no empty color.
    default_path = PLAINS_ASSET
    fallback_hexes = payload["hexes_fallback"]
    fallback_tiles = payload["tiles_after_fallback"]
    assert len(fallback_hexes) >= 3, fallback_hexes
    assert len(fallback_tiles) == len(fallback_hexes), (
        f"fallback hexes must each produce a tile (no drop on bad terrain): "
        f"hexes={fallback_hexes!r} tiles={fallback_tiles!r}"
    )
    for tile in fallback_tiles:
        assert tile["has_texture"] is True, (
            f"fallback hex ({tile['q']},{tile['r']}) must still carry a default "
            f"Texture2D from assets, got {tile!r}"
        )
        assert tile["texture_paths"], tile
        for path in tile["texture_paths"]:
            assert isinstance(path, str) and path.startswith("res://assets/"), (
                f"fallback texture must come from res://assets/, got {path!r}"
            )
        assert default_path in tile["texture_paths"], (
            f"fallback hex ({tile['q']},{tile['r']}) must use default {default_path}, "
            f"got paths={tile['texture_paths']!r}"
        )
        assert FOREST_ASSET not in tile["texture_paths"], (
            f"fallback hex ({tile['q']},{tile['r']}) must not invent Forest art, "
            f"paths={tile['texture_paths']!r}"
        )
        assert HILLS_ASSET not in tile["texture_paths"], (
            f"fallback hex ({tile['q']},{tile['r']}) must not invent Hills art, "
            f"paths={tile['texture_paths']!r}"
        )


def _side_layers(tile: dict) -> list[dict]:
    """Texture layers whose path is a public battle-side silhouette asset."""
    layers = tile.get("texture_layers") or []
    return [
        layer
        for layer in layers
        if isinstance(layer, dict) and layer.get("path") in SIDE_ASSETS
    ]


def test_battle_view_hex_tiles_overlay_side_silhouettes_on_terrain():
    """Occupied battle hexes must show side unit silhouettes on top of terrain.

    Realistic defect existing gates miss: BattleView still paints side only via
    terrain ``modulate`` (K85 visual keys + G87.1c-1 terrain paths stay green)
    while the player never sees a unit figure. Asset gates only prove the PNGs
    load on disk — they never require BattleView to place them. Unknown / empty
    side must keep terrain and omit both side assets without error.
    """
    assets_dir = GAME / "assets"
    for asset_name in ("side_attacker.png", "side_defender.png"):
        asset_path = assets_dir / asset_name
        assert asset_path.is_file(), (
            f"required side silhouette asset missing on disk: {asset_path} "
            "(missing file must red-gate, not paint a color-only tile)"
        )

    imported = _import_game_assets()
    assert imported.returncode == 0, (
        f"godot --import failed rc={imported.returncode} "
        f"stderr={imported.stderr!r} stdout={imported.stdout!r}"
    )

    payload = _load_battle_view()
    assert payload["battle_view_found"] is True, payload
    assert payload["has_render_model"] is True, payload

    hexes = payload["hexes"]
    first = payload["tiles_after_first"]
    assert len(first) == len(hexes), first
    by_qr = _by_qr(first)

    expected_side_path = {
        "attacker": SIDE_ATTACKER,
        "defender": SIDE_DEFENDER,
    }
    sides_seen = {str(h.get("side", "")) for h in hexes}
    assert "attacker" in sides_seen and "defender" in sides_seen, hexes
    assert any(s not in ("attacker", "defender") for s in sides_seen), (
        f"probe must include a non-attacker/defender side for no-silhouette "
        f"coverage, got sides {sorted(sides_seen)}"
    )

    for hex_row in hexes:
        qr = (int(hex_row["q"]), int(hex_row["r"]))
        tile = by_qr[qr]
        side = str(hex_row.get("side", ""))
        terrain = str(hex_row.get("terrain", ""))
        paths = list(tile.get("texture_paths") or [])
        layers = list(tile.get("texture_layers") or [])
        assert tile["has_texture"] is True, tile
        assert layers, f"hex {qr} must report texture_layers for size checks, got {tile!r}"

        # Terrain under the unit remains (G87.1c-1 choice unchanged).
        if terrain in TERRAIN_ASSETS:
            assert TERRAIN_ASSETS[terrain] in paths, (
                f"hex {qr} side={side!r} must keep terrain {TERRAIN_ASSETS[terrain]}, "
                f"got paths={paths!r}"
            )

        side_layers = _side_layers(tile)
        if side in expected_side_path:
            wanted = expected_side_path[side]
            assert wanted in paths, (
                f"hex {qr} side={side!r} must overlay {wanted} on terrain, "
                f"got paths={paths!r}"
            )
            assert len(side_layers) >= 1, (
                f"hex {qr} side={side!r} must expose a sized side layer, got {tile!r}"
            )
            # Tree order (DFS children): terrain must come before side so a
            # silhouette painted *under* ground cannot green-gate as "overlay".
            if terrain in TERRAIN_ASSETS:
                terrain_path = TERRAIN_ASSETS[terrain]
                assert paths.index(terrain_path) < paths.index(wanted), (
                    f"hex {qr} side={side!r} must draw silhouette over terrain "
                    f"(terrain path before side path in tree order), got paths={paths!r}"
                )
            for layer in side_layers:
                assert layer["path"] == wanted, (
                    f"hex {qr} side={side!r} must not carry the other side's "
                    f"silhouette, got layer={layer!r}"
                )
                # Silhouette smaller than the hex tile so terrain stays readable.
                assert float(layer["w"]) < float(tile["w"]), (
                    f"hex {qr} side silhouette must be narrower than the tile: "
                    f"layer_w={layer['w']} tile_w={tile['w']} layer={layer!r}"
                )
                assert float(layer["h"]) < float(tile["h"]), (
                    f"hex {qr} side silhouette must be shorter than the tile: "
                    f"layer_h={layer['h']} tile_h={tile['h']} layer={layer!r}"
                )
                assert layer.get("mouse_filter") == MOUSE_FILTER_IGNORE, (
                    f"hex {qr} side silhouette must not capture mouse, "
                    f"got layer={layer!r}"
                )
            other = SIDE_DEFENDER if side == "attacker" else SIDE_ATTACKER
            assert other not in paths, (
                f"hex {qr} side={side!r} must not also show {other}, paths={paths!r}"
            )
        else:
            for side_path in SIDE_ASSETS:
                assert side_path not in paths, (
                    f"hex {qr} side={side!r} must be terrain-only (no silhouette), "
                    f"but paths include {side_path}: {paths!r}"
                )
            assert side_layers == [], (
                f"hex {qr} side={side!r} must not report side layers, got {side_layers!r}"
            )

    # Sides remain machine-distinguishable by different silhouette files.
    attacker_qr = next(
        (int(h["q"]), int(h["r"])) for h in hexes if h.get("side") == "attacker"
    )
    defender_qr = next(
        (int(h["q"]), int(h["r"])) for h in hexes if h.get("side") == "defender"
    )
    attacker_side_paths = {layer["path"] for layer in _side_layers(by_qr[attacker_qr])}
    defender_side_paths = {layer["path"] for layer in _side_layers(by_qr[defender_qr])}
    assert attacker_side_paths == {SIDE_ATTACKER}, attacker_side_paths
    assert defender_side_paths == {SIDE_DEFENDER}, defender_side_paths
    assert attacker_side_paths != defender_side_paths, (
        f"attacker and defender must use different silhouette files: "
        f"{attacker_side_paths!r} vs {defender_side_paths!r}"
    )


def test_battle_view_base_hexes_form_pointy_top_axial_grid_from_plains_asset():
    """G98.1a: every occupied hex uses an undistorted plains base on a pointy-top lattice.

    Realistic defects existing gates miss:
    1) BattleView still lays HexTile_* as a rectangular card grid (TILE_SIZE
       96×56 + TILE_GAP) and lets Forest/Hills ground textures act as the hex
       body. The older axial gate only checks same-axis order and side paint,
       so a gapped rectangle table stays green while rows never offset, bases
       never share terrain_plains.png 120×140, and ``terrain`` still changes
       the painted hex footprint.
    2) Pointy-top AABBs interpenetrate (~0.25·h) and plains has transparent
       corners; painting HexTile_* in raw ``battle.hexes`` array order (or any
       non-geometry order) leaves a lower-r tile as a later sibling so it
       covers the overlap band of a higher-r neighbour — wrong stack order.
       Offset/size checks stay green while AC "bez wzajemnego przykrywania w
       złej kolejności" fails. Probe hexes are intentionally not (q,r)-sorted.
    """
    plains_disk = GAME / "assets" / "terrain_plains.png"
    assert plains_disk.is_file(), (
        f"base hex asset missing on disk: {plains_disk} "
        "(G98.1a requires terrain_plains.png as the shared hex body)"
    )
    _assert_credits_table_row("terrain_plains.png")

    imported = _import_game_assets()
    assert imported.returncode == 0, (
        f"godot --import failed rc={imported.returncode} "
        f"stderr={imported.stderr!r} stdout={imported.stdout!r}"
    )

    payload = _load_battle_view()
    assert payload["battle_view_found"] is True, payload
    assert payload["has_render_model"] is True, payload

    hexes = payload["hexes"]
    assert isinstance(hexes, list) and len(hexes) >= 3, hexes
    coords = {(int(h["q"]), int(h["r"])) for h in hexes}
    rows = {int(h["r"]) for h in hexes}
    assert max(rows) - min(rows) >= 2, (
        "probe must span at least three axial rows so pointy-top packing is "
        f"observable, got rows {sorted(rows)}"
    )
    terrains = {str(h.get("terrain", "")) for h in hexes}
    assert "Plains" in terrains, f"probe must include Plains, got {sorted(terrains)}"
    non_plains = terrains - {"Plains", ""}
    assert non_plains, (
        "probe must include non-Plains terrain so base size is independent of "
        f"terrain, got {sorted(terrains)}"
    )

    first = payload["tiles_after_first"]
    assert len(first) == len(hexes), first
    by_qr = _by_qr(first)
    assert set(by_qr) == coords, first

    # Shared base size = native terrain_plains.png, independent of terrain.
    for hex_row in hexes:
        qr = (int(hex_row["q"]), int(hex_row["r"]))
        tile = by_qr[qr]
        terrain = str(hex_row.get("terrain", ""))
        assert abs(float(tile["w"]) - BASE_HEX_W) <= _LAYOUT_TOL_PX, (
            f"hex {qr} terrain={terrain!r} base width must be {BASE_HEX_W}px "
            f"(terrain_plains native), got w={tile['w']}"
        )
        assert abs(float(tile["h"]) - BASE_HEX_H) <= _LAYOUT_TOL_PX, (
            f"hex {qr} terrain={terrain!r} base height must be {BASE_HEX_H}px "
            f"(terrain_plains native), got h={tile['h']}"
        )
        paths = list(tile.get("texture_paths") or [])
        assert PLAINS_ASSET in paths, (
            f"hex {qr} terrain={terrain!r} must paint {PLAINS_ASSET} as the "
            f"shared base body, got paths={paths!r}"
        )
        base_layers = _terrain_layers(tile, PLAINS_ASSET)
        assert base_layers, (
            f"hex {qr} must expose a sized plains base layer, got {tile!r}"
        )
        for layer in base_layers:
            assert layer_fills_tile(layer, tile), (
                f"hex {qr} plains base must fill the hex bounds undistorted "
                f"(120×140), layer={layer!r} tile={tile!r}"
            )
            assert layer.get("mouse_filter") == MOUSE_FILTER_IGNORE, (
                f"hex {qr} plains base must not capture mouse, layer={layer!r}"
            )

    sizes = {(round(float(t["w"]), 1), round(float(t["h"]), 1)) for t in first}
    assert len(sizes) == 1, (
        f"all base hexes must share one size regardless of terrain, got {sizes!r}"
    )

    # Pointy-top axial packing: same-q row step offsets by ~half width and
    # vertical pitch is strictly less than tile height (hex AABBs interpenetrate).
    assert (0, 0) in by_qr and (0, 1) in by_qr, (
        f"probe must include (0,0) and (0,1) for row packing, got {sorted(by_qr)}"
    )
    origin, down = by_qr[(0, 0)], by_qr[(0, 1)]
    tile_w = float(origin["w"])
    tile_h = float(origin["h"])
    row_dx = float(down["x"]) - float(origin["x"])
    row_dy = float(down["y"]) - float(origin["y"])
    assert abs(abs(row_dx) - tile_w * 0.5) <= _LAYOUT_TOL_PX, (
        f"pointy-top: same-q next row must offset by ~half tile width "
        f"((0,0)→(0,1) dx={row_dx}, expect ±{tile_w * 0.5}); "
        f"rectangular pitch leaves dx=0. tiles={origin!r} {down!r}"
    )
    # Pointy-top axial row pitch is 0.75·h (shared vertical edge), not a loose
    # band [0.5·h, h): dy≈0.55·h would leave a visible gap between hex edges.
    expected_row_pitch = tile_h * 0.75
    assert abs(row_dy - expected_row_pitch) <= _LAYOUT_TOL_PX, (
        f"pointy-top: vertical pitch must be ~0.75·tile_h "
        f"(dy={row_dy}, expect {expected_row_pitch}±{_LAYOUT_TOL_PX}, "
        f"tile_h={tile_h}); rectangular packing uses dy≥tile_h; sparse "
        f"non-touching rows use dy much below 0.75·h. "
        f"tiles={origin!r} {down!r}"
    )

    # Same-row neighbours touch horizontally (no card gap), without AABB overlap.
    assert (1, 0) in by_qr, f"probe must include (1,0) for horizontal pitch, got {sorted(by_qr)}"
    right = by_qr[(1, 0)]
    gap_x = _gap_between_axis_aligned(origin, right, axis="x")
    assert gap_x <= _LAYOUT_TOL_PX, (
        f"same-row axial neighbours (0,0) and (1,0) must touch (no rectangular "
        f"gap): gap={gap_x}px tiles={origin!r} {right!r}"
    )
    assert not _rects_overlap(origin, right), (
        f"same-row neighbours must not overlap AABBs: {origin!r} vs {right!r}"
    )
    pitch_x = float(right["x"]) - float(origin["x"])
    assert abs(pitch_x - tile_w) <= _LAYOUT_TOL_PX, (
        f"same-row pitch must equal base width (pointy-top flat-to-flat): "
        f"pitch_x={pitch_x}, tile_w={tile_w}; tiles={origin!r} {right!r}"
    )

    # Only snapshot hexes are drawn — no phantom HexTile_* beyond battle.hexes.
    assert int(payload["tile_count_after_first"]) == len(hexes), (
        "BattleView must draw exactly the hexes present in battle.hexes, "
        f"count={payload['tile_count_after_first']} hexes={len(hexes)}"
    )

    # Inter-row overlap stack independent of battle.hexes array order.
    _assert_pointy_top_cross_row_paint_order(by_qr)

