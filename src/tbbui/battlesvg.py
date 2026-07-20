"""Deterministic SVG render of a hex-battle field (terrain + unit markers)."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from tbb.battle import HexBattle
from tbb.hex import Hex
from tbbui.hexgeom import hex_corners, hex_to_pixel

# Outer radius of each hex in SVG units (shared by hex_to_pixel / hex_corners).
HEX_SIZE = 20.0
# Padding around the farthest hex corners so polygons are not clipped.
VIEW_PAD = 8.0
UNIT_MARKER_RADIUS = 6.0

# Fill per terrain name (distinct colors; unknown names share a default).
TERRAIN_FILL: dict[str, str] = {
    "Plains": "#c8b560",
    "Forest": "#2f6b2f",
    "Hills": "#8b7355",
}
DEFAULT_TERRAIN_FILL = "#9a9a9a"

# Side marker colors (purely cosmetic; tests key off data-* attrs).
SIDE_FILL = {
    "attacker": "#c04040",
    "defender": "#4060c0",
}


def _terrain_fill(terrain_name: str) -> str:
    return TERRAIN_FILL.get(terrain_name, DEFAULT_TERRAIN_FILL)


def _points_attr(corners: tuple[tuple[float, float], ...]) -> str:
    return " ".join(f"{x},{y}" for x, y in corners)


def _occupied_bbox(units: dict[Hex, object]) -> tuple[int, int, int, int] | None:
    """Return (q_min, q_max, r_min, r_max) for occupied hexes expanded by ±1."""
    if not units:
        return None
    qs = [h.q for h in units]
    rs = [h.r for h in units]
    return min(qs) - 1, max(qs) + 1, min(rs) - 1, max(rs) + 1


def render_battle_svg(battle: HexBattle) -> str:
    """Return a parsable SVG string of the battle field (hexes + unit markers).

    Renders every axial hex in the axis-aligned bounding box of occupied
    positions expanded by ±1 in ``q`` and ``r``. Each hex is a ``<polygon>``
    with ``data-q`` / ``data-r`` and ``fill`` from terrain name. One unit
    marker per occupied hex carries ``data-side``, ``data-hp``, and
    ``data-stunned`` at the hex pixel center.

    Pure and deterministic: no RNG/IO; ``battle`` is not mutated.
    """
    bbox = _occupied_bbox(battle.units)
    size = HEX_SIZE

    min_x = 0.0
    min_y = 0.0
    max_x = 0.0
    max_y = 0.0
    first_corner = True

    hexes: list[Hex] = []
    if bbox is not None:
        q_min, q_max, r_min, r_max = bbox
        for q in range(q_min, q_max + 1):
            for r in range(r_min, r_max + 1):
                hexes.append(Hex(q, r))
        for hex_coord in hexes:
            for x, y in hex_corners(hex_coord, size):
                if first_corner:
                    min_x = max_x = x
                    min_y = max_y = y
                    first_corner = False
                else:
                    if x < min_x:
                        min_x = x
                    if x > max_x:
                        max_x = x
                    if y < min_y:
                        min_y = y
                    if y > max_y:
                        max_y = y

    if first_corner:
        # Empty deployment: minimal canvas.
        width = VIEW_PAD * 2
        height = VIEW_PAD * 2
        origin_x = 0.0
        origin_y = 0.0
    else:
        origin_x = min_x - VIEW_PAD
        origin_y = min_y - VIEW_PAD
        width = (max_x - min_x) + VIEW_PAD * 2
        height = (max_y - min_y) + VIEW_PAD * 2

    svg = ET.Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "width": str(width),
            "height": str(height),
            "viewBox": f"{origin_x} {origin_y} {width} {height}",
        },
    )

    for hex_coord in hexes:
        corners = hex_corners(hex_coord, size)
        terrain_name = battle.battlefield.terrain_at(hex_coord).name
        ET.SubElement(
            svg,
            "polygon",
            {
                "points": _points_attr(corners),
                "data-q": str(hex_coord.q),
                "data-r": str(hex_coord.r),
                "fill": _terrain_fill(terrain_name),
                "stroke": "#333333",
                "stroke-width": "1",
            },
        )

    # Markers on top of terrain; stable order over occupied positions.
    for position in sorted(battle.units, key=lambda h: (h.q, h.r)):
        unit = battle.units[position]
        side = battle.side_at(position)
        cx, cy = hex_to_pixel(position, size)
        ET.SubElement(
            svg,
            "circle",
            {
                "cx": str(cx),
                "cy": str(cy),
                "r": str(UNIT_MARKER_RADIUS),
                "data-side": side.value,
                "data-hp": str(battle.current_hp_at(position)),
                "data-stunned": "true" if unit.stunned else "false",
                "fill": SIDE_FILL.get(side.value, "#888888"),
                "stroke": "#111111",
                "stroke-width": "1",
            },
        )

    return ET.tostring(svg, encoding="unicode")
