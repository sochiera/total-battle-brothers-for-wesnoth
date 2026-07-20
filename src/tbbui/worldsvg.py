"""Deterministic SVG skeleton of the strategic WorldMap (nodes + edges + markers)."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from tbb.world import WorldMap
from tbbui.layout import layout_world
from tbbui.palette import NEUTRAL_OWNER_COLOR, owner_palette

# Fixed pixel spacing between adjacent layout columns / rows.
PITCH_X = 100
PITCH_Y = 80
# Padding so node centers are not on the viewBox edge.
ORIGIN_X = 50
ORIGIN_Y = 50
NODE_RADIUS = 12
SETTLEMENT_MARKER_RADIUS = 6
PARTY_MARKER_RADIUS = 5


def _node_center(col: int, row: int) -> tuple[int, int]:
    """Pixel center of a layout cell (same basis as region node groups)."""
    return ORIGIN_X + col * PITCH_X, ORIGIN_Y + row * PITCH_Y


def _owner_attr(owner_id: str | None) -> str:
    """SVG ``data-owner`` value: explicit id or empty string when unowned."""
    return owner_id if owner_id is not None else ""


def _marker_fill(owner_id: str | None, palette: dict[str, str]) -> str:
    """Fill color for a settlement/party marker from the owner palette."""
    if owner_id is None:
        return NEUTRAL_OWNER_COLOR
    return palette[owner_id]


def render_world_svg(world: WorldMap) -> str:
    """Return a parsable SVG string with connection lines, labelled nodes, markers.

    One ``<line>`` per ``world.connections`` entry (same order), with
    ``data-from`` / ``data-to`` and endpoints at the region node centers.
    Node centers are an affine map of ``layout_world`` cells:
    ``x = ORIGIN_X + col * PITCH_X``, ``y = ORIGIN_Y + row * PITCH_Y``.
    Occupied regions get settlement / party markers (``data-settlement`` /
    ``data-party`` plus ``data-owner``) at the same node center; ``fill`` comes
    from ``owner_palette`` (or ``NEUTRAL_OWNER_COLOR`` when unowned).
    Pure and deterministic: no RNG, input map is not mutated.
    """
    positions = layout_world(world)
    palette = owner_palette(world)

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

    # Edges under nodes so region markers paint on top.
    for from_region, to_region in world.connections:
        x1, y1 = _node_center(*positions[from_region])
        x2, y2 = _node_center(*positions[to_region])
        ET.SubElement(
            svg,
            "line",
            {
                "x1": str(x1),
                "y1": str(y1),
                "x2": str(x2),
                "y2": str(y2),
                "data-from": from_region.name,
                "data-to": to_region.name,
                "stroke": "#666666",
                "stroke-width": "2",
            },
        )

    for region in world.regions:
        col, row = positions[region]
        x, y = _node_center(col, row)
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

        settlement = world.settlement_at(region)
        if settlement is not None:
            ET.SubElement(
                group,
                "circle",
                {
                    "cx": "0",
                    "cy": "0",
                    "r": str(SETTLEMENT_MARKER_RADIUS),
                    "data-settlement": region.name,
                    "data-owner": _owner_attr(settlement.owner_id),
                    "fill": _marker_fill(settlement.owner_id, palette),
                    "stroke": "#222222",
                },
            )

        party = world.party_at(region)
        if party is not None:
            ET.SubElement(
                group,
                "circle",
                {
                    "cx": "0",
                    "cy": "0",
                    "r": str(PARTY_MARKER_RADIUS),
                    "data-party": region.name,
                    "data-owner": _owner_attr(party.owner_id),
                    "fill": _marker_fill(party.owner_id, palette),
                    "stroke": "#222222",
                },
            )

    return ET.tostring(svg, encoding="unicode")
