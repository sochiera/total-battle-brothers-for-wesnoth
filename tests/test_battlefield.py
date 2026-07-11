"""Tests for sparse terrain on the battle hex grid."""

from tbb.battlefield import Battlefield
from tbb.hex import Hex
from tbb.terrain import FOREST, PLAINS


def test_default_battlefield_uses_plains_and_its_modifiers():
    battlefield = Battlefield()
    position = Hex(8, -3)

    assert battlefield.terrain_at(position) == PLAINS
    assert battlefield.move_cost_at(position) == 1
    assert battlefield.defense_at(position) == 0
    assert battlefield.accuracy_at(position) == 0


def test_override_affects_only_the_selected_hex():
    forest = Hex(0, 0)
    neighboring_plains = Hex(1, 0)
    battlefield = Battlefield({forest: FOREST})

    assert battlefield.terrain_at(forest) == FOREST
    assert battlefield.move_cost_at(forest) == 2
    assert battlefield.defense_at(forest) == 2
    assert battlefield.accuracy_at(forest) == -1
    assert battlefield.terrain_at(neighboring_plains) == PLAINS


def test_same_input_produces_equal_queries_without_mutating_input():
    position = Hex(-2, 4)
    overrides = {position: FOREST}
    first = Battlefield(overrides)
    second = Battlefield(overrides)

    overrides.clear()

    assert first.terrain_at(position) == second.terrain_at(position) == FOREST
