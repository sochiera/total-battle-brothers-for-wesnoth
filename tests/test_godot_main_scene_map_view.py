"""MapView contract: one visible tile per region, grid placement, owner paint."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from godot_runner import run_godot_script
from godot_tile_layer import MOUSE_FILTER_IGNORE, layer_fills_tile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PREFIX = "MAP_VIEW "


def _import_game_assets() -> subprocess.CompletedProcess[str]:
    """Headless import so res://assets/*.png resolve to Texture2D."""
    return subprocess.run(
        ["godot", "--headless", "--path", str(GAME), "--import"],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def _load_map_view() -> dict:
    result = run_godot_script(GAME, "res://tests/map_view_probe.gd", timeout=30)
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def _by_name(tiles: list[dict]) -> dict[str, dict]:
    return {tile["name"]: tile for tile in tiles}


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


def _body_texture_layers(tile: dict) -> list[dict]:
    """Tile-fill layers (ground/settlement), excluding the party corner mark."""
    layers = tile.get("texture_layers") or []
    return [
        layer
        for layer in layers
        if isinstance(layer, dict) and str(layer.get("name", "")) != "PlayerPartyMarker"
    ]


def _gap_between_axis_aligned(a: dict, b: dict, *, axis: str) -> float:
    """Non-negative gap between two AABBs along one axis ('x'/'w' or 'y'/'h').

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


# Shared layout float/snapping tolerance (neighbour gap, panel bounds, hex
# pitch). Label content width/height use a strict fit (no extra slack).
_LAYOUT_TOL_PX = 1.0


def _tile_inside_panel(
    tile: dict, panel: dict, *, tol: float = _LAYOUT_TOL_PX
) -> bool:
    """True when the tile's global rect lies fully inside the panel rect."""
    return (
        float(tile["x"]) >= float(panel["x"]) - tol
        and float(tile["y"]) >= float(panel["y"]) - tol
        and float(tile["x"]) + float(tile["w"])
        <= float(panel["x"]) + float(panel["w"]) + tol
        and float(tile["y"]) + float(tile["h"])
        <= float(panel["y"]) + float(panel["h"]) + tol
    )


def test_map_view_shows_one_grid_tile_per_region_with_owner_paint():
    """MapView must place one non-overlapping tile per region on the grid.

    Realistic defect this catches: the main scene still presents the map only as
    RegionList names — no MapView, no tiles, no ownership paint. Existing bind /
    layout / snapshot gates never look for MapView or tile geometry, so a pure
    list UI stays green while the player cannot play by looking.
    """
    payload = _load_map_view()

    assert payload["map_view_found"] is True, (
        "main scene must expose MapView findable from the root by name"
    )
    assert payload["has_render_model"] is True, (
        "MapView must expose public render_model(model)"
    )

    # Regions come from the probe payload — no hand-synced copy in Python.
    regions = payload["regions"]
    assert isinstance(regions, list) and len(regions) >= 3, (
        f"probe must emit the synthetic regions it used, got {regions!r}"
    )
    region_names = {r["name"] for r in regions}
    n = len(regions)

    first = payload["tiles_after_first"]
    second = payload["tiles_after_second"]
    empty = payload["tiles_after_empty"]
    direct = payload["tiles_after_direct_render"]

    # Absolute MapView child counts (not just first-label-per-name).
    assert payload["tile_count_after_first"] == n, payload
    assert payload["tile_count_after_second"] == n, (
        f"re-render must not accumulate tiles, got count "
        f"{payload['tile_count_after_second']}"
    )
    assert payload["tile_count_after_empty"] == 0, payload
    assert payload["tile_count_after_direct_render"] == n, payload

    assert len(first) == n, (
        f"exactly one tile per region after apply_model, got {first!r}"
    )
    assert {t["name"] for t in first} == region_names

    by_name = _by_name(first)
    by_region = {r["name"]: r for r in regions}
    for region in regions:
        tile = by_name[region["name"]]
        assert tile["visible"] is True, tile
        assert tile["w"] > 0 and tile["h"] > 0, (
            f"tile {region['name']} must have non-zero size, got {tile}"
        )

    # Grid: higher col → further right; higher row → further down (from coords).
    names = [r["name"] for r in regions]
    for left in names:
        for right in names:
            if left == right:
                continue
            lc, lr = by_region[left]["col"], by_region[left]["row"]
            rc, rr = by_region[right]["col"], by_region[right]["row"]
            if rc > lc:
                assert by_name[right]["x"] > by_name[left]["x"], (
                    f"col {rc} must sit right of col {lc}: "
                    f"{by_name[left]} vs {by_name[right]}"
                )
            if rr > lr:
                assert by_name[right]["y"] > by_name[left]["y"], (
                    f"row {rr} must sit below row {lr}: "
                    f"{by_name[left]} vs {by_name[right]}"
                )

    # Same-row AABBs must not stack (horizontal pitch = tile width). Cross-row
    # pairs may interpenetrate under pointy-top hex packing (odd-row half-width
    # offset + vertical pitch < tile height); still require a real vertical step
    # so almost-stacked rows (dy≈1px) stay red.
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            la, ra = by_name[left], by_name[right]
            if int(by_region[left]["row"]) == int(by_region[right]["row"]):
                assert not _rects_overlap(la, ra), (
                    f"same-row tiles must not overlap: {left}={la} "
                    f"vs {right}={ra}"
                )
            else:
                dy = abs(float(la["y"]) - float(ra["y"]))
                min_h = min(float(la["h"]), float(ra["h"]))
                assert dy >= min_h * 0.5, (
                    f"cross-row tiles must keep vertical pitch ≥ half tile "
                    f"height (pointy-top offset, e.g. Alpha–Gamma): "
                    f"dy={dy} min_h={min_h} {left}={la} vs {right}={ra}"
                )

    # Ownership is visible without reading names: pairwise different paint keys.
    owners = {r.get("owner"): r["name"] for r in regions}
    assert "player" in owners and "ai" in owners and None in owners, (
        f"probe regions must include player, null, and ai owners, got {regions!r}"
    )
    player_v = by_name[owners["player"]]["visual"]
    neutral_v = by_name[owners[None]]["visual"]
    ai_v = by_name[owners["ai"]]["visual"]
    assert player_v != neutral_v, (
        f"player and unowned tiles must differ visually: {player_v!r}"
    )
    assert player_v != ai_v, (
        f"player and AI tiles must differ visually: {player_v!r} vs {ai_v!r}"
    )
    assert neutral_v != ai_v, (
        f"unowned and AI tiles must differ visually: {neutral_v!r} vs {ai_v!r}"
    )

    # Re-render is idempotent (no tile accumulation); empty model clears tiles.
    assert len(second) == n, second
    assert {t["name"] for t in second} == region_names
    assert empty == [], f"empty regions must leave MapView without tiles, got {empty!r}"

    # Direct public API matches apply_model path.
    assert len(direct) == n, direct
    assert {t["name"] for t in direct} == region_names


def _assert_party_mark(
    sample: dict,
    *,
    marked: list[str],
    marker_count: int,
    label_contains: str | None = None,
) -> None:
    """One place for party-mark contract: exclusive tiles + optional label sync."""
    assert sample["marked_regions"] == marked, sample
    assert sample["marker_count"] == marker_count, sample
    if label_contains is not None:
        assert label_contains in sample["position_label"], sample


def test_map_view_marks_only_the_tile_of_player_party_region():
    """Player party tile mark must follow SnapshotModel.player_party_region.

    Realistic defect this catches: MapView paints ownership only and ignores
    player_party_region, so the army is visible solely as PlayerPartyPositionLabel
    text. Existing map_view / party_position gates never look for a map mark, so
    a pure-list-or-ownership map stays green while the player cannot see which
    tile holds their party after muster/march.
    """
    payload = _load_map_view()
    assert payload["map_view_found"] is True, payload
    assert payload["has_render_model"] is True, payload

    regions = payload["regions"]
    names = {r["name"] for r in regions}
    assert names >= {"Alpha", "Beta", "Gamma"}, regions

    on_alpha = payload["party_on_alpha"]
    absent = payload["party_absent"]
    on_beta = payload["party_on_beta"]
    direct_gamma = payload["party_direct_gamma"]

    # Only the party region tile is marked; never multiple marks; label agrees.
    _assert_party_mark(
        on_alpha, marked=["Alpha"], marker_count=1, label_contains="Alpha"
    )

    # No party → no marks; position label stays consistent with the map.
    _assert_party_mark(absent, marked=[], marker_count=0, label_contains="brak")

    # Moving the party in the model moves the mark (and the label).
    _assert_party_mark(on_beta, marked=["Beta"], marker_count=1, label_contains="Beta")

    # Direct render_model path marks from the model alone (no main.gd side channel).
    _assert_party_mark(direct_gamma, marked=["Gamma"], marker_count=1)


def test_map_view_tiles_carry_asset_textures_for_owner_settlement_and_party():
    """Region tiles and the party mark must show Texture2D from game/assets/.

    Realistic defect this catches: MapView still paints solid ColorRect tiles
    (and a ColorRect party mark). K84 geometry / owner-color / party-mark-count
    gates stay green while the player never sees real graphics, settlement art,
    or a textured army marker. Missing asset files must fail this gate (disk +
    import + non-empty res://assets/ texture paths), not yield a silent color tile.
    """
    assets_dir = GAME / "assets"
    for asset_name in ("map_ground.png", "settlement.png", "party_player.png"):
        asset_path = assets_dir / asset_name
        assert asset_path.is_file(), (
            f"required map asset missing on disk: {asset_path} "
            "(missing file must red-gate, not paint an empty color tile)"
        )

    imported = _import_game_assets()
    assert imported.returncode == 0, (
        f"godot --import failed rc={imported.returncode} "
        f"stderr={imported.stderr!r} stdout={imported.stdout!r}"
    )

    payload = _load_map_view()
    assert payload["map_view_found"] is True, payload
    assert payload["has_render_model"] is True, payload

    regions = payload["regions"]
    by_region = {r["name"]: r for r in regions}
    assert by_region["Alpha"].get("settlement") is not None, regions
    assert by_region["Beta"].get("settlement") is None, regions
    assert by_region["Gamma"].get("settlement") is None, regions

    first = payload["tiles_after_first"]
    assert len(first) == len(regions), first
    by_name = _by_name(first)

    for tile in first:
        assert tile["has_texture"] is True, (
            f"tile {tile['name']!r} must carry a Texture2D from assets, got {tile!r}"
        )
        assert tile["texture_paths"], tile
        for path in tile["texture_paths"]:
            assert isinstance(path, str) and path.startswith("res://assets/"), (
                f"tile {tile['name']!r} texture must come from res://assets/, "
                f"got {path!r} in {tile!r}"
            )

    # Settlement presence is visible as a different image set, not name text alone.
    # Owner distinction (texture swap vs modulate) is left to visual/K84 — do not
    # require Beta and Gamma (different owners, both without settlement) to share
    # the same body texture set; AC allows per-owner textures.
    alpha_paths = set(by_name["Alpha"]["texture_paths"])
    beta_paths = set(by_name["Beta"]["texture_paths"])
    assert alpha_paths != beta_paths, (
        f"region with settlement must differ by texture from region without: "
        f"Alpha={alpha_paths!r} Beta={beta_paths!r}"
    )

    # R87.1: body texture layers fill the tile bounds and do not capture mouse.
    # Compares probe global size to the parent tile — that guards PRESET_FULL_RECT
    # (control extents), not TextureRect.stretch_mode. A FULL_RECT + STRETCH_KEEP
    # regression would still pass size checks; paths alone would also stay green.
    # Also guards MOUSE_FILTER_IGNORE so layers do not steal map clicks.
    for tile in first:
        body = _body_texture_layers(tile)
        assert body, (
            f"tile {tile['name']!r} must report body texture_layers with size, "
            f"got {tile!r}"
        )
        assert tile.get("tile_mouse_filter") == MOUSE_FILTER_IGNORE, (
            f"tile {tile['name']!r} root must ignore mouse, got {tile!r}"
        )
        for layer in body:
            assert layer_fills_tile(layer, tile), (
                f"tile {tile['name']!r} body layer must fill the tile bounds "
                f"(FULL_RECT size), layer={layer!r} tile_w={tile['w']} "
                f"tile_h={tile['h']}"
            )
            assert layer.get("mouse_filter") == MOUSE_FILTER_IGNORE, (
                f"tile {tile['name']!r} body layer must not capture mouse, "
                f"got layer={layer!r}"
            )

    # Party mark is a texture, not a ColorRect swatch — and stays a small corner
    # mark (must not accidentally become a full-tile stretch layer).
    on_alpha = payload["party_on_alpha"]
    assert on_alpha["marker_count"] == 1, on_alpha
    assert on_alpha["marker_has_texture"] is True, (
        f"PlayerPartyMarker must carry Texture2D, got {on_alpha!r}"
    )
    marker_layers = on_alpha.get("marker_layers") or []
    assert len(marker_layers) == 1, on_alpha
    marker = marker_layers[0]
    assert str(marker.get("tile_name")) == "Alpha", marker
    assert float(marker["w"]) < float(marker["tile_w"]), (
        f"PlayerPartyMarker must be narrower than its tile (corner mark, not "
        f"full-tile stretch), got {marker!r}"
    )
    assert float(marker["h"]) < float(marker["tile_h"]), (
        f"PlayerPartyMarker must be shorter than its tile (corner mark, not "
        f"full-tile stretch), got {marker!r}"
    )
    assert marker.get("mouse_filter") == MOUSE_FILTER_IGNORE, (
        f"PlayerPartyMarker must not capture mouse, got {marker!r}"
    )


def test_map_view_adjacent_tiles_form_connected_grid_fitting_panel():
    """Grid neighbours must touch (no card gaps); five-region line fits MapView.

    Realistic defects this catches:
    - MapView still places RegionTile_* with a positive TILE_GAP pitch
      (separated rectangular cards). Existing gates only check col/row order
      and non-overlap, so a gapped five-card row stays green.
    - line pitch is only ordered (b.x > a.x) while gap==0 for both touch and
      overlap, so a 1px-step almost-stack would pass without a pitch/AABB check.
    - TILE_SIZE shrinks without adjusting labels: long fresh-party names
      ("player outpost", …) need more than tile width and spill into neighbours
      (or clip) while short probe names (Alpha, R0) stay green.
    - GRID_PITCH == TILE_SIZE with no odd-row offset is a rectangular card
      lattice, not the AC hex grid (regions_full Alpha row0 / Gamma row1).
    """
    payload = _load_map_view()
    assert payload["map_view_found"] is True, payload
    assert payload["has_render_model"] is True, payload

    # --- Neighbours in the main synthetic L (Alpha–Beta horizontal, Alpha–Gamma
    # vertical) must touch along the shared edge.
    regions = payload["regions"]
    by_region = {r["name"]: r for r in regions}
    tiles = _by_name(payload["tiles_after_first"])
    assert {"Alpha", "Beta", "Gamma"} <= set(tiles), payload
    neighbour_pairs = []
    names = list(by_region)
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            lc, lr = int(by_region[left]["col"]), int(by_region[left]["row"])
            rc, rr = int(by_region[right]["col"]), int(by_region[right]["row"])
            if abs(rc - lc) + abs(rr - lr) == 1:
                neighbour_pairs.append((left, right, lc, lr, rc, rr))
    assert neighbour_pairs, (
        f"probe regions must include at least one grid neighbour pair, got {regions!r}"
    )
    for left, right, lc, lr, rc, rr in neighbour_pairs:
        a, b = tiles[left], tiles[right]
        if rc != lc:
            gap = _gap_between_axis_aligned(a, b, axis="x")
            assert gap <= _LAYOUT_TOL_PX, (
                f"horizontal neighbours {left}(col={lc}) and {right}(col={rc}) "
                f"must touch (no card gap): gap={gap}px tiles={a!r} {b!r}"
            )
        if rr != lr:
            gap = _gap_between_axis_aligned(a, b, axis="y")
            assert gap <= _LAYOUT_TOL_PX, (
                f"vertical neighbours {left}(row={lr}) and {right}(row={rr}) "
                f"must touch (no card gap): gap={gap}px tiles={a!r} {b!r}"
            )

    # --- Minimal hex geometry (AC: połączona siatka heksów), not a pure
    # rectangular lattice. Probe Alpha (col=0,row=0) and Gamma (col=0,row=1):
    # odd row is shifted by ~half tile width, and vertical pitch is strictly
    # less than tile height (classic pointy-top offset packing).
    alpha, gamma = tiles["Alpha"], tiles["Gamma"]
    assert int(by_region["Alpha"]["col"]) == 0 and int(by_region["Alpha"]["row"]) == 0
    assert int(by_region["Gamma"]["col"]) == 0 and int(by_region["Gamma"]["row"]) == 1
    tile_w = float(alpha["w"])
    tile_h = float(alpha["h"])
    row_dx = float(gamma["x"]) - float(alpha["x"])
    row_dy = float(gamma["y"]) - float(alpha["y"])
    assert abs(abs(row_dx) - tile_w * 0.5) <= _LAYOUT_TOL_PX, (
        f"hex grid: odd row must be offset by ~half tile width "
        f"(Alpha→Gamma dx={row_dx}, expect ±{tile_w * 0.5}); "
        f"rectangular GRID_PITCH==TILE_SIZE leaves dx=0. tiles={alpha!r} {gamma!r}"
    )
    assert row_dy > 0, (
        f"row 1 must sit below row 0: Alpha→Gamma dy={row_dy} tiles={alpha!r} {gamma!r}"
    )
    assert row_dy < tile_h - _LAYOUT_TOL_PX, (
        f"hex grid: vertical pitch must be < tile height "
        f"(Alpha→Gamma dy={row_dy}, tile_h={tile_h}); "
        f"rectangular packing uses dy==tile_h. tiles={alpha!r} {gamma!r}"
    )
    # Alpha→Gamma also anchors the cross-row step floor used in owner-paint.
    assert row_dy >= tile_h * 0.5, (
        f"hex grid: Alpha→Gamma vertical step must be ≥ half tile height "
        f"(dy={row_dy}, tile_h={tile_h}); near-total row overlap stays red. "
        f"tiles={alpha!r} {gamma!r}"
    )

    # --- Fresh-party five-region line (col 0..4): connected strip + fits panel.
    line_regions = payload.get("line_regions") or []
    line_tiles = payload.get("line_tiles") or []
    panel = payload.get("map_view_rect")
    assert len(line_regions) == 5, (
        f"probe must emit five line regions for G94.1a, got {line_regions!r}"
    )
    assert len(line_tiles) == 5, (
        f"five line regions must each produce a tile, got {line_tiles!r}"
    )
    assert isinstance(panel, dict) and float(panel.get("w", 0)) > 0, (
        f"probe must emit MapView global rect, got {panel!r}"
    )
    line_by_name = _by_name(line_tiles)
    line_by_region = {r["name"]: r for r in line_regions}
    ordered = sorted(line_regions, key=lambda r: int(r["col"]))
    for left, right in zip(ordered, ordered[1:]):
        a = line_by_name[left["name"]]
        b = line_by_name[right["name"]]
        gap = _gap_between_axis_aligned(a, b, axis="x")
        assert gap <= _LAYOUT_TOL_PX, (
            f"line neighbours {left['name']}(col={left['col']}) and "
            f"{right['name']}(col={right['col']}) must touch (no card gap): "
            f"gap={gap}px tiles={a!r} {b!r}"
        )
        # gap helper returns 0 for both touch and overlap — require no AABB
        # overlap and a full-tile pitch so a 1px-step almost-stack stays red.
        assert not _rects_overlap(a, b), (
            f"line neighbours {left['name']} and {right['name']} must not "
            f"overlap: {a!r} vs {b!r}"
        )
        pitch = float(b["x"]) - float(a["x"])
        assert abs(pitch - float(a["w"])) <= _LAYOUT_TOL_PX, (
            f"line pitch for {left['name']}→{right['name']} must equal tile "
            f"width (no partial overlap): pitch={pitch} tile_w={a['w']} "
            f"tiles={a!r} {b!r}"
        )
        assert int(line_by_region[left["name"]]["row"]) == 0
        assert int(line_by_region[right["name"]]["row"]) == 0

    for tile in line_tiles:
        assert tile["visible"] is True, tile
        assert _tile_inside_panel(tile, panel), (
            f"five-region map tile {tile['name']!r} must fit fully inside MapView "
            f"(no clip_contents cut): tile={tile!r} panel={panel!r}"
        )
        # Name geometry: unwrapped label content must fit inside the tile so
        # long fresh-party names (e.g. "player outpost") neither spill into the
        # neighbour tile nor get clipped mid-word. Short synthetic names (R0)
        # hide this defect after TILE_SIZE shrinks. Strict (no +tol): probe
        # previously passed content_w=85 on tile_w=84 only via 1px slack.
        assert "label_content_w" in tile and "label_content_h" in tile, (
            f"probe must emit label content size for {tile['name']!r}, got {tile!r}"
        )
        assert float(tile["label_content_w"]) <= float(tile["w"]), (
            f"region name {tile['name']!r} content width must fit the tile "
            f"(no neighbour spill): content_w={tile['label_content_w']} "
            f"tile_w={tile['w']} tile={tile!r}"
        )
        assert float(tile["label_content_h"]) <= float(tile["h"]), (
            f"region name {tile['name']!r} content height must fit the tile "
            f"(no clip / no settlement cover by oversized text): "
            f"content_h={tile['label_content_h']} tile_h={tile['h']} tile={tile!r}"
        )

    # Odd-row offset can push high-col tiles past the panel; Gamma (row=1)
    # from regions_full must still lie fully inside MapView (clip_contents).
    for tile in tiles.values():
        assert _tile_inside_panel(tile, panel), (
            f"regions_full tile {tile['name']!r} (incl. odd row) must fit "
            f"inside MapView: tile={tile!r} panel={panel!r}"
        )
