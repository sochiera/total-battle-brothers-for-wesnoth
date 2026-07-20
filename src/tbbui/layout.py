"""Deterministic 2D layout of WorldMap regions for strategic map rendering."""

from __future__ import annotations

from tbb.world import Region, WorldMap


def layout_world(world: WorldMap) -> dict[Region, tuple[int, int]]:
    """Place every region on an integer grid without overlapping positions.

    Connected components are visited in ``world.regions`` order. Within a
    component, BFS runs from the first unplaced region (component root):
    column is graph distance from that root; within each BFS layer, regions
    are ordered by ``world.regions``. Row is the next free index in that
    column (column counters are global across components).
    """
    region_index = {region: index for index, region in enumerate(world.regions)}
    positions: dict[Region, tuple[int, int]] = {}
    placed: set[Region] = set()
    next_row: dict[int, int] = {}

    for root in world.regions:
        if root in placed:
            continue

        layer = [root]
        placed.add(root)
        distance = 0

        while layer:
            layer.sort(key=region_index.__getitem__)
            for region in layer:
                column = distance
                row = next_row.get(column, 0)
                next_row[column] = row + 1
                positions[region] = (column, row)

            next_layer: list[Region] = []
            next_seen: set[Region] = set()
            for region in layer:
                for neighbor in world.neighbors(region):
                    if neighbor not in placed and neighbor not in next_seen:
                        next_seen.add(neighbor)
                        next_layer.append(neighbor)
            placed.update(next_layer)
            layer = next_layer
            distance += 1

    return positions
