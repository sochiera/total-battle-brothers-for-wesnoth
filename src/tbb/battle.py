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
    _current_hp: Mapping[Hex, int] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        """Protect deployment data from mutation through the public mapping."""
        units = dict(self.units)
        current_hp = dict(self._current_hp)
        for position, unit in units.items():
            current_hp.setdefault(position, unit.hp)
        object.__setattr__(self, "units", MappingProxyType(units))
        object.__setattr__(self, "_current_hp", MappingProxyType(current_hp))

    def unit_at(self, position: Hex) -> Unit | None:
        """Return the unit at ``position``, if any."""
        return self.units.get(position)

    def is_occupied(self, position: Hex) -> bool:
        """Return whether a unit occupies ``position``."""
        return position in self.units

    def current_hp_at(self, position: Hex) -> int:
        """Return current HP of the unit at ``position``."""
        if not self.is_occupied(position):
            raise ValueError("cannot get HP from an empty hex")
        return self._current_hp[position]

    def deploy(self, unit: Unit, position: Hex) -> "HexBattle":
        """Return a new state with ``unit`` deployed at ``position``."""
        if self.is_occupied(position):
            raise ValueError("cannot deploy a unit on an occupied hex")
        units = dict(self.units)
        units[position] = unit
        current_hp = dict(self._current_hp)
        current_hp[position] = unit.hp
        return HexBattle(self.battlefield, units, current_hp)

    def damage(self, position: Hex, amount: int) -> "HexBattle":
        """Return a new state after dealing non-negative damage at ``position``."""
        if amount < 0:
            raise ValueError("damage cannot be negative")
        if not self.is_occupied(position):
            raise ValueError("cannot damage an empty hex")
        current_hp = dict(self._current_hp)
        current_hp[position] = max(0, current_hp[position] - amount)
        return HexBattle(self.battlefield, self.units, current_hp)

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
        current_hp = dict(self._current_hp)
        current_hp[destination] = current_hp.pop(source)
        return HexBattle(self.battlefield, units, current_hp)
