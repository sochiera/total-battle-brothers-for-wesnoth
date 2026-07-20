"""Tests for deterministic hex-battle field SVG (tbbui presentation layer)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import replace

from tbb.battle import BattleSide, HexBattle
from tbb.battlefield import Battlefield
from tbb.hex import Hex
from tbb.terrain import FOREST, PLAINS
from tbb.unit import Unit
from tbbui.battlesvg import render_battle_svg
from tbbui.hexgeom import hex_corners, hex_to_pixel


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _parse_points(points_attr: str) -> list[tuple[float, float]]:
    """Parse SVG polygon ``points`` into coordinate pairs."""
    tokens = [t for t in re.split(r"[\s,]+", points_attr.strip()) if t]
    assert len(tokens) % 2 == 0 and len(tokens) >= 12, (
        f"expected 6 corner pairs, got {len(tokens) // 2} from {points_attr!r}"
    )
    return [(float(tokens[i]), float(tokens[i + 1])) for i in range(0, len(tokens), 2)]


def _marker_center(element: ET.Element) -> tuple[float, float]:
    """Resolve a unit marker's pixel center from common SVG attrs / transform."""
    if element.get("cx") is not None and element.get("cy") is not None:
        return float(element.get("cx")), float(element.get("cy"))
    if element.get("x") is not None and element.get("y") is not None:
        return float(element.get("x")), float(element.get("y"))
    transform = element.get("transform") or ""
    match = re.search(
        r"translate\(\s*([-\d.]+)[,\s]+([-\d.]+)\s*\)",
        transform,
    )
    if match:
        return float(match.group(1)), float(match.group(2))
    raise AssertionError(
        f"unit marker {_local(element.tag)} data-side={element.get('data-side')!r} "
        "has no discoverable center (cx/cy, x/y, or translate)"
    )


def test_render_battle_svg_polygons_units_and_determinism():
    """Parsable SVG: bbox±1 polygons, unit markers, terrain fill, pure/det.

    Two units on distinct hexes (attacker damaged + stunned defender) on mixed
    terrain; axial bounding box of occupied hexes expanded by ±1 in q and r.
    """
    attacker_hex = Hex(0, 0)
    defender_hex = Hex(2, 1)
    battlefield = Battlefield(
        {
            attacker_hex: PLAINS,
            defender_hex: FOREST,
            Hex(1, 0): FOREST,
        }
    )
    attacker = Unit(training=1)
    defender = replace(Unit(), stunned=True)
    battle = (
        HexBattle(battlefield)
        .deploy(attacker, attacker_hex, BattleSide.ATTACKER)
        .deploy(defender, defender_hex, BattleSide.DEFENDER)
        .damage(attacker_hex, 1)
    )
    units_before = dict(battle.units)
    sides_before = dict(battle.sides)
    hp_before = {pos: battle.current_hp_at(pos) for pos in battle.units}
    stunned_before = {pos: unit.stunned for pos, unit in battle.units.items()}

    qs = [h.q for h in battle.units]
    rs = [h.r for h in battle.units]
    q_min, q_max = min(qs) - 1, max(qs) + 1
    r_min, r_max = min(rs) - 1, max(rs) + 1
    expected_hexes = {
        (q, r) for q in range(q_min, q_max + 1) for r in range(r_min, r_max + 1)
    }
    assert len(expected_hexes) == 5 * 4  # q: -1..3, r: -1..2

    svg = render_battle_svg(battle)

    root = ET.fromstring(svg)
    assert _local(root.tag) == "svg"

    polygons = [el for el in root.iter() if _local(el.tag) == "polygon"]
    assert len(polygons) == len(expected_hexes)

    by_qr: dict[tuple[int, int], ET.Element] = {}
    for poly in polygons:
        q_attr = poly.get("data-q")
        r_attr = poly.get("data-r")
        assert q_attr is not None and r_attr is not None
        key = (int(q_attr), int(r_attr))
        assert key not in by_qr, f"duplicate polygon data-q/r={key!r}"
        by_qr[key] = poly
    assert set(by_qr) == expected_hexes

    # Corners match hex_corners for a single shared size (derived once).
    sample_q, sample_r = next(iter(by_qr))
    sample_pts = _parse_points(by_qr[(sample_q, sample_r)].get("points") or "")
    assert len(sample_pts) == 6
    # Infer size from distance of first corner to center of sample hex's points.
    sx = sum(p[0] for p in sample_pts) / 6
    sy = sum(p[1] for p in sample_pts) / 6
    size = (
        (sample_pts[0][0] - sx) ** 2 + (sample_pts[0][1] - sy) ** 2
    ) ** 0.5
    assert size > 0

    fills_by_terrain: dict[str, set[str]] = {}
    for (q, r), poly in by_qr.items():
        hex_coord = Hex(q, r)
        expected_corners = hex_corners(hex_coord, size)
        actual = _parse_points(poly.get("points") or "")
        assert len(actual) == 6
        for (ax, ay), (ex, ey) in zip(actual, expected_corners, strict=True):
            assert abs(ax - ex) < 1e-6
            assert abs(ay - ey) < 1e-6
        fill = poly.get("fill")
        assert fill is not None and fill != ""
        terrain_name = battle.battlefield.terrain_at(hex_coord).name
        fills_by_terrain.setdefault(terrain_name, set()).add(fill)

    # Fill depends on terrain name: same terrain → same fill; Plains ≠ Forest.
    for terrain_name, fills in fills_by_terrain.items():
        assert len(fills) == 1, f"terrain {terrain_name!r} has mixed fills {fills}"
    assert fills_by_terrain[PLAINS.name] != fills_by_terrain[FOREST.name]

    markers = [
        el
        for el in root.iter()
        if el.get("data-side") is not None
    ]
    assert len(markers) == len(battle.units)

    markers_by_side_hp: dict[tuple[str, str, str], ET.Element] = {}
    for marker in markers:
        side = marker.get("data-side")
        hp = marker.get("data-hp")
        stunned = marker.get("data-stunned")
        assert side in {"attacker", "defender"}
        assert hp is not None and hp.isdigit()
        assert stunned in {"true", "false"}
        markers_by_side_hp[(side, hp, stunned)] = marker

    expected_markers = {
        (
            battle.side_at(pos).value,
            str(battle.current_hp_at(pos)),
            "true" if battle.units[pos].stunned else "false",
        ): pos
        for pos in battle.units
    }
    assert set(markers_by_side_hp) == set(expected_markers)

    for key, pos in expected_markers.items():
        marker = markers_by_side_hp[key]
        mx, my = _marker_center(marker)
        ex, ey = hex_to_pixel(pos, size)
        assert abs(mx - ex) < 1e-6
        assert abs(my - ey) < 1e-6

    again = render_battle_svg(battle)
    assert again == svg
    assert dict(battle.units) == units_before
    assert dict(battle.sides) == sides_before
    assert {pos: battle.current_hp_at(pos) for pos in battle.units} == hp_before
    assert {pos: unit.stunned for pos, unit in battle.units.items()} == stunned_before
