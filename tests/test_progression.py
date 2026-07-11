"""Tests for diminishing-return pillar progression."""

import pytest

from tbb import investment_for_level, pillar_level


@pytest.mark.parametrize(
    "investment, expected_level",
    [(0, 0), (1, 1), (2, 1), (3, 2), (5, 2), (6, 3), (10, 4)],
)
def test_pillar_level_at_known_triangular_thresholds(investment, expected_level):
    assert pillar_level(investment) == expected_level


def test_pillar_level_is_monotonically_non_decreasing():
    levels = [pillar_level(investment) for investment in range(101)]

    assert levels == sorted(levels)


def test_cost_of_each_next_level_increases_with_the_level():
    for level in range(100):
        assert investment_for_level(level + 1) - investment_for_level(level) == level + 1


def test_level_and_investment_are_consistent_at_thresholds():
    for level in range(101):
        threshold = investment_for_level(level)

        assert pillar_level(threshold) == level
        if level >= 1:
            assert pillar_level(threshold - 1) == level - 1


@pytest.mark.parametrize(
    "function, value",
    [(pillar_level, -1), (investment_for_level, -1)],
)
def test_negative_inputs_are_rejected(function, value):
    with pytest.raises(ValueError):
        function(value)
