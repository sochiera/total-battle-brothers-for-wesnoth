"""Tests for immutable axial hex coordinates."""

from dataclasses import FrozenInstanceError

import pytest

from tbb import Hex


def test_hex_has_value_equality_and_hashing():
    first = Hex(1, 2)
    equal = Hex(1, 2)

    assert first == equal
    assert first != Hex(2, 2)
    assert first != Hex(1, 3)
    assert hash(first) == hash(equal)
    assert {first, equal} == {Hex(1, 2)}
    assert {first: "value"}[equal] == "value"


def test_hex_is_immutable():
    hex_coord = Hex(1, 2)

    with pytest.raises(FrozenInstanceError):
        hex_coord.q = 5


@pytest.mark.parametrize("hex_coord", [Hex(0, 0), Hex(1, 2), Hex(-3, 4)])
def test_cube_conversion_round_trip_preserves_hex(hex_coord):
    cube = hex_coord.to_cube()

    assert sum(cube) == 0
    assert Hex.from_cube(*cube) == hex_coord


def test_from_cube_rejects_coordinates_that_do_not_sum_to_zero():
    with pytest.raises(ValueError):
        Hex.from_cube(1, 1, 1)


def test_distance_for_same_hex_neighbors_and_known_longer_paths():
    origin = Hex(0, 0)

    assert origin.distance(origin) == 0
    assert all(origin.distance(neighbor) == 1 for neighbor in origin.neighbors())
    assert origin.distance(Hex(3, 0)) == 3
    assert origin.distance(Hex(2, -3)) == 3


def test_distance_is_symmetric():
    first = Hex(-2, 5)
    second = Hex(4, -1)

    assert first.distance(second) == second.distance(first)


def test_neighbors_are_six_unique_adjacent_hexes_in_stable_order():
    hex_coord = Hex(3, -2)
    first_call = hex_coord.neighbors()

    assert len(first_call) == 6
    assert len(set(first_call)) == 6
    assert all(hex_coord.distance(neighbor) == 1 for neighbor in first_call)
    assert first_call == hex_coord.neighbors()
    assert first_call == (
        Hex(4, -2),
        Hex(4, -3),
        Hex(3, -3),
        Hex(2, -2),
        Hex(2, -1),
        Hex(3, -1),
    )


def test_neighbor_matches_neighbors_for_every_direction():
    hex_coord = Hex(3, -2)

    assert tuple(hex_coord.neighbor(i) for i in range(6)) == hex_coord.neighbors()


@pytest.mark.parametrize("direction", [-1, 6])
def test_neighbor_rejects_out_of_range_direction(direction):
    with pytest.raises(ValueError):
        Hex(0, 0).neighbor(direction)
