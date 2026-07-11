"""Immutable deployment state for a hex battle."""

from collections.abc import Mapping
from dataclasses import dataclass, field
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
