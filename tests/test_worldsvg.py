"""Tests for deterministic WorldMap SVG skeleton (tbbui presentation layer)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from itertools import combinations

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
