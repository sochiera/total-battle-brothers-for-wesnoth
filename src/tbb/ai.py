"""Pure, deterministic strategic AI queries."""

from collections import deque

import tbb.settlement as settlement_module

from tbb.building import FARM, MARKET, SMITH
from tbb.duchy import Duchy
from tbb.rng import Rng
from tbb.world import Region, WorldMap


def develop_duchy_settlement(world: WorldMap, duchy: Duchy) -> WorldMap:
    """Open one priority building in the first eligible owned settlement."""
    priorities = (FARM, SMITH, MARKET)
    for region in world.regions:
        settlement = world.settlements.get(region)
        if settlement is None or settlement.owner_id != duchy.duchy_id:
            continue

        building = next(
            (
                candidate
                for candidate in priorities
                if candidate not in settlement.active_buildings
            ),
            None,
        )
        if building is None or settlement.free < building.staff:
            continue

        settlements = dict(world.settlements)
        settlements[region] = settlement.open_building(building)
        return WorldMap(
            world.regions,
            world.connections,
            settlements,
            world.parties,
        )
    return world


def recruit_duchy_unit(world: WorldMap, duchy: Duchy) -> WorldMap:
    """Recruit one fresh unit in the first eligible owned settlement."""
    for region in world.regions:
        settlement = world.settlements.get(region)
        if (
            settlement is not None
            and settlement.owner_id == duchy.duchy_id
            and settlement.storage.gold >= settlement_module.RECRUIT_GOLD_COST
            and settlement.free > 0
            and len(settlement.garrison) < 12
        ):
            settlements = dict(world.settlements)
            settlements[region] = settlement.recruit()
            return WorldMap(
                world.regions,
                world.connections,
                settlements,
                world.parties,
            )
    return world


def muster_duchy_party(world: WorldMap, duchy: Duchy) -> WorldMap:
    """Muster a duchy's hero and first available owned settlement garrison."""
    if any(party.owner_id == duchy.duchy_id for party in world.parties.values()):
        return world
    if duchy.hero is None:
        return world

    for region in world.regions:
        settlement = world.settlements.get(region)
        if (
            settlement is not None
            and settlement.owner_id == duchy.duchy_id
            and region not in world.parties
        ):
            return world.muster_party(region, duchy.hero)
    return world


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


def assault_nearest_enemy_settlement(
    world: WorldMap, start: Region, rng: Rng
) -> WorldMap:
    """Resolve an assault when the party's nearest enemy settlement is adjacent."""
    if start not in world.regions:
        raise ValueError("start region is outside the world map")
    party = world.party_at(start)
    if party is None:
        raise ValueError("start region has no party")
    if party.owner_id is None:
        raise ValueError("party must have an explicit owner_id")

    target = nearest_enemy_settlement(world, start, party.owner_id)
    if target is None or target not in world.neighbors(start):
        return world
    return world.resolve_settlement_battle(start, target, rng)


def take_duchy_military_action(
    world: WorldMap, duchy: Duchy, rng: Rng
) -> WorldMap:
    """Muster, march once, and assault for one duchy's military action."""
    if duchy.hero is None:
        return world

    current = muster_duchy_party(world, duchy)
    position = _duchy_party_position(current, duchy.duchy_id)
    if position is None:
        return current
    if nearest_enemy_settlement(current, position, duchy.duchy_id) is None:
        return world

    current = march_toward_nearest_enemy(current, position)
    position = _duchy_party_position(current, duchy.duchy_id)
    if position is None:
        return current
    return assault_nearest_enemy_settlement(current, position, rng)


def take_duchy_turn(world: WorldMap, duchy: Duchy, rng: Rng) -> WorldMap:
    """Develop, recruit once, then perform one duchy's military action."""
    current = develop_duchy_settlement(world, duchy)
    current = recruit_duchy_unit(current, duchy)
    return take_duchy_military_action(current, duchy, rng)


def _duchy_party_position(world: WorldMap, duchy_id: str) -> Region | None:
    return next(
        (
            region
            for region in world.regions
            if (party := world.party_at(region)) is not None
            and party.owner_id == duchy_id
        ),
        None,
    )
