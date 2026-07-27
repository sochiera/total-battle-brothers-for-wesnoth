"""BattleView contract: one axial hex tile per battle hex, side paint, Polish result."""

from __future__ import annotations

import json
from pathlib import Path

from godot_runner import run_godot_script

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PREFIX = "BATTLE_VIEW "


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
