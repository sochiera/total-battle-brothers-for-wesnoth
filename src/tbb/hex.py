"""Immutable axial coordinates for the battle hex grid."""

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class Hex:
    """Represent one hex using axial ``q, r`` coordinates."""

    q: int
    r: int

    _DIRECTIONS: ClassVar[tuple[tuple[int, int], ...]] = (
        (1, 0),
        (1, -1),
        (0, -1),
        (-1, 0),
        (-1, 1),
        (0, 1),
    )

    def to_cube(self) -> tuple[int, int, int]:
        """Return the equivalent cube coordinates ``(x, y, z)``."""
        return self.q, -self.q - self.r, self.r

    @classmethod
    def from_cube(cls, x: int, y: int, z: int) -> "Hex":
        """Create an axial coordinate from valid cube coordinates."""
        if x + y + z != 0:
            raise ValueError("cube coordinates must sum to zero")
        return cls(x, z)

    def distance(self, other: "Hex") -> int:
        """Return the number of hex-grid steps to ``other``."""
        x1, y1, z1 = self.to_cube()
        x2, y2, z2 = other.to_cube()
        return (abs(x1 - x2) + abs(y1 - y2) + abs(z1 - z2)) // 2

    def neighbors(self) -> tuple["Hex", ...]:
        """Return all adjacent coordinates in deterministic direction order."""
        return tuple(self.neighbor(direction) for direction in range(6))

    def neighbor(self, direction: int) -> "Hex":
        """Return the adjacent coordinate in direction 0 through 5."""
        if direction < 0 or direction >= len(self._DIRECTIONS):
            raise ValueError("direction must be between 0 and 5")
        dq, dr = self._DIRECTIONS[direction]
        return Hex(self.q + dq, self.r + dr)
