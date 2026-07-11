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
