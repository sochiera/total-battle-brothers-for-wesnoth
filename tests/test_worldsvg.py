"""Tests for deterministic WorldMap SVG skeleton (tbbui presentation layer)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from itertools import combinations

from tbb.party import Party
from tbb.settlement import Settlement
from tbb.unit import Unit
from tbb.world import Region, WorldMap
from tbbui.layout import layout_world
from tbbui.worldsvg import render_world_svg


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _group_center(group: ET.Element) -> tuple[float, float]:
    """Resolve a region node's center from transform, circle, or text attrs."""
    transform = group.get("transform") or ""
    match = re.search(
        r"translate\(\s*([-\d.]+)[,\s]+([-\d.]+)\s*\)",
        transform,
    )
    if match:
        return float(match.group(1)), float(match.group(2))

    for child in group.iter():
        if _local(child.tag) == "circle" and child.get("cx") is not None:
            return float(child.get("cx")), float(child.get("cy", "0"))

    for child in group.iter():
        if _local(child.tag) == "text" and child.get("x") is not None:
            return float(child.get("x")), float(child.get("y", "0"))

    raise AssertionError(
        f"region group {group.get('data-region')!r} has no discoverable center"
    )


def test_render_world_svg_skeleton_nodes_unique_deterministic():
    """≥2 regions: parsable <svg>, one data-region group each, layout centers, pure.

    Graph: A—B, A—C plus isolated D (same fixture shape as layout tests).
    """
    a = Region("A")
    b = Region("B")
    c = Region("C")
    d = Region("D")
    world = WorldMap([a, b, c, d], [(a, b), (a, c)])
    connections_before = world.connections
    regions_before = world.regions
    layout = layout_world(world)

    svg = render_world_svg(world)

    root = ET.fromstring(svg)
    assert _local(root.tag) == "svg"

    groups_by_name: dict[str, ET.Element] = {}
    for element in root.iter():
        if _local(element.tag) != "g":
            continue
        name = element.get("data-region")
        if name is None:
            continue
        assert name not in groups_by_name, f"duplicate data-region={name!r}"
        groups_by_name[name] = element

    assert set(groups_by_name) == {region.name for region in world.regions}

    centers: dict[Region, tuple[float, float]] = {}
    for region in world.regions:
        group = groups_by_name[region.name]
        texts = [
            (child.text or "")
            for child in group.iter()
            if _local(child.tag) == "text"
        ]
        assert any(region.name in text for text in texts), (
            f"group data-region={region.name!r} missing text with region name"
        )
        centers[region] = _group_center(group)

    assert len(set(centers.values())) == len(centers)

    # Centers must be an affine map of layout (col,row) with constant spacing.
    # For every pair: Δx / Δcol and Δy / Δrow (when non-zero) share one pitch.
    sample = next(iter(world.regions))
    ox, oy = centers[sample]
    col0, row0 = layout[sample]
    pitch_x: float | None = None
    pitch_y: float | None = None
    for region in world.regions:
        col, row = layout[region]
        x, y = centers[region]
        dcol = col - col0
        drow = row - row0
        if dcol != 0:
            px = (x - ox) / dcol
            if pitch_x is None:
                pitch_x = px
            else:
                assert abs(px - pitch_x) < 1e-9
        if drow != 0:
            py = (y - oy) / drow
            if pitch_y is None:
                pitch_y = py
            else:
                assert abs(py - pitch_y) < 1e-9
        expected_x = ox + dcol * (pitch_x if dcol != 0 and pitch_x is not None else 0.0)
        expected_y = oy + drow * (pitch_y if drow != 0 and pitch_y is not None else 0.0)
        if pitch_x is not None and pitch_y is not None:
            assert abs(x - expected_x) < 1e-9
            assert abs(y - expected_y) < 1e-9
    assert pitch_x is not None and pitch_x != 0.0
    assert pitch_y is not None and pitch_y != 0.0

    # Extra pairwise check: distinct layout cells never collapse to same center.
    for r1, r2 in combinations(world.regions, 2):
        assert centers[r1] != centers[r2]
        assert layout[r1] != layout[r2]

    again = render_world_svg(world)
    assert again == svg
    assert world.regions is regions_before
    assert world.connections is connections_before
    assert world.regions == regions_before
    assert world.connections == connections_before


def test_render_world_svg_connection_lines_match_node_centers():
    """≥2 connections: one <line> each, data-from/to, ends at node centers, pure.

    Graph: A—B, A—C (order of world.connections preserved in SVG).
    Nodes from V13.2a remain present and labelled; input map is not mutated.
    """
    a = Region("A")
    b = Region("B")
    c = Region("C")
    world = WorldMap([a, b, c], [(a, b), (a, c)])
    connections_before = world.connections
    regions_before = world.regions

    svg = render_world_svg(world)

    root = ET.fromstring(svg)
    assert _local(root.tag) == "svg"

    groups_by_name: dict[str, ET.Element] = {}
    for element in root.iter():
        if _local(element.tag) != "g":
            continue
        name = element.get("data-region")
        if name is None:
            continue
        assert name not in groups_by_name, f"duplicate data-region={name!r}"
        groups_by_name[name] = element

    assert set(groups_by_name) == {region.name for region in world.regions}
    centers: dict[str, tuple[float, float]] = {}
    for region in world.regions:
        group = groups_by_name[region.name]
        texts = [
            (child.text or "")
            for child in group.iter()
            if _local(child.tag) == "text"
        ]
        assert any(region.name in text for text in texts), (
            f"group data-region={region.name!r} missing text with region name"
        )
        centers[region.name] = _group_center(group)

    lines = [el for el in root.iter() if _local(el.tag) == "line"]
    assert len(lines) == len(world.connections)
    assert len(world.connections) >= 2

    for line, (from_region, to_region) in zip(lines, world.connections, strict=True):
        assert line.get("data-from") == from_region.name
        assert line.get("data-to") == to_region.name
        x1 = float(line.get("x1"))
        y1 = float(line.get("y1"))
        x2 = float(line.get("x2"))
        y2 = float(line.get("y2"))
        fx, fy = centers[from_region.name]
        tx, ty = centers[to_region.name]
        assert abs(x1 - fx) < 1e-9
        assert abs(y1 - fy) < 1e-9
        assert abs(x2 - tx) < 1e-9
        assert abs(y2 - ty) < 1e-9

    again = render_world_svg(world)
    assert again == svg
    assert world.regions is regions_before
    assert world.connections is connections_before
    assert world.regions == regions_before
    assert world.connections == connections_before


def _marker_center(element: ET.Element) -> tuple[float, float]:
    """Resolve a marker's base position from transform, circle, or x/y attrs."""
    transform = element.get("transform") or ""
    match = re.search(
        r"translate\(\s*([-\d.]+)[,\s]+([-\d.]+)\s*\)",
        transform,
    )
    if match:
        return float(match.group(1)), float(match.group(2))

    if element.get("cx") is not None:
        return float(element.get("cx")), float(element.get("cy", "0"))

    if element.get("x") is not None:
        return float(element.get("x")), float(element.get("y", "0"))

    for child in element:
        if _local(child.tag) == "circle" and child.get("cx") is not None:
            return float(child.get("cx")), float(child.get("cy", "0"))
        if child.get("x") is not None:
            return float(child.get("x")), float(child.get("y", "0"))

    raise AssertionError(
        f"marker {_local(element.tag)} has no discoverable center "
        f"(attrs={element.attrib!r})"
    )


def test_render_world_svg_settlement_and_party_markers():
    """Settlement/party markers: data-*, owners, node centers, empty region, pure.

    Map: A has settlement owner_id='north', B has party owner_id='south',
    C is empty (no settlement, no party). Nodes (066) and lines (067) remain.
    """
    a = Region("A")
    b = Region("B")
    c = Region("C")
    settlement = Settlement("Keep A", population=1, owner_id="north")
    party = Party(Unit(), owner_id="south")
    world = WorldMap(
        [a, b, c],
        [(a, b), (a, c)],
        settlements={a: settlement},
        parties={b: party},
    )
    connections_before = world.connections
    regions_before = world.regions
    settlements_before = world.settlements
    parties_before = world.parties

    svg = render_world_svg(world)

    root = ET.fromstring(svg)
    assert _local(root.tag) == "svg"

    # Region nodes (066) still present and unique.
    groups_by_name: dict[str, ET.Element] = {}
    for element in root.iter():
        if _local(element.tag) != "g":
            continue
        name = element.get("data-region")
        if name is None:
            continue
        assert name not in groups_by_name, f"duplicate data-region={name!r}"
        groups_by_name[name] = element
    assert set(groups_by_name) == {region.name for region in world.regions}
    centers: dict[str, tuple[float, float]] = {
        name: _group_center(group) for name, group in groups_by_name.items()
    }

    # Connection lines (067) still present and endpoint-correct.
    lines = [el for el in root.iter() if _local(el.tag) == "line"]
    assert len(lines) == len(world.connections)
    for line, (from_region, to_region) in zip(lines, world.connections, strict=True):
        assert line.get("data-from") == from_region.name
        assert line.get("data-to") == to_region.name
        assert abs(float(line.get("x1")) - centers[from_region.name][0]) < 1e-9
        assert abs(float(line.get("y1")) - centers[from_region.name][1]) < 1e-9
        assert abs(float(line.get("x2")) - centers[to_region.name][0]) < 1e-9
        assert abs(float(line.get("y2")) - centers[to_region.name][1]) < 1e-9

    # Exactly one settlement marker for A; none for B/C.
    settlement_markers = [
        el for el in root.iter() if el.get("data-settlement") is not None
    ]
    assert len(settlement_markers) == 1
    s_marker = settlement_markers[0]
    assert s_marker.get("data-settlement") == a.name
    assert s_marker.get("data-owner") == "north"
    sx, sy = _marker_center(s_marker)
    # Marker base coords match region node center (or relative 0,0 inside its group).
    ax, ay = centers[a.name]
    if abs(sx) < 1e-9 and abs(sy) < 1e-9:
        # Relative to containing region group — must sit under data-region=A.
        ancestor_regions = [
            el.get("data-region")
            for el in root.iter()
            if _local(el.tag) == "g"
            and el.get("data-region") is not None
            and any(child is s_marker or s_marker in child.iter() for child in [el])
        ]
        assert a.name in ancestor_regions
    else:
        assert abs(sx - ax) < 1e-9
        assert abs(sy - ay) < 1e-9

    # Exactly one party marker for B; none for A/C.
    party_markers = [
        el for el in root.iter() if el.get("data-party") is not None
    ]
    assert len(party_markers) == 1
    p_marker = party_markers[0]
    assert p_marker.get("data-party") == b.name
    assert p_marker.get("data-owner") == "south"
    px, py = _marker_center(p_marker)
    bx, by = centers[b.name]
    if abs(px) < 1e-9 and abs(py) < 1e-9:
        ancestor_regions = [
            el.get("data-region")
            for el in root.iter()
            if _local(el.tag) == "g"
            and el.get("data-region") is not None
            and any(child is p_marker or p_marker in child.iter() for child in [el])
        ]
        assert b.name in ancestor_regions
    else:
        assert abs(px - bx) < 1e-9
        assert abs(py - by) < 1e-9

    # Empty region C: no settlement or party marker keyed to C.
    assert not any(el.get("data-settlement") == c.name for el in root.iter())
    assert not any(el.get("data-party") == c.name for el in root.iter())

    again = render_world_svg(world)
    assert again == svg
    assert world.regions is regions_before
    assert world.connections is connections_before
    assert world.settlements is settlements_before
    assert world.parties is parties_before
    assert world.regions == regions_before
    assert world.connections == connections_before


def test_render_world_svg_owner_fill_same_and_distinct():
    """Markers: same owner_id → identical fill; different owners → different fill.

    Fixture: A settlement+party both 'north', B settlement 'south', C unowned
    settlement. Also checks neutral fill for None and SVG determinism.
    """
    from tbbui.palette import NEUTRAL_OWNER_COLOR, owner_palette

    a = Region("A")
    b = Region("B")
    c = Region("C")
    world = WorldMap(
        [a, b, c],
        [(a, b), (b, c)],
        settlements={
            a: Settlement("Keep A", population=1, owner_id="north"),
            b: Settlement("Keep B", population=1, owner_id="south"),
            c: Settlement("Keep C", population=1, owner_id=None),
        },
        parties={
            a: Party(Unit(), owner_id="north"),
        },
    )
    palette = owner_palette(world)
    assert "north" in palette and "south" in palette
    assert palette["north"] != palette["south"]

    svg = render_world_svg(world)
    root = ET.fromstring(svg)
    assert _local(root.tag) == "svg"

    def _markers_with(attr: str, region_name: str) -> list[ET.Element]:
        return [
            el
            for el in root.iter()
            if el.get(attr) == region_name
        ]

    a_settlement = _markers_with("data-settlement", a.name)
    a_party = _markers_with("data-party", a.name)
    b_settlement = _markers_with("data-settlement", b.name)
    c_settlement = _markers_with("data-settlement", c.name)
    assert len(a_settlement) == 1 and len(a_party) == 1
    assert len(b_settlement) == 1 and len(c_settlement) == 1

    fill_a_s = a_settlement[0].get("fill")
    fill_a_p = a_party[0].get("fill")
    fill_b = b_settlement[0].get("fill")
    fill_c = c_settlement[0].get("fill")

    # Same faction markers share fill; different factions differ.
    assert fill_a_s == fill_a_p == palette["north"]
    assert fill_b == palette["south"]
    assert fill_a_s != fill_b
    # Unowned marker uses neutral fill (not an owner palette entry).
    assert fill_c == NEUTRAL_OWNER_COLOR
    assert fill_c not in (fill_a_s, fill_b)

    again = render_world_svg(world)
    assert again == svg
