"""Pointy-top hex geometry for battle field rendering (stdlib only)."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tbb.hex import Hex


def hex_to_pixel(hex: Hex, size: float) -> tuple[float, float]:
    """Return the pixel center of an axial hex in pointy-top orientation.

    Formulas follow the standard axial layout (q horizontal, r down-right):
    ``x = size * (√3 * q + √3/2 * r)``, ``y = size * (3/2 * r)``.
    """
    q = hex.q
    r = hex.r
    x = size * (math.sqrt(3.0) * q + math.sqrt(3.0) / 2.0 * r)
    y = size * (3.0 / 2.0 * r)
    return (x, y)


def hex_corners(hex: Hex, size: float) -> tuple[tuple[float, float], ...]:
    """Return the six corner points of a pointy-top hex (outer radius = size).

    Corners lie on a circle of radius ``size`` around ``hex_to_pixel(hex, size)``,
    at angles ``60° * i - 30°`` (pointy vertex on top).
    """
    cx, cy = hex_to_pixel(hex, size)
    corners: list[tuple[float, float]] = []
    for i in range(6):
        angle_rad = math.radians(60 * i - 30)
        corners.append((cx + size * math.cos(angle_rad), cy + size * math.sin(angle_rad)))
    return tuple(corners)
