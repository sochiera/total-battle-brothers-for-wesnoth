"""Tests for an immutable settlement population pool."""

from dataclasses import FrozenInstanceError

import pytest

from tbb import Settlement


def test_construction_defaults_all_population_to_free():
    settlement = Settlement("A", population=10)

    assert settlement.occupied == 0
    assert settlement.free == 10


def test_construction_with_occupied_population():
    assert Settlement("A", 10, occupied=3).free == 7


@pytest.mark.parametrize(
    "population, occupied", [(-1, 0), (10, -1), (10, 11)]
)
def test_invalid_population_pool_is_rejected(population, occupied):
    with pytest.raises(ValueError):
        Settlement("A", population, occupied)


def test_settlement_is_immutable():
    settlement = Settlement("A", 10)

    with pytest.raises(FrozenInstanceError):
        settlement.occupied = 1


def test_occupy_returns_new_state_without_changing_original():
    original = Settlement("A", 10)

    occupied = original.occupy(4)

    assert occupied.occupied == 4
    assert occupied.free == 6
    assert original == Settlement("A", 10)
    assert occupied is not original


def test_occupy_rejects_more_than_free_population_without_changing_state():
    settlement = Settlement("A", 10)

    with pytest.raises(ValueError):
        settlement.occupy(11)

    assert settlement == Settlement("A", 10)


def test_occupy_rejects_negative_amount():
    with pytest.raises(ValueError):
        Settlement("A", 10).occupy(-1)


def test_release_returns_new_state():
    original = Settlement("A", 10, occupied=5)

    released = original.release(2)

    assert released.occupied == 3
    assert released.free == 7
    assert original == Settlement("A", 10, occupied=5)


def test_release_rejects_more_than_occupied_population():
    with pytest.raises(ValueError):
        Settlement("A", 10, occupied=5).release(6)


def test_release_rejects_negative_amount():
    with pytest.raises(ValueError):
        Settlement("A", 10).release(-1)


def test_occupying_all_free_population_closes_pool():
    settlement = Settlement("A", 10, occupied=3)

    assert settlement.occupy(settlement.free).free == 0


def test_zero_amount_transitions_are_allowed():
    settlement = Settlement("A", 10, occupied=3)

    assert settlement.occupy(0) == settlement
    assert settlement.release(0) == settlement
