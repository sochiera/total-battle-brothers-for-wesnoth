"""Tests for deterministic strategic AI queries."""

from dataclasses import FrozenInstanceError

import pytest
import tbb

from tbb import (
    Duchy,
    Party,
    Region,
    Settlement,
    Unit,
    WorldMap,
    assault_nearest_enemy_settlement,
    march_toward_nearest_enemy,
    muster_duchy_party,
    nearest_enemy_settlement,
    next_march_step,
)


def _settlement(name: str, owner_id: str | None) -> Settlement:
    return Settlement(name, population=1, owner_id=owner_id)


def _party(name: str) -> Party:
    return Party(Unit(experience=len(name)))


def _owned_party(name: str, owner_id: str = "ai") -> Party:
    return Party(Unit(experience=len(name)), owner_id=owner_id)


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


def test_march_moves_exactly_one_step_and_preserves_input_and_party():
    start, step, target = map(Region, ("Start", "Step", "Target"))
    party = _owned_party("Hero")
    world = WorldMap(
        [start, step, target],
        [(start, step), (step, target)],
        settlements={target: _settlement("Target", "enemy")},
        parties={start: party},
    )

    moved = march_toward_nearest_enemy(world, start)

    assert moved.party_at(step) is party
    assert moved.party_at(start) is None
    assert world.party_at(start) is party
    assert world.party_at(step) is None


def test_march_target_and_route_ties_follow_world_region_order():
    start, first, second, first_target, second_target = map(
        Region, ("Start", "First", "Second", "First target", "Second target")
    )
    party = _owned_party("Hero")
    world = WorldMap(
        [start, first, second, first_target, second_target],
        [
            (start, second), (second, second_target),
            (start, first), (first, first_target),
        ],
        settlements={
            second_target: _settlement("Second target", "enemy"),
            first_target: _settlement("First target", "enemy"),
        },
        parties={start: party},
    )

    moved = march_toward_nearest_enemy(world, start)

    assert moved.party_at(first) is party


@pytest.mark.parametrize("case", ["adjacent", "no_enemy", "blocked"])
def test_march_stays_put_when_no_step_is_available(case):
    start, step, target = map(Region, ("Start", "Step", "Target"))
    party = _owned_party("Hero")
    connections = [(start, target)] if case == "adjacent" else [(start, step), (step, target)]
    settlements = {} if case == "no_enemy" else {target: _settlement("Target", "enemy")}
    parties = {start: party}
    if case == "blocked":
        parties[step] = _owned_party("Blocker", "other")
    world = WorldMap([start, step, target], connections, settlements, parties)

    result = march_toward_nearest_enemy(world, start)

    assert result is world
    assert result.party_at(start) is party


@pytest.mark.parametrize("case", ["outside", "empty", "ownerless"])
def test_march_rejects_invalid_start_or_party(case):
    start = Region("Start")
    known = Region("Known")
    parties = {known: _party("Hero")} if case == "ownerless" else {}
    world = WorldMap([known], parties=parties)
    selected = start if case == "outside" else known

    with pytest.raises(ValueError):
        march_toward_nearest_enemy(world, selected)


def test_assault_resolves_adjacent_enemy_settlement():
    start, target = Region("Start"), Region("Target")
    party = Party(Unit(training=5, equipment=6), owner_id="ai")
    settlement = Settlement(
        "Target", population=1, garrison=(Unit(equipment=1),), owner_id="enemy"
    )
    world = WorldMap(
        [start, target],
        [(start, target)],
        settlements={target: settlement},
        parties={start: party},
    )

    resolved = assault_nearest_enemy_settlement(world, start, tbb.Rng(2))

    assert resolved == world.resolve_settlement_battle(start, target, tbb.Rng(2))
    assert resolved != world


class _ForbiddenRng:
    def randint(self, *_args):
        raise AssertionError("RNG must not be consumed")

    def chance(self, *_args):
        raise AssertionError("RNG must not be consumed")


@pytest.mark.parametrize("case", ["distant", "no_enemy"])
def test_assault_is_noop_without_adjacent_enemy_and_does_not_use_rng(case):
    start, middle, target = map(Region, ("Start", "Middle", "Target"))
    settlements = (
        {target: _settlement("Target", "enemy")} if case == "distant" else {}
    )
    world = WorldMap(
        [start, middle, target],
        [(start, middle), (middle, target)],
        settlements=settlements,
        parties={start: _owned_party("Hero")},
    )

    assert assault_nearest_enemy_settlement(world, start, _ForbiddenRng()) is world


@pytest.mark.parametrize("case", ["outside", "empty", "ownerless"])
def test_assault_rejects_invalid_start_or_party(case):
    known = Region("Known")
    parties = {known: _party("Hero")} if case == "ownerless" else {}
    world = WorldMap([known], parties=parties)
    selected = Region("Outside") if case == "outside" else known

    with pytest.raises(ValueError):
        assault_nearest_enemy_settlement(world, selected, _ForbiddenRng())


def test_assault_is_deterministic_and_preserves_input_objects():
    start, target = Region("Start"), Region("Target")
    party = Party(Unit(equipment=5), [Unit(equipment=2)], "ai")
    settlement = Settlement(
        "Target", population=2, garrison=(Unit(equipment=4),), owner_id="enemy"
    )
    world = WorldMap(
        [start, target], [(start, target)], {target: settlement}, {start: party}
    )

    first = assault_nearest_enemy_settlement(world, start, tbb.Rng(12))
    second = assault_nearest_enemy_settlement(world, start, tbb.Rng(12))

    assert first == second
    assert world.party_at(start) is party
    assert world.settlement_at(target) is settlement
    assert party.units == (Unit(equipment=2),)
    assert settlement.owner_id == "enemy"


def test_assault_transition_is_publicly_exported():
    assert tbb.assault_nearest_enemy_settlement is assault_nearest_enemy_settlement


def test_muster_duchy_party_moves_hero_and_garrison_without_mutating_input():
    home = Region("Home")
    hero = Unit(training=4)
    garrison = (Unit(equipment=1), Unit(experience=2))
    settlement = Settlement(
        "Home", population=3, occupied=2, garrison=garrison, owner_id="ai"
    )
    world = WorldMap([home], settlements={home: settlement})
    duchy = Duchy("ai", hero, settlements=(settlement,))

    mustered = muster_duchy_party(world, duchy)

    assert mustered.party_at(home) == Party(hero, garrison, owner_id="ai")
    assert mustered.party_at(home).units == garrison
    assert mustered.settlement_at(home).garrison == ()
    assert world.settlement_at(home) is settlement
    assert world.party_at(home) is None
    assert settlement.garrison == garrison
    assert duchy.hero is hero
    assert duchy.settlements == (settlement,)


def test_muster_duchy_party_tie_uses_world_region_order():
    first, second = Region("First"), Region("Second")
    first_settlement = Settlement("First", 1, owner_id="ai")
    second_settlement = Settlement("Second", 1, owner_id="ai")
    world = WorldMap(
        [first, second],
        settlements={second: second_settlement, first: first_settlement},
    )

    mustered = muster_duchy_party(world, Duchy("ai", Unit()))

    assert mustered.party_at(first) is not None
    assert mustered.party_at(second) is None


def test_muster_duchy_party_is_noop_when_party_already_exists():
    home, camp = Region("Home"), Region("Camp")
    hero = Unit(training=3)
    garrison = (Unit(),)
    settlement = Settlement("Home", 2, 1, garrison=garrison, owner_id="ai")
    party = Party(hero, owner_id="ai")
    world = WorldMap(
        [home, camp], settlements={home: settlement}, parties={camp: party}
    )

    assert muster_duchy_party(world, Duchy("ai", hero)) is world
    assert world.settlement_at(home).garrison == garrison


@pytest.mark.parametrize("case", ["no_hero", "no_own_settlement", "all_occupied"])
def test_muster_duchy_party_is_noop_without_eligible_source(case):
    own, other = Region("Own"), Region("Other")
    hero = None if case == "no_hero" else Unit()
    owner = "enemy" if case == "no_own_settlement" else "ai"
    settlement = Settlement("Seat", 1, owner_id=owner)
    parties = {own: Party(Unit(), owner_id="enemy")} if case == "all_occupied" else {}
    world = WorldMap([own, other], settlements={own: settlement}, parties=parties)

    assert muster_duchy_party(world, Duchy("ai", hero)) is world


def test_muster_duchy_party_transition_is_publicly_exported():
    assert tbb.muster_duchy_party is muster_duchy_party
