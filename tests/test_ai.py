"""Tests for deterministic strategic AI queries."""

from dataclasses import FrozenInstanceError

import pytest

from tbb import Region, Settlement, WorldMap, nearest_enemy_settlement


def _settlement(name: str, owner_id: str | None) -> Settlement:
    return Settlement(name, population=1, owner_id=owner_id)


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
