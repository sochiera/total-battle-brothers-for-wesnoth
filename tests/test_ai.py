"""Tests for deterministic strategic AI queries."""

from dataclasses import FrozenInstanceError

import pytest
import tbb
import tbb.settlement as settlement_module
from tbb.ai import develop_duchy_settlement, raise_duchy_hero

from tbb import (
    Duchy,
    Party,
    Region,
    Resources,
    Settlement,
    Unit,
    WorldMap,
    assault_nearest_enemy_settlement,
    march_toward_nearest_enemy,
    muster_duchy_party,
    nearest_enemy_settlement,
    next_march_step,
    recruit_duchy_unit,
    take_duchy_military_action,
    take_duchy_turn,
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


def test_duchy_military_action_musters_marches_once_and_assaults():
    home, road, target = map(Region, ("Home", "Road", "Target"))
    hero = Unit(training=5, equipment=6)
    guard = Unit(equipment=2)
    home_settlement = Settlement(
        "Home", 2, occupied=1, garrison=(guard,), owner_id="ai"
    )
    enemy_settlement = Settlement(
        "Target", 1, garrison=(Unit(),), owner_id="enemy"
    )
    world = WorldMap(
        [home, road, target],
        [(home, road), (road, target)],
        {home: home_settlement, target: enemy_settlement},
    )
    duchy = Duchy("ai", hero, settlements=(home_settlement,))

    result = take_duchy_military_action(world, duchy, tbb.Rng(4))
    mustered = muster_duchy_party(world, duchy)
    marched = march_toward_nearest_enemy(mustered, home)
    expected = assault_nearest_enemy_settlement(marched, road, tbb.Rng(4))

    assert result == expected
    assert result != marched


def test_duchy_military_action_reuses_party_and_assaults_from_marched_position():
    start, road, target = map(Region, ("Start", "Road", "Target"))
    party = Party(Unit(training=5, equipment=6), owner_id="ai")
    world = WorldMap(
        [start, road, target],
        [(start, road), (road, target)],
        {target: Settlement("Target", 1, garrison=(Unit(),), owner_id="enemy")},
        {start: party},
    )
    duchy = Duchy("ai", party.hero, parties=(party,))

    result = take_duchy_military_action(world, duchy, tbb.Rng(8))
    marched = march_toward_nearest_enemy(world, start)

    assert result == assault_nearest_enemy_settlement(marched, road, tbb.Rng(8))
    assert world.party_at(start) is party


@pytest.mark.parametrize("case", ["no_hero", "no_source", "no_enemy"])
def test_duchy_military_action_noop_does_not_use_rng_without_battle(case):
    home = Region("Home")
    hero = None if case == "no_hero" else Unit()
    settlements = (
        {home: Settlement("Home", 1, owner_id="ai")}
        if case != "no_source"
        else {}
    )
    parties = {home: Party(hero, owner_id="ai")} if case == "no_enemy" else {}
    world = WorldMap([home], settlements=settlements, parties=parties)

    assert take_duchy_military_action(world, Duchy("ai", hero), _ForbiddenRng()) is world


def test_duchy_military_action_discards_successful_muster_without_enemy_target():
    home = Region("Home")
    hero = Unit()
    garrison = (Unit(),)
    settlement = Settlement(
        "Home", 2, occupied=1, garrison=garrison, owner_id="ai"
    )
    world = WorldMap([home], settlements={home: settlement})

    result = take_duchy_military_action(world, Duchy("ai", hero), _ForbiddenRng())

    assert result is world
    assert world.party_at(home) is None
    assert world.settlement_at(home) is settlement
    assert settlement.garrison == garrison


def test_duchy_military_action_is_deterministic_and_preserves_inputs():
    start, target = Region("Start"), Region("Target")
    party = Party(Unit(equipment=5), owner_id="ai")
    settlement = Settlement(
        "Target", 1, garrison=(Unit(equipment=4),), owner_id="enemy"
    )
    world = WorldMap(
        [start, target], [(start, target)], {target: settlement}, {start: party}
    )
    duchy = Duchy("ai", party.hero, parties=(party,))

    first = take_duchy_military_action(world, duchy, tbb.Rng(12))
    second = take_duchy_military_action(world, duchy, tbb.Rng(12))

    assert first == second
    assert world.party_at(start) is party
    assert world.settlement_at(target) is settlement
    assert duchy.parties == (party,)


def test_duchy_military_action_is_publicly_exported():
    assert tbb.take_duchy_military_action is take_duchy_military_action


def test_recruit_duchy_unit_adds_exactly_one_fresh_unit_without_mutating_inputs():
    home = Region("Home")
    settlement = Settlement(
        "Home",
        3,
        occupied=1,
        storage=Resources(0, 1),
        garrison=(Unit(training=1),),
        owner_id="ai",
    )
    world = WorldMap([home], settlements={home: settlement})
    duchy = Duchy("ai", Unit(), settlements=(settlement,))

    recruited = recruit_duchy_unit(world, duchy)

    updated = recruited.settlement_at(home)
    assert updated.occupied == settlement.occupied + 1
    assert updated.garrison == settlement.garrison + (Unit(),)
    assert world.settlement_at(home) is settlement
    assert settlement.occupied == 1
    assert settlement.garrison == (Unit(training=1),)
    assert duchy.settlements == (settlement,)


def test_recruit_duchy_unit_uses_region_order_not_settlement_mapping_order():
    first, second = Region("First"), Region("Second")
    first_settlement = Settlement(
        "First", 1, storage=Resources(0, 1), owner_id="ai"
    )
    second_settlement = Settlement(
        "Second", 1, storage=Resources(0, 1), owner_id="ai"
    )
    world = WorldMap(
        [first, second],
        settlements={second: second_settlement, first: first_settlement},
    )

    recruited = recruit_duchy_unit(world, Duchy("ai", Unit()))

    assert recruited.settlement_at(first).garrison == (Unit(),)
    assert recruited.settlement_at(second) is second_settlement


def test_recruit_duchy_unit_uses_settlement_module_gold_cost(monkeypatch):
    first, second = Region("First"), Region("Second")
    first_settlement = Settlement(
        "First", 1, storage=Resources(0, 1), owner_id="ai"
    )
    second_settlement = Settlement(
        "Second", 1, storage=Resources(0, 2), owner_id="ai"
    )
    world = WorldMap(
        [first, second],
        settlements={first: first_settlement, second: second_settlement},
    )
    monkeypatch.setattr(settlement_module, "RECRUIT_GOLD_COST", 2)

    recruited = recruit_duchy_unit(world, Duchy("ai", Unit()))

    assert recruited.settlement_at(first) is first_settlement
    assert recruited.settlement_at(second).garrison == (Unit(),)
    assert recruited.settlement_at(second).storage == Resources(0, 0)


def test_recruit_duchy_unit_skips_every_ineligible_settlement():
    foreign, unowned, no_free, full, eligible = map(
        Region, ("Foreign", "Unowned", "No free", "Full", "Eligible")
    )
    full_garrison = tuple(Unit(experience=index) for index in range(12))
    settlements = {
        foreign: Settlement("Foreign", 1, owner_id="enemy"),
        unowned: Settlement("Unowned", 1),
        no_free: Settlement("No free", 1, occupied=1, owner_id="ai"),
        full: Settlement(
            "Full", 13, occupied=12, garrison=full_garrison, owner_id="ai"
        ),
        eligible: Settlement(
            "Eligible", 1, storage=Resources(0, 1), owner_id="ai"
        ),
    }
    world = WorldMap(
        [foreign, unowned, no_free, full, eligible], settlements=settlements
    )

    recruited = recruit_duchy_unit(world, Duchy("ai", Unit()))

    assert recruited.settlement_at(eligible).garrison == (Unit(),)
    for region in (foreign, unowned, no_free, full):
        assert recruited.settlement_at(region) is settlements[region]


def test_recruit_duchy_unit_is_noop_without_eligible_settlement():
    home = Region("Home")
    settlement = Settlement("Home", 1, occupied=1, owner_id="ai")
    world = WorldMap([home], settlements={home: settlement})
    duchy = Duchy("ai", Unit(), settlements=(settlement,))

    assert recruit_duchy_unit(world, duchy) is world
    assert world.settlement_at(home) is settlement
    assert duchy.settlements == (settlement,)


def test_recruit_duchy_unit_is_publicly_exported():
    assert tbb.recruit_duchy_unit is recruit_duchy_unit


def test_develop_duchy_settlement_fulfills_priority_selection_and_purity_contract():
    foreign, unowned, full, first, second = map(
        Region, ("Foreign", "Unowned", "Full", "First", "Second")
    )
    party = Party(Unit(), owner_id="ai")
    settlements = {
        foreign: Settlement("Foreign", population=1, owner_id="enemy"),
        unowned: Settlement("Unowned", population=1),
        full: Settlement("Full", population=1, occupied=1, owner_id="ai"),
        first: Settlement("First", population=3, owner_id="ai"),
        second: Settlement("Second", population=3, owner_id="ai"),
    }
    world_regions = [foreign, unowned, full, first, second]
    world = WorldMap(
        world_regions,
        settlements={
            region: settlements[region] for region in reversed(world_regions)
        },
        parties={second: party},
    )
    duchy = Duchy("ai", Unit())

    developed = develop_duchy_settlement(world, duchy)
    repeated = develop_duchy_settlement(world, duchy)

    assert developed.settlement_at(first).active_buildings == (tbb.FARM,)
    assert developed.settlement_at(first).occupied == tbb.FARM.staff
    assert repeated == developed
    assert developed.regions is world.regions
    assert developed.connections is world.connections
    assert developed.party_at(second) is party
    for region in (foreign, unowned, full, second):
        assert developed.settlement_at(region) is settlements[region]
    for region in world_regions:
        assert world.settlement_at(region) is settlements[region]

    with_smith = develop_duchy_settlement(developed, duchy)
    assert with_smith.settlement_at(first).active_buildings == (tbb.FARM, tbb.SMITH)
    with_market = develop_duchy_settlement(with_smith, duchy)
    assert with_market.settlement_at(first).active_buildings == (
        tbb.FARM,
        tbb.SMITH,
        tbb.MARKET,
    )

    no_candidate = develop_duchy_settlement(with_market, duchy)
    assert no_candidate.settlement_at(second).active_buildings == (tbb.FARM,)
    exhausted_world = WorldMap(
        [foreign, unowned, full],
        settlements={
            region: settlements[region] for region in (foreign, unowned, full)
        },
    )
    assert develop_duchy_settlement(exhausted_world, duchy) is exhausted_world


def test_duchy_turn_develops_farm_before_recruiting_one_unit():
    home = Region("Home")
    settlement = Settlement(
        "Home", population=3, storage=Resources(0, 1), owner_id="ai"
    )
    world = WorldMap([home], settlements={home: settlement})
    duchy = Duchy("ai", Unit(), settlements=(settlement,))

    result = take_duchy_turn(world, duchy, tbb.Rng(31))

    updated = result.settlement_at(home)
    assert updated.active_buildings == (tbb.FARM,)
    assert updated.garrison == (Unit(),)
    assert world.settlement_at(home) is settlement
    assert settlement.active_buildings == ()
    assert settlement.garrison == ()


def test_consecutive_duchy_turns_advance_from_farm_to_smith_without_enemy():
    home = Region("Home")
    hero = Unit(training=2)
    settlement = Settlement(
        "Home", population=5, storage=Resources(0, 2), owner_id="ai"
    )
    world = WorldMap([home], settlements={home: settlement})
    duchy = Duchy("ai", hero, settlements=(settlement,))

    def take_two_turns():
        rng = tbb.Rng(37)
        first = take_duchy_turn(world, duchy, rng)
        second = take_duchy_turn(first, duchy, rng)
        return first, second

    first, second = take_two_turns()
    repeated_first, repeated_second = take_two_turns()

    assert first.settlement_at(home).active_buildings == (tbb.FARM,)
    assert second.settlement_at(home).active_buildings == (tbb.FARM, tbb.SMITH)
    assert len(first.settlement_at(home).garrison) == 1
    assert len(second.settlement_at(home).garrison) == 2
    assert dict(first.parties) == {}
    assert dict(second.parties) == {}
    assert (repeated_first, repeated_second) == (first, second)

    assert world.settlement_at(home) is settlement
    assert dict(world.parties) == {}
    assert settlement.active_buildings == ()
    assert settlement.garrison == ()
    assert settlement.occupied == 0
    assert settlement.storage == Resources(0, 2)
    assert duchy.hero is hero
    assert duchy.settlements == (settlement,)
    assert duchy.parties == ()


def test_duchy_turn_development_uses_last_free_resident_before_recruitment():
    home = Region("Home")
    settlement = Settlement(
        "Home", population=1, storage=Resources(0, 1), owner_id="ai"
    )
    world = WorldMap([home], settlements={home: settlement})
    duchy = Duchy("ai", Unit(), settlements=(settlement,))

    result = take_duchy_turn(world, duchy, tbb.Rng(31))

    updated = result.settlement_at(home)
    assert updated.active_buildings == (tbb.FARM,)
    assert updated.garrison == ()
    assert updated.storage == Resources(0, 1)


def test_duchy_turn_recruits_and_marches_when_all_buildings_are_already_open():
    home, road, front, target = map(Region, ("Home", "Road", "Front", "Target"))
    hero = Unit(training=2)
    settlement = Settlement(
        "Home",
        population=4,
        occupied=3,
        active_buildings=(tbb.FARM, tbb.SMITH, tbb.MARKET),
        storage=Resources(0, 1),
        owner_id="ai",
    )
    world = WorldMap(
        [home, road, front, target],
        [(home, road), (road, front), (front, target)],
        {home: settlement, target: _settlement("Target", "enemy")},
    )
    duchy = Duchy("ai", hero, settlements=(settlement,))

    result = take_duchy_turn(world, duchy, _ForbiddenRng())

    assert result.party_at(road) == Party(hero, (Unit(),), owner_id="ai")
    assert result.settlement_at(home).active_buildings == settlement.active_buildings
    assert result.settlement_at(home).storage == Resources(0, 0)
    assert world.settlement_at(home) is settlement
    assert world.party_at(road) is None


def test_duchy_turn_recruits_before_muster_march_and_adjacent_assault():
    home, road, target = map(Region, ("Home", "Road", "Target"))
    hero = Unit(training=8, equipment=8)
    home_settlement = Settlement(
        "Home", 2, storage=Resources(0, 1), owner_id="ai"
    )
    enemy_settlement = Settlement(
        "Target", 1, garrison=(Unit(),), owner_id="enemy"
    )
    world = WorldMap(
        [home, road, target],
        [(home, road), (road, target)],
        {home: home_settlement, target: enemy_settlement},
    )
    duchy = Duchy("ai", hero, settlements=(home_settlement,))

    result = take_duchy_turn(world, duchy, tbb.Rng(17))
    developed = develop_duchy_settlement(world, duchy)
    recruited = recruit_duchy_unit(developed, duchy)
    expected = take_duchy_military_action(recruited, duchy, tbb.Rng(17))

    assert result == expected
    assert result.settlement_at(home).garrison == ()
    assert result.party_at(target).units == (Unit(),)


def test_duchy_turn_leaves_recruit_in_garrison_when_party_already_exists():
    home, start, road, target = map(Region, ("Home", "Start", "Road", "Target"))
    hero = Unit(training=2)
    veteran = Unit(equipment=2)
    party = Party(hero, (veteran,), owner_id="ai")
    home_settlement = Settlement(
        "Home", 2, storage=Resources(0, 1), owner_id="ai"
    )
    world = WorldMap(
        [home, start, road, target],
        [(start, road), (road, target)],
        {home: home_settlement, target: _settlement("Target", "enemy")},
        {start: party},
    )
    duchy = Duchy("ai", hero, settlements=(home_settlement,), parties=(party,))

    result = take_duchy_turn(world, duchy, _ForbiddenRng())

    assert result.settlement_at(home).garrison == (Unit(),)
    assert result.party_at(target).units == (veteran,)


def test_duchy_turn_takes_military_action_when_recruitment_is_unavailable():
    start, road, target = map(Region, ("Start", "Road", "Target"))
    hero = Unit()
    party = Party(hero, owner_id="ai")
    world = WorldMap(
        [start, road, target],
        [(start, road), (road, target)],
        {target: _settlement("Target", "enemy")},
        {start: party},
    )
    duchy = Duchy("ai", hero, parties=(party,))

    result = take_duchy_turn(world, duchy, _ForbiddenRng())

    assert result.party_at(target) == party


def test_duchy_turn_is_deterministic_and_preserves_all_inputs():
    home, target = Region("Home"), Region("Target")
    hero = Unit(training=7, equipment=7)
    settlement = Settlement("Home", 2, owner_id="ai")
    enemy = Settlement("Target", 1, garrison=(Unit(),), owner_id="enemy")
    world = WorldMap(
        [home, target], [(home, target)], {home: settlement, target: enemy}
    )
    duchy = Duchy("ai", hero, settlements=(settlement,))

    first = take_duchy_turn(world, duchy, tbb.Rng(23))
    second = take_duchy_turn(world, duchy, tbb.Rng(23))

    assert first == second
    assert world.settlement_at(home) is settlement
    assert world.settlement_at(target) is enemy
    assert world.party_at(home) is None
    assert settlement.garrison == ()
    assert settlement.occupied == 0
    assert duchy.hero is hero
    assert duchy.settlements == (settlement,)


def test_duchy_turn_is_publicly_exported():
    assert tbb.take_duchy_turn is take_duchy_turn


def test_raise_duchy_hero_raises_from_first_owned_settlement_by_region_order():
    """Without a hero, raise from the first eligible owned settlement (region order)."""
    foreign, unowned, poor, first, second = map(
        Region, ("Foreign", "Unowned", "Poor", "First", "Second")
    )
    garrison = (Unit(training=1),)
    settlements = {
        foreign: Settlement(
            "Foreign",
            3,
            storage=Resources(0, settlement_module.HERO_GOLD_COST),
            owner_id="enemy",
        ),
        unowned: Settlement(
            "Unowned",
            3,
            storage=Resources(0, settlement_module.HERO_GOLD_COST),
        ),
        poor: Settlement(
            "Poor",
            3,
            storage=Resources(0, settlement_module.HERO_GOLD_COST - 1),
            owner_id="ai",
        ),
        first: Settlement(
            "First",
            population=4,
            occupied=1,
            storage=Resources(wheat=2, gold=settlement_module.HERO_GOLD_COST + 1),
            garrison=garrison,
            owner_id="ai",
        ),
        second: Settlement(
            "Second",
            3,
            storage=Resources(0, settlement_module.HERO_GOLD_COST + 5),
            owner_id="ai",
        ),
    }
    world_regions = [foreign, unowned, poor, first, second]
    world = WorldMap(
        world_regions,
        settlements={
            region: settlements[region] for region in reversed(world_regions)
        },
    )
    duchy = Duchy(
        "ai",
        None,
        morale=5,
        settlements=(settlements[poor], settlements[first], settlements[second]),
    )

    result = raise_duchy_hero(world, duchy)
    repeated = raise_duchy_hero(world, duchy)

    assert isinstance(result, tuple)
    assert len(result) == 2
    result_world, result_duchy = result
    assert repeated == result
    assert isinstance(result_world, WorldMap)
    assert isinstance(result_duchy, Duchy)

    expected_settlement, expected_hero = settlements[first].raise_hero()
    assert result_world.settlement_at(first) == expected_settlement
    assert result_duchy.hero == expected_hero
    assert result_duchy.hero == Unit()
    assert result_duchy.has_hero is True
    assert result_duchy.duchy_id == "ai"
    assert result_duchy.morale == 5
    assert result_duchy.heir is None
    assert result_duchy.parties == ()
    assert result_duchy.settlements == duchy.settlements
    assert result_world.settlement_at(second) is settlements[second]
    for region in (foreign, unowned, poor):
        assert result_world.settlement_at(region) is settlements[region]
    assert world.settlement_at(first) is settlements[first]
    assert duchy.hero is None
    assert duchy.morale == 5
    assert duchy.has_hero is False
    assert settlements[first].population == 4
    assert settlements[first].storage == Resources(
        wheat=2, gold=settlement_module.HERO_GOLD_COST + 1
    )
    assert settlements[first].garrison == garrison
