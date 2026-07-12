"""Immutable strategic party composition."""

from dataclasses import dataclass
from typing import Iterable

from tbb.unit import Unit


@dataclass(frozen=True)
class Party:
    """A required hero and up to twelve subordinate units."""

    hero: Unit
    units: tuple[Unit, ...] = ()
    owner_id: str | None = None

    def __init__(
        self,
        hero: Unit,
        units: Iterable[Unit] = (),
        owner_id: str | None = None,
    ) -> None:
        if not isinstance(hero, Unit):
            raise TypeError("party hero must be a Unit")
        if owner_id is not None and not isinstance(owner_id, str):
            raise TypeError("party owner_id must be text or None")
        if owner_id == "":
            raise ValueError("party owner_id cannot be empty")

        copied_units = tuple(units)
        if len(copied_units) > 12:
            raise ValueError("party cannot have more than twelve subordinates")
        if any(not isinstance(unit, Unit) for unit in copied_units):
            raise TypeError("party subordinates must be Units")

        object.__setattr__(self, "hero", hero)
        object.__setattr__(self, "units", copied_units)
        object.__setattr__(self, "owner_id", owner_id)

    @classmethod
    def reconstruct(
        cls, original: "Party", survivors: Iterable[Unit]
    ) -> "Party":
        """Create a new party from one side's survivors in deployment order."""
        ordered_survivors = tuple(survivors)
        if not ordered_survivors:
            raise ValueError("cannot reconstruct a party without a surviving hero")
        return cls(
            hero=ordered_survivors[0],
            units=ordered_survivors[1:],
            owner_id=original.owner_id,
        )
