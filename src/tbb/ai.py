"""Pure, deterministic strategic AI queries."""

from collections import deque
from collections.abc import Iterable

import tbb.settlement as settlement_module

from tbb.battle import HexBattle
from tbb.building import BARRACKS, FARM, MARKET, SMITH
from tbb.duchy import Duchy
from tbb.party import Party
from tbb.rng import Rng
from tbb.unit import Unit
from tbb.world import Region, WorldMap


_DEVELOPMENT_PRIORITIES = (FARM, SMITH, BARRACKS, MARKET)
_MINIMUM_ASSAULT_STRENGTH_RATIO = 2


def _combat_strength(units: Iterable[Unit]) -> int:
    """Return the deterministic strategic strength of a unit collection."""
    return sum(unit.hp + unit.damage + unit.defense for unit in units)


def develop_duchy_settlement(world: WorldMap, duchy: Duchy) -> WorldMap:
    """Open one priority building in the first eligible owned settlement."""
    for region in world.regions:
        settlement = world.settlements.get(region)
        if settlement is None or settlement.owner_id != duchy.duchy_id:
            continue

        building = next(
            (
                candidate
                for candidate in _DEVELOPMENT_PRIORITIES
                if candidate not in settlement.active_buildings
            ),
            None,
        )
        if building is None or settlement.free < building.staff:
            continue

        return world.with_settlement(region, settlement.open_building(building))
    return world


def raise_duchy_hero(world: WorldMap, duchy: Duchy) -> tuple[WorldMap, Duchy]:
    """Raise a hero for a heroless duchy from its first eligible owned settlement."""
    if duchy.has_hero:
        return world, duchy

    for region in world.regions:
        settlement = world.settlements.get(region)
        if (
            settlement is None
            or settlement.owner_id != duchy.duchy_id
            or settlement.free < 1
            or settlement.storage.gold < settlement_module.HERO_GOLD_COST
        ):
            continue

        raised, hero = settlement.raise_hero()
        return world.with_settlement(region, raised), Duchy(
            duchy_id=duchy.duchy_id,
            hero=hero,
            morale=duchy.morale,
            heir=duchy.heir,
            settlements=duchy.settlements,
            parties=duchy.parties,
        )
    return world, duchy


def designate_duchy_heir(world: WorldMap, duchy: Duchy) -> tuple[WorldMap, Duchy]:
    """Designate an heir for a duchy that has a hero but no heir yet."""
    if not duchy.has_hero or duchy.heir is not None:
        return world, duchy

    for region in world.regions:
        settlement = world.settlements.get(region)
        if (
            settlement is None
            or settlement.owner_id != duchy.duchy_id
            or settlement.free < 1
            or settlement.storage.gold < settlement_module.HERO_GOLD_COST
        ):
            continue

        raised, heir = settlement.raise_hero()
        return world.with_settlement(region, raised), Duchy(
            duchy_id=duchy.duchy_id,
            hero=duchy.hero,
            morale=duchy.morale,
            heir=heir,
            settlements=duchy.settlements,
            parties=duchy.parties,
        )
    return world, duchy


def _region_distances(world: WorldMap, start: Region) -> dict[Region, int]:
    distances = {start: 0}
    pending = deque([start])
    while pending:
        current = pending.popleft()
        for neighbor in world.neighbors(current):
            if neighbor not in distances:
                distances[neighbor] = distances[current] + 1
                pending.append(neighbor)
    return distances


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
            return world.with_settlement(region, settlement.recruit())
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


def reinforce_duchy_party(world: WorldMap, duchy: Duchy) -> WorldMap:
    """Reinforce a duchy's party from the settlement where it is standing."""
    position = _duchy_party_position(world, duchy.duchy_id)
    if position is None:
        return world
    return world.reinforce_party(position)


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

    distances = _region_distances(world, start)

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


def region_distance(
    world: WorldMap, start: Region, target: Region
) -> int | None:
    """Return BFS edge distance between regions; ignore party occupancy."""
    if start not in world.regions or target not in world.regions:
        raise ValueError("start and target regions must belong to the world map")
    if start == target:
        return 0

    return _region_distances(world, start).get(target)


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


def _is_foreign_party(party: Party, owner_id: str) -> bool:
    return party.owner_id != owner_id


def _foreign_party_regions_on_shortest_routes(
    world: WorldMap,
    start: Region,
    owner_id: str,
    destination: Region,
) -> tuple[Region, ...]:
    distances_from_start = _region_distances(world, start)
    shortest_distance = distances_from_start.get(destination)
    if shortest_distance is None:
        return ()

    distances_to_destination = _region_distances(world, destination)
    return tuple(
        region
        for region in world.regions
        if (
            region != start
            and region != destination
            and (party := world.parties.get(region)) is not None
            and _is_foreign_party(party, owner_id)
            and distances_from_start.get(region) is not None
            and distances_to_destination.get(region) is not None
            and distances_from_start[region]
            + distances_to_destination[region]
            == shortest_distance
        )
    )


def _world_without_party(world: WorldMap, region: Region) -> WorldMap:
    parties = dict(world.parties)
    del parties[region]
    return WorldMap(world.regions, world.connections, world.settlements, parties)


def blocking_foreign_party_region(
    world: WorldMap,
    start: Region,
    owner_id: str,
    target: Region | None = None,
) -> Region | None:
    """Return the foreign party region blocking a march route, if any.

    The query follows the same route and occupancy semantics as
    :func:`next_march_step`, but reports a foreign occupied region when that
    occupancy is the only reason no step is available.
    """
    if not isinstance(owner_id, str):
        raise TypeError("owner_id must be text")
    if owner_id == "":
        raise ValueError("owner_id cannot be empty")
    if start not in world.regions:
        raise ValueError("start region is outside the world map")
    if target is not None and target not in world.regions:
        raise ValueError("target region is outside the world map")

    explicit_target = target is not None
    destination = (
        target
        if explicit_target
        else nearest_enemy_settlement(world, start, owner_id)
    )
    if destination is None or destination == start:
        return None
    if destination in world.neighbors(start):
        party = world.parties.get(destination)
        if (
            explicit_target
            and party is not None
            and _is_foreign_party(party, owner_id)
        ):
            return destination
        return None
    if next_march_step(world, start, destination) is not None:
        return None

    candidates = _foreign_party_regions_on_shortest_routes(
        world, start, owner_id, destination
    )
    # Explicit adjacent targets are handled above; after removing a candidate,
    # verify that no second foreign blocker still prevents the route.
    for candidate in candidates:
        candidate_removed = _world_without_party(world, candidate)
        if next_march_step(candidate_removed, start, destination) is None:
            continue
        if not _foreign_party_regions_on_shortest_routes(
            candidate_removed, start, owner_id, destination
        ):
            return candidate
    return None


def _move_party_one_step(
    world: WorldMap, source: Region, destination: Region
) -> WorldMap:
    return world.move_party(source, destination, 1)


def _can_enter_adjacent_region(
    world: WorldMap, source: Region, target: Region, owner_id: str
) -> bool:
    if target not in world.neighbors(source) or target in world.parties:
        return False
    settlement = world.settlement_at(target)
    return settlement is None or settlement.owner_id == owner_id


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
    return _move_party_one_step(world, start, step)


def march_duchy_party(world: WorldMap, duchy: Duchy) -> WorldMap:
    """March the duchy's party one step toward its nearest enemy settlement."""
    position = _duchy_party_position(world, duchy.duchy_id)
    if position is None:
        return world
    return march_toward_nearest_enemy(world, position)


def march_duchy_party_to(
    world: WorldMap, duchy: Duchy, target: Region
) -> WorldMap:
    """March the duchy's party one step toward an explicit target region."""
    position = _duchy_party_position(world, duchy.duchy_id)
    if position is None:
        return world
    step = next_march_step(world, position, target)
    if step is None:
        return world
    return _move_party_one_step(world, position, step)


def move_duchy_party_to_adjacent(
    world: WorldMap, duchy: Duchy, target: Region
) -> WorldMap:
    """Move one step to an adjacent empty region or one with the duchy's settlement."""
    position = _duchy_party_position(world, duchy.duchy_id)
    if position is None:
        return world
    if not _can_enter_adjacent_region(world, position, target, duchy.duchy_id):
        return world
    return _move_party_one_step(world, position, target)


def assault_duchy_party(
    world: WorldMap,
    duchy: Duchy,
    rng: Rng,
    morale_by_owner: dict[str, int] | None = None,
) -> WorldMap:
    """Assault the nearest enemy settlement from the duchy's party position."""
    position = _duchy_party_position(world, duchy.duchy_id)
    if position is None:
        return world
    return assault_nearest_enemy_settlement(
        world, position, rng, morale_by_owner=morale_by_owner
    )


def assault_duchy_party_recorded(
    world: WorldMap,
    duchy: Duchy,
    rng: Rng,
    morale_by_owner: dict[str, int] | None = None,
) -> tuple[WorldMap, HexBattle | None]:
    """Assault nearest adjacent enemy settlement; return map and battle.

    No-op paths return ``(world, None)`` without consuming RNG. On a hit the
    map matches ``assault_duchy_party`` for the same inputs.
    """
    position = _duchy_party_position(world, duchy.duchy_id)
    if position is None:
        return world, None
    party = world.party_at(position)
    if party is None:
        return world, None
    if party.owner_id is None:
        raise ValueError("party must have an explicit owner_id")

    target = nearest_enemy_settlement(world, position, party.owner_id)
    if target is None or not _is_legal_assault_target(world, position, target):
        return world, None

    attacker_morale = 0
    defender_morale = 0
    if morale_by_owner is not None:
        settlement = world.settlement_at(target)
        attacker_morale = morale_by_owner.get(party.owner_id, 0)
        defender_morale = morale_by_owner.get(settlement.owner_id, 0)
    return _resolve_settlement_assault(
        world,
        position,
        target,
        rng,
        recorded=True,
        attacker_morale=attacker_morale,
        defender_morale=defender_morale,
    )


def engage_duchy_party_recorded(
    world: WorldMap,
    duchy: Duchy,
    rng: Rng,
    morale_by_owner: dict[str, int] | None = None,
) -> tuple[WorldMap, HexBattle | None]:
    """Engage the first adjacent enemy party; return map and battle.

    Target is the first neighbor (in ``world.neighbors`` order) that holds a
    party with a different explicit ``owner_id``. No-op paths return
    ``(world, None)`` without consuming RNG.
    """
    position = _duchy_party_position(world, duchy.duchy_id)
    if position is None:
        return world, None
    party = world.party_at(position)
    if party is None:
        return world, None
    if party.owner_id is None:
        raise ValueError("party must have an explicit owner_id")

    target = None
    for neighbor in world.neighbors(position):
        other = world.party_at(neighbor)
        if (
            other is not None
            and other.owner_id is not None
            and other.owner_id != party.owner_id
        ):
            target = neighbor
            break
    if target is None:
        return world, None

    attacker_morale = 0
    defender_morale = 0
    if morale_by_owner is not None:
        enemy = world.party_at(target)
        attacker_morale = morale_by_owner.get(party.owner_id, 0)
        defender_morale = morale_by_owner.get(enemy.owner_id, 0)
    return world.resolve_party_battle_recorded(
        position,
        target,
        rng,
        attacker_morale=attacker_morale,
        defender_morale=defender_morale,
    )


def engage_duchy_party_to_recorded(
    world: WorldMap,
    duchy: Duchy,
    target: Region,
    rng: Rng,
    morale_by_owner: dict[str, int] | None = None,
) -> tuple[WorldMap, HexBattle | None]:
    """Engage an explicit adjacent enemy party; return map and battle.

    No-op paths return ``(world, None)`` without consuming RNG. On a hit the
    map matches ``engage_duchy_party_recorded`` when that auto-target is the
    same ``target``.
    """
    position = _duchy_party_position(world, duchy.duchy_id)
    if position is None:
        return world, None
    party = world.party_at(position)
    if party is None:
        return world, None
    if party.owner_id is None:
        raise ValueError("party must have an explicit owner_id")
    if target not in world.neighbors(position):
        return world, None
    other = world.party_at(target)
    if (
        other is None
        or other.owner_id is None
        or other.owner_id == party.owner_id
    ):
        return world, None

    attacker_morale = 0
    defender_morale = 0
    if morale_by_owner is not None:
        attacker_morale = morale_by_owner.get(party.owner_id, 0)
        defender_morale = morale_by_owner.get(other.owner_id, 0)
    return world.resolve_party_battle_recorded(
        position,
        target,
        rng,
        attacker_morale=attacker_morale,
        defender_morale=defender_morale,
    )


def assault_duchy_party_to(
    world: WorldMap,
    duchy: Duchy,
    target: Region,
    rng: Rng,
    morale_by_owner: dict[str, int] | None = None,
) -> WorldMap:
    """Assault an explicit adjacent enemy settlement from the duchy's party."""
    position = _duchy_party_position(world, duchy.duchy_id)
    if position is None:
        return world
    if not _is_legal_assault_target(world, position, target):
        return world
    settlement = world.settlement_at(target)
    if (
        settlement is None
        or settlement.owner_id is None
        or settlement.owner_id == duchy.duchy_id
    ):
        return world

    party = world.party_at(position)
    attacker_morale = 0
    defender_morale = 0
    if morale_by_owner is not None:
        attacker_morale = morale_by_owner.get(party.owner_id, 0)
        defender_morale = morale_by_owner.get(settlement.owner_id, 0)
    return _resolve_settlement_assault(
        world,
        position,
        target,
        rng,
        recorded=False,
        attacker_morale=attacker_morale,
        defender_morale=defender_morale,
    )


def assault_duchy_party_to_recorded(
    world: WorldMap,
    duchy: Duchy,
    target: Region,
    rng: Rng,
    morale_by_owner: dict[str, int] | None = None,
) -> tuple[WorldMap, HexBattle | None]:
    """Assault an explicit adjacent enemy settlement; return map and battle.

    No-op paths return ``(world, None)`` without consuming RNG. On a hit the
    map matches ``assault_duchy_party_to`` for the same inputs.
    """
    position = _duchy_party_position(world, duchy.duchy_id)
    if position is None:
        return world, None
    if not _is_legal_assault_target(world, position, target):
        return world, None
    settlement = world.settlement_at(target)
    if (
        settlement is None
        or settlement.owner_id is None
        or settlement.owner_id == duchy.duchy_id
    ):
        return world, None

    party = world.party_at(position)
    attacker_morale = 0
    defender_morale = 0
    if morale_by_owner is not None:
        attacker_morale = morale_by_owner.get(party.owner_id, 0)
        defender_morale = morale_by_owner.get(settlement.owner_id, 0)
    return _resolve_settlement_assault(
        world,
        position,
        target,
        rng,
        recorded=True,
        attacker_morale=attacker_morale,
        defender_morale=defender_morale,
    )


def assault_nearest_enemy_settlement(
    world: WorldMap,
    start: Region,
    rng: Rng,
    morale_by_owner: dict[str, int] | None = None,
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
    if target is None or not _is_legal_assault_target(world, start, target):
        return world

    attacker_morale = 0
    defender_morale = 0
    if morale_by_owner is not None:
        settlement = world.settlement_at(target)
        attacker_morale = morale_by_owner.get(party.owner_id, 0)
        defender_morale = morale_by_owner.get(settlement.owner_id, 0)
    return _resolve_settlement_assault(
        world,
        start,
        target,
        rng,
        recorded=False,
        attacker_morale=attacker_morale,
        defender_morale=defender_morale,
    )


def _has_assault_advantage(
    attackers: Iterable[Unit], defenders: Iterable[Unit]
) -> bool:
    """Return whether attackers meet the deterministic 2:1 strength ratio."""
    return _combat_strength(attackers) >= (
        _MINIMUM_ASSAULT_STRENGTH_RATIO * _combat_strength(defenders)
    )


def _resolve_settlement_assault(
    world: WorldMap,
    position: Region,
    target: Region,
    rng: Rng,
    *,
    recorded: bool,
    attacker_morale: int,
    defender_morale: int,
) -> WorldMap | tuple[WorldMap, HexBattle | None]:
    """Resolve an adjacent or in-place settlement assault in either API form."""
    if target == position:
        resolver = (
            world.resolve_settlement_battle_at_recorded
            if recorded
            else world.resolve_settlement_battle_at
        )
        return resolver(
            position,
            rng,
            attacker_morale=attacker_morale,
            defender_morale=defender_morale,
        )

    resolver = (
        world.resolve_settlement_battle_recorded
        if recorded
        else world.resolve_settlement_battle
    )
    return resolver(
        position,
        target,
        rng,
        attacker_morale=attacker_morale,
        defender_morale=defender_morale,
    )


def _is_legal_assault_target(
    world: WorldMap, position: Region, target: Region
) -> bool:
    """Return whether target is adjacent or the settlement occupied by position."""
    return target == position or target in world.neighbors(position)


def take_duchy_military_action(
    world: WorldMap,
    duchy: Duchy,
    rng: Rng,
    morale_by_owner: dict[str, int] | None = None,
) -> WorldMap:
    """Muster, march once, and assault only with a strength advantage.

    The assault is effective only when muster and march leave the party's
    monthly action available; either operation may make the assault a no-op.
    """
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
    target = nearest_enemy_settlement(current, position, duchy.duchy_id)
    party = current.party_at(position)
    if target is None or party is None or not _has_assault_advantage(
        (party.hero, *party.units), current.settlement_defenders(target)
    ):
        return current
    return assault_duchy_party_to(
        current, duchy, target, rng, morale_by_owner=morale_by_owner
    )


def take_duchy_turn(
    world: WorldMap,
    duchy: Duchy,
    rng: Rng,
    morale_by_owner: dict[str, int] | None = None,
) -> WorldMap:
    """Develop, recruit once, then perform one duchy's military action."""
    current = develop_duchy_settlement(world, duchy)
    current = recruit_duchy_unit(current, duchy)
    return take_duchy_military_action(
        current, duchy, rng, morale_by_owner=morale_by_owner
    )


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
