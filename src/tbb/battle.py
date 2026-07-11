"""Immutable deployment state for a hex battle."""

from collections.abc import Mapping
from dataclasses import dataclass, field
import heapq
from types import MappingProxyType

from tbb.battlefield import Battlefield
from tbb.hex import Hex
from tbb.unit import Unit


@dataclass(frozen=True)
class HexBattle:
    """Combine battlefield terrain with units deployed on hexes."""

    battlefield: Battlefield
    units: Mapping[Hex, Unit] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Protect deployment data from mutation through the public mapping."""
        object.__setattr__(self, "units", MappingProxyType(dict(self.units)))

    def unit_at(self, position: Hex) -> Unit | None:
        """Return the unit at ``position``, if any."""
        return self.units.get(position)

    def is_occupied(self, position: Hex) -> bool:
        """Return whether a unit occupies ``position``."""
        return position in self.units

    def deploy(self, unit: Unit, position: Hex) -> "HexBattle":
        """Return a new state with ``unit`` deployed at ``position``."""
        if self.is_occupied(position):
            raise ValueError("cannot deploy a unit on an occupied hex")
        units = dict(self.units)
        units[position] = unit
        return HexBattle(self.battlefield, units)

    def reachable(self, source: Hex, move_points: int) -> set[Hex]:
        """Return unoccupied hexes reachable within ``move_points``."""
        best_cost = {source: 0}
        frontier = [(0, source.q, source.r)]
        reachable: set[Hex] = set()

        while frontier:
            cost, q, r = heapq.heappop(frontier)
            position = Hex(q, r)
            if cost != best_cost[position]:
                continue

            for neighbor in position.neighbors():
                if self.is_occupied(neighbor):
                    continue
                next_cost = cost + self.battlefield.move_cost_at(neighbor)
                if next_cost > move_points or next_cost >= best_cost.get(
                    neighbor, next_cost + 1
                ):
                    continue
                best_cost[neighbor] = next_cost
                reachable.add(neighbor)
                heapq.heappush(frontier, (next_cost, neighbor.q, neighbor.r))

        return reachable

    def move(
        self, source: Hex, destination: Hex, move_points: int
    ) -> "HexBattle":
        """Return a new state with the source unit moved to a reachable hex."""
        unit = self.unit_at(source)
        if unit is None:
            raise ValueError("cannot move from an empty hex")
        if self.is_occupied(destination):
            raise ValueError("cannot move to an occupied hex")
        if destination not in self.reachable(source, move_points):
            raise ValueError("destination is outside the movement budget")

        units = dict(self.units)
        del units[source]
        units[destination] = unit
        return HexBattle(self.battlefield, units)
