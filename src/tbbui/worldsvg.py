"""Deterministic SVG skeleton of the strategic WorldMap (region nodes)."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from tbb.world import WorldMap
from tbbui.layout import layout_world

# Fixed pixel spacing between adjacent layout columns / rows.
PITCH_X = 100
PITCH_Y = 80
# Padding so node centers are not on the viewBox edge.
ORIGIN_X = 50
ORIGIN_Y = 50
NODE_RADIUS = 12


def render_world_svg(world: WorldMap) -> str:
    """Return a parsable SVG string with one labelled node per region.

    Node centers are an affine map of ``layout_world`` cells:
    ``x = ORIGIN_X + col * PITCH_X``, ``y = ORIGIN_Y + row * PITCH_Y``.
    Pure and deterministic: no RNG, input map is not mutated.
    """
    positions = layout_world(world)

    max_col = 0
    max_row = 0
    for col, row in positions.values():
        if col > max_col:
            max_col = col
        if row > max_row:
            max_row = row

    width = ORIGIN_X * 2 + max_col * PITCH_X
    height = ORIGIN_Y * 2 + max_row * PITCH_Y
    # Ensure non-zero canvas even for a single cell.
    if width < ORIGIN_X * 2:
        width = ORIGIN_X * 2
    if height < ORIGIN_Y * 2:
        height = ORIGIN_Y * 2

    svg = ET.Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "width": str(width),
            "height": str(height),
            "viewBox": f"0 0 {width} {height}",
        },
    )

    for region in world.regions:
        col, row = positions[region]
        x = ORIGIN_X + col * PITCH_X
        y = ORIGIN_Y + row * PITCH_Y
        group = ET.SubElement(
            svg,
            "g",
            {
                "data-region": region.name,
                "transform": f"translate({x}, {y})",
            },
        )
        ET.SubElement(
            group,
            "circle",
            {
                "cx": "0",
                "cy": "0",
                "r": str(NODE_RADIUS),
                "fill": "#cccccc",
                "stroke": "#333333",
            },
        )
        text = ET.SubElement(
            group,
            "text",
            {
                "x": "0",
                "y": str(NODE_RADIUS + 14),
                "text-anchor": "middle",
                "font-size": "12",
            },
        )
        text.text = region.name

    return ET.tostring(svg, encoding="unicode")
