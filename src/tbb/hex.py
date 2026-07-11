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

    def line_to(self, other: "Hex") -> tuple["Hex", ...]:
        """Return the deterministic, endpoint-inclusive line to ``other``."""
        if self == other:
            return (self,)

        if (self.q, self.r) > (other.q, other.r):
            return tuple(reversed(other.line_to(self)))

        distance = self.distance(other)
        start = self.to_cube()
        end = other.to_cube()

        line = []
        for step in range(distance + 1):
            numerators = tuple(
                coordinate * distance + (target - coordinate) * step
                for coordinate, target in zip(start, end)
            )
            line.append(self._from_rational_cube(*numerators, distance))
        return tuple(line)

    @classmethod
    def _from_rational_cube(
        cls, x: int, y: int, z: int, denominator: int
    ) -> "Hex":
        """Round exact rational cube coordinates, with a stable boundary tie."""
        rounded_x = cls._round_ratio(x, denominator, tie_up=True)
        rounded_y = cls._round_ratio(y, denominator, tie_up=True)
        rounded_z = cls._round_ratio(z, denominator, tie_up=False)
        x_error = abs(rounded_x * denominator - x)
        y_error = abs(rounded_y * denominator - y)
        z_error = abs(rounded_z * denominator - z)

        if x_error > y_error and x_error > z_error:
            rounded_x = -rounded_y - rounded_z
        elif y_error > z_error:
            rounded_y = -rounded_x - rounded_z
        else:
            rounded_z = -rounded_x - rounded_y
        return cls.from_cube(rounded_x, rounded_y, rounded_z)

    @staticmethod
    def _round_ratio(numerator: int, denominator: int, *, tie_up: bool) -> int:
        """Round an exact ratio to nearest, resolving halves without floats."""
        lower, remainder = divmod(numerator, denominator)
        doubled_remainder = 2 * remainder
        if doubled_remainder < denominator:
            return lower
        if doubled_remainder > denominator:
            return lower + 1
        return lower + int(tie_up)

    def neighbors(self) -> tuple["Hex", ...]:
        """Return all adjacent coordinates in deterministic direction order."""
        return tuple(self.neighbor(direction) for direction in range(6))

    def neighbor(self, direction: int) -> "Hex":
        """Return the adjacent coordinate in direction 0 through 5."""
        if direction < 0 or direction >= len(self._DIRECTIONS):
            raise ValueError("direction must be between 0 and 5")
        dq, dr = self._DIRECTIONS[direction]
        return Hex(self.q + dq, self.r + dr)
