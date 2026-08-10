"""Tests for immutable unit deployment on a hex battlefield."""

from dataclasses import replace

import pytest

from tbb.battle import BattleReport, BattleResult, BattleSide, BattleSideReport, HexBattle
from tbb.battlefield import Battlefield
from tbb.hex import Hex
from tbb.terrain import FOREST
from tbb.unit import Unit
from tbb.rng import Rng
from tbb.wound import BRUISE, MAIMED


def test_empty_battle_has_no_units():
    battle = HexBattle(Battlefield())

    assert battle.unit_at(Hex(0, 0)) is None
    assert battle.unit_at(Hex(7, -3)) is None
    assert battle.is_occupied(Hex(0, 0)) is False
    assert battle.units == {}


def test_nearest_enemy_returns_closer_enemy_and_ignores_same_side_unit():
    source = Hex(0, 0)
    ally = Hex(1, 0)
    closer_enemy = Hex(2, 0)
    farther_enemy = Hex(4, 0)
    battle = HexBattle(Battlefield()).deploy(Unit(), source, BattleSide.ATTACKER)
    battle = battle.deploy(Unit(), ally, BattleSide.ATTACKER)
    battle = battle.deploy(Unit(), farther_enemy, BattleSide.DEFENDER)
    battle = battle.deploy(Unit(), closer_enemy, BattleSide.DEFENDER)

    assert battle.nearest_enemy(source) == closer_enemy


def test_nearest_enemy_breaks_distance_tie_by_deployment_order():
    source = Hex(0, 0)
    first_enemy = Hex(2, 0)
    second_enemy = Hex(0, 2)
    battle = HexBattle(Battlefield()).deploy(Unit(), source, BattleSide.ATTACKER)
    battle = battle.deploy(Unit(), first_enemy, BattleSide.DEFENDER)
    battle = battle.deploy(Unit(), second_enemy, BattleSide.DEFENDER)

    assert battle.nearest_enemy(source) == first_enemy


def test_nearest_enemy_ignores_stunned_and_zero_hp_enemies():
    source = Hex(0, 0)
    stunned_enemy = Hex(1, 0)
    defeated_enemy = Hex(2, 0)
    battle = HexBattle(Battlefield()).deploy(Unit(), source, BattleSide.ATTACKER)
    battle = battle.deploy(replace(Unit(), stunned=True), stunned_enemy, BattleSide.DEFENDER)
    battle = battle.deploy(Unit(), defeated_enemy, BattleSide.DEFENDER)
    battle = battle.damage(defeated_enemy, battle.current_hp_at(defeated_enemy))

    assert battle.nearest_enemy(source) is None


def test_nearest_enemy_returns_none_when_no_enemies_are_deployed():
    source = Hex(0, 0)
    battle = HexBattle(Battlefield()).deploy(Unit(), source, BattleSide.ATTACKER)
    battle = battle.deploy(Unit(), Hex(1, 0), BattleSide.ATTACKER)

    assert battle.nearest_enemy(source) is None


def test_nearest_enemy_rejects_empty_source_hex():
    battle = HexBattle(Battlefield()).deploy(Unit(), Hex(0, 0), BattleSide.ATTACKER)

    with pytest.raises(ValueError):
        battle.nearest_enemy(Hex(1, 0))


def test_nearest_enemy_does_not_mutate_battle_state():
    source = Hex(0, 0)
    enemy = Hex(1, 0)
    battle = HexBattle(Battlefield()).deploy(Unit(), source, BattleSide.ATTACKER)
    battle = battle.deploy(Unit(), enemy, BattleSide.DEFENDER).damage(enemy, 1)
    units_before = dict(battle.units)
    sides_before = dict(battle.sides)
    hp_before = {position: battle.current_hp_at(position) for position in battle.units}

    battle.nearest_enemy(source)

    assert dict(battle.units) == units_before
    assert dict(battle.sides) == sides_before
    assert {position: battle.current_hp_at(position) for position in battle.units} == hp_before


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


def _ranged_battle(ranged_range=3, battlefield=None):
    attacker, target = Hex(0, 0), Hex(ranged_range, 0)
    battle = HexBattle(battlefield or Battlefield()).deploy(
        Unit(equipment=3, ranged_range=ranged_range), attacker, BattleSide.ATTACKER
    )
    return battle.deploy(Unit(), target, BattleSide.DEFENDER), attacker, target


@pytest.mark.parametrize("distance", [2, 4])
def test_ranged_attack_accepts_minimum_and_maximum_range(distance):
    battle, attacker, target = _ranged_battle(ranged_range=distance)

    result = battle.ranged_attack(attacker, target, morale=50, rng=Rng(1))

    assert result.current_hp_at(target) == battle.current_hp_at(target) - 3


@pytest.mark.parametrize("distance", [1, 4])
def test_ranged_attack_rejects_too_close_and_too_far_targets(distance):
    attacker, target = Hex(0, 0), Hex(distance, 0)
    battle = HexBattle(Battlefield()).deploy(
        Unit(ranged_range=3), attacker, BattleSide.ATTACKER
    ).deploy(Unit(), target, BattleSide.DEFENDER)

    with pytest.raises(ValueError):
        battle.ranged_attack(attacker, target, morale=0, rng=Rng(1))


def test_ranged_attack_rejects_unit_without_ranged_profile():
    attacker, target = Hex(0, 0), Hex(2, 0)
    battle = HexBattle(Battlefield()).deploy(Unit(), attacker, BattleSide.ATTACKER)
    battle = battle.deploy(Unit(), target, BattleSide.DEFENDER)

    with pytest.raises(ValueError):
        battle.ranged_attack(attacker, target, morale=0, rng=Rng(1))


@pytest.mark.parametrize(
    ("attacker", "target"),
    [(Hex(5, 0), Hex(2, 0)), (Hex(0, 0), Hex(5, 0))],
)
def test_ranged_attack_rejects_empty_source_or_target(attacker, target):
    battle, _, _ = _ranged_battle(ranged_range=2)

    with pytest.raises(ValueError):
        battle.ranged_attack(attacker, target, morale=0, rng=Rng(1))


def test_ranged_attack_rejects_same_side():
    attacker, target = Hex(0, 0), Hex(2, 0)
    battle = HexBattle(Battlefield()).deploy(
        Unit(ranged_range=2), attacker, BattleSide.ATTACKER
    ).deploy(Unit(), target, BattleSide.ATTACKER)

    with pytest.raises(ValueError):
        battle.ranged_attack(attacker, target, morale=0, rng=Rng(1))


def test_ranged_hit_changes_only_target_hp_in_new_state_without_counterattack():
    battle, attacker, target = _ranged_battle()
    attacker_hp = battle.current_hp_at(attacker)

    result = battle.ranged_attack(attacker, target, morale=50, rng=Rng(1))

    assert result is not battle
    assert result.current_hp_at(attacker) == attacker_hp
    assert battle.current_hp_at(target) == Unit().hp
    assert result.unit_at(attacker) == battle.unit_at(attacker)
    assert result.sides == battle.sides


def test_ranged_miss_preserves_target_hp_and_uses_exactly_one_roll():
    class CountingRng(Rng):
        def __init__(self):
            self.calls = 0

        def chance(self, p):
            self.calls += 1
            return False

    battle, attacker, target = _ranged_battle()
    rng = CountingRng()

    result = battle.ranged_attack(attacker, target, morale=0, rng=rng)

    assert rng.calls == 1
    assert result.current_hp_at(target) == battle.current_hp_at(target)


def test_ranged_attack_applies_terrain_and_morale_to_hit_chance():
    class RecordingRng(Rng):
        def __init__(self):
            self.probabilities = []

        def chance(self, p):
            self.probabilities.append(p)
            return False

    attacker, target = Hex(0, 0), Hex(2, 0)
    battle, _, _ = _ranged_battle(
        ranged_range=2, battlefield=Battlefield({attacker: FOREST, target: FOREST})
    )
    rng = RecordingRng()

    battle.ranged_attack(attacker, target, morale=7, rng=rng)

    assert rng.probabilities == [0.54]


def test_ranged_attack_allows_a_clear_axial_line():
    battle, attacker, target = _ranged_battle(ranged_range=3)

    result = battle.ranged_attack(attacker, target, morale=50, rng=Rng(1))

    assert result.current_hp_at(target) == battle.current_hp_at(target) - 3


def test_allied_unit_in_the_middle_blocks_ranged_attack_before_rng_and_hp_change():
    class FailingRng(Rng):
        def __init__(self):
            self.calls = 0

        def chance(self, p):
            self.calls += 1
            raise AssertionError("blocked shot must not call RNG")

    battle, attacker, target = _ranged_battle(ranged_range=3)
    blocker = Hex(1, 0)
    battle = battle.deploy(Unit(), blocker, BattleSide.ATTACKER)
    target_hp = battle.current_hp_at(target)
    rng = FailingRng()

    with pytest.raises(ValueError):
        battle.ranged_attack(attacker, target, morale=50, rng=rng)

    assert rng.calls == 0
    assert battle.current_hp_at(target) == target_hp
    assert battle.unit_at(blocker) == Unit()


def test_enemy_unit_in_the_middle_blocks_ranged_attack():
    battle, attacker, target = _ranged_battle(ranged_range=3)
    battle = battle.deploy(Unit(), Hex(2, 0), BattleSide.DEFENDER)

    with pytest.raises(ValueError):
        battle.ranged_attack(attacker, target, morale=50, rng=Rng(1))


def test_minimum_range_shot_ignores_attacker_and_target_as_obstacles():
    battle, attacker, target = _ranged_battle(ranged_range=2)

    result = battle.ranged_attack(attacker, target, morale=50, rng=Rng(1))

    assert attacker.line_to(target) == (attacker, Hex(1, 0), target)
    assert result.current_hp_at(target) == battle.current_hp_at(target) - 3


class ControlledRng:
    def __init__(self, result):
        self.result = result
        self.probabilities = []

    def chance(self, probability):
        self.probabilities.append(probability)
        return self.result


def test_resolve_defeat_death_removes_all_position_state_without_mutating_input():
    position = Hex(0, 0)
    unit = Unit(training=2)
    battle = HexBattle(Battlefield()).deploy(unit, position, BattleSide.ATTACKER)
    defeated = battle.damage(position, unit.hp)
    rng = ControlledRng(True)

    resolved = defeated.resolve_defeat(position, rng)

    assert rng.probabilities == [0.5]
    assert resolved.unit_at(position) is None
    assert position not in resolved.units
    assert position not in resolved.sides
    with pytest.raises(ValueError):
        resolved.current_hp_at(position)
    assert defeated.unit_at(position) is unit
    assert defeated.current_hp_at(position) == 0
    assert defeated.side_at(position) is BattleSide.ATTACKER


def test_resolve_defeat_survival_stuns_and_appends_bruise_without_mutation():
    position = Hex(0, 0)
    unit = Unit(training=2, wounds=(MAIMED,))
    battle = HexBattle(Battlefield()).deploy(unit, position, BattleSide.DEFENDER)
    defeated = battle.damage(position, unit.hp)
    rng = ControlledRng(False)

    resolved = defeated.resolve_defeat(position, rng)

    survivor = resolved.unit_at(position)
    assert rng.probabilities == [0.5]
    assert survivor is not unit
    assert survivor.stunned is True
    assert survivor.wounds == (MAIMED, BRUISE)
    assert resolved.current_hp_at(position) == 0
    assert resolved.side_at(position) is BattleSide.DEFENDER
    assert defeated.unit_at(position) is unit
    assert unit.stunned is False
    assert unit.wounds == (MAIMED,)


@pytest.mark.parametrize("case", ["empty", "healthy", "stunned"])
def test_resolve_defeat_rejects_invalid_target_before_rng(case):
    position = Hex(0, 0)
    if case == "empty":
        battle = HexBattle(Battlefield())
    else:
        battle = HexBattle(Battlefield()).deploy(
            Unit(stunned=case == "stunned"), position, BattleSide.ATTACKER
        )
        if case == "stunned":
            battle = battle.damage(position, battle.current_hp_at(position))
    rng = ControlledRng(True)

    with pytest.raises(ValueError):
        battle.resolve_defeat(position, rng)

    assert rng.probabilities == []


def test_stunned_unit_cannot_move():
    source = Hex(0, 0)
    battle = HexBattle(Battlefield()).deploy(
        Unit(stunned=True), source, BattleSide.ATTACKER
    )

    with pytest.raises(ValueError):
        battle.move(source, Hex(1, 0), move_points=1)


@pytest.mark.parametrize("attack_kind", ["melee", "ranged"])
def test_stunned_unit_cannot_attack_before_rng(attack_kind):
    attacker = Hex(0, 0)
    target = Hex(1, 0) if attack_kind == "melee" else Hex(2, 0)
    unit = Unit(stunned=True, ranged_range=2)
    battle = HexBattle(Battlefield()).deploy(unit, attacker, BattleSide.ATTACKER)
    battle = battle.deploy(Unit(), target, BattleSide.DEFENDER)
    rng = ControlledRng(True)

    with pytest.raises(ValueError):
        getattr(battle, f"{attack_kind}_attack")(attacker, target, morale=0, rng=rng)

    assert rng.probabilities == []


def _battle_with_both_sides():
    attacker, defender = Hex(0, 0), Hex(1, 0)
    battle = HexBattle(Battlefield()).deploy(
        Unit(), attacker, BattleSide.ATTACKER
    )
    return (
        battle.deploy(Unit(), defender, BattleSide.DEFENDER),
        attacker,
        defender,
    )


def test_battle_with_active_units_on_both_sides_has_no_result():
    battle, _, _ = _battle_with_both_sides()

    assert battle.result() is None


@pytest.mark.parametrize("defeat", ["death", "stun"])
def test_defeating_the_last_active_unit_makes_the_other_side_win(defeat):
    battle, _, defender = _battle_with_both_sides()
    defeated = battle.damage(defender, battle.current_hp_at(defender))
    if defeat == "death":
        defeated = defeated.resolve_defeat(defender, ControlledRng(True))

    assert defeated.result() is BattleResult.ATTACKER_WIN


def test_stunned_unit_remaining_on_the_board_does_not_keep_battle_running():
    attacker, defender = Hex(0, 0), Hex(1, 0)
    battle = HexBattle(Battlefield()).deploy(
        Unit(stunned=True), attacker, BattleSide.ATTACKER
    ).deploy(Unit(), defender, BattleSide.DEFENDER)

    assert battle.is_occupied(attacker)
    assert battle.current_hp_at(attacker) > 0
    assert battle.result() is BattleResult.DEFENDER_WIN


def test_no_active_units_on_either_side_is_a_draw():
    battle, attacker, defender = _battle_with_both_sides()
    battle = battle.damage(attacker, battle.current_hp_at(attacker))
    battle = battle.damage(defender, battle.current_hp_at(defender))

    assert battle.result() is BattleResult.DRAW


def test_reading_result_is_repeatable_and_does_not_mutate_battle_state():
    battle, attacker, defender = _battle_with_both_sides()
    units_before = dict(battle.units)
    hp_before = {
        attacker: battle.current_hp_at(attacker),
        defender: battle.current_hp_at(defender),
    }
    sides_before = dict(battle.sides)

    assert battle.result() is None
    assert battle.result() is None
    assert dict(battle.units) == units_before
    assert {
        attacker: battle.current_hp_at(attacker),
        defender: battle.current_hp_at(defender),
    } == hp_before
    assert dict(battle.sides) == sides_before


def test_report_keeps_dead_unit_and_its_original_side_after_removal():
    dead = Unit(training=3)
    dead_position = Hex(1, 0)
    battle = HexBattle(Battlefield()).deploy(
        Unit(), Hex(0, 0), BattleSide.ATTACKER
    ).deploy(dead, dead_position, BattleSide.DEFENDER)
    battle = battle.damage(dead_position, dead.hp).resolve_defeat(
        dead_position, ControlledRng(True)
    )

    report = battle.report()

    assert report.result is BattleResult.ATTACKER_WIN
    assert report.defender.fallen == (dead,)
    assert report.attacker.fallen == ()


def test_report_classifies_stunned_and_active_units_for_each_side():
    active_attacker = Unit(training=1)
    stunned_attacker = Unit(training=2)
    active_defender = Unit(equipment=1)
    battle = HexBattle(Battlefield()).deploy(
        active_attacker, Hex(0, 0), BattleSide.ATTACKER
    ).deploy(stunned_attacker, Hex(1, 0), BattleSide.ATTACKER)
    battle = battle.deploy(active_defender, Hex(2, 0), BattleSide.DEFENDER)
    battle = battle.damage(Hex(1, 0), stunned_attacker.hp).resolve_defeat(
        Hex(1, 0), ControlledRng(False)
    )
    battle = battle.damage(Hex(2, 0), active_defender.hp).resolve_defeat(
        Hex(2, 0), ControlledRng(True)
    )

    report = battle.report()

    assert report.attacker.active == (active_attacker,)
    assert report.attacker.stunned[0].stunned is True
    assert report.defender.active == ()
    assert report.defender.stunned == ()
    assert report.defender.fallen == (active_defender,)


def test_report_rejects_an_unfinished_battle():
    battle, _, _ = _battle_with_both_sides()

    with pytest.raises(ValueError):
        battle.report()


def test_report_is_repeatable_stable_and_does_not_mutate_battle():
    first = Unit(training=1)
    second = Unit(training=2)
    defender = Unit()
    positions = (Hex(2, 0), Hex(0, 0), Hex(3, 0))
    battle = HexBattle(Battlefield()).deploy(
        first, positions[0], BattleSide.ATTACKER
    ).deploy(second, positions[1], BattleSide.ATTACKER)
    battle = battle.deploy(defender, positions[2], BattleSide.DEFENDER)
    battle = battle.damage(positions[2], defender.hp).resolve_defeat(
        positions[2], ControlledRng(True)
    )
    units_before = dict(battle.units)
    hp_before = dict(battle._current_hp)
    sides_before = dict(battle.sides)

    first_report = battle.report()
    second_report = battle.report()

    assert first_report == second_report
    assert first_report.attacker.active == (first, second)
    assert isinstance(first_report, BattleReport)
    assert isinstance(first_report.attacker, BattleSideReport)
    assert dict(battle.units) == units_before
    assert dict(battle._current_hp) == hp_before
    assert dict(battle.sides) == sides_before


def test_report_keeps_deployment_order_after_a_unit_moves():
    first = Unit(training=1)
    second = Unit(training=2)
    defender = Unit()
    first_start = Hex(0, 0)
    second_position = Hex(2, 0)
    defender_position = Hex(4, 0)
    battle = HexBattle(Battlefield()).deploy(
        first, first_start, BattleSide.ATTACKER
    ).deploy(second, second_position, BattleSide.ATTACKER)
    battle = battle.deploy(defender, defender_position, BattleSide.DEFENDER)
    battle = battle.move(first_start, Hex(0, 1), move_points=1)
    battle = battle.damage(defender_position, defender.hp).resolve_defeat(
        defender_position, ControlledRng(True)
    )

    assert battle.report().attacker.active == (first, second)


def test_side_survivors_contains_surviving_units_but_not_fallen_units():
    survivor = Unit(training=1)
    fallen = Unit(training=2)
    survivor_position = Hex(0, 0)
    fallen_position = Hex(1, 0)
    battle = HexBattle(Battlefield()).deploy(
        survivor, survivor_position, BattleSide.ATTACKER
    ).deploy(fallen, fallen_position, BattleSide.ATTACKER)
    battle = battle.damage(fallen_position, fallen.hp).resolve_defeat(
        fallen_position, ControlledRng(True)
    )

    assert battle.side_survivors(BattleSide.ATTACKER) == (survivor,)


def test_side_fallen_lists_fallen_units_on_unfinished_battle():
    """Fallen are readable without report() while both sides still fight.

    Defect: casualties live only in private _fallen and exit solely via
    report(), which raises on unfinished battles — so a mid-assault bridge
    cannot assemble loss data for either side.
    """
    survivor = Unit(training=1)
    fallen = Unit(training=2)
    defender = Unit(training=3)
    survivor_position = Hex(0, 0)
    fallen_position = Hex(1, 0)
    defender_position = Hex(2, 0)
    battle = (
        HexBattle(Battlefield())
        .deploy(survivor, survivor_position, BattleSide.ATTACKER)
        .deploy(fallen, fallen_position, BattleSide.ATTACKER)
        .deploy(defender, defender_position, BattleSide.DEFENDER)
    )
    battle = battle.damage(fallen_position, fallen.hp).resolve_defeat(
        fallen_position, ControlledRng(True)
    )

    assert battle.result() is None
    assert hasattr(HexBattle, "side_fallen"), (
        "HexBattle must expose public side_fallen(side) for mid-battle losses"
    )
    assert battle.side_fallen(BattleSide.ATTACKER) == (fallen,)
    assert battle.side_fallen(BattleSide.DEFENDER) == ()
    with pytest.raises(ValueError, match="cannot report an unfinished battle"):
        battle.report()


def test_side_fallen_matches_report_fallen_on_resolved_battle():
    """Resolved battle: side_fallen and report() share one fallen source."""
    survivor = Unit(training=1)
    fallen_attacker = Unit(training=2)
    fallen_defender = Unit(training=3)
    positions = (Hex(0, 0), Hex(1, 0), Hex(2, 0))
    battle = (
        HexBattle(Battlefield())
        .deploy(survivor, positions[0], BattleSide.ATTACKER)
        .deploy(fallen_attacker, positions[1], BattleSide.ATTACKER)
        .deploy(fallen_defender, positions[2], BattleSide.DEFENDER)
    )
    battle = battle.damage(positions[1], fallen_attacker.hp).resolve_defeat(
        positions[1], ControlledRng(True)
    )
    battle = battle.damage(positions[2], fallen_defender.hp).resolve_defeat(
        positions[2], ControlledRng(True)
    )

    report = battle.report()
    assert battle.result() is BattleResult.ATTACKER_WIN
    assert battle.side_fallen(BattleSide.ATTACKER) == report.attacker.fallen
    assert battle.side_fallen(BattleSide.DEFENDER) == report.defender.fallen
    assert battle.side_fallen(BattleSide.ATTACKER) == (fallen_attacker,)
    assert battle.side_fallen(BattleSide.DEFENDER) == (fallen_defender,)


def test_side_fallen_empty_when_nobody_fell():
    attacker = Unit(training=1)
    defender = Unit(training=2)
    battle = (
        HexBattle(Battlefield())
        .deploy(attacker, Hex(0, 0), BattleSide.ATTACKER)
        .deploy(defender, Hex(1, 0), BattleSide.DEFENDER)
    )

    assert battle.side_fallen(BattleSide.ATTACKER) == ()
    assert battle.side_fallen(BattleSide.DEFENDER) == ()


def test_side_fallen_preserves_order_units_fell():
    first = Unit(training=1)
    second = Unit(training=2)
    defender = Unit(training=3)
    first_pos, second_pos, defender_pos = Hex(0, 0), Hex(1, 0), Hex(2, 0)
    battle = (
        HexBattle(Battlefield())
        .deploy(first, first_pos, BattleSide.ATTACKER)
        .deploy(second, second_pos, BattleSide.ATTACKER)
        .deploy(defender, defender_pos, BattleSide.DEFENDER)
    )
    battle = battle.damage(second_pos, second.hp).resolve_defeat(
        second_pos, ControlledRng(True)
    )
    battle = battle.damage(first_pos, first.hp).resolve_defeat(
        first_pos, ControlledRng(True)
    )

    assert battle.side_fallen(BattleSide.ATTACKER) == (second, first)


def test_side_fallen_is_repeatable_and_does_not_mutate_battle_state():
    survivor = Unit(training=1)
    fallen = Unit(training=2)
    defender = Unit(training=3)
    survivor_pos, fallen_pos, defender_pos = Hex(0, 0), Hex(1, 0), Hex(2, 0)
    battle = (
        HexBattle(Battlefield())
        .deploy(survivor, survivor_pos, BattleSide.ATTACKER)
        .deploy(fallen, fallen_pos, BattleSide.ATTACKER)
        .deploy(defender, defender_pos, BattleSide.DEFENDER)
    )
    battle = battle.damage(fallen_pos, fallen.hp).resolve_defeat(
        fallen_pos, ControlledRng(True)
    )
    units_before = dict(battle.units)
    sides_before = dict(battle.sides)
    result_before = battle.result()
    survivors_before = {
        BattleSide.ATTACKER: battle.side_survivors(BattleSide.ATTACKER),
        BattleSide.DEFENDER: battle.side_survivors(BattleSide.DEFENDER),
    }

    first = battle.side_fallen(BattleSide.ATTACKER)
    second = battle.side_fallen(BattleSide.ATTACKER)
    defender_fallen = battle.side_fallen(BattleSide.DEFENDER)

    assert first == second == (fallen,)
    assert defender_fallen == ()
    assert dict(battle.units) == units_before
    assert dict(battle.sides) == sides_before
    assert battle.result() is result_before is None
    assert battle.side_survivors(BattleSide.ATTACKER) == survivors_before[
        BattleSide.ATTACKER
    ]
    assert battle.side_survivors(BattleSide.DEFENDER) == survivors_before[
        BattleSide.DEFENDER
    ]
    with pytest.raises(ValueError, match="cannot report an unfinished battle"):
        battle.report()


def test_side_survivors_interleaves_stunned_and_active_by_deployment_order():
    stunned = Unit(training=1)
    active = Unit(training=2)
    stunned_position = Hex(0, 0)
    active_position = Hex(1, 0)
    battle = HexBattle(Battlefield()).deploy(
        stunned, stunned_position, BattleSide.ATTACKER
    ).deploy(active, active_position, BattleSide.ATTACKER)
    battle = battle.damage(stunned_position, stunned.hp).resolve_defeat(
        stunned_position, ControlledRng(False)
    )

    survivors = battle.side_survivors(BattleSide.ATTACKER)

    assert survivors[0].stunned is True
    assert survivors[1] is active


def test_side_survivors_filters_the_requested_battle_side():
    attacker = Unit(training=1)
    defender = Unit(training=2)
    battle = HexBattle(Battlefield()).deploy(
        attacker, Hex(0, 0), BattleSide.ATTACKER
    ).deploy(defender, Hex(1, 0), BattleSide.DEFENDER)

    assert battle.side_survivors(BattleSide.ATTACKER) == (attacker,)
    assert battle.side_survivors(BattleSide.DEFENDER) == (defender,)


def test_side_survivors_returns_empty_tuple_when_the_whole_side_fell():
    attacker = Unit()
    position = Hex(0, 0)
    battle = HexBattle(Battlefield()).deploy(
        attacker, position, BattleSide.ATTACKER
    )
    battle = battle.damage(position, attacker.hp).resolve_defeat(
        position, ControlledRng(True)
    )

    assert battle.side_survivors(BattleSide.ATTACKER) == ()


def test_side_survivors_is_repeatable_and_does_not_mutate_battle_state():
    attacker = Unit(training=1)
    defender = Unit(training=2)
    battle = HexBattle(Battlefield()).deploy(
        attacker, Hex(0, 0), BattleSide.ATTACKER
    ).deploy(defender, Hex(1, 0), BattleSide.DEFENDER)
    units_before = dict(battle.units)
    sides_before = dict(battle.sides)
    hp_before = dict(battle._current_hp)

    first = battle.side_survivors(BattleSide.ATTACKER)
    second = battle.side_survivors(BattleSide.ATTACKER)

    assert first == second
    assert dict(battle.units) == units_before
    assert dict(battle.sides) == sides_before
    assert dict(battle._current_hp) == hp_before


def test_side_survivors_with_slots_keeps_distinct_ids_for_value_equal_units_after_move():
    """Public survivor read pairs each unit with a stable deploy-place id.

    Realistic defect: side_survivors returns bare Units in deploy order. Unit is
    compared by value, so two identical recruits from different deploy places
    (e.g. garrison vs defending party) become indistinguishable after either
    moves — the world layer cannot map survivors back to their origin slots.
    """
    twin_a = Unit(training=1, equipment=1)
    twin_b = Unit(training=1, equipment=1)
    assert twin_a == twin_b
    pos_a, pos_b = Hex(0, 0), Hex(2, 0)
    battle = (
        HexBattle(Battlefield())
        .deploy(twin_a, pos_a, BattleSide.ATTACKER)
        .deploy(twin_b, pos_b, BattleSide.ATTACKER)
    )

    before = battle.side_survivors_with_slots(BattleSide.ATTACKER)
    ids_before = tuple(slot for slot, _unit in before)
    assert len(ids_before) == 2
    assert len(set(ids_before)) == 2
    assert [unit for _slot, unit in before] == list(
        battle.side_survivors(BattleSide.ATTACKER)
    )

    moved = battle.move(pos_a, Hex(0, 1), move_points=1)
    after = moved.side_survivors_with_slots(BattleSide.ATTACKER)
    assert tuple(slot for slot, _unit in after) == ids_before
    assert [unit for _slot, unit in after] == list(
        moved.side_survivors(BattleSide.ATTACKER)
    )


def test_side_survivors_with_slots_stable_across_swap_stun_and_ally_death():
    """Slot ids survive swap and ally death; stunned stays, fallen drops out."""
    twin = Unit(training=1, equipment=1)
    ally = Unit(training=2)
    pos_a, pos_b, pos_ally = Hex(0, 0), Hex(1, 0), Hex(2, 0)
    battle = (
        HexBattle(Battlefield())
        .deploy(twin, pos_a, BattleSide.ATTACKER)
        .deploy(twin, pos_b, BattleSide.ATTACKER)
        .deploy(ally, pos_ally, BattleSide.ATTACKER)
    )
    baseline = battle.side_survivors_with_slots(BattleSide.ATTACKER)
    ids_by_order = tuple(slot for slot, _unit in baseline)
    assert len(set(ids_by_order)) == 3
    id_a, id_b, id_ally = ids_by_order

    swapped = battle._swap(pos_a, pos_b)
    after_swap = swapped.side_survivors_with_slots(BattleSide.ATTACKER)
    assert tuple(slot for slot, _unit in after_swap) == (id_a, id_b, id_ally)
    assert [unit for _slot, unit in after_swap] == list(
        swapped.side_survivors(BattleSide.ATTACKER)
    )

    stunned_state = swapped.damage(pos_a, twin.hp).resolve_defeat(
        pos_a, ControlledRng(False)
    )
    after_stun = stunned_state.side_survivors_with_slots(BattleSide.ATTACKER)
    assert tuple(slot for slot, _unit in after_stun) == (id_a, id_b, id_ally)
    assert after_stun[1][1].stunned is True
    assert [unit for _slot, unit in after_stun] == list(
        stunned_state.side_survivors(BattleSide.ATTACKER)
    )

    after_death = stunned_state.damage(pos_ally, ally.hp).resolve_defeat(
        pos_ally, ControlledRng(True)
    )
    survivors = after_death.side_survivors_with_slots(BattleSide.ATTACKER)
    assert tuple(slot for slot, _unit in survivors) == (id_a, id_b)
    assert id_ally not in {slot for slot, _unit in survivors}
    assert [unit for _slot, unit in survivors] == list(
        after_death.side_survivors(BattleSide.ATTACKER)
    )
    assert after_death.side_fallen(BattleSide.ATTACKER) == (ally,)


def test_award_experience_rewards_only_survivors_and_preserves_report():
    active = Unit(training=1, experience=2, wounds=(MAIMED,))
    stunned = Unit(equipment=2, experience=4, wounds=(MAIMED,))
    fallen = Unit(training=3, experience=6, wounds=(BRUISE,))
    positions = (Hex(0, 0), Hex(1, 0), Hex(2, 0))
    battle = HexBattle(Battlefield()).deploy(
        active, positions[0], BattleSide.ATTACKER
    ).deploy(stunned, positions[1], BattleSide.ATTACKER)
    battle = battle.deploy(fallen, positions[2], BattleSide.DEFENDER)
    battle = battle.damage(positions[1], stunned.hp).resolve_defeat(
        positions[1], ControlledRng(False)
    )
    battle = battle.damage(positions[2], fallen.hp).resolve_defeat(
        positions[2], ControlledRng(True)
    )
    base_report = battle.report()

    rewarded = battle.award_experience()

    assert rewarded == BattleReport(
        result=base_report.result,
        attacker=BattleSideReport(
            fallen=(),
            stunned=(replace(base_report.attacker.stunned[0], experience=5),),
            active=(replace(active, experience=3),),
        ),
        defender=base_report.defender,
    )
    assert rewarded.attacker.stunned[0].stunned is True
    assert rewarded.attacker.stunned[0].wounds == (MAIMED, BRUISE)


def test_award_experience_rejects_an_unfinished_battle():
    battle, _, _ = _battle_with_both_sides()

    with pytest.raises(ValueError):
        battle.award_experience()


def test_award_experience_is_repeatable_without_mutating_battle_or_base_report():
    survivor = Unit(experience=7)
    battle = HexBattle(Battlefield()).deploy(
        survivor, Hex(0, 0), BattleSide.ATTACKER
    )
    base_report = battle.report()
    units_before = dict(battle.units)

    first = battle.award_experience()
    second = battle.award_experience()

    assert first == second
    assert first.attacker.active == (replace(survivor, experience=8),)
    assert battle.report() == base_report
    assert dict(battle.units) == units_before


def test_take_unit_turn_attacks_adjacent_enemy_with_seeded_hit():
    attacker, target = Hex(0, 0), Hex(1, 0)
    unit = Unit(equipment=3)
    battle = HexBattle(Battlefield()).deploy(unit, attacker, BattleSide.ATTACKER)
    battle = battle.deploy(Unit(), target, BattleSide.DEFENDER)

    result = battle.take_unit_turn(attacker, move_points=1, morale=0, rng=Rng(1))

    assert result.current_hp_at(target) == battle.current_hp_at(target) - unit.damage


def _take_unit_turn_with_attack_target(battle, source, target):
    """Invoke the public one-turn API with an optional attack intention.

    Keep a missing or incompatible public entry point as a contract assertion
    so the first red gate fails for the intended reason rather than with a
    collection or uncaught invocation error.
    """
    try:
        return battle.take_unit_turn(
            source, move_points=1, morale=0, rng=Rng(1), attack_target=target
        )
    except Exception as exc:
        pytest.fail(
            "HexBattle.take_unit_turn must accept a public attack_target "
            f"intention and apply it; got {type(exc).__name__}: {exc}"
        )


def test_take_unit_turn_uses_a_valid_adjacent_attack_target_instead_of_nearest():
    """AC1: a valid non-nearest adjacent enemy is the sole melee target."""
    source, nearest, indicated = Hex(0, 0), Hex(1, 0), Hex(0, 1)
    attacker = Unit(equipment=3)
    battle = (
        HexBattle(Battlefield())
        .deploy(attacker, source, BattleSide.ATTACKER)
        .deploy(Unit(training=3), nearest, BattleSide.DEFENDER)
        .deploy(Unit(training=3), indicated, BattleSide.DEFENDER)
    )

    result = _take_unit_turn_with_attack_target(battle, source, indicated)

    assert result.current_hp_at(indicated) == battle.current_hp_at(indicated) - attacker.damage
    assert result.current_hp_at(nearest) == battle.current_hp_at(nearest)
    assert result.unit_at(source) is attacker


def test_take_unit_turn_moves_toward_valid_distant_target_without_attacking_adjacent_enemy():
    """AC1: a valid distant target controls movement, not a nearer neighbour."""
    source, nearest, indicated = Hex(0, 0), Hex(1, 0), Hex(3, -1)
    attacker = Unit(equipment=3)
    battle = (
        HexBattle(Battlefield())
        .deploy(attacker, source, BattleSide.ATTACKER)
        .deploy(Unit(training=3), nearest, BattleSide.DEFENDER)
        .deploy(Unit(training=3), indicated, BattleSide.DEFENDER)
    )

    result = _take_unit_turn_with_attack_target(battle, source, indicated)
    moved_to = next(position for position, unit in result.units.items() if unit is attacker)

    assert moved_to.distance(indicated) < source.distance(indicated)
    assert result.current_hp_at(nearest) == battle.current_hp_at(nearest)
    assert result.current_hp_at(indicated) == battle.current_hp_at(indicated)


def _battle_with_invalid_attack_target(kind):
    source, nearest, invalid = Hex(0, 0), Hex(1, 0), Hex(0, 1)
    attacker = Unit(equipment=3)
    battle = (
        HexBattle(Battlefield())
        .deploy(attacker, source, BattleSide.ATTACKER)
        .deploy(Unit(training=3), nearest, BattleSide.DEFENDER)
    )
    if kind == "ally":
        battle = battle.deploy(Unit(training=2), invalid, BattleSide.ATTACKER)
    elif kind == "dead":
        dead = Unit(training=2)
        battle = battle.deploy(dead, invalid, BattleSide.DEFENDER)
        battle = battle.damage(invalid, dead.hp)
    elif kind == "stunned":
        battle = battle.deploy(Unit(training=2, stunned=True), invalid, BattleSide.DEFENDER)
    elif kind == "empty":
        pass
    elif kind == "outside":
        invalid = Hex(99, 99)
    else:
        raise AssertionError(f"unknown invalid target case: {kind}")
    return battle, source, nearest, invalid


@pytest.mark.parametrize("kind", ["empty", "ally", "dead", "stunned", "outside"])
def test_take_unit_turn_falls_back_to_nearest_enemy_for_invalid_attack_target(kind):
    """AC2: invalid intent is ignored and retains the existing nearest-enemy rule."""
    battle, source, nearest, invalid = _battle_with_invalid_attack_target(kind)
    attacker = battle.unit_at(source)

    result = _take_unit_turn_with_attack_target(battle, source, invalid)

    assert result.current_hp_at(nearest) == battle.current_hp_at(nearest) - attacker.damage
    if battle.is_occupied(invalid):
        assert result.unit_at(invalid) == battle.unit_at(invalid)
        assert result.current_hp_at(invalid) == battle.current_hp_at(invalid)


def _resolve_round_with_attack_targets(battle, attack_targets, move_points=0):
    """Resolve one round through the public per-unit target intention."""
    resolve_round = getattr(battle, "resolve_round", None)
    assert callable(resolve_round), "HexBattle must expose public resolve_round"
    try:
        return resolve_round(
            move_points=move_points, rng=Rng(1), attack_targets=attack_targets
        )
    except TypeError as exc:
        pytest.fail(
            "HexBattle.resolve_round must accept the public attack_targets map "
            f"(attacker hex -> target hex); got TypeError: {exc}"
        )


def test_resolve_round_honors_attack_target_map_for_the_attacking_unit():
    """AC1: resolve_round passes a valid target to that unit's turn."""
    source, nearest, indicated = Hex(0, 0), Hex(1, 0), Hex(0, 1)
    attacker = Unit(equipment=3)
    battle = (
        HexBattle(Battlefield())
        .deploy(attacker, source, BattleSide.ATTACKER)
        .deploy(Unit(), nearest, BattleSide.DEFENDER)
        .deploy(Unit(), indicated, BattleSide.DEFENDER)
    )

    result = _resolve_round_with_attack_targets(battle, {source: indicated})

    assert result.current_hp_at(indicated) == battle.current_hp_at(indicated) - attacker.damage
    assert result.current_hp_at(nearest) == battle.current_hp_at(nearest)


def test_resolve_round_moves_attacking_unit_toward_valid_distant_target():
    """AC1: resolve_round uses the indicated target for movement as well."""
    source, nearest, indicated = Hex(0, 0), Hex(1, 0), Hex(3, -1)
    attacker = Unit(equipment=3)
    battle = (
        HexBattle(Battlefield())
        .deploy(attacker, source, BattleSide.ATTACKER)
        .deploy(Unit(), nearest, BattleSide.DEFENDER)
        .deploy(Unit(), indicated, BattleSide.DEFENDER)
    )
    nearest_unit = battle.unit_at(nearest)
    indicated_unit = battle.unit_at(indicated)

    result = _resolve_round_with_attack_targets(
        battle, {source: indicated}, move_points=1
    )
    moved_to = next(position for position, unit in result.units.items() if unit is attacker)
    nearest_position = next(
        position for position, unit in result.units.items() if unit is nearest_unit
    )
    indicated_position = next(
        position for position, unit in result.units.items() if unit is indicated_unit
    )

    assert moved_to.distance(indicated) < source.distance(indicated)
    assert result.current_hp_at(nearest_position) == battle.current_hp_at(nearest)
    assert result.current_hp_at(indicated_position) == battle.current_hp_at(indicated)


@pytest.mark.parametrize("kind", ["empty", "ally", "dead", "stunned", "outside"])
def test_resolve_round_falls_back_to_nearest_enemy_for_invalid_attack_target(kind):
    """AC2: resolve_round ignores every invalid target kind."""
    battle, source, nearest, invalid = _battle_with_invalid_attack_target(kind)
    attacker = battle.unit_at(source)

    result = _resolve_round_with_attack_targets(battle, {source: invalid})

    assert result.current_hp_at(nearest) == battle.current_hp_at(nearest) - attacker.damage
    if battle.is_occupied(invalid):
        assert result.unit_at(invalid) == battle.unit_at(invalid)
        assert result.current_hp_at(invalid) == battle.current_hp_at(invalid)


def test_resolve_round_consumes_attack_target_before_the_following_round():
    """AC3: an indicated target affects one round and is not remembered."""
    source, nearest, indicated = Hex(0, 0), Hex(1, 0), Hex(0, 1)
    attacker = Unit(equipment=3)
    battle = (
        HexBattle(Battlefield())
        .deploy(attacker, source, BattleSide.ATTACKER)
        .deploy(Unit(), nearest, BattleSide.DEFENDER)
        .deploy(Unit(), indicated, BattleSide.DEFENDER)
    )

    first_round = _resolve_round_with_attack_targets(battle, {source: indicated})
    second_round = first_round.resolve_round(move_points=0, rng=Rng(1))

    assert first_round.current_hp_at(indicated) == battle.current_hp_at(indicated) - attacker.damage
    assert second_round.current_hp_at(nearest) == first_round.current_hp_at(nearest) - attacker.damage
    assert second_round.current_hp_at(indicated) == first_round.current_hp_at(indicated)


@pytest.mark.parametrize(("seed", "dies"), [(4, True), (1, False)])
def test_take_unit_turn_resolves_enemy_reduced_to_zero_hp(seed, dies):
    attacker, target = Hex(0, 0), Hex(1, 0)
    defeated = Unit()
    battle = HexBattle(Battlefield()).deploy(
        Unit(equipment=defeated.hp), attacker, BattleSide.ATTACKER
    ).deploy(defeated, target, BattleSide.DEFENDER)

    result = battle.take_unit_turn(attacker, move_points=0, morale=100, rng=Rng(seed))

    if dies:
        assert result.unit_at(target) is None
        assert result._fallen == ((BattleSide.DEFENDER, defeated),)
    else:
        assert result.unit_at(target).stunned is True
        assert result.unit_at(target).wounds == (BRUISE,)


def test_take_unit_turn_moves_one_step_closer_within_budget():
    source, enemy = Hex(0, 0), Hex(3, 0)
    unit = Unit(training=2)
    ally = Unit(equipment=1)
    battle = HexBattle(Battlefield()).deploy(unit, source, BattleSide.ATTACKER)
    battle = battle.deploy(ally, Hex(-1, 0), BattleSide.ATTACKER)
    battle = battle.deploy(Unit(), enemy, BattleSide.DEFENDER)

    result = battle.take_unit_turn(source, move_points=1, morale=0, rng=Rng(7))
    moved_to = next(position for position, deployed in result.units.items() if deployed == unit)

    assert moved_to.distance(enemy) == 2
    assert moved_to in battle.reachable(source, 1)
    assert result.unit_at(Hex(-1, 0)) == ally
    assert result.unit_at(enemy) == battle.unit_at(enemy)


def test_take_unit_turn_breaks_movement_tie_by_distance_then_coordinates():
    source, enemy = Hex(0, 0), Hex(3, -1)
    battle = HexBattle(Battlefield()).deploy(Unit(), source, BattleSide.ATTACKER)
    battle = battle.deploy(Unit(), enemy, BattleSide.DEFENDER)

    destinations = {
        next(position for position in battle.take_unit_turn(
            source, 1, 0, Rng(seed)
        ).units if position != enemy)
        for seed in range(5)
    }

    assert destinations == {Hex(1, -1)}


def test_take_unit_turn_with_zero_budget_is_no_op():
    source = Hex(0, 0)
    battle = HexBattle(Battlefield()).deploy(Unit(), source, BattleSide.ATTACKER)
    battle = battle.deploy(Unit(), Hex(3, 0), BattleSide.DEFENDER)

    assert battle.take_unit_turn(source, 0, 0, Rng(1)) is battle


def test_take_unit_turn_when_fully_blocked_is_no_op():
    source = Hex(0, 0)
    battle = HexBattle(Battlefield()).deploy(Unit(), source, BattleSide.ATTACKER)
    for neighbor in source.neighbors():
        battle = battle.deploy(Unit(), neighbor, BattleSide.ATTACKER)
    battle = battle.deploy(Unit(), Hex(3, 0), BattleSide.DEFENDER)

    assert battle.take_unit_turn(source, 3, 0, Rng(1)) is battle


@pytest.mark.parametrize(
    "fill_other_neighbors",
    [
        pytest.param(False, id="free_reachable_do_not_shorten"),
        pytest.param(True, id="no_free_reachable"),
    ],
)
def test_take_unit_turn_swaps_past_own_stunned_ally_when_only_closer_hex(
    fill_other_neighbors,
):
    """G89.2a-1: only closer hex holds own stunned ally → swap past them.

    Realistic defects:
    - free reachable hexes do not shorten distance and the sole closer hex is
      a same-side stunned unit (hp=0) → no-op instead of swap.
    - reachable is empty (all neighbors occupied, including own stunned on the
      only closer hex) → early return skips the swap branch (review G89.2a-1).
    """
    source, blocked, enemy = Hex(0, 0), Hex(1, 0), Hex(3, 0)
    unit = Unit(training=2)
    stunned_ally = Unit(stunned=True)
    enemy_unit = Unit()
    battle = (
        HexBattle(Battlefield())
        .deploy(unit, source, BattleSide.ATTACKER)
        .deploy(stunned_ally, blocked, BattleSide.ATTACKER)
        .deploy(enemy_unit, enemy, BattleSide.DEFENDER)
    )
    battle = battle.damage(blocked, battle.current_hp_at(blocked))
    if fill_other_neighbors:
        for neighbor in source.neighbors():
            if neighbor != blocked and not battle.is_occupied(neighbor):
                battle = battle.deploy(Unit(), neighbor, BattleSide.ATTACKER)
    free_reachable = battle.reachable(source, move_points=1)

    if fill_other_neighbors:
        assert not free_reachable
    else:
        assert free_reachable
        assert all(
            hex_.distance(enemy) >= source.distance(enemy) for hex_ in free_reachable
        )
    assert blocked.distance(enemy) < source.distance(enemy)
    assert battle.unit_at(blocked).stunned is True
    assert battle.current_hp_at(blocked) == 0

    result = battle.take_unit_turn(source, move_points=1, morale=0, rng=Rng(1))

    assert result.unit_at(blocked) == unit
    assert result.unit_at(source) == stunned_ally
    assert result.current_hp_at(source) == 0
    assert result.unit_at(source).stunned is True
    assert result.side_at(source) is BattleSide.ATTACKER
    assert result.side_at(blocked) is BattleSide.ATTACKER
    assert result.unit_at(enemy) == enemy_unit
    assert result.current_hp_at(enemy) == battle.current_hp_at(enemy)
    assert result._fallen == battle._fallen
    assert result is not battle
    assert battle.unit_at(source) == unit
    assert battle.unit_at(blocked) == stunned_ally


def test_take_unit_turn_prefers_free_closer_hex_over_swap_with_own_stunned():
    """G89.2a-1 AC2: free closer hex wins over swap with own stunned on another closer.

    Regression: swap-first would land on the stunned ally even when a free
    closer neighbor exists (review suggestions after G89.2a-1 accept).
    """
    source, free_closer, stunned_hex, enemy = (
        Hex(0, 0), Hex(1, -1), Hex(1, 0), Hex(2, -1),
    )
    unit = Unit(training=2)
    stunned_ally = Unit(stunned=True)
    battle = (
        HexBattle(Battlefield())
        .deploy(unit, source, BattleSide.ATTACKER)
        .deploy(stunned_ally, stunned_hex, BattleSide.ATTACKER)
        .deploy(Unit(), enemy, BattleSide.DEFENDER)
    )
    battle = battle.damage(stunned_hex, battle.current_hp_at(stunned_hex))

    assert free_closer.distance(enemy) < source.distance(enemy)
    assert stunned_hex.distance(enemy) < source.distance(enemy)
    assert free_closer in battle.reachable(source, move_points=1)

    result = battle.take_unit_turn(source, move_points=1, morale=0, rng=Rng(1))

    assert result.unit_at(free_closer) == unit
    assert result.unit_at(stunned_hex) == stunned_ally
    assert not result.is_occupied(source)
    assert result.unit_at(enemy) == battle.unit_at(enemy)


def test_take_unit_turn_does_not_swap_with_stunned_enemy_on_closer_hex():
    """G89.2a-1 AC3: stunned enemy on the only closer neighbor → no swap (no-op).

    Living active enemy stays further away so nearest_enemy is not the stunned
    blocker; sides filter must refuse swap with DEFENDER.
    """
    source, blocked, enemy = Hex(0, 0), Hex(1, 0), Hex(3, 0)
    unit = Unit(training=2)
    stunned_enemy = Unit(stunned=True)
    living_enemy = Unit()
    battle = (
        HexBattle(Battlefield())
        .deploy(unit, source, BattleSide.ATTACKER)
        .deploy(stunned_enemy, blocked, BattleSide.DEFENDER)
        .deploy(living_enemy, enemy, BattleSide.DEFENDER)
    )
    battle = battle.damage(blocked, battle.current_hp_at(blocked))

    assert blocked.distance(enemy) < source.distance(enemy)
    assert battle.nearest_enemy(source) == enemy
    assert battle.side_at(blocked) is BattleSide.DEFENDER
    assert battle.unit_at(blocked).stunned is True

    result = battle.take_unit_turn(source, move_points=1, morale=0, rng=Rng(1))

    assert result is battle
    assert result.unit_at(source) == unit
    assert result.unit_at(blocked) == stunned_enemy
    assert result.unit_at(enemy) == living_enemy


def test_take_unit_turn_does_not_swap_with_active_ally_on_closer_hex():
    """G89.2a-1 AC3: living (non-stunned) ally on the only closer neighbor → no-op.

    Mirror of stunned-enemy no-op: same geometry, own side, active body with
    hp>0 and stunned=False. Free neighbors do not get closer, so only a bad
    swap would move. Regression: dropping the ``stunned`` filter (or mistaking
    it for hp==0 alone) would exchange places with a fighting ally.
    """
    source, blocked, enemy = Hex(0, 0), Hex(1, 0), Hex(3, 0)
    unit = Unit(training=2)
    active_ally = Unit()
    living_enemy = Unit()
    battle = (
        HexBattle(Battlefield())
        .deploy(unit, source, BattleSide.ATTACKER)
        .deploy(active_ally, blocked, BattleSide.ATTACKER)
        .deploy(living_enemy, enemy, BattleSide.DEFENDER)
    )

    assert blocked.distance(enemy) < source.distance(enemy)
    assert battle.nearest_enemy(source) == enemy
    assert battle.side_at(blocked) is BattleSide.ATTACKER
    assert battle.unit_at(blocked).stunned is False
    assert battle.current_hp_at(blocked) > 0
    free_closer = [
        neighbor
        for neighbor in source.neighbors()
        if not battle.is_occupied(neighbor)
        and neighbor.distance(enemy) < source.distance(enemy)
    ]
    assert free_closer == []

    result = battle.take_unit_turn(source, move_points=1, morale=0, rng=Rng(1))

    assert result is battle
    assert result.unit_at(source) == unit
    assert result.unit_at(blocked) == active_ally
    assert result.unit_at(enemy) == living_enemy


def test_take_unit_turn_when_reachable_hexes_do_not_get_closer_is_no_op():
    source, enemy = Hex(0, 0), Hex(3, 0)
    battle = HexBattle(Battlefield()).deploy(Unit(), source, BattleSide.ATTACKER)
    battle = battle.deploy(Unit(), Hex(1, 0), BattleSide.ATTACKER)
    battle = battle.deploy(Unit(), enemy, BattleSide.DEFENDER)

    reachable = battle.reachable(source, move_points=1)

    assert reachable
    assert all(hex_.distance(enemy) >= source.distance(enemy) for hex_ in reachable)
    assert battle.take_unit_turn(source, 1, 0, Rng(1)) is battle


def test_take_unit_turn_without_enemy_is_no_op():
    source = Hex(0, 0)
    battle = HexBattle(Battlefield()).deploy(Unit(), source, BattleSide.ATTACKER)

    assert battle.take_unit_turn(source, 2, 0, Rng(1)) is battle


@pytest.mark.parametrize("inactive", [Unit(stunned=True), Unit()])
def test_take_unit_turn_for_inactive_unit_is_no_op(inactive):
    source = Hex(0, 0)
    battle = HexBattle(Battlefield()).deploy(inactive, source, BattleSide.ATTACKER)
    battle = battle.deploy(Unit(), Hex(1, 0), BattleSide.DEFENDER)
    if not inactive.stunned:
        battle = battle.damage(source, inactive.hp)

    assert battle.take_unit_turn(source, 1, 0, Rng(1)) is battle


def test_take_unit_turn_rejects_empty_source():
    battle = HexBattle(Battlefield()).deploy(Unit(), Hex(0, 0), BattleSide.ATTACKER)

    with pytest.raises(ValueError):
        battle.take_unit_turn(Hex(1, 0), 1, 0, Rng(1))


def test_take_unit_turn_is_deterministic_and_does_not_mutate_input():
    source, target = Hex(0, 0), Hex(1, 0)
    battle = HexBattle(Battlefield()).deploy(
        Unit(equipment=3), source, BattleSide.ATTACKER
    ).deploy(Unit(), target, BattleSide.DEFENDER)
    before = HexBattle(
        battle.battlefield, dict(battle.units), dict(battle._current_hp),
        dict(battle.sides), battle._fallen, battle._deployment_order,
    )

    first = battle.take_unit_turn(source, 1, 0, Rng(1))
    second = battle.take_unit_turn(source, 1, 0, Rng(1))

    assert first == second
    assert battle == before


def test_auto_resolve_finishes_seeded_duel_and_produces_report():
    attacker, defender = Hex(0, 0), Hex(1, 0)
    battle = HexBattle(Battlefield()).deploy(
        Unit(equipment=10), attacker, BattleSide.ATTACKER
    ).deploy(Unit(), defender, BattleSide.DEFENDER)

    resolved = battle.auto_resolve(
        move_points=1, rng=Rng(4), attacker_morale=100, defender_morale=100
    )

    assert resolved.result() is BattleResult.ATTACKER_WIN
    assert resolved.report().result is BattleResult.ATTACKER_WIN


@pytest.mark.parametrize("seed", [0, 1, 12, 42, 99])
def test_auto_resolve_is_deterministic_for_the_same_seed(seed):
    battle = HexBattle(Battlefield()).deploy(
        Unit(equipment=3), Hex(0, 0), BattleSide.ATTACKER
    ).deploy(Unit(equipment=2), Hex(3, 0), BattleSide.DEFENDER)

    first = battle.auto_resolve(move_points=1, rng=Rng(seed))
    second = battle.auto_resolve(move_points=1, rng=Rng(seed))

    assert first == second
    assert first.result() is not None


def test_auto_resolve_stops_after_maximum_rounds_before_resolution():
    battle = HexBattle(Battlefield()).deploy(
        Unit(equipment=1), Hex(0, 0), BattleSide.ATTACKER
    ).deploy(Unit(equipment=1), Hex(4, 0), BattleSide.DEFENDER)

    partial = battle.auto_resolve(
        move_points=1, rng=Rng(1), max_rounds=1
    )

    assert partial.result() is None


def test_auto_resolve_active_acts_at_most_once_per_round_after_swap_past_stunned():
    """G89.2a-1 / auto_resolve: swap must not grant a second turn same round.

    Realistic defect: auto_resolve freezes turn hexes from deployment order for
    the round. Ordinary move vacates the old hex so the unit is not revisited,
    but _swap leaves the active body on the stunned ally's hex, which is still
    upcoming when the active unit was deployed earlier than that ally. The same
    unit then takes a second turn (swap + move) — two hexes of progress with
    move_points=1 in a single round. Reverse deploy order (stunned before
    active) hides the bug; this layout is active → stunned → enemy.
    """
    source, blocked, enemy_hex = Hex(0, 0), Hex(1, 0), Hex(3, 0)
    active = Unit()
    stunned_ally = Unit(stunned=True)
    battle = (
        HexBattle(Battlefield())
        .deploy(active, source, BattleSide.ATTACKER)
        .deploy(stunned_ally, blocked, BattleSide.ATTACKER)
        .deploy(Unit(), enemy_hex, BattleSide.DEFENDER)
    )
    battle = battle.damage(blocked, battle.current_hp_at(blocked))
    assert source.distance(enemy_hex) == 3
    assert blocked.distance(enemy_hex) == 2

    resolved = battle.auto_resolve(move_points=1, rng=Rng(1), max_rounds=1)

    # One turn (mp=1): only swap onto the closer stunned hex. Do not assert
    # emptiness of Hex(2, 0): the defender may step there on its own turn.
    assert resolved.unit_at(blocked) is active
    assert resolved.unit_at(source) is stunned_ally
    assert resolved.unit_at(source).stunned is True
    assert resolved.current_hp_at(source) == 0


def test_auto_resolve_does_not_mutate_the_input_battle():
    attacker, defender = Hex(0, 0), Hex(1, 0)
    battle = HexBattle(Battlefield()).deploy(
        Unit(equipment=10), attacker, BattleSide.ATTACKER
    ).deploy(Unit(), defender, BattleSide.DEFENDER)
    units_before = dict(battle.units)
    hp_before = {position: battle.current_hp_at(position) for position in battle.units}

    battle.auto_resolve(
        move_points=1, rng=Rng(4), attacker_morale=100, defender_morale=100
    )

    assert dict(battle.units) == units_before
    assert {
        position: battle.current_hp_at(position) for position in battle.units
    } == hp_before
    assert battle.result() is None


def test_auto_resolve_is_no_op_for_an_already_resolved_battle():
    battle = HexBattle(Battlefield()).deploy(
        Unit(), Hex(0, 0), BattleSide.ATTACKER
    )

    resolved = battle.auto_resolve(move_points=1, rng=Rng(1))

    assert resolved is battle
    assert resolved.result() is BattleResult.ATTACKER_WIN


def test_auto_resolve_side_morale_advantage_decides_symmetric_duel():
    """Per-side morale: +45 beats -45 in a 1v1; swapping sides reverses the winner."""
    attacker, defender = Hex(0, 0), Hex(1, 0)
    battle = (
        HexBattle(Battlefield())
        .deploy(Unit(equipment=2), attacker, BattleSide.ATTACKER)
        .deploy(Unit(equipment=2), defender, BattleSide.DEFENDER)
    )

    high_attacker = battle.auto_resolve(
        move_points=1, rng=Rng(0), attacker_morale=45, defender_morale=-45
    )
    high_defender = battle.auto_resolve(
        move_points=1, rng=Rng(0), attacker_morale=-45, defender_morale=45
    )

    assert high_attacker.result() is BattleResult.ATTACKER_WIN
    assert high_defender.result() is BattleResult.DEFENDER_WIN


@pytest.mark.parametrize("seed", [0, 1, 12, 42, 99])
def test_auto_resolve_equal_side_morale_matches_uniform_morale_semantics(seed):
    """Equal attacker/defender morale matches the former uniform morale=X path.

    Same seed and multi-unit layout → same result and full battle state as
    driving every unit turn with a single morale value X. The reference loop
    tracks unit identity across the round (like production auto_resolve), so a
    body that _swap moved onto a later deployment hex still acts at most once.
    """
    x = 30
    move_points = 1
    battle = (
        HexBattle(Battlefield())
        .deploy(Unit(equipment=4), Hex(0, 0), BattleSide.ATTACKER)
        .deploy(Unit(equipment=2), Hex(2, 0), BattleSide.DEFENDER)
        .deploy(Unit(equipment=3), Hex(0, 1), BattleSide.ATTACKER)
        .deploy(Unit(equipment=1), Hex(2, 1), BattleSide.DEFENDER)
    )

    via_sides = battle.auto_resolve(
        move_points=move_points,
        rng=Rng(seed),
        attacker_morale=x,
        defender_morale=x,
    )

    # Reference: uniform morale X on each turn, unit-identity round order.
    reference = battle
    rng = Rng(seed)
    rounds = 0
    max_rounds = 1000
    while reference.result() is None and rounds < max_rounds:
        turn_order = tuple(
            (position, reference.unit_at(position))
            for position in reference._deployment_order
        )
        acted = set()
        for _position, unit_at_round_start in turn_order:
            if reference.result() is not None:
                break
            if id(unit_at_round_start) in acted:
                continue
            current_position = next(
                (
                    pos
                    for pos, unit in reference.units.items()
                    if unit is unit_at_round_start
                ),
                None,
            )
            if current_position is None:
                continue
            unit = reference.unit_at(current_position)
            if (
                unit is None
                or reference.current_hp_at(current_position) == 0
                or unit.stunned
            ):
                continue
            acted.add(id(unit))
            reference = reference.take_unit_turn(
                current_position, move_points, x, rng
            )
        rounds += 1

    assert via_sides == reference
    assert via_sides.result() is not None


def test_resolve_round_advances_each_unit_once_and_returns_new_state():
    attacker_position, defender_position = Hex(0, 0), Hex(4, 0)
    attacker = Unit()
    defender = Unit()
    battle = (
        HexBattle(Battlefield())
        .deploy(attacker, attacker_position, BattleSide.ATTACKER)
        .deploy(defender, defender_position, BattleSide.DEFENDER)
    )
    resolve_round = getattr(battle, "resolve_round", None)
    assert callable(resolve_round), "HexBattle must expose public resolve_round"

    rounded = resolve_round(move_points=1, rng=Rng(0))

    assert rounded is not battle
    assert rounded.unit_at(Hex(1, 0)) is attacker
    assert rounded.unit_at(Hex(3, 0)) is defender
    assert rounded.result() is None
    assert battle.unit_at(attacker_position) is attacker
    assert battle.unit_at(defender_position) is defender


def test_resolve_round_stops_after_resolution_before_remaining_deployment_positions(
    monkeypatch,
):
    defender = Unit()
    attacker = Unit(equipment=defender.hp)
    support = Unit()
    battle = (
        HexBattle(Battlefield())
        .deploy(attacker, Hex(0, 0), BattleSide.ATTACKER)
        .deploy(defender, Hex(1, 0), BattleSide.DEFENDER)
        .deploy(support, Hex(3, 0), BattleSide.ATTACKER)
    )
    original_take_unit_turn = HexBattle.take_unit_turn
    visited = []

    def record_turn(self, position, move_points, morale, rng):
        visited.append(self.unit_at(position))
        return original_take_unit_turn(self, position, move_points, morale, rng)

    monkeypatch.setattr(HexBattle, "take_unit_turn", record_turn)

    resolved = battle.resolve_round(move_points=1, rng=ControlledRng(True), attacker_morale=100)

    assert resolved.result() is BattleResult.ATTACKER_WIN
    assert visited == [attacker]


def test_resolve_round_composes_to_auto_resolve_and_honors_max_rounds():
    battle = (
        HexBattle(Battlefield())
        .deploy(Unit(equipment=0), Hex(0, 0), BattleSide.ATTACKER)
        .deploy(Unit(equipment=0), Hex(5, 0), BattleSide.DEFENDER)
    )
    resolve_round = getattr(battle, "resolve_round", None)
    assert callable(resolve_round), "HexBattle must expose public resolve_round"
    max_rounds = 2

    stepped = battle
    stepped_rng = Rng(42)
    rounds = 0
    while stepped.result() is None and rounds < max_rounds:
        stepped = stepped.resolve_round(
            move_points=1, rng=stepped_rng, attacker_morale=9,
            defender_morale=-4,
        )
        rounds += 1

    automatic = battle.auto_resolve(
        move_points=1,
        rng=Rng(42),
        attacker_morale=9,
        defender_morale=-4,
        max_rounds=max_rounds,
    )

    assert rounds == max_rounds
    assert stepped == automatic
    assert automatic.result() is None
