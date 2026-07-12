"""Tests for an immutable settlement population pool."""

from dataclasses import FrozenInstanceError

import pytest

from tbb import Building, FARM, MARKET, Resources, Settlement, SMITH, Unit


def test_construction_defaults_all_population_to_free():
    settlement = Settlement("A", population=10)

    assert settlement.occupied == 0
    assert settlement.free == 10


def test_construction_with_occupied_population():
    assert Settlement("A", 10, occupied=3).free == 7


def test_settlement_owner_id_defaults_to_none_and_preserves_explicit_value():
    assert Settlement("A", 10).owner_id is None
    assert Settlement("A", 10, owner_id="north").owner_id == "north"


@pytest.mark.parametrize("owner_id", ["", 1, object()])
def test_settlement_rejects_empty_or_non_text_owner_id(owner_id):
    with pytest.raises((TypeError, ValueError)):
        Settlement("A", 10, owner_id=owner_id)


@pytest.mark.parametrize(
    "population, occupied", [(-1, 0), (10, -1), (10, 11)]
)
def test_invalid_population_pool_is_rejected(population, occupied):
    with pytest.raises(ValueError):
        Settlement("A", population, occupied)


def test_settlement_is_immutable():
    settlement = Settlement("A", 10)

    with pytest.raises(FrozenInstanceError):
        settlement.occupied = 1
    with pytest.raises(FrozenInstanceError):
        settlement.owner_id = "changed"


def test_occupy_returns_new_state_without_changing_original():
    original = Settlement("A", 10)

    occupied = original.occupy(4)

    assert occupied.occupied == 4
    assert occupied.free == 6
    assert original == Settlement("A", 10)
    assert occupied is not original


def test_occupy_rejects_more_than_free_population_without_changing_state():
    settlement = Settlement("A", 10)

    with pytest.raises(ValueError):
        settlement.occupy(11)

    assert settlement == Settlement("A", 10)


def test_occupy_rejects_negative_amount():
    with pytest.raises(ValueError):
        Settlement("A", 10).occupy(-1)


def test_release_returns_new_state():
    original = Settlement("A", 10, occupied=5)

    released = original.release(2)

    assert released.occupied == 3
    assert released.free == 7
    assert original == Settlement("A", 10, occupied=5)


def test_release_rejects_more_than_occupied_population():
    with pytest.raises(ValueError):
        Settlement("A", 10, occupied=5).release(6)


def test_release_rejects_negative_amount():
    with pytest.raises(ValueError):
        Settlement("A", 10).release(-1)


def test_occupying_all_free_population_closes_pool():
    settlement = Settlement("A", 10, occupied=3)

    assert settlement.occupy(settlement.free).free == 0


def test_zero_amount_transitions_are_allowed():
    settlement = Settlement("A", 10, occupied=3)

    assert settlement.occupy(0) == settlement
    assert settlement.release(0) == settlement


def test_open_building_assigns_staff_and_keeps_original_unchanged():
    original = Settlement("A", population=3)

    opened = original.open_building(SMITH)

    assert opened.occupied == 1
    assert opened.free == 2
    assert opened.active_buildings == (SMITH,)
    assert original == Settlement("A", population=3)
    assert opened is not original


def test_open_building_rejects_insufficient_free_population():
    settlement = Settlement("A", population=1, occupied=1)

    with pytest.raises(ValueError):
        settlement.open_building(SMITH)

    assert settlement == Settlement("A", population=1, occupied=1)


def test_close_building_releases_staff_and_keeps_original_unchanged():
    original = Settlement("A", population=3).open_building(SMITH)

    closed = original.close_building(SMITH)

    assert closed.occupied == 0
    assert closed.free == 3
    assert closed.active_buildings == ()
    assert original.active_buildings == (SMITH,)
    assert closed is not original


def test_close_inactive_building_is_rejected_without_changing_state():
    settlement = Settlement("A", population=3)
    mill = Building("Mill", staff=1)

    with pytest.raises(ValueError):
        settlement.close_building(mill)

    assert settlement == Settlement("A", population=3)


def test_settlement_without_buildings_has_no_production():
    assert Settlement("A", population=3).production == Resources(0, 0)


def test_production_sums_outputs_of_active_buildings():
    settlement = Settlement("A", population=2).open_building(FARM).open_building(MARKET)

    assert settlement.production == Resources(wheat=3, gold=2)


def test_consumption_equals_total_population():
    assert Settlement("A", population=5).consumption == Resources(wheat=5, gold=0)


def test_tick_economy_applies_production_and_consumption():
    settlement = Settlement("A", population=2).open_building(FARM)

    ticked = settlement.tick_economy()

    assert ticked.storage == Resources(wheat=1, gold=0)


def test_tick_economy_clamps_wheat_shortage_to_zero():
    settlement = Settlement("A", population=5)

    assert settlement.tick_economy().storage.wheat == 0


def test_tick_economy_returns_new_state_without_changing_original():
    original = Settlement("A", population=2).open_building(FARM)

    ticked = original.tick_economy()

    assert original.storage == Resources(0, 0)
    assert ticked is not original
    assert ticked.population == original.population
    assert ticked.occupied == original.occupied
    assert ticked.active_buildings == original.active_buildings


def test_capacity_defaults_to_unlimited_and_valid_limits_are_accepted():
    assert Settlement("A", population=2).capacity is None
    assert Settlement("A", population=2, capacity=2).capacity == 2
    assert Settlement("A", population=2, capacity=3).capacity == 3


def test_capacity_below_population_is_rejected():
    with pytest.raises(ValueError):
        Settlement("A", population=3, capacity=2)


def test_fed_settlement_grows_free_population_only():
    original = Settlement(
        "A", population=2, occupied=1, active_buildings=(FARM,),
        storage=Resources(1, 0),
    )

    grown = original.tick_growth()

    assert grown.population == 3
    assert grown.free == original.free + 1
    assert grown.occupied == original.occupied
    assert grown.active_buildings == original.active_buildings


def test_starving_settlement_does_not_grow():
    settlement = Settlement("A", population=2, storage=Resources(0, 0))

    assert settlement.tick_growth().population == settlement.population


def test_settlement_at_capacity_does_not_grow_despite_wheat_surplus():
    settlement = Settlement(
        "A", population=5, capacity=5, storage=Resources(3, 0)
    )

    assert settlement.tick_growth().population == settlement.population


def test_settlement_without_capacity_grows_with_wheat_surplus():
    settlement = Settlement("A", population=5, storage=Resources(3, 0))

    assert settlement.tick_growth().population == 6


def test_tick_growth_returns_new_state_without_mutating_original():
    original = Settlement("A", population=2, storage=Resources(1, 0))

    grown = original.tick_growth()

    assert grown is not original
    assert grown.population == 3
    assert original.population == 2
    assert original.storage == Resources(1, 0)


def test_prosperous_fed_settlement_attracts_free_immigrant():
    original = Settlement(
        "A", population=2, occupied=1, capacity=4, storage=Resources(1, 1)
    )

    grown = original.tick_immigration()

    assert grown.population == original.population + 1
    assert grown.free == original.free + 1
    assert grown.occupied == original.occupied


def test_settlement_without_gold_does_not_attract_immigrant():
    settlement = Settlement("A", population=2, storage=Resources(1, 0))

    assert settlement.tick_immigration().population == settlement.population


def test_starving_prosperous_settlement_does_not_attract_immigrant():
    settlement = Settlement("A", population=2, storage=Resources(0, 1))

    assert settlement.tick_immigration().population == settlement.population


def test_settlement_at_capacity_does_not_attract_immigrant():
    settlement = Settlement(
        "A", population=2, capacity=2, storage=Resources(1, 1)
    )

    assert settlement.tick_immigration().population == settlement.population


def test_settlement_without_capacity_attracts_immigrant():
    settlement = Settlement("A", population=2, storage=Resources(1, 1))

    assert settlement.tick_immigration().population == 3


def test_tick_immigration_does_not_consume_resources():
    settlement = Settlement("A", population=2, storage=Resources(3, 4))

    assert settlement.tick_immigration().storage == Resources(3, 4)


def test_tick_immigration_returns_new_state_without_mutating_original():
    original = Settlement("A", population=2, storage=Resources(1, 1))

    grown = original.tick_immigration()

    assert grown is not original
    assert grown.population == 3
    assert original.population == 2
    assert original.storage == Resources(1, 1)


def test_recruit_creates_fresh_recruit_and_occupies_population():
    settlement = Settlement("A", population=2)

    recruited = settlement.recruit()

    assert recruited.population == 2
    assert recruited.occupied == 1
    assert recruited.free == 1
    assert recruited.garrison == (Unit(),)


def test_recruit_adds_custom_unit_to_garrison():
    unit = Unit(training=2, equipment=1, experience=3)

    recruited = Settlement("A", population=1).recruit(unit)

    assert recruited.garrison == (unit,)
    assert recruited.garrison[0] is unit


def test_recruit_returns_new_state_without_mutating_original():
    original = Settlement("A", population=1)

    recruited = original.recruit()

    assert recruited is not original
    assert original.occupied == 0
    assert original.garrison == ()


def test_recruit_rejects_settlement_without_free_population():
    settlement = Settlement("A", population=2, occupied=2)

    with pytest.raises(ValueError):
        settlement.recruit()

    assert settlement == Settlement("A", population=2, occupied=2)


def test_two_recruits_occupy_two_population_and_join_garrison():
    recruited = Settlement("A", population=2).recruit().recruit()

    assert recruited.occupied == 2
    assert recruited.free == 0
    assert len(recruited.garrison) == 2


def test_muster_moves_garrison_to_party_and_preserves_free_population():
    units = (Unit(training=1), Unit(equipment=2), Unit(experience=3))
    original = Settlement("A", population=8, occupied=4).recruit(units[0]).recruit(
        units[1]
    ).recruit(units[2])
    hero = Unit(training=4)

    party, mustered = original.muster(hero)

    assert party.hero is hero
    assert party.units == units
    assert mustered.garrison == ()
    assert mustered.population == original.population - 3
    assert mustered.occupied == original.occupied - 3
    assert mustered.free == original.free


@pytest.mark.parametrize("owner_id", ["north", None])
def test_muster_propagates_settlement_owner_to_party(owner_id):
    hero = Unit()
    settlement = Settlement("A", population=1, owner_id=owner_id).recruit()

    party, _ = settlement.muster(hero)

    assert party.owner_id == owner_id


def test_muster_preserves_settlement_fields_and_does_not_mutate_original():
    original = Settlement(
        "A",
        population=5,
        occupied=2,
        active_buildings=(SMITH,),
        storage=Resources(7, 9),
        capacity=10,
        garrison=(Unit(),),
        owner_id="north",
    )

    _, mustered = original.muster(Unit())

    assert mustered.name == original.name
    assert mustered.storage == original.storage
    assert mustered.active_buildings == original.active_buildings
    assert mustered.capacity == original.capacity
    assert mustered.owner_id == original.owner_id
    assert original.garrison == (Unit(),)
    assert original.population == 5
    assert original.occupied == 2


def test_muster_rejects_garrison_over_party_limit():
    settlement = Settlement(
        "A", population=13, occupied=13, garrison=(Unit(),) * 13
    )

    with pytest.raises(ValueError):
        settlement.muster(Unit())


def test_muster_rejects_non_unit_hero():
    with pytest.raises(TypeError):
        Settlement("A", population=1).muster("not a hero")


def test_muster_empty_garrison_creates_hero_only_party_without_population_change():
    original = Settlement("A", population=4, occupied=1, owner_id="north")
    hero = Unit()

    party, mustered = original.muster(hero)

    assert party.hero is hero
    assert party.units == ()
    assert mustered.garrison == ()
    assert mustered.population == original.population
    assert mustered.occupied == original.occupied
