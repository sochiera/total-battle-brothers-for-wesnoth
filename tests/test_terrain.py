"""Tests for immutable terrain definitions."""

from dataclasses import FrozenInstanceError

import pytest

from tbb.terrain import FOREST, HILLS, PLAINS, Terrain


def test_terrain_has_expected_fields():
    terrain = Terrain("Marsh", move_cost=3, defense_mod=-2, accuracy_mod=-1)

    assert terrain.name == "Marsh"
    assert terrain.move_cost == 3
    assert terrain.defense_mod == -2
    assert terrain.accuracy_mod == -1


def test_terrain_is_immutable():
    terrain = Terrain("Marsh", move_cost=3, defense_mod=-2, accuracy_mod=-1)

    with pytest.raises(FrozenInstanceError):
        terrain.move_cost = 1


@pytest.mark.parametrize("move_cost", [0, -1])
def test_terrain_rejects_non_positive_move_cost(move_cost):
    with pytest.raises(ValueError):
        Terrain("Impassable", move_cost, defense_mod=0, accuracy_mod=0)


def test_negative_defense_and_accuracy_modifiers_are_allowed():
    terrain = Terrain("Marsh", move_cost=1, defense_mod=-2, accuracy_mod=-3)

    assert terrain.defense_mod == -2
    assert terrain.accuracy_mod == -3


def test_starting_terrain_catalog_has_exact_values():
    assert PLAINS == Terrain("Plains", 1, 0, 0)
    assert FOREST == Terrain("Forest", 2, 2, -1)
    assert HILLS == Terrain("Hills", 2, 1, 1)
