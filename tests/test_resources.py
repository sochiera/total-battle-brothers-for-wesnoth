"""Tests for immutable wheat and gold resource values."""

from dataclasses import FrozenInstanceError

import pytest

from tbb import Resources


def test_construction_and_value_equality():
    assert Resources(3, 5) == Resources(3, 5)
    assert Resources(3, 5) != Resources(4, 5)
    assert Resources(3, 5) != Resources(3, 4)


def test_resources_are_immutable():
    resources = Resources(3, 5)

    with pytest.raises(FrozenInstanceError):
        resources.wheat = 4


@pytest.mark.parametrize("wheat, gold", [(-1, 0), (0, -2)])
def test_negative_resources_are_rejected(wheat, gold):
    with pytest.raises(ValueError):
        Resources(wheat, gold)


def test_add_returns_sum_without_changing_operands():
    first = Resources(1, 2)
    second = Resources(3, 4)

    result = first.add(second)

    assert result == Resources(4, 6)
    assert result is not first
    assert result is not second
    assert first == Resources(1, 2)
    assert second == Resources(3, 4)


def test_subtract_returns_difference():
    assert Resources(5, 5).subtract(Resources(2, 1)) == Resources(3, 4)


@pytest.mark.parametrize("available, cost", [
    (Resources(1, 5), Resources(2, 1)),
    (Resources(5, 1), Resources(1, 2)),
])
def test_subtract_rejects_insufficient_resources(available, cost):
    with pytest.raises(ValueError):
        available.subtract(cost)


def test_subtract_can_explicitly_clamp_shortage_to_zero():
    assert Resources(1, 5).subtract(
        Resources(3, 2), allow_negative=True
    ) == Resources(0, 3)


def test_can_afford_checks_both_resources_without_raising():
    resources = Resources(3, 5)

    assert resources.can_afford(Resources(3, 5)) is True
    assert resources.can_afford(Resources(4, 5)) is False
    assert resources.can_afford(Resources(3, 6)) is False
