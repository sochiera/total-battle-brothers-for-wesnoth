"""Tests for units built from three independent quality pillars."""

import random
from dataclasses import FrozenInstanceError

import pytest

from tbb import BRUISE, MAIMED, Unit, investment_for_level, pillar_level


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


def test_training_progress_defaults_to_zero_and_is_immutable():
    unit = Unit()

    assert unit.training_progress == 0
    with pytest.raises(FrozenInstanceError):
        unit.training_progress = 1


def test_train_uses_triangular_progress_and_is_a_pure_rng_free_transition():
    default_unit = Unit()
    assert default_unit.training_progress == 0
    with pytest.raises(FrozenInstanceError):
        default_unit.training_progress = 1
    with pytest.raises(ValueError):
        Unit(training=2, training_progress=-1)
    with pytest.raises(ValueError):
        Unit(training=2, training_progress=3)

    original = Unit(
        training=2,
        training_progress=1,
        equipment=4,
        experience=5,
        ranged_range=3,
        wounds=(BRUISE,),
        stunned=True,
    )

    assert original.train(0) == original
    with pytest.raises(ValueError):
        original.train(-1)

    rng_state = random.getstate()
    months = 2
    total = (
        investment_for_level(original.training)
        + original.training_progress
        + months
    )

    trained = original.train(months)

    expected_training = pillar_level(total)
    assert trained.training == expected_training
    assert (
        trained.training_progress
        == total - investment_for_level(expected_training)
    )
    assert (
        trained.equipment,
        trained.experience,
        trained.ranged_range,
        trained.wounds,
        trained.stunned,
    ) == (4, 5, 3, (BRUISE,), True)
    assert (trained.hp, trained.accuracy) == (13, 7)
    assert original == Unit(
        training=2,
        training_progress=1,
        equipment=4,
        experience=5,
        ranged_range=3,
        wounds=(BRUISE,),
        stunned=True,
    )
    assert random.getstate() == rng_state
    assert original.train(months) == trained
    assert Unit().train(1) == Unit(training=1)
    assert Unit().train(2) == Unit(training=1, training_progress=1)
    assert Unit().train(3) == Unit(training=2)


def test_ranged_range_defaults_to_zero_and_accepts_two_or_more():
    assert Unit().ranged_range == 0
    assert Unit(ranged_range=2).ranged_range == 2
    assert Unit(ranged_range=5).ranged_range == 5


@pytest.mark.parametrize("ranged_range", [-1, 1])
def test_invalid_ranged_range_is_rejected(ranged_range):
    with pytest.raises(ValueError):
        Unit(ranged_range=ranged_range)


def test_ranged_range_is_immutable():
    unit = Unit(ranged_range=2)

    with pytest.raises(FrozenInstanceError):
        unit.ranged_range = 3


def test_unit_without_wounds_keeps_existing_stats():
    unit = Unit(training=2, equipment=3, experience=4)

    assert unit.wounds == ()
    assert (unit.hp, unit.accuracy, unit.damage, unit.defense) == (12, 6, 3, 7)


def test_one_wound_reduces_only_accuracy_and_defense():
    unit = Unit(training=3, equipment=4, experience=2, wounds=(BRUISE,))

    assert (unit.hp, unit.accuracy, unit.damage, unit.defense) == (13, 4, 4, 5)


def test_multiple_wounds_stack_with_accuracy_and_defense_floored_at_zero():
    unit = Unit(training=1, equipment=1, wounds=(BRUISE, MAIMED))

    assert (unit.hp, unit.accuracy, unit.damage, unit.defense) == (11, 0, 1, 0)


def test_unit_copies_input_wounds_to_an_immutable_tuple():
    wounds = [BRUISE]
    unit = Unit(wounds=wounds)

    wounds.append(MAIMED)

    assert unit.wounds == (BRUISE,)
    assert isinstance(unit.wounds, tuple)


def test_stunned_defaults_to_false_and_is_immutable():
    unit = Unit()

    assert unit.stunned is False
    with pytest.raises(FrozenInstanceError):
        unit.stunned = True
