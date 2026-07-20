"""Tests for an immutable settlement population pool."""

import random
from dataclasses import FrozenInstanceError

import pytest

import tbb.settlement as settlement_module
from tbb import (
    BRUISE,
    MAIMED,
    Building,
    FARM,
    MARKET,
    Resources,
    Settlement,
    SMITH,
    Unit,
)


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
    settlement = Settlement("A", population=2, storage=Resources(0, 1))

    recruited = settlement.recruit()

    assert recruited.population == 2
    assert recruited.occupied == 1
    assert recruited.free == 1
    assert recruited.garrison == (Unit(),)


def test_recruit_pays_exported_gold_cost_without_mutating_input_or_using_rng():
    assert settlement_module.RECRUIT_GOLD_COST == 1
    original = Settlement(
        "A",
        population=2,
        storage=Resources(wheat=4, gold=settlement_module.RECRUIT_GOLD_COST + 2),
    )
    rng_state = random.getstate()

    first = original.recruit()
    second = original.recruit()

    assert first == second
    assert first.storage == Resources(wheat=4, gold=2)
    assert first.population == original.population
    assert first.occupied == original.occupied + 1
    assert first.garrison == (Unit(),)
    assert original.storage == Resources(
        wheat=4, gold=settlement_module.RECRUIT_GOLD_COST + 2
    )
    assert original.occupied == 0
    assert original.garrison == ()
    assert random.getstate() == rng_state


def test_recruit_adds_custom_unit_to_garrison():
    unit = Unit(training=2, equipment=1, experience=3)

    recruited = Settlement(
        "A", population=1, storage=Resources(0, 1)
    ).recruit(unit)

    assert recruited.garrison == (unit,)
    assert recruited.garrison[0] is unit


def test_recruit_returns_new_state_without_mutating_original():
    original = Settlement("A", population=1, storage=Resources(0, 1))

    recruited = original.recruit()

    assert recruited is not original
    assert original.occupied == 0
    assert original.garrison == ()


def test_recruit_rejects_settlement_without_free_population():
    settlement = Settlement(
        "A", population=2, occupied=2, storage=Resources(0, 1)
    )

    with pytest.raises(ValueError):
        settlement.recruit()

    assert settlement == Settlement(
        "A", population=2, occupied=2, storage=Resources(0, 1)
    )


def test_recruit_rejects_insufficient_gold_without_mutating_settlement():
    settlement = Settlement(
        "A",
        population=2,
        occupied=1,
        storage=Resources(3, settlement_module.RECRUIT_GOLD_COST - 1),
        garrison=(Unit(training=1),),
    )

    with pytest.raises(ValueError):
        settlement.recruit()

    assert settlement == Settlement(
        "A",
        population=2,
        occupied=1,
        storage=Resources(3, settlement_module.RECRUIT_GOLD_COST - 1),
        garrison=(Unit(training=1),),
    )


def test_two_recruits_occupy_two_population_and_join_garrison():
    recruited = Settlement(
        "A", population=2, storage=Resources(0, 2)
    ).recruit().recruit()

    assert recruited.occupied == 2
    assert recruited.free == 0
    assert len(recruited.garrison) == 2


def test_raise_hero_spends_free_population_and_exported_gold_without_garrison_or_mutation():
    assert settlement_module.HERO_GOLD_COST == 2
    garrison = (Unit(training=1), Unit(equipment=2))
    original = Settlement(
        "Keep",
        population=6,
        occupied=3,
        active_buildings=(SMITH,),
        storage=Resources(
            wheat=5, gold=settlement_module.HERO_GOLD_COST + 1
        ),
        capacity=10,
        garrison=garrison,
        owner_id="north",
    )
    rng_state = random.getstate()

    first = original.raise_hero()
    second = original.raise_hero()

    raised, hero = first
    assert first == second
    assert raised is not original
    assert hero == Unit()
    assert (
        hero.training,
        hero.equipment,
        hero.experience,
    ) == (0, 0, 0)
    assert raised.population == original.population - 1
    assert raised.occupied == original.occupied
    assert raised.free == original.free - 1
    assert raised.storage == Resources(wheat=5, gold=1)
    assert raised.garrison == garrison
    assert hero not in raised.garrison
    assert (
        raised.name,
        raised.active_buildings,
        raised.capacity,
        raised.owner_id,
    ) == (
        original.name,
        original.active_buildings,
        original.capacity,
        original.owner_id,
    )
    assert original.population == 6
    assert original.occupied == 3
    assert original.free == 3
    assert original.storage == Resources(
        wheat=5, gold=settlement_module.HERO_GOLD_COST + 1
    )
    assert original.garrison == garrison
    assert random.getstate() == rng_state


def test_raise_hero_rejects_no_free_population_or_insufficient_gold_without_mutation():
    no_free = Settlement(
        "Keep",
        population=2,
        occupied=2,
        storage=Resources(wheat=1, gold=settlement_module.HERO_GOLD_COST),
        garrison=(Unit(training=1),),
        owner_id="north",
    )
    low_gold = Settlement(
        "Keep",
        population=3,
        occupied=1,
        active_buildings=(SMITH,),
        storage=Resources(
            wheat=4, gold=settlement_module.HERO_GOLD_COST - 1
        ),
        capacity=8,
        garrison=(Unit(equipment=1),),
        owner_id="south",
    )

    with pytest.raises(ValueError):
        no_free.raise_hero()
    with pytest.raises(ValueError):
        low_gold.raise_hero()

    assert no_free == Settlement(
        "Keep",
        population=2,
        occupied=2,
        storage=Resources(wheat=1, gold=settlement_module.HERO_GOLD_COST),
        garrison=(Unit(training=1),),
        owner_id="north",
    )
    assert low_gold == Settlement(
        "Keep",
        population=3,
        occupied=1,
        active_buildings=(SMITH,),
        storage=Resources(
            wheat=4, gold=settlement_module.HERO_GOLD_COST - 1
        ),
        capacity=8,
        garrison=(Unit(equipment=1),),
        owner_id="south",
    )


def test_muster_moves_garrison_to_party_and_preserves_free_population():
    units = (Unit(training=1), Unit(equipment=2), Unit(experience=3))
    original = Settlement(
        "A", population=8, occupied=4, storage=Resources(0, 3)
    ).recruit(units[0]).recruit(units[1]).recruit(units[2])
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
    settlement = Settlement(
        "A", population=1, storage=Resources(0, 1), owner_id=owner_id
    ).recruit()

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


def test_absorb_defenders_replaces_garrison_and_accounts_for_fallen_purely():
    defenders = (
        Unit(training=1),
        Unit(equipment=2),
        Unit(experience=3),
    )
    original = Settlement(
        "Keep",
        population=8,
        occupied=4,
        active_buildings=(SMITH,),
        storage=Resources(7, 9),
        capacity=10,
        garrison=defenders,
        owner_id="north",
    )
    survivors = [defenders[2], defenders[0]]
    rng_state = random.getstate()

    absorbed = original.absorb_defenders(survivors)

    assert absorbed is not original
    assert absorbed.garrison == tuple(survivors)
    assert absorbed.garrison[0] is defenders[2]
    assert absorbed.garrison[1] is defenders[0]
    assert absorbed.population == original.population - 1
    assert absorbed.occupied == original.occupied - 1
    assert absorbed.free == original.free
    assert (
        absorbed.name,
        absorbed.storage,
        absorbed.active_buildings,
        absorbed.capacity,
        absorbed.owner_id,
    ) == ("Keep", Resources(7, 9), (SMITH,), 10, "north")
    assert original.garrison == defenders
    assert original.population == 8
    assert original.occupied == 4
    assert random.getstate() == rng_state


def test_absorb_defenders_clears_stun_and_preserves_survivor_state_purely():
    stunned = Unit(
        training=2,
        equipment=3,
        experience=4,
        ranged_range=5,
        wounds=(BRUISE, MAIMED),
        stunned=True,
        training_progress=1,
        equipment_progress=2,
    )
    ready = Unit(training=1, experience=6, wounds=(MAIMED,))
    fallen = Unit(equipment=2)
    original = Settlement(
        "Keep",
        population=8,
        occupied=4,
        garrison=(ready, fallen, stunned),
        owner_id="north",
    )
    survivors = [stunned, ready]
    survivors_before = list(survivors)

    absorbed = original.absorb_defenders(survivors)

    assert absorbed.garrison == (
        Unit(
            training=2,
            equipment=3,
            experience=4,
            ranged_range=5,
            wounds=(BRUISE, MAIMED),
            stunned=False,
            training_progress=1,
            equipment_progress=2,
        ),
        ready,
    )
    assert absorbed.garrison[1] is ready
    assert (absorbed.population, absorbed.occupied, absorbed.free) == (7, 3, 4)
    assert survivors == survivors_before
    assert stunned.stunned is True
    assert original.garrison == (ready, fallen, stunned)
    assert (original.population, original.occupied, original.free) == (8, 4, 4)


def test_absorb_defenders_rejects_extra_survivors_and_accepts_none():
    defenders = (Unit(), Unit(), Unit())
    original = Settlement(
        "Keep",
        population=8,
        occupied=4,
        garrison=defenders,
    )

    with pytest.raises(ValueError):
        original.absorb_defenders((*defenders, Unit()))

    emptied = original.absorb_defenders(())

    assert emptied.garrison == ()
    assert emptied.population == original.population - len(defenders)
    assert emptied.occupied == original.occupied - len(defenders)
    assert emptied.free == original.free
    assert original.garrison == defenders
    assert original.population == 8
    assert original.occupied == 4


def test_tick_training_gives_every_unit_the_exported_months_and_keeps_order(
    monkeypatch,
):
    assert settlement_module.TRAINING_MONTHS_PER_TURN == 1
    units = (Unit(), Unit(training=2, training_progress=1, equipment=3))
    original = Settlement("A", population=2, occupied=2, garrison=units)

    trained = original.tick_training()

    assert trained is not original
    assert trained.garrison == tuple(
        unit.train(settlement_module.TRAINING_MONTHS_PER_TURN) for unit in units
    )
    assert original.garrison == units

    after_three_turns = Settlement(
        "B", population=1, occupied=1, garrison=(Unit(),)
    )
    for _ in range(3):
        after_three_turns = after_three_turns.tick_training()
    assert after_three_turns.garrison[0].training == 2

    monkeypatch.setattr(settlement_module, "TRAINING_MONTHS_PER_TURN", 3)
    assert original.tick_training().garrison == tuple(unit.train(3) for unit in units)


def test_tick_training_empty_garrison_is_noop_and_other_state_is_pure_rng_free():
    empty = Settlement(
        "Empty", population=2, storage=Resources(1, 2), owner_id="south"
    )
    empty_ticked = empty.tick_training()
    assert empty_ticked == empty
    assert empty_ticked is not empty

    units = (Unit(training=1), Unit(equipment=2))
    original = Settlement(
        "A",
        population=5,
        occupied=3,
        active_buildings=(SMITH,),
        storage=Resources(7, 9),
        capacity=8,
        garrison=units,
        owner_id="north",
    )
    rng_state = random.getstate()

    trained = original.tick_training()

    assert (
        trained.population,
        trained.occupied,
        trained.storage,
        trained.active_buildings,
        trained.capacity,
        trained.owner_id,
    ) == (5, 3, Resources(7, 9), (SMITH,), 8, "north")
    assert original.garrison == units
    assert random.getstate() == rng_state


def test_tick_healing_empty_garrison_is_noop_and_other_state_is_pure_rng_free():
    empty = Settlement(
        "Empty", population=2, storage=Resources(1, 2), owner_id="south"
    )
    empty_ticked = empty.tick_healing()
    assert empty_ticked == empty
    assert empty_ticked is not empty

    units = (
        Unit(training=2, wounds=(BRUISE, MAIMED)),
        Unit(equipment=3, experience=4, wounds=(BRUISE,)),
    )
    original = Settlement(
        "A",
        population=5,
        occupied=3,
        active_buildings=(SMITH,),
        storage=Resources(7, 9),
        capacity=8,
        garrison=units,
        owner_id="north",
    )
    rng_state = random.getstate()

    healed = original.tick_healing()

    assert (
        healed.population,
        healed.occupied,
        healed.storage,
        healed.active_buildings,
        healed.capacity,
        healed.owner_id,
    ) == (5, 3, Resources(7, 9), (SMITH,), 8, "north")
    assert original.garrison == units
    assert random.getstate() == rng_state


def test_tick_healing_ticks_every_garrison_wound_and_preserves_settlement_state():
    units = (
        Unit(training=2, wounds=(BRUISE, MAIMED)),
        Unit(equipment=3, experience=4, wounds=(BRUISE,)),
    )
    original = Settlement(
        "A",
        population=5,
        occupied=3,
        active_buildings=(SMITH,),
        storage=Resources(7, 9),
        capacity=8,
        garrison=units,
        owner_id="north",
    )
    rng_state = random.getstate()

    healed = original.tick_healing()

    assert healed is not original
    assert healed.garrison == tuple(unit.tick_wounds(1) for unit in units)
    assert (
        healed.name,
        healed.population,
        healed.occupied,
        healed.active_buildings,
        healed.storage,
        healed.capacity,
        healed.owner_id,
    ) == (
        original.name,
        original.population,
        original.occupied,
        original.active_buildings,
        original.storage,
        original.capacity,
        original.owner_id,
    )
    assert original.garrison == units
    assert original.tick_healing() == healed
    assert random.getstate() == rng_state


def test_tick_equipment_uses_exported_cost_to_equip_earliest_least_equipped_unit(
    monkeypatch,
):
    assert settlement_module.EQUIP_GOLD_COST == 1
    assert settlement_module.EQUIP_INVESTMENT_PER_TURN == 1
    units = (
        Unit(training=2, equipment=2),
        Unit(equipment=0),
        Unit(equipment=0, experience=3),
    )
    original = Settlement(
        "A",
        population=5,
        occupied=4,
        active_buildings=(SMITH,),
        storage=Resources(wheat=11, gold=7),
        capacity=8,
        garrison=units,
        owner_id="north",
    )
    rng_state = random.getstate()

    equipped = original.tick_equipment()

    assert equipped is not original
    assert equipped.garrison == (
        units[0],
        units[1].equip(settlement_module.EQUIP_INVESTMENT_PER_TURN),
        units[2],
    )
    assert equipped.storage == Resources(wheat=11, gold=6)
    assert (
        equipped.name,
        equipped.population,
        equipped.occupied,
        equipped.active_buildings,
        equipped.capacity,
        equipped.owner_id,
    ) == ("A", 5, 4, (SMITH,), 8, "north")
    assert original.garrison == units
    assert original.storage == Resources(wheat=11, gold=7)
    assert random.getstate() == rng_state

    monkeypatch.setattr(settlement_module, "EQUIP_GOLD_COST", 3)
    monkeypatch.setattr(settlement_module, "EQUIP_INVESTMENT_PER_TURN", 2)
    configured = original.tick_equipment()
    assert configured.garrison == (
        units[0],
        units[1].equip(2),
        units[2],
    )
    assert configured.storage == Resources(wheat=11, gold=4)


def test_tick_equipment_succeeds_when_gold_exactly_matches_cost():
    unit = Unit()
    original = Settlement(
        "A",
        population=2,
        occupied=2,
        active_buildings=(SMITH,),
        storage=Resources(wheat=4, gold=settlement_module.EQUIP_GOLD_COST),
        garrison=(unit,),
    )

    equipped = original.tick_equipment()

    assert equipped.garrison == (
        unit.equip(settlement_module.EQUIP_INVESTMENT_PER_TURN),
    )
    assert equipped.storage == Resources(wheat=4, gold=0)


@pytest.mark.parametrize(
    "active_buildings, storage, garrison",
    [
        ((), Resources(2, 1), (Unit(),)),
        ((MARKET,), Resources(2, 1), (Unit(),)),
        ((SMITH,), Resources(2, 0), (Unit(),)),
        ((SMITH,), Resources(2, 1), ()),
    ],
    ids=(
        "no-active-buildings",
        "active-non-smith-building",
        "insufficient-gold",
        "empty-garrison",
    ),
)
def test_tick_equipment_noop_returns_equal_new_settlement_when_requirement_missing(
    active_buildings, storage, garrison
):
    original = Settlement(
        "A",
        population=3,
        occupied=1,
        active_buildings=active_buildings,
        storage=storage,
        capacity=5,
        garrison=garrison,
        owner_id="north",
    )

    rng_state = random.getstate()
    equipped = original.tick_equipment()

    assert equipped == original
    assert equipped is not original
    assert original.tick_equipment() == equipped
    assert random.getstate() == rng_state
