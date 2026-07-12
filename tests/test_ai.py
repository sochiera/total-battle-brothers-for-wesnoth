"""Tests for deterministic strategic AI queries."""

from dataclasses import FrozenInstanceError

import pytest

from tbb import (
    Party,
    Region,
    Settlement,
    Unit,
    WorldMap,
    nearest_enemy_settlement,
    next_march_step,
)


def _settlement(name: str, owner_id: str | None) -> Settlement:
    return Settlement(name, population=1, owner_id=owner_id)


def _party(name: str) -> Party:
    return Party(Unit(experience=len(name)))


def test_nearest_enemy_wins_regardless_of_settlement_mapping_order():
    start = Region("Start")
    near = Region("Near")
    middle = Region("Middle")
    far = Region("Far")
    world = WorldMap(
        [start, near, middle, far],
        [(start, near), (start, middle), (middle, far)],
        settlements={far: _settlement("Far", "enemy"), near: _settlement("Near", "enemy")},
    )

    assert nearest_enemy_settlement(world, start, "ai") is near


def test_equal_distance_is_broken_by_world_region_order():
    start = Region("Start")
    first = Region("First")
    second = Region("Second")
    world = WorldMap(
        [start, first, second],
        [(start, second), (start, first)],
        settlements={second: _settlement("Second", "enemy"), first: _settlement("First", "enemy")},
    )

    assert nearest_enemy_settlement(world, start, "ai") is first


def test_own_unowned_and_disconnected_settlements_are_ignored():
    start = Region("Start")
    own = Region("Own")
    unowned = Region("Unowned")
    disconnected = Region("Disconnected")
    world = WorldMap(
        [start, own, unowned, disconnected],
        [(start, own), (own, unowned)],
        settlements={
            own: _settlement("Own", "ai"),
            unowned: _settlement("Unowned", None),
            disconnected: _settlement("Enemy", "enemy"),
        },
    )

    assert nearest_enemy_settlement(world, start, "ai") is None


@pytest.mark.parametrize("owner_id", ["", None, 7])
def test_invalid_owner_id_is_rejected(owner_id):
    start = Region("Start")
    world = WorldMap([start])

    with pytest.raises((TypeError, ValueError)):
        nearest_enemy_settlement(world, start, owner_id)


def test_start_region_outside_world_is_rejected():
    with pytest.raises(ValueError):
        nearest_enemy_settlement(WorldMap([Region("Known")]), Region("Unknown"), "ai")


def test_query_does_not_mutate_world_settlement_mapping_or_settlements():
    start = Region("Start")
    target = Region("Target")
    settlement = _settlement("Target", "enemy")
    world = WorldMap([start, target], [(start, target)], {target: settlement})
    before = dict(world.settlements)

    nearest_enemy_settlement(world, start, "ai")

    assert dict(world.settlements) == before
    assert world.settlement_at(target) is settlement
    assert settlement.owner_id == "enemy"
    with pytest.raises(TypeError):
        world.settlements[start] = settlement
    with pytest.raises(FrozenInstanceError):
        settlement.owner_id = "ai"


def test_next_march_step_uses_shortest_path_when_longer_branch_is_first():
    start, long, middle, short, target = map(
        Region, ("Start", "Long", "Middle", "Short", "Target")
    )
    world = WorldMap(
        [start, long, middle, short, target],
        [(start, long), (long, middle), (middle, target), (start, short), (short, target)],
        parties={start: _party("Hero")},
    )

    assert next_march_step(world, start, target) is short


def test_next_march_step_tie_uses_region_order_not_connection_order():
    start, first, second, target = map(Region, ("Start", "First", "Second", "Target"))
    world = WorldMap(
        [start, first, second, target],
        [(start, second), (second, target), (start, first), (first, target)],
        parties={start: _party("Hero")},
    )

    assert next_march_step(world, start, target) is first


def test_next_march_step_avoids_occupied_regions_or_returns_none_when_blocked():
    start, blocked, detour, target = map(Region, ("Start", "Blocked", "Detour", "Target"))
    party = _party("Hero")
    blocker = _party("Blocker")
    world = WorldMap(
        [start, blocked, detour, target],
        [(start, blocked), (blocked, target), (start, detour), (detour, target)],
        parties={start: party, blocked: blocker},
    )

    assert next_march_step(world, start, target) is detour
    fully_blocked = WorldMap(
        world.regions,
        world.connections,
        parties={start: party, blocked: blocker, detour: _party("Other")},
    )
    assert next_march_step(fully_blocked, start, target) is None


def test_next_march_step_stops_when_target_is_adjacent():
    start, target = Region("Start"), Region("Target")
    party = _party("Hero")
    world = WorldMap([start, target], [(start, target)], parties={start: party})

    assert next_march_step(world, start, target) is None
    assert world.party_at(start) is party
    assert world.party_at(target) is None


@pytest.mark.parametrize("outside_argument", ["start", "target"])
def test_next_march_step_rejects_regions_outside_map_without_mutation(outside_argument):
    start, step, target = Region("Start"), Region("Step"), Region("Target")
    party = _party("Hero")
    world = WorldMap([start, step, target], [(start, step), (step, target)], parties={start: party})
    before = dict(world.parties)
    arguments = {
        "start": Region("Outside") if outside_argument == "start" else start,
        "target": Region("Outside") if outside_argument == "target" else target,
    }

    with pytest.raises(ValueError):
        next_march_step(world, arguments["start"], arguments["target"])

    assert dict(world.parties) == before
    assert world.party_at(start) is party
