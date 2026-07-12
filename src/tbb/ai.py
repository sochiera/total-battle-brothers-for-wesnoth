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


def next_march_step(
    world: WorldMap, start: Region, target: Region
) -> Region | None:
    """Return the first free step on a shortest route beside ``target``."""
    if start not in world.regions or target not in world.regions:
        raise ValueError("start and target regions must belong to the world map")
    if start == target or target in world.neighbors(start):
        return None

    pending = deque([(start, None)])
    visited = {start}
    while pending:
        current, first_step = pending.popleft()
        for neighbor in world.neighbors(current):
            if neighbor == target:
                return first_step
            if neighbor in visited or neighbor in world.parties:
                continue
            visited.add(neighbor)
            pending.append((neighbor, neighbor if first_step is None else first_step))
    return None


def march_toward_nearest_enemy(world: WorldMap, start: Region) -> WorldMap:
    """Move the party at ``start`` one step toward its nearest enemy settlement."""
    if start not in world.regions:
        raise ValueError("start region is outside the world map")
    party = world.party_at(start)
    if party is None:
        raise ValueError("start region has no party")
    if party.owner_id is None:
        raise ValueError("party must have an explicit owner_id")

    target = nearest_enemy_settlement(world, start, party.owner_id)
    if target is None:
        return world
    step = next_march_step(world, start, target)
    if step is None:
        return world
    return world.move_party(start, step, 1)
