"""Tests for deterministic WorldMap region layout (tbbui presentation layer)."""

from tbb.world import Region, WorldMap
from tbbui.layout import layout_world


def test_layout_world_bfs_columns_unique_positions_two_components_deterministic():
    """Two components; one column with ≥2 regions; distances, no collisions, pure.

    Graph:
      Component rooted at A: A—B, A—C  → A col 0; B and C both col 1 (rows 0,1)
      Component rooted at D: isolated D → second occupant of col 0

    Column counters are global across components, so D gets (0, 1) after A.
    """
    a = Region("A")
    b = Region("B")
    c = Region("C")
    d = Region("D")
    world = WorldMap([a, b, c, d], [(a, b), (a, c)])
    connections_before = world.connections
    regions_before = world.regions

    positions = layout_world(world)

    assert set(positions) == {a, b, c, d}
    assert positions[a] == (0, 0)
    assert positions[b] == (1, 0)
    assert positions[c] == (1, 1)
    assert positions[d] == (0, 1)
    assert len(positions) == len(set(positions.values()))

    # Column 1 has ≥2 regions (B and C); two connected components (A-side, D).
    by_column: dict[int, list[Region]] = {}
    for region, (col, _row) in positions.items():
        by_column.setdefault(col, []).append(region)
    assert len(by_column[1]) >= 2

    again = layout_world(world)
    assert again == positions
    assert world.regions is regions_before
    assert world.connections is connections_before
    assert world.regions == regions_before
    assert world.connections == connections_before
