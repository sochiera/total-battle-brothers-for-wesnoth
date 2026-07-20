"""Sparse terrain map for a hex battlefield."""

from collections.abc import Mapping

from tbb.hex import Hex
from tbb.terrain import PLAINS, Terrain


class Battlefield:
    """Map selected hexes to terrain, using Plains everywhere else."""

    def __init__(self, terrain: Mapping[Hex, Terrain] | None = None) -> None:
        self._terrain = dict(terrain or {})

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Battlefield):
            return NotImplemented
        return self._terrain == other._terrain

    def terrain_at(self, position: Hex) -> Terrain:
        """Return terrain at ``position`` or Plains when it is not overridden."""
        return self._terrain.get(position, PLAINS)

    def move_cost_at(self, position: Hex) -> int:
        """Return the movement cost for entering ``position``."""
        return self.terrain_at(position).move_cost

    def defense_at(self, position: Hex) -> int:
        """Return the defense modifier at ``position``."""
        return self.terrain_at(position).defense_mod

    def accuracy_at(self, position: Hex) -> int:
        """Return the accuracy modifier at ``position``."""
        return self.terrain_at(position).accuracy_mod
