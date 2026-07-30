"""MapView contract: one visible tile per region, grid placement, owner paint."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from godot_png_assets import LICENSE_RE, assert_asset_credited, hex_floor_sample_alphas
from godot_runner import run_godot_script
from godot_tile_layer import MOUSE_FILTER_IGNORE, layer_fills_tile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PREFIX = "MAP_VIEW "

# G96.1a public paths: army marks are unit silhouettes, not the old banner.
PARTY_PLAYER_UNIT_REL = "assets/party_player_unit.png"
PARTY_PLAYER_UNIT_RES = f"res://{PARTY_PLAYER_UNIT_REL}"
PARTY_AI_UNIT_REL = "assets/party_ai_unit.png"
PARTY_AI_UNIT_RES = f"res://{PARTY_AI_UNIT_REL}"
# Replaced prototype banner (may remain on disk); must not be the unit source.
PARTY_BANNER_REL = "assets/party_player.png"
_CREDITS_ROW_RE = re.compile(
    r"^\|\s*(?P<file>[^|]+?)\s*\|\s*(?P<source>[^|]+?)\s*\|\s*(?P<author>[^|]+?)\s*\|\s*(?P<license>[^|]+?)\s*\|",
    re.MULTILINE,
)
# Pack-relative path or URL — positive source signal (not a bare license token).
_CREDITS_SOURCE_RE = re.compile(r"https?://\S+|PNG/")


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
    for asset_name in (
        "map_ground_grass.png",
        "settlement.png",
        # G96.1a carrier (not the prototype banner party_player.png).
        "party_player_unit.png",
    ):
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
    # G96.1a: mark texture path is the public unit carrier, not the banner.
    assert marker.get("path") == PARTY_PLAYER_UNIT_RES, (
        f"PlayerPartyMarker must use public unit silhouette {PARTY_PLAYER_UNIT_RES}, "
        f"got {marker.get('path')!r} (prototype banner is not the G96.1a carrier)"
    )


def test_player_party_marker_uses_credited_unit_silhouette_not_banner():
    """Disk + CREDITS for party_player_unit.png (unique vs geometry/texture gates).

    Realistic defect existing gates miss: MapView still preloads the prototype
    banner while CREDITS either omits the unit row or attributes a hollow/wrong
    source. Marker count/texture presence and path wiring live in
    ``test_map_view_tiles_carry_asset_textures_for_owner_settlement_and_party``;
    this gate only asserts the public file on disk and a positive CREDITS row
    (non-empty pack path/URL + CC0/CC-BY), not a single banned source literal.
    """
    unit_path = GAME / PARTY_PLAYER_UNIT_REL
    assert unit_path.is_file(), (
        f"committed player unit silhouette missing on disk: {unit_path} "
        "(public contract: game/assets/party_player_unit.png)"
    )
    banner_path = GAME / PARTY_BANNER_REL
    if banner_path.is_file():
        assert unit_path.read_bytes() != banner_path.read_bytes(), (
            "party_player_unit.png must not be a byte-copy of the prototype "
            f"banner {PARTY_BANNER_REL}"
        )

    credits_path = GAME / "assets" / "CREDITS.md"
    assert_asset_credited(credits_path, unit_path.name)
    rows = _credits_table_rows(credits_path.read_text(encoding="utf-8"))
    unit_row = rows.get(unit_path.name)
    assert unit_row is not None, (
        f"CREDITS.md must have a table row attributing {unit_path.name}"
    )
    unit_source = unit_row["source"]
    assert unit_source, (
        f"CREDITS.md row for {unit_path.name} must list a non-empty source path/page"
    )
    assert _CREDITS_SOURCE_RE.search(unit_source), (
        f"CREDITS.md row for {unit_path.name} must give a pack-relative path "
        f"(PNG/…) or http(s) page, got {unit_source!r}"
    )
    assert LICENSE_RE.search(unit_row["license"]), (
        f"CREDITS.md row for {unit_path.name} must state CC0 or CC-BY in the "
        f"license cell, got {unit_row['license']!r}"
    )
    banner_row = rows.get(Path(PARTY_BANNER_REL).name)
    if banner_row is not None:
        assert unit_source != banner_row["source"], (
            f"CREDITS.md must not present the replaced banner source as the "
            f"unit silhouette source; both rows cite {unit_source!r}"
        )


def _credits_table_rows(credits_text: str) -> dict[str, dict[str, str]]:
    """Parse CREDITS.md pipe rows → file → {source, author, license}."""
    return {
        m.group("file").strip(): {
            "source": m.group("source").strip(),
            "author": m.group("author").strip(),
            "license": m.group("license").strip(),
        }
        for m in _CREDITS_ROW_RE.finditer(credits_text)
    }


def test_map_view_marks_ai_party_with_distinct_unit_silhouette_from_party_owner():
    """AI army mark must follow region.party.owner with party_ai_unit.png.

    Realistic defect existing gates miss: MapView only paints PlayerPartyMarker
    from ``player_party_region`` and always preloads ``party_player_unit.png``.
    A region with ``party.owner == "ai"`` stays unmarked (or reuses the player
    silhouette), so the AI army is invisible or indistinguishable. Player-mark
    count/path and player-only CREDITS gates never set ``region.party`` nor look
    for ``party_ai_unit.png``, so that gap stays green.
    """
    ai_path = GAME / PARTY_AI_UNIT_REL
    assert ai_path.is_file(), (
        f"committed AI unit silhouette missing on disk: {ai_path} "
        "(public contract: game/assets/party_ai_unit.png)"
    )
    player_path = GAME / PARTY_PLAYER_UNIT_REL
    assert player_path.is_file(), (
        f"committed player unit silhouette missing on disk: {player_path} "
        "(public contract: game/assets/party_player_unit.png)"
    )
    assert ai_path.read_bytes() != player_path.read_bytes(), (
        "party_ai_unit.png must differ byte-wise from party_player_unit.png "
        "(sides must be distinguishable without tint alone)"
    )

    # Public contract + AC: CREDITS must attribute party_ai_unit with a pack
    # path/page, author, and license, and share the RTS unit family with player
    # without reusing the same source file (shape, not tint-only).
    credits_path = GAME / "assets" / "CREDITS.md"
    assert_asset_credited(credits_path, ai_path.name)
    rows = _credits_table_rows(credits_path.read_text(encoding="utf-8"))
    ai_row = rows.get(ai_path.name)
    assert ai_row is not None, (
        f"CREDITS.md must have a table row attributing {ai_path.name}"
    )
    assert ai_row["source"], (
        f"CREDITS.md row for {ai_path.name} must list a non-empty source path/page"
    )
    assert _CREDITS_SOURCE_RE.search(ai_row["source"]), (
        f"CREDITS.md row for {ai_path.name} must give a pack-relative path "
        f"(PNG/…) or http(s) page, got {ai_row['source']!r}"
    )
    assert LICENSE_RE.search(ai_row["license"]), (
        f"CREDITS.md row for {ai_path.name} must state CC0 or CC-BY in the "
        f"license cell, got {ai_row['license']!r}"
    )
    player_row = rows.get(player_path.name)
    assert player_row is not None, (
        f"CREDITS.md must have a table row attributing {player_path.name} "
        "(public contract — required for shared-family check vs AI)"
    )
    assert player_row.get("source"), (
        f"CREDITS.md row for {player_path.name} must list a non-empty source path/page"
    )
    assert ai_row["source"] != player_row["source"], (
        "CREDITS.md must attribute distinct RTS unit sources for player vs AI "
        f"silhouettes; both cite {ai_row['source']!r}"
    )
    # Shared family: both unit rows point at Kenney RTS unit PNGs (not banner).
    for label, source in (
        ("player", player_row["source"]),
        ("ai", ai_row["source"]),
    ):
        assert "Unit/" in source or "unit" in source.lower(), (
            f"CREDITS.md {label} unit source must stay in the RTS unit family, "
            f"got {source!r}"
        )

    imported = _import_game_assets()
    assert imported.returncode == 0, (
        f"godot --import failed rc={imported.returncode} "
        f"stderr={imported.stderr!r} stdout={imported.stdout!r}"
    )

    payload = _load_map_view()
    assert payload["map_view_found"] is True, payload
    assert payload["has_render_model"] is True, payload

    sample = payload.get("party_owner_silhouettes") or {}
    assert sample.get("skipped") is not True, (
        "party_owner_silhouettes was skipped (no MapView.render_model); "
        f"cannot assert AI/player unit paths, sample={sample!r}"
    )
    by_region = sample.get("unit_paths_by_region") or {}
    assert by_region.get("Gamma") == PARTY_AI_UNIT_RES, (
        f"region with party.owner=ai must show public AI unit silhouette "
        f"{PARTY_AI_UNIT_RES}, got unit_paths_by_region={by_region!r}"
    )
    assert by_region.get("Alpha") == PARTY_PLAYER_UNIT_RES, (
        f"region with party.owner=player must keep public player unit silhouette "
        f"{PARTY_PLAYER_UNIT_RES} when an AI party is also present, "
        f"got unit_paths_by_region={by_region!r}"
    )
    assert "Beta" not in by_region, (
        f"region without party must not carry a unit silhouette, "
        f"got unit_paths_by_region={by_region!r}"
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


# G94.1b: decorative strategic ground variants (not mechanical terrain).
DECORATIVE_GROUND_ASSETS: tuple[str, ...] = (
    "map_ground_grass.png",
    "map_ground_earth.png",
    "map_ground_stone.png",
)
_DECORATIVE_GROUND_RES: frozenset[str] = frozenset(
    f"res://assets/{name}" for name in DECORATIVE_GROUND_ASSETS
)


def _ground_texture_path(tile: dict) -> str:
    """Public ground layer path under a region tile (layer name Ground)."""
    for layer in tile.get("texture_layers") or []:
        if not isinstance(layer, dict):
            continue
        if str(layer.get("name", "")) == "Ground":
            path = layer.get("path")
            assert isinstance(path, str) and path, (
                f"Ground layer must report a texture path, got {layer!r} "
                f"on tile {tile!r}"
            )
            return path
    raise AssertionError(
        f"tile {tile.get('name')!r} must expose a Ground texture layer, "
        f"got texture_layers={tile.get('texture_layers')!r}"
    )


def test_map_view_decorative_ground_variants_from_col_row():
    """Five fresh-party regions must show ≥3 col/row-driven ground variants.

    Realistic defect this catches: MapView still paints every RegionTile with the
    single ``map_ground.png`` (or solid color). Existing texture / geometry /
    connected-grid gates only require *some* ``res://assets/`` ground path and
    stay green while the strategic map has no decorative variety, no three named
    variants on disk, and no deterministic selection from public ``col``/``row``.
    """
    assets_dir = GAME / "assets"
    for asset_name in DECORATIVE_GROUND_ASSETS:
        asset_path = assets_dir / asset_name
        assert asset_path.is_file(), (
            f"required decorative ground asset missing on disk: {asset_path}"
        )

    credits = (assets_dir / "CREDITS.md").read_text(encoding="utf-8")
    for asset_name in DECORATIVE_GROUND_ASSETS:
        assert asset_name in credits, (
            f"CREDITS.md must attribute decorative ground file {asset_name}"
        )

    imported = _import_game_assets()
    assert imported.returncode == 0, (
        f"godot --import failed rc={imported.returncode} "
        f"stderr={imported.stderr!r} stdout={imported.stdout!r}"
    )

    payload = _load_map_view()
    assert payload["map_view_found"] is True, payload
    assert payload["has_render_model"] is True, payload

    line_regions = payload.get("line_regions") or []
    line_tiles = payload.get("line_tiles") or []
    assert len(line_regions) == 5 and len(line_tiles) == 5, (
        f"probe must emit five fresh-party line regions/tiles, got "
        f"regions={line_regions!r} tiles={line_tiles!r}"
    )

    line_by_name = _by_name(line_tiles)
    ground_by_region: dict[str, str] = {}
    for region in line_regions:
        name = region["name"]
        tile = line_by_name[name]
        path = _ground_texture_path(tile)
        assert path in _DECORATIVE_GROUND_RES, (
            f"region {name!r} ground must be one of {sorted(_DECORATIVE_GROUND_RES)}, "
            f"got {path!r} (single map_ground.png or other paths are not G94.1b)"
        )
        ground_by_region[name] = path

    distinct = set(ground_by_region.values())
    assert len(distinct) >= 3, (
        f"five fresh-party regions must show at least three ground variants "
        f"at once, got {len(distinct)}: {ground_by_region!r}"
    )

    # Determinism: re-render of the same synthetic regions keeps the same ground.
    first = _by_name(payload["tiles_after_first"])
    second = _by_name(payload["tiles_after_second"])
    for name in first:
        assert _ground_texture_path(first[name]) == _ground_texture_path(
            second[name]
        ), (
            f"ground for {name!r} must be stable across re-render: "
            f"{_ground_texture_path(first[name])!r} vs "
            f"{_ground_texture_path(second[name])!r}"
        )

    # Same public (col, row) → same variant (independent of region name / owner).
    # Alpha (0,0) matches "player lands" (0,0); Beta (1,0) matches "player outpost".
    full_regions = {r["name"]: r for r in payload["regions"]}
    line_region_by_name = {r["name"]: r for r in line_regions}
    assert (
        int(full_regions["Alpha"]["col"]),
        int(full_regions["Alpha"]["row"]),
    ) == (0, 0)
    assert (
        int(line_region_by_name["player lands"]["col"]),
        int(line_region_by_name["player lands"]["row"]),
    ) == (0, 0)
    assert (
        int(full_regions["Beta"]["col"]),
        int(full_regions["Beta"]["row"]),
    ) == (1, 0)
    assert (
        int(line_region_by_name["player outpost"]["col"]),
        int(line_region_by_name["player outpost"]["row"]),
    ) == (1, 0)
    assert _ground_texture_path(first["Alpha"]) == ground_by_region[
        "player lands"
    ], (
        "ground must depend only on col/row: Alpha(0,0) vs player lands(0,0) "
        f"got {_ground_texture_path(first['Alpha'])!r} vs "
        f"{ground_by_region['player lands']!r}"
    )
    assert _ground_texture_path(first["Beta"]) == ground_by_region[
        "player outpost"
    ], (
        "ground must depend only on col/row: Beta(1,0) vs player outpost(1,0) "
        f"got {_ground_texture_path(first['Beta'])!r} vs "
        f"{ground_by_region['player outpost']!r}"
    )


# G94.1c: distinct keep / outpost settlement art (presentation only).
SETTLEMENT_KEEP_ASSET = "settlement_keep.png"
SETTLEMENT_OUTPOST_ASSET = "settlement_outpost.png"
SETTLEMENT_TYPE_ASSETS: tuple[str, ...] = (
    SETTLEMENT_KEEP_ASSET,
    SETTLEMENT_OUTPOST_ASSET,
)
_SETTLEMENT_KEEP_RES = f"res://assets/{SETTLEMENT_KEEP_ASSET}"
_SETTLEMENT_OUTPOST_RES = f"res://assets/{SETTLEMENT_OUTPOST_ASSET}"


def _settlement_layer(tile: dict) -> dict:
    """Public Settlement texture layer under a region tile."""
    for layer in tile.get("texture_layers") or []:
        if not isinstance(layer, dict):
            continue
        if str(layer.get("name", "")) == "Settlement":
            path = layer.get("path")
            assert isinstance(path, str) and path, (
                f"Settlement layer must report a texture path, got {layer!r} "
                f"on tile {tile!r}"
            )
            return layer
    raise AssertionError(
        f"tile {tile.get('name')!r} must expose a Settlement texture layer, "
        f"got texture_layers={tile.get('texture_layers')!r}"
    )


def _settlement_texture_path(tile: dict) -> str:
    """Public Settlement layer path under a region tile (layer name Settlement)."""
    return str(_settlement_layer(tile)["path"])


def _asset_path_from_res(assets_dir: Path, res_path: str) -> Path:
    """Map ``res://assets/...`` probe paths to files under ``game/assets``."""
    assert res_path.startswith("res://assets/"), res_path
    return assets_dir / res_path.removeprefix("res://assets/")


def _settlement_floor_alphas(tile: dict, assets_dir: Path) -> list[int]:
    """Hex-floor rim alphas for the Settlement texture on ``tile``."""
    return hex_floor_sample_alphas(
        _asset_path_from_res(assets_dir, str(_settlement_layer(tile)["path"]))
    )


def _settlement_leaves_owner_ground_visible(tile: dict, assets_dir: Path) -> bool:
    """True when Settlement does not fully occlude owner-tinted Ground.

    Accepts either a smaller-than-tile building sprite (ground rim stays visible)
    or a full-tile overlay whose hex floor samples are transparent.
    """
    layer = _settlement_layer(tile)
    if not layer_fills_tile(layer, tile):
        return True
    floor_alphas = _settlement_floor_alphas(tile, assets_dir)
    # Any fully opaque floor sample means the underlay (owner modulate) is hidden
    # at that rim point — the defect under review for keep/outpost assets.
    return max(floor_alphas) < 32


def test_map_view_settlement_keep_and_outpost_use_distinct_assets_by_name():
    """Keep vs outpost settlements must use distinct textures from settlement name.

    Realistic defects this catches:
    - MapView still paints every settled tile with the single ``settlement.png``.
      Path/CREDITS gates stay green while keep and outpost look identical.
    - Settlement is a full-tile overlay with a baked opaque hex floor (green on
      keep, brown on outpost), so Ground.modulate (owner colour) and G94.1b
      ground variants are invisible on all four settled fresh-party regions.
      Path-only gates stay green while region affiliation is unreadable.
    """
    assets_dir = GAME / "assets"
    for asset_name in SETTLEMENT_TYPE_ASSETS:
        asset_path = assets_dir / asset_name
        assert asset_path.is_file(), (
            f"required settlement-type asset missing on disk: {asset_path}"
        )

    keep_bytes = (assets_dir / SETTLEMENT_KEEP_ASSET).read_bytes()
    outpost_bytes = (assets_dir / SETTLEMENT_OUTPOST_ASSET).read_bytes()
    assert keep_bytes != outpost_bytes, (
        "settlement_keep.png and settlement_outpost.png must differ byte-wise "
        "(two settlement types, not one image under two names)"
    )

    credits = (assets_dir / "CREDITS.md").read_text(encoding="utf-8")
    for asset_name in SETTLEMENT_TYPE_ASSETS:
        assert asset_name in credits, (
            f"CREDITS.md must attribute settlement-type file {asset_name}"
        )

    # Owner-ground occlusion is asserted only on probe tiles via
    # ``_settlement_leaves_owner_ground_visible`` (full-rect ⇒ floor a<32;
    # smaller-than-tile building sprites are accepted without rim samples).

    imported = _import_game_assets()
    assert imported.returncode == 0, (
        f"godot --import failed rc={imported.returncode} "
        f"stderr={imported.stderr!r} stdout={imported.stdout!r}"
    )

    payload = _load_map_view()
    assert payload["map_view_found"] is True, payload
    assert payload["has_render_model"] is True, payload

    line_regions = payload.get("line_regions") or []
    line_tiles = payload.get("line_tiles") or []
    assert len(line_regions) == 5 and len(line_tiles) == 5, (
        f"probe must emit five fresh-party line regions/tiles, got "
        f"regions={line_regions!r} tiles={line_tiles!r}"
    )

    by_region = {r["name"]: r for r in line_regions}
    by_tile = _by_name(line_tiles)

    # Probe fixtures mirror fresh-party names: lands → Keep, outpost → Outpost.
    keep_settlement = by_region["player lands"].get("settlement") or {}
    outpost_settlement = by_region["player outpost"].get("settlement") or {}
    assert "keep" in str(keep_settlement.get("name", "")).lower(), (
        f"line fixture player lands must carry a keep settlement name, "
        f"got {keep_settlement!r}"
    )
    assert "outpost" in str(outpost_settlement.get("name", "")).lower(), (
        f"line fixture player outpost must carry an outpost settlement name, "
        f"got {outpost_settlement!r}"
    )

    keep_path = _settlement_texture_path(by_tile["player lands"])
    outpost_path = _settlement_texture_path(by_tile["player outpost"])
    assert keep_path == _SETTLEMENT_KEEP_RES, (
        f"settlement name with 'keep' must use {_SETTLEMENT_KEEP_RES}, "
        f"got {keep_path!r} on player lands"
    )
    assert outpost_path == _SETTLEMENT_OUTPOST_RES, (
        f"settlement name with 'outpost' must use {_SETTLEMENT_OUTPOST_RES}, "
        f"got {outpost_path!r} on player outpost"
    )
    assert keep_path != outpost_path, (
        f"keep and outpost must be distinguishable by texture path at once, "
        f"got keep={keep_path!r} outpost={outpost_path!r}"
    )

    # Same rule on the AI side of the fresh-party strip (both types simultaneous).
    assert _settlement_texture_path(by_tile["ai lands"]) == _SETTLEMENT_KEEP_RES
    assert _settlement_texture_path(by_tile["ai outpost"]) == _SETTLEMENT_OUTPOST_RES

    # Owner-tinted Ground must remain observable under Settlement on every settled
    # owned region (not only border). Full-rect keep/outpost with baked opaque
    # hex floors hide player/AI colour and ground variants; keep (green floor)
    # vs outpost (brown floor) also break G94.1b consistency.
    settled_owned = (
        "player lands",
        "player outpost",
        "ai outpost",
        "ai lands",
    )
    for name in settled_owned:
        tile = by_tile[name]
        assert _ground_texture_path(tile) in _DECORATIVE_GROUND_RES, (
            f"settled region {name!r} must still use decorative Ground under "
            f"the building, got {_ground_texture_path(tile)!r}"
        )
        assert _settlement_leaves_owner_ground_visible(tile, assets_dir), (
            f"settled region {name!r}: Settlement must not fully hide "
            f"owner-tinted Ground (use transparent-floor keep/outpost assets "
            f"or a smaller-than-tile building sprite). layer="
            f"{_settlement_layer(tile)!r} floor_alphas="
            f"{_settlement_floor_alphas(tile, assets_dir)!r}"
        )


