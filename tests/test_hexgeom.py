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
