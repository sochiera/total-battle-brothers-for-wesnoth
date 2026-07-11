"""Immutable strategic party composition."""

from dataclasses import dataclass
from typing import Iterable

from tbb.unit import Unit


@dataclass(frozen=True)
class Party:
    """A required hero and up to twelve subordinate units."""

    hero: Unit
    units: tuple[Unit, ...] = ()

    def __init__(self, hero: Unit, units: Iterable[Unit] = ()) -> None:
        if not isinstance(hero, Unit):
            raise TypeError("party hero must be a Unit")

        copied_units = tuple(units)
        if len(copied_units) > 12:
            raise ValueError("party cannot have more than twelve subordinates")
        if any(not isinstance(unit, Unit) for unit in copied_units):
            raise TypeError("party subordinates must be Units")

        object.__setattr__(self, "hero", hero)
        object.__setattr__(self, "units", copied_units)
