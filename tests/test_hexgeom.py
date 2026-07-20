"""Tests for pointy-top hex geometry (tbbui presentation layer)."""

from __future__ import annotations

import math

import pytest

from tbb.hex import Hex
from tbbui.hexgeom import hex_corners, hex_to_pixel


def test_hex_corners_are_six_at_size_from_center():
    """hex_corners returns 6 corners, each ~size from hex_to_pixel center."""
    hex_coord = Hex(2, -1)
    size = 10.0
    center = hex_to_pixel(hex_coord, size)
    corners = hex_corners(hex_coord, size)

    assert isinstance(corners, tuple)
    assert len(corners) == 6
    assert all(isinstance(c, tuple) and len(c) == 2 for c in corners)

    cx, cy = center
    for x, y in corners:
        dist = math.hypot(x - cx, y - cy)
        assert dist == pytest.approx(size)


def test_six_neighbors_are_equidistant_in_pixels():
    """Pixel centers of all six neighbors share one Euclidean distance from origin."""
    origin = Hex(1, -2)
    size = 12.0
    ox, oy = hex_to_pixel(origin, size)
    neighbors = origin.neighbors()

    assert len(neighbors) == 6
    distances = [
        math.hypot(px - ox, py - oy)
        for px, py in (hex_to_pixel(n, size) for n in neighbors)
    ]
    expected = distances[0]
    assert expected > 0
    for dist in distances:
        assert dist == pytest.approx(expected)


def test_hexgeom_is_deterministic_and_does_not_mutate_args():
    """Same args yield same values; Hex argument is not mutated."""
    hex_coord = Hex(3, -1)
    size = 8.5
    q_before, r_before = hex_coord.q, hex_coord.r

    first_pixel = hex_to_pixel(hex_coord, size)
    second_pixel = hex_to_pixel(hex_coord, size)
    first_corners = hex_corners(hex_coord, size)
    second_corners = hex_corners(hex_coord, size)

    assert first_pixel == second_pixel
    assert first_corners == second_corners
    assert hex_coord.q == q_before and hex_coord.r == r_before
    assert hex_coord == Hex(3, -1)
