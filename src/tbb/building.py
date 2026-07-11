"""Immutable building definitions."""

from dataclasses import dataclass

from tbb.resources import Resources


@dataclass(frozen=True)
class Building:
    """A building type with its fixed population requirement."""

    name: str
    staff: int
    output: Resources = Resources(0, 0)

    def __post_init__(self) -> None:
        if self.staff < 0:
            raise ValueError("staff cannot be negative")


SMITH = Building("Smith", staff=1)
FARM = Building("Farm", staff=1, output=Resources(wheat=3, gold=0))
MARKET = Building("Market", staff=1, output=Resources(wheat=0, gold=2))
