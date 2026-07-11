"""Tests for immutable unit deployment on a hex battlefield."""

import pytest

from tbb.battle import BattleSide, HexBattle
from tbb.battlefield import Battlefield
from tbb.hex import Hex
from tbb.terrain import FOREST
from tbb.unit import Unit
from tbb.rng import Rng


def test_empty_battle_has_no_units():
    battle = HexBattle(Battlefield())

    assert battle.unit_at(Hex(0, 0)) is None
    assert battle.unit_at(Hex(7, -3)) is None
    assert battle.is_occupied(Hex(0, 0)) is False
    assert battle.units == {}


def test_deploy_places_one_unit():
    unit = Unit(training=1)
    position = Hex(2, -1)

    deployed = HexBattle(Battlefield()).deploy(unit, position, BattleSide.ATTACKER)

    assert deployed.unit_at(position) == unit
    assert deployed.is_occupied(position) is True
    assert deployed.units[position] == unit


def test_deploy_returns_a_new_state_without_changing_the_original():
    original = HexBattle(Battlefield())
    position = Hex(1, 1)

    deployed = original.deploy(Unit(), position, BattleSide.ATTACKER)

    assert deployed is not original
    assert original.unit_at(position) is None
    assert original.units == {}


def test_two_units_can_be_deployed_on_different_hexes():
    first_position = Hex(0, 0)
    second_position = Hex(1, 0)
    first = Unit(training=1)
    second = Unit(equipment=2)

    battle = HexBattle(Battlefield()).deploy(first, first_position, BattleSide.ATTACKER)
    battle = battle.deploy(second, second_position, BattleSide.DEFENDER)

    assert battle.unit_at(first_position) == first
    assert battle.unit_at(second_position) == second


def test_deploy_rejects_an_occupied_hex():
    position = Hex(-2, 4)
    battle = HexBattle(Battlefield()).deploy(Unit(), position, BattleSide.ATTACKER)

    with pytest.raises(ValueError):
        battle.deploy(Unit(training=3), position, BattleSide.DEFENDER)


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
    original = HexBattle(Battlefield()).deploy(unit, source, BattleSide.ATTACKER)

    moved = original.move(source, destination, move_points=1)

    assert moved.unit_at(source) is None
    assert moved.unit_at(destination) == unit
    assert original.unit_at(source) == unit
    assert original.unit_at(destination) is None


def test_forest_and_two_plains_hexes_require_two_move_points():
    source = Hex(0, 0)
    forest = Hex(1, 0)
    two_plains_away = Hex(2, 0)
    battle = HexBattle(Battlefield({forest: FOREST})).deploy(Unit(), source, BattleSide.ATTACKER)

    assert forest not in battle.reachable(source, move_points=1)
    assert forest in battle.reachable(source, move_points=2)
    assert two_plains_away in HexBattle(Battlefield()).deploy(Unit(), source, BattleSide.ATTACKER).reachable(
        source, move_points=2
    )


def test_reachable_uses_cheaper_detour_around_expensive_terrain():
    source = Hex(0, 0)
    expensive_direct_step = Hex(1, 0)
    destination = Hex(1, 1)
    battle = HexBattle(Battlefield({expensive_direct_step: FOREST})).deploy(
        Unit(), source, BattleSide.ATTACKER
    )

    assert destination in battle.reachable(source, move_points=2)


def test_units_block_routes_and_occupied_destinations():
    source = Hex(0, 0)
    destination = Hex(1, 1)
    blocker = Hex(0, 1)
    battle = HexBattle(Battlefield({Hex(1, 0): FOREST})).deploy(Unit(), source, BattleSide.ATTACKER)
    battle = battle.deploy(Unit(training=2), blocker, BattleSide.DEFENDER)

    assert destination not in battle.reachable(source, move_points=2)

    occupied_destination = battle.deploy(Unit(equipment=1), destination, BattleSide.DEFENDER)
    with pytest.raises(ValueError):
        occupied_destination.move(source, destination, move_points=10)


def test_move_rejects_empty_source_and_destination_outside_budget():
    source = Hex(0, 0)
    battle = HexBattle(Battlefield()).deploy(Unit(), source, BattleSide.ATTACKER)

    with pytest.raises(ValueError):
        battle.move(Hex(-1, 0), Hex(0, 1), move_points=1)
    with pytest.raises(ValueError):
        battle.move(source, Hex(2, 0), move_points=1)


def test_reachable_omits_source_and_occupied_hexes_and_is_repeatable():
    source = Hex(0, 0)
    occupied = Hex(1, 0)
    battle = HexBattle(Battlefield()).deploy(Unit(), source, BattleSide.ATTACKER)
    battle = battle.deploy(Unit(training=3), occupied, BattleSide.DEFENDER)

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

    battle = HexBattle(Battlefield()).deploy(healthy, healthy_position, BattleSide.ATTACKER)
    battle = battle.deploy(trained, trained_position, BattleSide.DEFENDER)

    assert battle.current_hp_at(healthy_position) == healthy.hp
    assert battle.current_hp_at(trained_position) == trained.hp


def test_damage_returns_new_state_and_does_not_mutate_input():
    position = Hex(0, 0)
    original = HexBattle(Battlefield()).deploy(Unit(training=2), position, BattleSide.ATTACKER)

    damaged = original.damage(position, 3)

    assert damaged.current_hp_at(position) == original.current_hp_at(position) - 3
    assert original.current_hp_at(position) == Unit(training=2).hp


def test_damage_floors_current_hp_at_zero():
    position = Hex(0, 0)
    battle = HexBattle(Battlefield()).deploy(Unit(), position, BattleSide.ATTACKER)

    damaged = battle.damage(position, battle.current_hp_at(position) + 100)

    assert damaged.current_hp_at(position) == 0


def test_move_preserves_current_hp_and_removes_it_from_source():
    source = Hex(0, 0)
    destination = Hex(1, 0)
    battle = HexBattle(Battlefield()).deploy(Unit(training=3), source, BattleSide.ATTACKER).damage(source, 4)

    moved = battle.move(source, destination, move_points=1)

    assert moved.current_hp_at(destination) == battle.current_hp_at(source)
    with pytest.raises(ValueError):
        moved.current_hp_at(source)


def test_current_hp_and_damage_reject_empty_hex_and_negative_damage():
    occupied = Hex(0, 0)
    empty = Hex(1, 0)
    battle = HexBattle(Battlefield()).deploy(Unit(), occupied, BattleSide.ATTACKER)

    with pytest.raises(ValueError):
        battle.current_hp_at(empty)
    with pytest.raises(ValueError):
        battle.damage(empty, 1)
    with pytest.raises(ValueError):
        battle.damage(occupied, -1)


def test_sides_are_exposed_and_move_with_units_without_mutating_original():
    source = Hex(0, 0)
    destination = Hex(1, 0)
    defender = Hex(2, 0)
    original = HexBattle(Battlefield()).deploy(Unit(), source, BattleSide.ATTACKER)
    original = original.deploy(Unit(), defender, BattleSide.DEFENDER)

    moved = original.move(source, destination, move_points=1)

    assert original.side_at(source) is BattleSide.ATTACKER
    assert original.side_at(defender) is BattleSide.DEFENDER
    assert moved.side_at(destination) is BattleSide.ATTACKER
    with pytest.raises(ValueError):
        moved.side_at(source)


@pytest.mark.parametrize(
    ("attacker", "target"),
    [
        (Hex(0, 1), Hex(1, 0)),
        (Hex(0, 0), Hex(0, 1)),
        (Hex(0, 0), Hex(2, 0)),
    ],
)
def test_melee_attack_rejects_empty_or_non_adjacent_hexes(attacker, target):
    battle = HexBattle(Battlefield()).deploy(Unit(), Hex(0, 0), BattleSide.ATTACKER)
    battle = battle.deploy(Unit(), Hex(1, 0), BattleSide.DEFENDER)

    with pytest.raises(ValueError):
        battle.melee_attack(attacker, target, morale=0, rng=Rng(1))


def test_melee_attack_rejects_a_unit_on_the_same_side():
    battle = HexBattle(Battlefield()).deploy(Unit(), Hex(0, 0), BattleSide.ATTACKER)
    battle = battle.deploy(Unit(), Hex(1, 0), BattleSide.ATTACKER)

    with pytest.raises(ValueError):
        battle.melee_attack(Hex(0, 0), Hex(1, 0), morale=0, rng=Rng(1))


def test_seeded_miss_preserves_hp_and_seeded_hit_deals_attacker_damage():
    attacker, target = Hex(0, 0), Hex(1, 0)
    unit = Unit(equipment=3)
    battle = HexBattle(Battlefield()).deploy(unit, attacker, BattleSide.ATTACKER)
    battle = battle.deploy(Unit(), target, BattleSide.DEFENDER)

    missed = battle.melee_attack(attacker, target, morale=0, rng=Rng(0))
    hit = battle.melee_attack(attacker, target, morale=0, rng=Rng(1))

    assert missed.current_hp_at(target) == battle.current_hp_at(target)
    assert hit.current_hp_at(target) == battle.current_hp_at(target) - unit.damage


def test_same_state_and_seed_repeat_result_without_mutating_inputs():
    attacker, target = Hex(0, 0), Hex(1, 0)
    first = HexBattle(Battlefield()).deploy(Unit(equipment=2), attacker, BattleSide.ATTACKER)
    first = first.deploy(Unit(training=1), target, BattleSide.DEFENDER)
    second = HexBattle(Battlefield()).deploy(Unit(equipment=2), attacker, BattleSide.ATTACKER)
    second = second.deploy(Unit(training=1), target, BattleSide.DEFENDER)

    first_result = first.melee_attack(attacker, target, morale=0, rng=Rng(1))
    second_result = second.melee_attack(attacker, target, morale=0, rng=Rng(1))

    assert first_result.current_hp_at(target) == second_result.current_hp_at(target)
    assert first.current_hp_at(target) == Unit(training=1).hp
    assert second.current_hp_at(target) == Unit(training=1).hp


def test_terrain_and_morale_change_the_result_of_the_same_roll():
    attacker, target = Hex(0, 0), Hex(1, 0)
    neutral = HexBattle(Battlefield()).deploy(Unit(equipment=1), attacker, BattleSide.ATTACKER)
    neutral = neutral.deploy(Unit(), target, BattleSide.DEFENDER)
    hindered = HexBattle(Battlefield({attacker: FOREST})).deploy(Unit(equipment=1), attacker, BattleSide.ATTACKER)
    hindered = hindered.deploy(Unit(), target, BattleSide.DEFENDER)

    boosted_result = neutral.melee_attack(attacker, target, morale=40, rng=Rng(0))
    hindered_result = hindered.melee_attack(attacker, target, morale=0, rng=Rng(0))

    assert boosted_result.current_hp_at(target) == neutral.current_hp_at(target) - 1
    assert hindered_result.current_hp_at(target) == hindered.current_hp_at(target)


def test_melee_attack_uses_exactly_one_rng_roll():
    class CountingRng(Rng):
        def __init__(self):
            self.calls = 0

        def chance(self, p):
            self.calls += 1
            return False

    attacker, target = Hex(0, 0), Hex(1, 0)
    battle = HexBattle(Battlefield()).deploy(Unit(), attacker, BattleSide.ATTACKER)
    battle = battle.deploy(Unit(), target, BattleSide.DEFENDER)
    rng = CountingRng()

    battle.melee_attack(attacker, target, morale=0, rng=rng)

    assert rng.calls == 1
