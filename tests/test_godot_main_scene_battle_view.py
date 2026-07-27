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


def _fully_inside(outer: dict, inner: dict) -> bool:
    """True if inner's closed rectangle lies entirely within outer (edges may touch)."""
    return (
        inner["x"] >= outer["x"]
        and inner["y"] >= outer["y"]
        and inner["x"] + inner["w"] <= outer["x"] + outer["w"]
        and inner["y"] + inner["h"] <= outer["y"] + outer["h"]
    )


def test_battle_view_shows_one_axial_tile_per_hex_with_side_paint_and_polish_result():
    """BattleView must place one non-overlapping tile per battle hex on axial axes.

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

    # Axial placement: higher q → further right; higher r → further down.
    qr_list = list(coords)
    for left in qr_list:
        for right in qr_list:
            if left == right:
                continue
            lq, lr = left
            rq, rr = right
            if rq > lq:
                assert by_qr[right]["x"] > by_qr[left]["x"], (
                    f"q {rq} must sit right of q {lq}: "
                    f"{by_qr[left]} vs {by_qr[right]}"
                )
            if rr > lr:
                assert by_qr[right]["y"] > by_qr[left]["y"], (
                    f"r {rr} must sit below r {lr}: "
                    f"{by_qr[left]} vs {by_qr[right]}"
                )

    for i, left in enumerate(qr_list):
        for right in qr_list[i + 1 :]:
            assert not _rects_overlap(by_qr[left], by_qr[right]), (
                f"hex tiles must not overlap: {left}={by_qr[left]} "
                f"vs {right}={by_qr[right]}"
            )

    # Side is machine-readable paint, not only label text.
    sides = {h["side"]: (int(h["q"]), int(h["r"])) for h in hexes}
    assert "attacker" in sides and "defender" in sides, hexes
    attacker_v = by_qr[sides["attacker"]]["visual"]
    defender_v = by_qr[sides["defender"]]["visual"]
    assert attacker_v != defender_v, (
        f"attacker and defender tiles must differ visually: "
        f"{attacker_v!r} vs {defender_v!r}"
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


def test_battle_view_hex_tiles_carry_terrain_textures_from_assets():
    """Each battle hex tile must show terrain Texture2D from game/assets/.

    Realistic defect this catches: BattleView still paints solid ColorRect tiles
    with a terrain name Label (K85 geometry / side-color / Polish-result gates
    stay green) while the player never sees Plains/Forest/Hills art. Missing
    terrain PNGs must fail at the disk gate, not yield a silent color tile.
    Unknown / empty / missing terrain must still paint a default asset tile.
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
        assert tile["has_texture"] is True, (
            f"hex {qr} terrain={terrain!r} must carry Texture2D from assets, "
            f"got {tile!r}"
        )
        assert tile["texture_paths"], tile
        for path in tile["texture_paths"]:
            assert isinstance(path, str) and path.startswith("res://assets/"), (
                f"hex {qr} texture must come from res://assets/, got {path!r} "
                f"in {tile!r}"
            )
        expected = TERRAIN_ASSETS[terrain]
        assert expected in tile["texture_paths"], (
            f"hex {qr} terrain={terrain!r} must include {expected}, "
            f"got paths={tile['texture_paths']!r}"
        )
        # R87.1: ground terrain layer fills hex bounds and does not capture mouse.
        # Size check is PRESET_FULL_RECT (control extents via global rect), not
        # TextureRect.stretch_mode — FULL_RECT + STRETCH_KEEP would still pass.
        # Also guards MOUSE_FILTER_IGNORE so terrain does not steal battle clicks.
        assert tile.get("tile_mouse_filter") == MOUSE_FILTER_IGNORE, (
            f"hex {qr} root must ignore mouse, got {tile!r}"
        )
        ground_layers = _terrain_layers(tile, expected)
        assert ground_layers, (
            f"hex {qr} must report sized terrain layer for {expected}, got {tile!r}"
        )
        for layer in ground_layers:
            assert layer_fills_tile(layer, tile), (
                f"hex {qr} terrain layer must fill the tile bounds (FULL_RECT size), "
                f"layer={layer!r} tile_w={tile['w']} tile_h={tile['h']}"
            )
            assert layer.get("mouse_filter") == MOUSE_FILTER_IGNORE, (
                f"hex {qr} terrain layer must not capture mouse, got layer={layer!r}"
            )

    # Three core terrains must be three different images (not one shared fill).
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
    # with the default asset (Plains) — no drop, no script error, no empty color.
    default_path = TERRAIN_ASSETS["Plains"]
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

