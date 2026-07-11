"""Tests for units built from three independent quality pillars."""

from dataclasses import FrozenInstanceError

import pytest

from tbb import Unit


def test_unit_defaults_to_zero_pillars_and_base_stats():
    unit = Unit()

    assert (unit.training, unit.equipment, unit.experience) == (0, 0, 0)
    assert (unit.hp, unit.accuracy, unit.damage, unit.defense) == (10, 0, 0, 0)


def test_unit_stats_are_derived_from_all_pillars():
    unit = Unit(training=2, equipment=3, experience=4)

    assert unit.hp == 12
    assert unit.accuracy == 6
    assert unit.damage == 3
    assert unit.defense == 7


@pytest.mark.parametrize(
    "pillars, expected_stats",
    [
        ({"training": 2}, (12, 2, 0, 0)),
        ({"equipment": 3}, (10, 0, 3, 3)),
        ({"experience": 4}, (10, 4, 0, 4)),
    ],
)
def test_each_pillar_changes_only_its_stats(pillars, expected_stats):
    unit = Unit(**pillars)

    assert (unit.hp, unit.accuracy, unit.damage, unit.defense) == expected_stats


@pytest.mark.parametrize(
    "pillars",
    [
        {"training": -1},
        {"equipment": -1},
        {"experience": -1},
    ],
)
def test_negative_pillars_are_rejected(pillars):
    with pytest.raises(ValueError):
        Unit(**pillars)


def test_unit_is_immutable():
    unit = Unit()

    with pytest.raises(FrozenInstanceError):
        unit.training = 1
