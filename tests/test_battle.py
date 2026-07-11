"""Tests for immutable unit deployment on a hex battlefield."""

import pytest

from tbb.battle import HexBattle
from tbb.battlefield import Battlefield
from tbb.hex import Hex
from tbb.terrain import FOREST
from tbb.unit import Unit


def test_empty_battle_has_no_units():
    battle = HexBattle(Battlefield())

    assert battle.unit_at(Hex(0, 0)) is None
    assert battle.unit_at(Hex(7, -3)) is None
    assert battle.is_occupied(Hex(0, 0)) is False
    assert battle.units == {}


def test_deploy_places_one_unit():
    unit = Unit(training=1)
    position = Hex(2, -1)

    deployed = HexBattle(Battlefield()).deploy(unit, position)

    assert deployed.unit_at(position) == unit
    assert deployed.is_occupied(position) is True
    assert deployed.units[position] == unit


def test_deploy_returns_a_new_state_without_changing_the_original():
    original = HexBattle(Battlefield())
    position = Hex(1, 1)

    deployed = original.deploy(Unit(), position)

    assert deployed is not original
    assert original.unit_at(position) is None
    assert original.units == {}


def test_two_units_can_be_deployed_on_different_hexes():
    first_position = Hex(0, 0)
    second_position = Hex(1, 0)
    first = Unit(training=1)
    second = Unit(equipment=2)

    battle = HexBattle(Battlefield()).deploy(first, first_position)
    battle = battle.deploy(second, second_position)

    assert battle.unit_at(first_position) == first
    assert battle.unit_at(second_position) == second


def test_deploy_rejects_an_occupied_hex():
    position = Hex(-2, 4)
    battle = HexBattle(Battlefield()).deploy(Unit(), position)

    with pytest.raises(ValueError):
        battle.deploy(Unit(training=3), position)


def test_battle_exposes_its_battlefield():
    forest = Hex(3, -2)
    battlefield = Battlefield({forest: FOREST})

    battle = HexBattle(battlefield)

    assert battle.battlefield is battlefield
    assert battle.battlefield.move_cost_at(forest) == battlefield.move_cost_at(forest)


def test_move_to_adjacent_plains_with_exact_budget_preserves_original():
    source = Hex(0, 0)
    destination = Hex(1, 0)
    unit = Unit(training=1)
    original = HexBattle(Battlefield()).deploy(unit, source)

    moved = original.move(source, destination, move_points=1)

    assert moved.unit_at(source) is None
    assert moved.unit_at(destination) == unit
    assert original.unit_at(source) == unit
    assert original.unit_at(destination) is None


def test_forest_and_two_plains_hexes_require_two_move_points():
    source = Hex(0, 0)
    forest = Hex(1, 0)
    two_plains_away = Hex(2, 0)
    battle = HexBattle(Battlefield({forest: FOREST})).deploy(Unit(), source)

    assert forest not in battle.reachable(source, move_points=1)
    assert forest in battle.reachable(source, move_points=2)
    assert two_plains_away in HexBattle(Battlefield()).deploy(Unit(), source).reachable(
        source, move_points=2
    )


def test_reachable_uses_cheaper_detour_around_expensive_terrain():
    source = Hex(0, 0)
    expensive_direct_step = Hex(1, 0)
    destination = Hex(1, 1)
    battle = HexBattle(Battlefield({expensive_direct_step: FOREST})).deploy(
        Unit(), source
    )

    assert destination in battle.reachable(source, move_points=2)


def test_units_block_routes_and_occupied_destinations():
    source = Hex(0, 0)
    destination = Hex(1, 1)
    blocker = Hex(0, 1)
    battle = HexBattle(Battlefield({Hex(1, 0): FOREST})).deploy(Unit(), source)
    battle = battle.deploy(Unit(training=2), blocker)

    assert destination not in battle.reachable(source, move_points=2)

    occupied_destination = battle.deploy(Unit(equipment=1), destination)
    with pytest.raises(ValueError):
        occupied_destination.move(source, destination, move_points=10)


def test_move_rejects_empty_source_and_destination_outside_budget():
    source = Hex(0, 0)
    battle = HexBattle(Battlefield()).deploy(Unit(), source)

    with pytest.raises(ValueError):
        battle.move(Hex(-1, 0), Hex(0, 1), move_points=1)
    with pytest.raises(ValueError):
        battle.move(source, Hex(2, 0), move_points=1)


def test_reachable_omits_source_and_occupied_hexes_and_is_repeatable():
    source = Hex(0, 0)
    occupied = Hex(1, 0)
    battle = HexBattle(Battlefield()).deploy(Unit(), source)
    battle = battle.deploy(Unit(training=3), occupied)

    first = battle.reachable(source, move_points=2)
    second = battle.reachable(source, move_points=2)

    assert source not in first
    assert occupied not in first
    assert first == second


def test_deploy_initializes_current_hp_from_unit_hp():
    healthy_position = Hex(0, 0)
    trained_position = Hex(1, 0)
    healthy = Unit()
    trained = Unit(training=4)

    battle = HexBattle(Battlefield()).deploy(healthy, healthy_position)
    battle = battle.deploy(trained, trained_position)

    assert battle.current_hp_at(healthy_position) == healthy.hp
    assert battle.current_hp_at(trained_position) == trained.hp


def test_damage_returns_new_state_and_does_not_mutate_input():
    position = Hex(0, 0)
    original = HexBattle(Battlefield()).deploy(Unit(training=2), position)

    damaged = original.damage(position, 3)

    assert damaged.current_hp_at(position) == original.current_hp_at(position) - 3
    assert original.current_hp_at(position) == Unit(training=2).hp


def test_damage_floors_current_hp_at_zero():
    position = Hex(0, 0)
    battle = HexBattle(Battlefield()).deploy(Unit(), position)

    damaged = battle.damage(position, battle.current_hp_at(position) + 100)

    assert damaged.current_hp_at(position) == 0


def test_move_preserves_current_hp_and_removes_it_from_source():
    source = Hex(0, 0)
    destination = Hex(1, 0)
    battle = HexBattle(Battlefield()).deploy(Unit(training=3), source).damage(source, 4)

    moved = battle.move(source, destination, move_points=1)

    assert moved.current_hp_at(destination) == battle.current_hp_at(source)
    with pytest.raises(ValueError):
        moved.current_hp_at(source)


def test_current_hp_and_damage_reject_empty_hex_and_negative_damage():
    occupied = Hex(0, 0)
    empty = Hex(1, 0)
    battle = HexBattle(Battlefield()).deploy(Unit(), occupied)

    with pytest.raises(ValueError):
        battle.current_hp_at(empty)
    with pytest.raises(ValueError):
        battle.damage(empty, 1)
    with pytest.raises(ValueError):
        battle.damage(occupied, -1)
