"""Pure, deterministic strategic AI queries."""

from collections import deque

from tbb.world import Region, WorldMap


def nearest_enemy_settlement(
    world: WorldMap, start: Region, owner_id: str
) -> Region | None:
    """Return the nearest reachable enemy settlement region."""
    if not isinstance(owner_id, str):
        raise TypeError("owner_id must be text")
    if owner_id == "":
        raise ValueError("owner_id cannot be empty")
    if start not in world.regions:
        raise ValueError("start region is outside the world map")

    distances = {start: 0}
    pending = deque([start])
    while pending:
        current = pending.popleft()
        for neighbor in world.neighbors(current):
            if neighbor not in distances:
                distances[neighbor] = distances[current] + 1
                pending.append(neighbor)

    best: Region | None = None
    best_distance: int | None = None
    for region in world.regions:
        settlement = world.settlements.get(region)
        if (
            region not in distances
            or settlement is None
            or settlement.owner_id is None
            or settlement.owner_id == owner_id
        ):
            continue
        distance = distances[region]
        if best_distance is None or distance < best_distance:
            best = region
            best_distance = distance
    return best
