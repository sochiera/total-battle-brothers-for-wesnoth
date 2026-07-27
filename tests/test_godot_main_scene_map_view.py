"""MapView contract: one visible tile per region, grid placement, owner paint."""

from __future__ import annotations

import json
from pathlib import Path

from godot_runner import run_godot_script

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PREFIX = "MAP_VIEW "


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

    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            assert not _rects_overlap(by_name[left], by_name[right]), (
                f"tiles must not overlap: {left}={by_name[left]} "
                f"vs {right}={by_name[right]}"
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
